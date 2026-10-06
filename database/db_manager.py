"""
DBManager — the ONLY place raw SQL lives in Momentum.

Responsibilities:
- connection handling (PRAGMA foreign_keys = ON)
- schema creation on first run
- parameterized CRUD for every table
- analytics/streak helpers queried in one place
- graceful error handling: sqlite3 errors are logged internally and surfaced
  as DatabaseError (or returned as safe defaults) so no traceback reaches the UI
"""
from __future__ import annotations

import sqlite3
import os
from datetime import date, timedelta
from typing import Optional

# Import as absolute paths from the momentum/ project root (main.py sets sys.path),
# falling back to package-relative imports for robustness.
try:
    from models import Track, Habit, DailyLog, Task, Plan
    from utils.streak_calculator import (
        compute_current_streak,
        compute_best_streak,
        compute_completion_percentage,
    )
except ImportError:  # pragma: no cover
    from ..models import Track, Habit, DailyLog, Task, Plan
    from ..utils.streak_calculator import (
        compute_current_streak,
        compute_best_streak,
        compute_completion_percentage,
    )


class DatabaseError(Exception):
    """Clean, user-presentable database exception (never shown as a traceback)."""

    def __init__(self, friendly: str, technical: str = ""):
        self.friendly = friendly
        self.technical = technical
        super().__init__(friendly)


def _log_technical(message: str) -> None:
    """Internal log only — the end user never sees raw sqlite3 errors."""
    try:
        print(f"[Momentum:DB] {message}")
    except Exception:
        pass


class DBManager:
    """All SQL for the Momentum app. Single shared instance passed into UI frames."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._ensure_db_file()
        self.connect()
        self.initialize_schema()

    # ------------------------------------------------------------------ #
    # Connection / schema
    # ------------------------------------------------------------------ #
    def _ensure_db_file(self) -> None:
        """Create the .db file (and its folder) automatically on first run."""
        try:
            folder = os.path.dirname(os.path.abspath(self.db_path))
            if folder:
                os.makedirs(folder, exist_ok=True)
        except OSError as exc:
            _log_technical(f"Could not create database folder: {exc}")
            raise DatabaseError(
                "Could not create the folder for your data file. Check folder permissions."
            ) from exc

    def connect(self) -> sqlite3.Connection:
        if self.conn is not None:
            return self.conn
        try:
            self.conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys = ON")
            return self.conn
        except sqlite3.Error as exc:
            _log_technical(f"connect failed: {exc}")
            self.conn = None
            raise DatabaseError(
                "Could not access your data file. It may be open elsewhere.",
                str(exc),
            ) from exc

    def _cursor(self) -> sqlite3.Cursor:
        self.connect()
        assert self.conn is not None
        return self.conn.cursor()

    def _commit(self) -> None:
        try:
            if self.conn is not None:
                self.conn.commit()
        except sqlite3.Error as exc:
            _log_technical(f"commit failed: {exc}")
            raise DatabaseError("Could not save your changes.", str(exc)) from exc

    def initialize_schema(self) -> None:
        """Create every table if it does not exist. Safe to call on every launch."""
        ddl = """
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            color_hex TEXT NOT NULL,
            icon TEXT,
            created_date TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id INTEGER,
            name TEXT NOT NULL,
            icon TEXT,
            target_frequency INTEGER DEFAULT 7,
            created_date TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            log_date TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            value REAL,
            UNIQUE(habit_id, log_date),
            FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            due_date TEXT NOT NULL,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Pending',
            linked_track_id INTEGER,
            carried_over INTEGER DEFAULT 0,
            created_date TEXT NOT NULL,
            FOREIGN KEY (linked_track_id) REFERENCES tracks(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            weekly_target INTEGER,
            notes TEXT,
            FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_logs_habit_date ON daily_logs(habit_id, log_date);
        CREATE INDEX IF NOT EXISTS idx_logs_date ON daily_logs(log_date);
        CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_date, status);
        """
        try:
            cur = self._cursor()
            cur.executescript(ddl)
            self._commit()
        except sqlite3.Error as exc:
            _log_technical(f"schema init failed: {exc}")
            raise DatabaseError("Could not prepare your database. It may be corrupted.", str(exc)) from exc

    def close(self) -> None:
        """Cleanly close the SQLite connection (called on app exit)."""
        try:
            if self.conn is not None:
                self.conn.commit()
                self.conn.close()
        except sqlite3.Error as exc:
            _log_technical(f"close failed: {exc}")
        finally:
            self.conn = None

    # ------------------------------------------------------------------ #
    # Tracks
    # ------------------------------------------------------------------ #
    def create_track(self, name: str, category: str = "", color_hex: str = "#7C5CFC",
                     icon: str = "📁") -> int:
        sql = ("INSERT INTO tracks (name, category, color_hex, icon, created_date) "
               "VALUES (?, ?, ?, ?, ?)")
        try:
            cur = self._cursor()
            cur.execute(sql, (name, category, color_hex, icon, date.today().isoformat()))
            self._commit()
            return int(cur.lastrowid or 0)
        except sqlite3.Error as exc:
            _log_technical(f"create_track: {exc}")
            raise DatabaseError("Could not save the track. Check the name and try again.", str(exc)) from exc

    def get_all_tracks(self) -> list[Track]:
        sql = ("SELECT t.*, "
               "(SELECT COUNT(*) FROM habits h WHERE h.track_id = t.id AND h.is_active = 1) AS habit_count "
               "FROM tracks t ORDER BY t.name COLLATE NOCASE")
        try:
            rows = self._cursor().execute(sql).fetchall()
            return [Track(
                id=r["id"], name=r["name"], category=r["category"] or "",
                color_hex=r["color_hex"], icon=r["icon"] or "📁",
                created_date=r["created_date"], habit_count=r["habit_count"],
            ) for r in rows]
        except sqlite3.Error as exc:
            _log_technical(f"get_all_tracks: {exc}")
            return []

    def get_track(self, track_id: int) -> Optional[Track]:
        try:
            row = self._cursor().execute(
                "SELECT * FROM tracks WHERE id = ?", (track_id,)).fetchone()
            if row is None:
                return None
            return Track(id=row["id"], name=row["name"], category=row["category"] or "",
                         color_hex=row["color_hex"], icon=row["icon"] or "📁",
                         created_date=row["created_date"])
        except sqlite3.Error as exc:
            _log_technical(f"get_track: {exc}")
            return None

    def delete_track(self, track_id: int) -> None:
        """
        Deletes the track.
        - Its habits are SOFT-deactivated first (history preserved, no clutter)
        - plans cascade-delete; tasks unlink (FK SET NULL) per schema
        """
        try:
            cur = self._cursor()
            # Soft-delete the track's habits so daily_logs stay intact (schema:
            # habits.track_id → ON DELETE SET NULL handles the unlink)
            cur.execute("UPDATE habits SET is_active = 0 WHERE track_id = ?", (track_id,))
            cur.execute("DELETE FROM tracks WHERE id = ?", (track_id,))
            self._commit()
        except sqlite3.Error as exc:
            _log_technical(f"delete_track: {exc}")
            raise DatabaseError("Could not delete the track. It may still be in use.", str(exc)) from exc

    def update_track(self, track_id: int, **fields) -> None:
        allowed = {"name", "category", "color_hex", "icon"}
        updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
        if not updates:
            return
        try:
            cols = ", ".join(f"{k} = ?" for k in updates)
            self._cursor().execute(f"UPDATE tracks SET {cols} WHERE id = ?",
                                   (*updates.values(), track_id))
            self._commit()
        except sqlite3.Error as exc:
            _log_technical(f"update_track: {exc}")
            raise DatabaseError("Could not update the track.", str(exc)) from exc

    def track_exists(self, name: str) -> bool:
        try:
            row = self._cursor().execute(
                "SELECT 1 FROM tracks WHERE LOWER(name) = LOWER(?) LIMIT 1",
                (name.strip(),)).fetchone()
            return row is not None
        except sqlite3.Error:
            return False

    # ------------------------------------------------------------------ #
    # Habits (soft delete via is_active)
    # ------------------------------------------------------------------ #
    def create_habit(self, track_id: Optional[int], name: str, icon: str = "✅",
                     target_frequency: int = 7) -> int:
        try:
            freq = max(1, min(7, int(target_frequency)))
        except (TypeError, ValueError):
            freq = 7
        sql = ("INSERT INTO habits (track_id, name, icon, target_frequency, created_date, is_active) "
               "VALUES (?, ?, ?, ?, ?, 1)")
        try:
            cur = self._cursor()
            cur.execute(sql, (track_id, name, icon, freq, date.today().isoformat()))
            self._commit()
            return int(cur.lastrowid or 0)
        except sqlite3.IntegrityError as exc:
            _log_technical(f"create_habit integrity: {exc}")
            raise DatabaseError("That habit already exists here. Choose a different name.", str(exc)) from exc
        except sqlite3.Error as exc:
            _log_technical(f"create_habit: {exc}")
            raise DatabaseError("Could not save the habit.", str(exc)) from exc

    def _habit_from_row(self, r: sqlite3.Row) -> Habit:
        keys = r.keys()
        return Habit(
            id=r["id"], track_id=r["track_id"],
            name=r["name"], icon=r["icon"] or "✅",
            target_frequency=r["target_frequency"] or 7,
            created_date=r["created_date"], is_active=r["is_active"],
            track_name=(r["track_name"] if "track_name" in keys else "") or "",
            track_color=(r["track_color"] if "track_color" in keys else "") or "#7C5CFC",
        )

    def get_active_habits(self) -> list[Habit]:
        sql = ("SELECT h.*, t.name AS track_name, t.color_hex AS track_color "
               "FROM habits h LEFT JOIN tracks t ON t.id = h.track_id "
               "WHERE h.is_active = 1 ORDER BY h.name COLLATE NOCASE")
        try:
            rows = self._cursor().execute(sql).fetchall()
            return [self._habit_from_row(r) for r in rows]
        except sqlite3.Error as exc:
            _log_technical(f"get_active_habits: {exc}")
            return []

    def get_all_habits(self, include_inactive: bool = False) -> list[Habit]:
        sql = ("SELECT h.*, t.name AS track_name, t.color_hex AS track_color "
               "FROM habits h LEFT JOIN tracks t ON t.id = h.track_id")
        if not include_inactive:
            sql += " WHERE h.is_active = 1"
        sql += " ORDER BY h.name COLLATE NOCASE"
        try:
            rows = self._cursor().execute(sql).fetchall()
            return [self._habit_from_row(r) for r in rows]
        except sqlite3.Error as exc:
            _log_technical(f"get_all_habits: {exc}")
            return []

    def get_habits_by_track(self, track_id: int, active_only: bool = True) -> list[Habit]:
        sql = ("SELECT h.*, t.name AS track_name, t.color_hex AS track_color "
               "FROM habits h LEFT JOIN tracks t ON t.id = h.track_id WHERE h.track_id = ?")
        if active_only:
            sql += " AND h.is_active = 1"
        sql += " ORDER BY h.name COLLATE NOCASE"
        try:
            rows = self._cursor().execute(sql, (track_id,)).fetchall()
            return [self._habit_from_row(r) for r in rows]
        except sqlite3.Error as exc:
            _log_technical(f"get_habits_by_track: {exc}")
            return []

    def get_habit(self, habit_id: int) -> Optional[Habit]:
        sql = ("SELECT h.*, t.name AS track_name, t.color_hex AS track_color "
               "FROM habits h LEFT JOIN tracks t ON t.id = h.track_id WHERE h.id = ?")
        try:
            row = self._cursor().execute(sql, (habit_id,)).fetchone()
            return self._habit_from_row(row) if row else None
        except sqlite3.Error as exc:
            _log_technical(f"get_habit: {exc}")
            return None

    def update_habit(self, habit_id: int, **fields) -> None:
        allowed = {"name", "icon", "target_frequency", "track_id", "is_active", "created_date"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if "target_frequency" in updates:
            try:
                updates["target_frequency"] = max(1, min(7, int(updates["target_frequency"])))
            except (TypeError, ValueError):
                updates.pop("target_frequency")
        if not updates:
            return
        try:
            cols = ", ".join(f"{k} = ?" for k in updates)
            self._cursor().execute(f"UPDATE habits SET {cols} WHERE id = ?",
                                   (*updates.values(), habit_id))
            self._commit()
        except sqlite3.IntegrityError as exc:
            _log_technical(f"update_habit integrity: {exc}")
            raise DatabaseError("That habit name is already used in this track.", str(exc)) from exc
        except sqlite3.Error as exc:
            _log_technical(f"update_habit: {exc}")
            raise DatabaseError("Could not update the habit.", str(exc)) from exc

    def deactivate_habit(self, habit_id: int) -> None:
        """Soft delete — keeps daily_logs for analytics/streak history."""
        self.update_habit(habit_id, is_active=0)

    def reactivate_habit(self, habit_id: int) -> None:
        self.update_habit(habit_id, is_active=1)

    def habit_name_in_track_exists(self, name: str, track_id: Optional[int],
                                   exclude_habit_id: Optional[int] = None) -> bool:
        """Duplicate habit check within the same track (case-insensitive)."""
        try:
            sql = "SELECT 1 FROM habits WHERE LOWER(name) = LOWER(?) AND is_active = 1"
            params: list = [name.strip()]
            if track_id is None:
                sql += " AND track_id IS NULL"
            else:
                sql += " AND track_id = ?"
                params.append(track_id)
            if exclude_habit_id is not None:
                sql += " AND id != ?"
                params.append(exclude_habit_id)
            sql += " LIMIT 1"
            return self._cursor().execute(sql, params).fetchone() is not None
        except sqlite3.Error:
            return False

    # ------------------------------------------------------------------ #
    # Daily logs (one row per habit per day, upsert)
    # ------------------------------------------------------------------ #
    def toggle_completion(self, habit_id: int, log_date: str, completed: bool,
                          value: Optional[float] = None) -> None:
        """
        Set/clear completion for a habit on a date.
        Uses upsert so rapid toggling never creates duplicate rows.
        """
        flag = 1 if completed else 0
        if value is None:
            sql = ("INSERT INTO daily_logs (habit_id, log_date, completed, value) "
                   "VALUES (?, ?, ?, NULL) "
                   "ON CONFLICT(habit_id, log_date) DO UPDATE SET completed = excluded.completed")
            params = (habit_id, log_date, flag)
        else:
            sql = ("INSERT INTO daily_logs (habit_id, log_date, completed, value) "
                   "VALUES (?, ?, ?, ?) "
                   "ON CONFLICT(habit_id, log_date) DO UPDATE SET "
                   "completed = excluded.completed, value = excluded.value")
            params = (habit_id, log_date, flag, value)
        try:
            self._cursor().execute(sql, params)
            self._commit()
        except sqlite3.IntegrityError as exc:
            _log_technical(f"toggle_completion integrity: {exc}")
            raise DatabaseError("That habit could not be updated for this date.", str(exc)) from exc
        except sqlite3.Error as exc:
            _log_technical(f"toggle_completion: {exc}")
            raise DatabaseError("Could not save today's progress.", str(exc)) from exc

    def set_completion(self, habit_id: int, log_date: str, completed: bool,
                       value: Optional[float] = None) -> None:
        self.toggle_completion(habit_id, log_date, completed, value)

    def get_logs_for_habit(self, habit_id: int, start_date: str, end_date: str) -> list[DailyLog]:
        sql = ("SELECT * FROM daily_logs WHERE habit_id = ? AND log_date BETWEEN ? AND ? "
               "ORDER BY log_date")
        try:
            rows = self._cursor().execute(sql, (habit_id, start_date, end_date)).fetchall()
            return [DailyLog(id=r["id"], habit_id=r["habit_id"], log_date=r["log_date"],
                             completed=r["completed"], value=r["value"]) for r in rows]
        except sqlite3.Error as exc:
            _log_technical(f"get_logs_for_habit: {exc}")
            return []

    def get_logs_for_month(self, year: int, month: int) -> list[DailyLog]:
        """All habits' logs for a calendar month (for heatmap/grid rendering)."""
        start = f"{year:04d}-{month:02d}-01"
        if month == 12:
            end = f"{year + 1:04d}-01-01"
        else:
            end = f"{year:04d}-{month + 1:02d}-01"
        # inclusive of last day: use < next month via BETWEEN with last day computed
        try:
            if month == 12:
                last_day = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = date(year, month + 1, 1) - timedelta(days=1)
            end = last_day.isoformat()
        except ValueError:
            pass
        sql = "SELECT * FROM daily_logs WHERE log_date BETWEEN ? AND ? ORDER BY habit_id, log_date"
        try:
            rows = self._cursor().execute(sql, (start, end)).fetchall()
            return [DailyLog(id=r["id"], habit_id=r["habit_id"], log_date=r["log_date"],
                             completed=r["completed"], value=r["value"]) for r in rows]
        except sqlite3.Error as exc:
            _log_technical(f"get_logs_for_month: {exc}")
            return []

    def get_logs_between(self, start_date: str, end_date: str) -> list[DailyLog]:
        sql = "SELECT * FROM daily_logs WHERE log_date BETWEEN ? AND ? ORDER BY habit_id, log_date"
        try:
            rows = self._cursor().execute(sql, (start_date, end_date)).fetchall()
            return [DailyLog(id=r["id"], habit_id=r["habit_id"], log_date=r["log_date"],
                             completed=r["completed"], value=r["value"]) for r in rows]
        except sqlite3.Error as exc:
            _log_technical(f"get_logs_between: {exc}")
            return []

    def get_completion_map(self, habit_id: int, start_date: str, end_date: str) -> dict[str, int]:
        """{iso_date: completed} for sparklines / fast lookups."""
        logs = self.get_logs_for_habit(habit_id, start_date, end_date)
        return {log.log_date: int(log.completed) for log in logs}

    def get_logs_for_day(self, day: str) -> list[DailyLog]:
        sql = "SELECT * FROM daily_logs WHERE log_date = ? ORDER BY habit_id"
        try:
            rows = self._cursor().execute(sql, (day,)).fetchall()
            return [DailyLog(id=r["id"], habit_id=r["habit_id"], log_date=r["log_date"],
                             completed=r["completed"], value=r["value"]) for r in rows]
        except sqlite3.Error as exc:
            _log_technical(f"get_logs_for_day: {exc}")
            return []

    # ------------------------------------------------------------------ #
    # Tasks
    # ------------------------------------------------------------------ #
    def create_task(self, title: str, due_date: str, priority: str = "Medium",
                    linked_track_id: Optional[int] = None, status: str = "Pending",
                    carried_over: int = 0, created_date: Optional[str] = None) -> int:
        if priority not in ("Low", "Medium", "High"):
            priority = "Medium"
        sql = ("INSERT INTO tasks (title, due_date, priority, status, linked_track_id, "
               "carried_over, created_date) VALUES (?, ?, ?, ?, ?, ?, ?)")
        try:
            cur = self._cursor()
            cur.execute(sql, (title, due_date, priority, status, linked_track_id,
                              1 if carried_over else 0,
                              created_date or date.today().isoformat()))
            self._commit()
            return int(cur.lastrowid or 0)
        except sqlite3.Error as exc:
            _log_technical(f"create_task: {exc}")
            raise DatabaseError("Could not save the task.", str(exc)) from exc

    def get_tasks_for_date(self, target_date: str) -> list[Task]:
        sql = ("SELECT tk.*, t.name AS track_name, t.color_hex AS track_color "
               "FROM tasks tk LEFT JOIN tracks t ON t.id = tk.linked_track_id "
               "WHERE tk.due_date = ? ORDER BY "
               "CASE tk.priority WHEN 'High' THEN 0 WHEN 'Medium' THEN 1 ELSE 2 END, tk.id")
        try:
            rows = self._cursor().execute(sql, (target_date,)).fetchall()
            return [self._task_from_row(r) for r in rows]
        except sqlite3.Error as exc:
            _log_technical(f"get_tasks_for_date: {exc}")
            return []

    def get_tasks_between(self, start_date: str, end_date: str,
                          status: Optional[str] = None) -> list[Task]:
        sql = ("SELECT tk.*, t.name AS track_name, t.color_hex AS track_color "
               "FROM tasks tk LEFT JOIN tracks t ON t.id = tk.linked_track_id "
               "WHERE tk.due_date BETWEEN ? AND ?")
        params: list = [start_date, end_date]
        if status:
            sql += " AND tk.status = ?"
            params.append(status)
        sql += (" ORDER BY tk.due_date, "
                "CASE tk.priority WHEN 'High' THEN 0 WHEN 'Medium' THEN 1 ELSE 2 END, tk.id")
        try:
            rows = self._cursor().execute(sql, params).fetchall()
            return [self._task_from_row(r) for r in rows]
        except sqlite3.Error as exc:
            _log_technical(f"get_tasks_between: {exc}")
            return []

    def _task_from_row(self, r: sqlite3.Row) -> Task:
        keys = r.keys()
        return Task(
            id=r["id"], title=r["title"], due_date=r["due_date"],
            priority=r["priority"] or "Medium", status=r["status"] or "Pending",
            linked_track_id=r["linked_track_id"], carried_over=r["carried_over"] or 0,
            created_date=r["created_date"],
            track_name=(r["track_name"] if "track_name" in keys else "") or "",
            track_color=(r["track_color"] if "track_color" in keys else "") or "",
        )

    def get_task(self, task_id: int) -> Optional[Task]:
        sql = ("SELECT tk.*, t.name AS track_name, t.color_hex AS track_color "
               "FROM tasks tk LEFT JOIN tracks t ON t.id = tk.linked_track_id WHERE tk.id = ?")
        try:
            row = self._cursor().execute(sql, (task_id,)).fetchone()
            return self._task_from_row(row) if row else None
        except sqlite3.Error as exc:
            _log_technical(f"get_task: {exc}")
            return None

    def update_task(self, task_id: int, **fields) -> None:
        allowed = {"title", "due_date", "priority", "status",
                   "linked_track_id", "carried_over"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return
        if "priority" in updates and updates["priority"] not in ("Low", "Medium", "High"):
            updates["priority"] = "Medium"
        if "status" in updates and updates["status"] not in ("Pending", "Done"):
            updates["status"] = "Pending"
        try:
            cols = ", ".join(f"{k} = ?" for k in updates)
            self._cursor().execute(f"UPDATE tasks SET {cols} WHERE id = ?",
                                   (*updates.values(), task_id))
            self._commit()
        except sqlite3.Error as exc:
            _log_technical(f"update_task: {exc}")
            raise DatabaseError("Could not update the task.", str(exc)) from exc

    def update_task_status(self, task_id: int, status: str) -> None:
        self.update_task(task_id, status=status)

    def delete_task(self, task_id: int) -> None:
        try:
            self._cursor().execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            self._commit()
        except sqlite3.Error as exc:
            _log_technical(f"delete_task: {exc}")
            raise DatabaseError("Could not delete the task.", str(exc)) from exc

    def roll_over_incomplete_tasks(self, from_date: str, to_date: str) -> int:
        """
        Move Pending tasks dated <= from_date forward to to_date and flag them
        as carried over. Returns number of tasks rolled.
        """
        sql = ("UPDATE tasks SET due_date = ?, carried_over = 1 "
               "WHERE status = 'Pending' AND due_date <= ? AND due_date <> ?")
        try:
            cur = self._cursor().execute(sql, (to_date, from_date, to_date))
            self._commit()
            return int(cur.rowcount or 0)
        except sqlite3.Error as exc:
            _log_technical(f"roll_over_incomplete_tasks: {exc}")
            return 0

    def get_carried_over_tasks(self) -> list[Task]:
        sql = ("SELECT tk.*, t.name AS track_name, t.color_hex AS track_color "
               "FROM tasks tk LEFT JOIN tracks t ON t.id = tk.linked_track_id "
               "WHERE tk.carried_over = 1 AND tk.status = 'Pending' ORDER BY tk.due_date")
        try:
            return [self._task_from_row(r) for r in self._cursor().execute(sql).fetchall()]
        except sqlite3.Error as exc:
            _log_technical(f"get_carried_over_tasks: {exc}")
            return []

    # ------------------------------------------------------------------ #
    # Plans
    # ------------------------------------------------------------------ #
    def create_plan(self, track_id: int, start_date: str, end_date: str,
                    weekly_target: int, notes: str = "") -> int:
        try:
            target = max(1, min(7, int(weekly_target)))
        except (TypeError, ValueError):
            target = 3
        sql = ("INSERT INTO plans (track_id, start_date, end_date, weekly_target, notes) "
               "VALUES (?, ?, ?, ?, ?)")
        try:
            cur = self._cursor()
            cur.execute(sql, (track_id, start_date, end_date, target, notes))
            self._commit()
            return int(cur.lastrowid or 0)
        except sqlite3.Error as exc:
            _log_technical(f"create_plan: {exc}")
            raise DatabaseError("Could not save the plan.", str(exc)) from exc

    def get_plans_for_track(self, track_id: int) -> list[Plan]:
        sql = ("SELECT p.*, t.name AS track_name, t.color_hex AS track_color, t.icon AS track_icon "
               "FROM plans p JOIN tracks t ON t.id = p.track_id "
               "WHERE p.track_id = ? ORDER BY p.start_date DESC")
        try:
            rows = self._cursor().execute(sql, (track_id,)).fetchall()
            return [Plan(id=r["id"], track_id=r["track_id"], start_date=r["start_date"],
                         end_date=r["end_date"], weekly_target=r["weekly_target"] or 3,
                         notes=r["notes"] or "", track_name=r["track_name"],
                         track_color=r["track_color"], track_icon=r["track_icon"] or "📁")
                    for r in rows]
        except sqlite3.Error as exc:
            _log_technical(f"get_plans_for_track: {exc}")
            return []

    def get_all_plans(self) -> list[Plan]:
        sql = ("SELECT p.*, t.name AS track_name, t.color_hex AS track_color, t.icon AS track_icon "
               "FROM plans p JOIN tracks t ON t.id = p.track_id "
               "ORDER BY p.start_date DESC")
        try:
            rows = self._cursor().execute(sql).fetchall()
            return [Plan(id=r["id"], track_id=r["track_id"], start_date=r["start_date"],
                         end_date=r["end_date"], weekly_target=r["weekly_target"] or 3,
                         notes=r["notes"] or "", track_name=r["track_name"],
                         track_color=r["track_color"], track_icon=r["track_icon"] or "📁")
                    for r in rows]
        except sqlite3.Error as exc:
            _log_technical(f"get_all_plans: {exc}")
            return []

    def delete_plan(self, plan_id: int) -> None:
        try:
            self._cursor().execute("DELETE FROM plans WHERE id = ?", (plan_id,))
            self._commit()
        except sqlite3.Error as exc:
            _log_technical(f"delete_plan: {exc}")
            raise DatabaseError("Could not delete the plan.", str(exc)) from exc

    # ------------------------------------------------------------------ #
    # Analytics helpers
    # ------------------------------------------------------------------ #
    def get_completion_percentage(self, habit_id: int, start_date: str, end_date: str,
                                  expected_days: Optional[int] = None) -> float:
        logs = self.get_logs_for_habit(habit_id, start_date, end_date)
        return compute_completion_percentage(logs, start_date, end_date, expected_days)

    def get_current_streak(self, habit_id: int, today: Optional[date] = None) -> int:
        try:
            ref = today or date.today()
            # Start from the habit's EARLIEST log (robust even when created_date
            # is today or history predates it — e.g. seeded demo data)
            row = self._cursor().execute(
                "SELECT MIN(log_date) AS first FROM daily_logs WHERE habit_id = ?",
                (habit_id,)).fetchone()
            first = row["first"] if row else None
            if not first:
                return 0
            logs = self.get_logs_for_habit(habit_id, first, ref.isoformat())
            return compute_current_streak(logs, ref)
        except sqlite3.Error as exc:
            _log_technical(f"get_current_streak: {exc}")
            return 0

    def get_best_streak(self, habit_id: int) -> int:
        try:
            logs = self.get_logs_for_habit(habit_id, "2000-01-01", "2999-12-31")
            return compute_best_streak(logs)
        except sqlite3.Error as exc:
            _log_technical(f"get_best_streak: {exc}")
            return 0

    def get_habit_stats(self, habit_id: int, ref_date: Optional[date] = None) -> dict:
        """Bundle of per-habit stats used by detail panes and cards."""
        ref = ref_date or date.today()
        try:
            habit = self.get_habit(habit_id)
            if habit is None:
                return {"exists": False, "current_streak": 0, "best_streak": 0,
                        "month_pct": 0.0, "all_time_completions": 0, "today_done": False}
            start_of_month = ref.replace(day=1).isoformat()
            month_pct = self.get_completion_percentage(habit_id, start_of_month, ref.isoformat())
            current = self.get_current_streak(habit_id, ref)
            best = self.get_best_streak(habit_id)
            total = self._count_completions(habit_id)
            today_done = any(l.log_date == ref.isoformat() and l.completed
                             for l in self.get_logs_for_habit(habit_id, ref.isoformat(), ref.isoformat()))
            return {"exists": True, "habit": habit, "current_streak": current,
                    "best_streak": best, "month_pct": month_pct,
                    "all_time_completions": total, "today_done": today_done}
        except sqlite3.Error as exc:
            _log_technical(f"get_habit_stats: {exc}")
            return {"exists": False, "current_streak": 0, "best_streak": 0,
                    "month_pct": 0.0, "all_time_completions": 0, "today_done": False}

    def _count_completions(self, habit_id: int) -> int:
        try:
            row = self._cursor().execute(
                "SELECT COUNT(*) AS n FROM daily_logs WHERE habit_id = ? AND completed = 1",
                (habit_id,)).fetchone()
            return int(row["n"]) if row else 0
        except sqlite3.Error:
            return 0

    def get_category_breakdown(self, start_date: str, end_date: str) -> dict:
        """{track_name: completion_count} for the per-category donut chart."""
        sql = ("SELECT COALESCE(t.name, 'Other') AS cat, COUNT(*) AS n "
               "FROM daily_logs dl "
               "JOIN habits h ON h.id = dl.habit_id "
               "LEFT JOIN tracks t ON t.id = h.track_id "
               "WHERE dl.completed = 1 AND dl.log_date BETWEEN ? AND ? "
               "GROUP BY cat ORDER BY n DESC")
        try:
            rows = self._cursor().execute(sql, (start_date, end_date)).fetchall()
            return {r["cat"]: int(r["n"]) for r in rows}
        except sqlite3.Error as exc:
            _log_technical(f"get_category_breakdown: {exc}")
            return {}

    def get_category_colors(self) -> dict:
        """{track_name: color_hex} for donut chart slices."""
        try:
            rows = self._cursor().execute(
                "SELECT name, color_hex FROM tracks").fetchall()
            return {r["name"]: r["color_hex"] for r in rows}
        except sqlite3.Error:
            return {}

    def get_daily_overall_completion(self, day: str) -> float:
        """Overall completion ratio across all active habits for one day."""
        try:
            row = self._cursor().execute(
                "SELECT COUNT(*) AS n FROM habits WHERE is_active = 1").fetchone()
            total = int(row["n"]) if row else 0
            if total == 0:
                return 0.0
            row = self._cursor().execute(
                "SELECT COUNT(*) AS n FROM daily_logs dl "
                "JOIN habits h ON h.id = dl.habit_id "
                "WHERE dl.log_date = ? AND dl.completed = 1 AND h.is_active = 1",
                (day,)).fetchone()
            done = int(row["n"]) if row else 0
            return done / total
        except sqlite3.Error as exc:
            _log_technical(f"get_daily_overall_completion: {exc}")
            return 0.0

    def get_overall_completion_for_range(self, start_date: str, end_date: str) -> float:
        """Average daily overall completion across a date range."""
        try:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
        except (TypeError, ValueError):
            return 0.0
        if end < start:
            return 0.0
        total = 0.0
        cursor = start
        days = 0
        while cursor <= end:
            total += self.get_daily_overall_completion(cursor.isoformat())
            days += 1
            cursor += timedelta(days=1)
        return round((total / days) * 100.0, 1) if days else 0.0

    def get_habit_completion_by_day(self, habit_id: int, start_date: str,
                                    end_date: str) -> dict[str, bool]:
        logs = self.get_logs_for_habit(habit_id, start_date, end_date)
        return {l.log_date: bool(l.completed) for l in logs}

    def get_weekly_bar_data(self, start_date: str, end_date: str) -> dict[str, int]:
        """{iso_date: count of completions} per day — Analytics weekly bar chart."""
        sql = ("SELECT log_date, COUNT(*) AS n FROM daily_logs "
               "WHERE completed = 1 AND log_date BETWEEN ? AND ? "
               "GROUP BY log_date ORDER BY log_date")
        try:
            rows = self._cursor().execute(sql, (start_date, end_date)).fetchall()
            return {r["log_date"]: int(r["n"]) for r in rows}
        except sqlite3.Error as exc:
            _log_technical(f"get_weekly_bar_data: {exc}")
            return {}

    def get_monthly_trend(self, months: int = 6) -> list[tuple[str, float]]:
        """[(YYYY-MM, completion%)] over the last N months — trend line chart."""
        ref = date.today().replace(day=1)
        results: list[tuple[str, float]] = []
        try:
            cursor = ref
            buckets: list[tuple[str, date, date]] = []
            for _ in range(max(1, months)):
                label = cursor.strftime("%Y-%m")
                next_month = (date(cursor.year + 1, 1, 1) if cursor.month == 12
                              else date(cursor.year, cursor.month + 1, 1))
                last_day = next_month - timedelta(days=1)
                buckets.append((label, cursor, last_day))
                cursor = cursor - timedelta(days=1)
                cursor = cursor.replace(day=1)
            for label, start, end in buckets:
                pct = self.get_overall_completion_for_range(start.isoformat(), end.isoformat())
                results.append((label, pct))
            results.reverse()  # oldest → newest for chart X axis
            return results
        except sqlite3.Error as exc:
            _log_technical(f"get_monthly_trend: {exc}")
            return []

    def get_top_and_needs_attention(self, start_date: str, end_date: str) -> tuple[list, list]:
        """(top_habits, needs_attention) by completion % — simple computed logic, no AI."""
        habits = self.get_active_habits()
        scored = []
        for h in habits:
            pct = self.get_completion_percentage(h.id, start_date, end_date)
            scored.append((h, pct))
        scored.sort(key=lambda x: x[1], reverse=True)
        # Only habits with some activity or at least 1 expected day count
        top = [s for s in scored if s[1] > 0][:5]
        needs = [s for s in reversed(scored) if s[1] < 100.0][:5]
        needs = sorted(needs, key=lambda x: x[1])
        return top, needs

    def get_today_progress(self, today: Optional[date] = None) -> dict:
        """Dashboard header stats: today %, active streaks, best streak."""
        ref = (today or date.today()).isoformat()
        habits = self.get_active_habits()
        if not habits:
            return {"percent": 0.0, "done": 0, "total": 0,
                    "active_streaks": 0, "best_streak": 0, "best_habit": None}
        done = 0
        active_streaks = 0
        best_streak = 0
        best_habit = None
        for h in habits:
            logs = self.get_logs_for_habit(h.id, h.created_date or "2000-01-01", ref)
            if any(l.log_date == ref and l.completed for l in logs):
                done += 1
            streak = compute_current_streak(logs, date.fromisoformat(ref))
            if streak > 0:
                active_streaks += 1
            if streak > best_streak:
                best_streak = streak
                best_habit = h
        percent = round((done / len(habits)) * 100.0, 1)
        return {"percent": percent, "done": done, "total": len(habits),
                "active_streaks": active_streaks, "best_streak": best_streak,
                "best_habit": best_habit}

    def is_empty(self) -> bool:
        """True when no tracks exist yet (first run / reset)."""
        try:
            row = self._cursor().execute("SELECT COUNT(*) AS n FROM tracks").fetchone()
            return int(row["n"]) == 0
        except sqlite3.Error:
            return True

    def reset_all_data(self) -> None:
        """Settings → Reset all data (drops all rows, keeps schema)."""
        try:
            cur = self._cursor()
            for table in ("daily_logs", "tasks", "plans", "habits", "tracks"):
                cur.execute(f"DELETE FROM {table}")
            self._commit()
        except sqlite3.Error as exc:
            _log_technical(f"reset_all_data: {exc}")
            raise DatabaseError("Could not reset the data.", str(exc)) from exc
