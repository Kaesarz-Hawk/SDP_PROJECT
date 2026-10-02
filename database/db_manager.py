"""Database manager for Momentum.

Encapsulates all SQLite connection lifecycle and queries.
Ensures parameterized SQL queries, foreign key enforcement,
consistent error handling, and object mapping to data models.
"""

import logging
import os
import sqlite3
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from models.daily_log import DailyLog
from models.habit import Habit
from models.plan import Plan
from models.task import Task
from models.track import Track
from utils.streak_calculator import compute_best_streak, compute_current_streak

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Clean custom exception for database failures presented to the UI."""
    pass


class DBManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._connect()
        self.initialize_schema()

    def _connect(self) -> None:
        """Establishes SQLite connection with foreign keys and row factory."""
        try:
            # Ensure containing directory exists
            db_dir = os.path.dirname(self.db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)

            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON;")
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to SQLite at {self.db_path}: {e}")
            raise DatabaseError("Could not access your data file. It may be locked or open elsewhere.") from e

    def get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._connect()
        return self._conn

    def close(self) -> None:
        """Closes the database connection cleanly."""
        if self._conn:
            try:
                self._conn.close()
            except sqlite3.Error as e:
                logger.error(f"Error closing database connection: {e}")
            finally:
                self._conn = None

    def initialize_schema(self) -> None:
        """Creates tables if they don't exist."""
        schema = """
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
        """
        try:
            conn = self.get_connection()
            with conn:
                conn.executescript(schema)
        except sqlite3.Error as e:
            logger.error(f"Error creating database schema: {e}")
            raise DatabaseError("Failed to initialize database schema.") from e

    # ==========================================
    # Tracks CRUD
    # ==========================================

    def create_track(self, name: str, category: str, color_hex: str, icon: str) -> int:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Track name cannot be empty.")
        created_date = date.today().isoformat()
        try:
            conn = self.get_connection()
            with conn:
                cursor = conn.execute(
                    "INSERT INTO tracks (name, category, color_hex, icon, created_date) VALUES (?, ?, ?, ?, ?)",
                    (clean_name, category.strip(), color_hex.strip(), icon.strip(), created_date),
                )
                return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Database error in create_track: {e}")
            raise DatabaseError(f"Failed to create track '{clean_name}'.") from e

    def get_all_tracks(self) -> List[Track]:
        try:
            conn = self.get_connection()
            cursor = conn.execute("SELECT id, name, category, color_hex, icon, created_date FROM tracks ORDER BY id ASC")
            rows = cursor.fetchall()
            return [
                Track(
                    id=row["id"],
                    name=row["name"],
                    category=row["category"] or "",
                    color_hex=row["color_hex"],
                    icon=row["icon"] or "🎯",
                    created_date=row["created_date"],
                )
                for row in rows
            ]
        except sqlite3.Error as e:
            logger.error(f"Database error in get_all_tracks: {e}")
            raise DatabaseError("Failed to retrieve tracks.") from e

    def get_track_by_id(self, track_id: int) -> Optional[Track]:
        try:
            conn = self.get_connection()
            cursor = conn.execute(
                "SELECT id, name, category, color_hex, icon, created_date FROM tracks WHERE id = ?",
                (track_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return Track(
                id=row["id"],
                name=row["name"],
                category=row["category"] or "",
                color_hex=row["color_hex"],
                icon=row["icon"] or "🎯",
                created_date=row["created_date"],
            )
        except sqlite3.Error as e:
            logger.error(f"Database error in get_track_by_id: {e}")
            raise DatabaseError("Failed to retrieve track.") from e

    def update_track(self, track_id: int, name: str, category: str, color_hex: str, icon: str) -> None:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Track name cannot be empty.")
        try:
            conn = self.get_connection()
            with conn:
                conn.execute(
                    "UPDATE tracks SET name = ?, category = ?, color_hex = ?, icon = ? WHERE id = ?",
                    (clean_name, category.strip(), color_hex.strip(), icon.strip(), track_id),
                )
        except sqlite3.Error as e:
            logger.error(f"Database error in update_track: {e}")
            raise DatabaseError("Failed to update track.") from e

    def delete_track(self, track_id: int) -> None:
        """Deletes a track. Foreign key ON DELETE SET NULL decouples habits, tasks, while plans cascade."""
        try:
            conn = self.get_connection()
            with conn:
                conn.execute("DELETE FROM tracks WHERE id = ?", (track_id,))
        except sqlite3.Error as e:
            logger.error(f"Database error in delete_track: {e}")
            raise DatabaseError("Failed to delete track.") from e

    # ==========================================
    # Habits CRUD & Queries
    # ==========================================

    def create_habit(self, track_id: Optional[int], name: str, icon: str, target_frequency: int = 7) -> int:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Habit name cannot be empty.")
        if target_frequency < 1 or target_frequency > 7:
            target_frequency = max(1, min(7, target_frequency))

        created_date = date.today().isoformat()
        try:
            conn = self.get_connection()
            with conn:
                cursor = conn.execute(
                    "INSERT INTO habits (track_id, name, icon, target_frequency, created_date, is_active) VALUES (?, ?, ?, ?, ?, 1)",
                    (track_id, clean_name, icon.strip(), target_frequency, created_date),
                )
                return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Database error in create_habit: {e}")
            raise DatabaseError(f"Failed to create habit '{clean_name}'.") from e

    def get_active_habits(self) -> List[Habit]:
        """Returns all habits marked is_active = 1."""
        try:
            conn = self.get_connection()
            cursor = conn.execute(
                "SELECT id, track_id, name, icon, target_frequency, created_date, is_active FROM habits WHERE is_active = 1 ORDER BY id ASC"
            )
            rows = cursor.fetchall()
            return [
                Habit(
                    id=row["id"],
                    track_id=row["track_id"],
                    name=row["name"],
                    icon=row["icon"] or "⚡",
                    target_frequency=row["target_frequency"] or 7,
                    created_date=row["created_date"],
                    is_active=row["is_active"],
                )
                for row in rows
            ]
        except sqlite3.Error as e:
            logger.error(f"Database error in get_active_habits: {e}")
            raise DatabaseError("Failed to retrieve active habits.") from e

    def get_habits_by_track(self, track_id: int) -> List[Habit]:
        try:
            conn = self.get_connection()
            cursor = conn.execute(
                "SELECT id, track_id, name, icon, target_frequency, created_date, is_active FROM habits WHERE track_id = ? AND is_active = 1 ORDER BY id ASC",
                (track_id,),
            )
            rows = cursor.fetchall()
            return [
                Habit(
                    id=row["id"],
                    track_id=row["track_id"],
                    name=row["name"],
                    icon=row["icon"] or "⚡",
                    target_frequency=row["target_frequency"] or 7,
                    created_date=row["created_date"],
                    is_active=row["is_active"],
                )
                for row in rows
            ]
        except sqlite3.Error as e:
            logger.error(f"Database error in get_habits_by_track: {e}")
            raise DatabaseError("Failed to retrieve habits for track.") from e

    def get_habit_by_id(self, habit_id: int) -> Optional[Habit]:
        try:
            conn = self.get_connection()
            cursor = conn.execute(
                "SELECT id, track_id, name, icon, target_frequency, created_date, is_active FROM habits WHERE id = ?",
                (habit_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return Habit(
                id=row["id"],
                track_id=row["track_id"],
                name=row["name"],
                icon=row["icon"] or "⚡",
                target_frequency=row["target_frequency"] or 7,
                created_date=row["created_date"],
                is_active=row["is_active"],
            )
        except sqlite3.Error as e:
            logger.error(f"Database error in get_habit_by_id: {e}")
            raise DatabaseError("Failed to retrieve habit.") from e

    def update_habit(self, habit_id: int, **fields: Any) -> None:
        """Updates specific fields for a habit."""
        if not fields:
            return
        allowed = {"track_id", "name", "icon", "target_frequency", "is_active"}
        updates = []
        params = []
        for key, val in fields.items():
            if key in allowed:
                if key == "name" and isinstance(val, str):
                    val = val.strip()
                    if not val:
                        raise ValueError("Habit name cannot be empty.")
                updates.append(f"{key} = ?")
                params.append(val)
        if not updates:
            return
        params.append(habit_id)
        sql = f"UPDATE habits SET {', '.join(updates)} WHERE id = ?"
        try:
            conn = self.get_connection()
            with conn:
                conn.execute(sql, params)
        except sqlite3.Error as e:
            logger.error(f"Database error in update_habit: {e}")
            raise DatabaseError("Failed to update habit.") from e

    def deactivate_habit(self, habit_id: int) -> None:
        """Soft-deletes habit by setting is_active = 0 to preserve historical logs."""
        self.update_habit(habit_id, is_active=0)

    # ==========================================
    # Daily Logs
    # ==========================================

    def toggle_completion(self, habit_id: int, log_date: str, completed: bool, value: Optional[float] = None) -> None:
        """Upserts a daily log for habit_id and log_date."""
        completed_int = 1 if completed else 0
        try:
            conn = self.get_connection()
            with conn:
                conn.execute(
                    """
                    INSERT INTO daily_logs (habit_id, log_date, completed, value)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(habit_id, log_date)
                    DO UPDATE SET completed = excluded.completed,
                                  value = COALESCE(excluded.value, daily_logs.value)
                    """,
                    (habit_id, log_date, completed_int, value),
                )
        except sqlite3.Error as e:
            logger.error(f"Database error in toggle_completion: {e}")
            raise DatabaseError("Failed to update completion status.") from e

    def log_daily_completion(self, habit_id: int, log_date: str, completed: bool, value: Optional[float] = None) -> None:
        """Convenience alias for toggle_completion."""
        self.toggle_completion(habit_id, log_date, completed, value)

    def is_habit_completed(self, habit_id: int, log_date: str) -> bool:
        """Returns True if the habit is marked completed on log_date."""
        try:
            conn = self.get_connection()
            cursor = conn.execute(
                "SELECT completed FROM daily_logs WHERE habit_id = ? AND log_date = ?",
                (habit_id, log_date),
            )
            row = cursor.fetchone()
            return bool(row["completed"]) if row else False
        except sqlite3.Error as e:
            logger.error(f"Database error in is_habit_completed: {e}")
            return False

    def get_logs_for_habit(self, habit_id: int, start_date: str, end_date: str) -> List[DailyLog]:
        try:
            conn = self.get_connection()
            cursor = conn.execute(
                """
                SELECT id, habit_id, log_date, completed, value
                FROM daily_logs
                WHERE habit_id = ? AND log_date BETWEEN ? AND ?
                ORDER BY log_date ASC
                """,
                (habit_id, start_date, end_date),
            )
            rows = cursor.fetchall()
            return [
                DailyLog(
                    id=row["id"],
                    habit_id=row["habit_id"],
                    log_date=row["log_date"],
                    completed=row["completed"],
                    value=row["value"],
                )
                for row in rows
            ]
        except sqlite3.Error as e:
            logger.error(f"Database error in get_logs_for_habit: {e}")
            raise DatabaseError("Failed to retrieve habit logs.") from e

    def get_all_completed_dates_for_habit(self, habit_id: int) -> List[str]:
        """Returns sorted list of ISO date strings where habit was completed."""
        try:
            conn = self.get_connection()
            cursor = conn.execute(
                "SELECT log_date FROM daily_logs WHERE habit_id = ? AND completed = 1 ORDER BY log_date ASC",
                (habit_id,),
            )
            rows = cursor.fetchall()
            return [row["log_date"] for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Database error in get_all_completed_dates_for_habit: {e}")
            return []

    def get_logs_for_month(self, year: int, month: int) -> List[DailyLog]:
        """Returns all completed/logged entries across active habits for a given month."""
        start_date = f"{year:04d}-{month:02d}-01"
        # Determine last day of month
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)
        last_day = (next_month - timedelta(days=1)).strftime("%Y-%m-%d")

        try:
            conn = self.get_connection()
            cursor = conn.execute(
                """
                SELECT d.id, d.habit_id, d.log_date, d.completed, d.value
                FROM daily_logs d
                JOIN habits h ON d.habit_id = h.id
                WHERE h.is_active = 1 AND d.log_date BETWEEN ? AND ?
                ORDER BY d.log_date ASC
                """,
                (start_date, last_day),
            )
            rows = cursor.fetchall()
            return [
                DailyLog(
                    id=row["id"],
                    habit_id=row["habit_id"],
                    log_date=row["log_date"],
                    completed=row["completed"],
                    value=row["value"],
                )
                for row in rows
            ]
        except sqlite3.Error as e:
            logger.error(f"Database error in get_logs_for_month: {e}")
            raise DatabaseError("Failed to retrieve month logs.") from e

    # ==========================================
    # Tasks CRUD & Rollover
    # ==========================================

    def create_task(self, title: str, due_date: str, priority: str = "Medium", linked_track_id: Optional[int] = None) -> int:
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Task title cannot be empty.")
        if priority not in ("Low", "Medium", "High"):
            priority = "Medium"
        created_date = date.today().isoformat()
        try:
            conn = self.get_connection()
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO tasks (title, due_date, priority, status, linked_track_id, carried_over, created_date)
                    VALUES (?, ?, ?, 'Pending', ?, 0, ?)
                    """,
                    (clean_title, due_date.strip(), priority, linked_track_id, created_date),
                )
                return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Database error in create_task: {e}")
            raise DatabaseError("Failed to create task.") from e

    def get_tasks_for_date(self, target_date: str) -> List[Task]:
        try:
            conn = self.get_connection()
            cursor = conn.execute(
                """
                SELECT id, title, due_date, priority, status, linked_track_id, carried_over, created_date
                FROM tasks
                WHERE due_date = ?
                ORDER BY status DESC,
                         CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 WHEN 'Low' THEN 3 ELSE 4 END ASC,
                         id ASC
                """,
                (target_date,),
            )
            rows = cursor.fetchall()
            return [
                Task(
                    id=row["id"],
                    title=row["title"],
                    due_date=row["due_date"],
                    priority=row["priority"],
                    status=row["status"],
                    linked_track_id=row["linked_track_id"],
                    carried_over=row["carried_over"],
                    created_date=row["created_date"],
                )
                for row in rows
            ]
        except sqlite3.Error as e:
            logger.error(f"Database error in get_tasks_for_date: {e}")
            raise DatabaseError("Failed to retrieve tasks.") from e

    def update_task_status(self, task_id: int, status: str) -> None:
        if status not in ("Pending", "Done"):
            status = "Pending"
        try:
            conn = self.get_connection()
            with conn:
                conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
        except sqlite3.Error as e:
            logger.error(f"Database error in update_task_status: {e}")
            raise DatabaseError("Failed to update task status.") from e

    def update_task(self, task_id: int, title: str, due_date: str, priority: str, linked_track_id: Optional[int]) -> None:
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Task title cannot be empty.")
        if priority not in ("Low", "Medium", "High"):
            priority = "Medium"
        try:
            conn = self.get_connection()
            with conn:
                conn.execute(
                    "UPDATE tasks SET title = ?, due_date = ?, priority = ?, linked_track_id = ? WHERE id = ?",
                    (clean_title, due_date.strip(), priority, linked_track_id, task_id),
                )
        except sqlite3.Error as e:
            logger.error(f"Database error in update_task: {e}")
            raise DatabaseError("Failed to update task.") from e

    def delete_task(self, task_id: int) -> None:
        try:
            conn = self.get_connection()
            with conn:
                conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        except sqlite3.Error as e:
            logger.error(f"Database error in delete_task: {e}")
            raise DatabaseError("Failed to delete task.") from e

    def roll_over_incomplete_tasks(self, from_date: Optional[str] = None, to_date: Optional[str] = None) -> int:
        """Rolls over pending tasks with due_date strictly before to_date.

        Defaults to_date to today. Updates due_date to to_date and carried_over = 1.
        Returns count of rolled over tasks.
        """
        if to_date is None:
            to_date = date.today().isoformat()
        try:
            conn = self.get_connection()
            with conn:
                if from_date:
                    cursor = conn.execute(
                        """
                        UPDATE tasks
                        SET due_date = ?, carried_over = 1
                        WHERE status = 'Pending' AND due_date = ?
                        """,
                        (to_date, from_date),
                    )
                else:
                    cursor = conn.execute(
                        """
                        UPDATE tasks
                        SET due_date = ?, carried_over = 1
                        WHERE status = 'Pending' AND due_date < ?
                        """,
                        (to_date, to_date),
                    )
                return cursor.rowcount
        except sqlite3.Error as e:
            logger.error(f"Database error in roll_over_incomplete_tasks: {e}")
            raise DatabaseError("Failed to roll over incomplete tasks.") from e

    # ==========================================
    # Plans CRUD
    # ==========================================

    def create_plan(self, track_id: int, start_date: str, end_date: str, weekly_target: int, notes: str = "") -> int:
        # Validate date range
        try:
            d_start = date.fromisoformat(start_date)
            d_end = date.fromisoformat(end_date)
        except ValueError as ve:
            raise ValueError("Invalid start or end date format.") from ve

        if d_end <= d_start:
            raise ValueError("Plan end date must be after start date.")

        if weekly_target < 1:
            weekly_target = 1

        try:
            conn = self.get_connection()
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO plans (track_id, start_date, end_date, weekly_target, notes)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (track_id, start_date, end_date, weekly_target, notes.strip()),
                )
                return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Database error in create_plan: {e}")
            raise DatabaseError("Failed to create plan.") from e

    def get_plans_for_track(self, track_id: int) -> List[Plan]:
        try:
            conn = self.get_connection()
            cursor = conn.execute(
                "SELECT id, track_id, start_date, end_date, weekly_target, notes FROM plans WHERE track_id = ? ORDER BY start_date DESC",
                (track_id,),
            )
            rows = cursor.fetchall()
            return [
                Plan(
                    id=row["id"],
                    track_id=row["track_id"],
                    start_date=row["start_date"],
                    end_date=row["end_date"],
                    weekly_target=row["weekly_target"],
                    notes=row["notes"] or "",
                )
                for row in rows
            ]
        except sqlite3.Error as e:
            logger.error(f"Database error in get_plans_for_track: {e}")
            raise DatabaseError("Failed to retrieve plans.") from e

    def get_all_plans(self) -> List[Plan]:
        try:
            conn = self.get_connection()
            cursor = conn.execute(
                "SELECT id, track_id, start_date, end_date, weekly_target, notes FROM plans ORDER BY start_date DESC"
            )
            rows = cursor.fetchall()
            return [
                Plan(
                    id=row["id"],
                    track_id=row["track_id"],
                    start_date=row["start_date"],
                    end_date=row["end_date"],
                    weekly_target=row["weekly_target"],
                    notes=row["notes"] or "",
                )
                for row in rows
            ]
        except sqlite3.Error as e:
            logger.error(f"Database error in get_all_plans: {e}")
            raise DatabaseError("Failed to retrieve plans.") from e

    def delete_plan(self, plan_id: int) -> None:
        try:
            conn = self.get_connection()
            with conn:
                conn.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
        except sqlite3.Error as e:
            logger.error(f"Database error in delete_plan: {e}")
            raise DatabaseError("Failed to delete plan.") from e

    # ==========================================
    # Analytics & Aggregation Helpers
    # ==========================================

    def get_current_streak(self, habit_id: int) -> int:
        """Returns current streak for a habit using streak_calculator."""
        dates = self.get_all_completed_dates_for_habit(habit_id)
        return compute_current_streak(dates)

    def get_best_streak(self, habit_id: int) -> int:
        """Returns best streak ever for a habit."""
        dates = self.get_all_completed_dates_for_habit(habit_id)
        return compute_best_streak(dates)

    def get_total_completions(self, habit_id: int) -> int:
        """Returns count of all-time completions for a habit."""
        try:
            conn = self.get_connection()
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM daily_logs WHERE habit_id = ? AND completed = 1",
                (habit_id,),
            )
            row = cursor.fetchone()
            return row["count"] if row else 0
        except sqlite3.Error:
            return 0

    def get_completion_percentage(self, habit_id: int, start_date: str, end_date: str) -> float:
        """Calculates completion rate (0.0 to 1.0) for habit within date range."""
        try:
            d_start = date.fromisoformat(start_date)
            d_end = date.fromisoformat(end_date)
            total_days = (d_end - d_start).days + 1
            if total_days <= 0:
                return 0.0

            conn = self.get_connection()
            cursor = conn.execute(
                """
                SELECT COUNT(*) as completed_count
                FROM daily_logs
                WHERE habit_id = ? AND completed = 1 AND log_date BETWEEN ? AND ?
                """,
                (habit_id, start_date, end_date),
            )
            row = cursor.fetchone()
            completed_count = row["completed_count"] if row else 0
            return min(1.0, completed_count / total_days)
        except Exception as e:
            logger.error(f"Error computing completion percentage: {e}")
            return 0.0

    def get_overall_completion_for_date(self, target_date: str) -> float:
        """Returns fraction (0.0 to 1.0) of all active habits completed on target_date."""
        active_habits = self.get_active_habits()
        if not active_habits:
            return 0.0
        try:
            conn = self.get_connection()
            cursor = conn.execute(
                """
                SELECT COUNT(DISTINCT d.habit_id) as cnt
                FROM daily_logs d
                JOIN habits h ON d.habit_id = h.id
                WHERE h.is_active = 1 AND d.completed = 1 AND d.log_date = ?
                """,
                (target_date,),
            )
            row = cursor.fetchone()
            completed = row["cnt"] if row else 0
            return completed / len(active_habits)
        except sqlite3.Error as e:
            logger.error(f"Error computing overall completion for date: {e}")
            return 0.0

    def get_overall_heatmap_data(self, start_date: str, end_date: str) -> Dict[str, float]:
        """Returns dict mapping date string to overall completion ratio (0.0 to 1.0)."""
        active_habits = self.get_active_habits()
        total_active = len(active_habits)
        if total_active == 0:
            return {}

        try:
            conn = self.get_connection()
            cursor = conn.execute(
                """
                SELECT d.log_date, COUNT(DISTINCT d.habit_id) as cnt
                FROM daily_logs d
                JOIN habits h ON d.habit_id = h.id
                WHERE h.is_active = 1 AND d.completed = 1 AND d.log_date BETWEEN ? AND ?
                GROUP BY d.log_date
                """,
                (start_date, end_date),
            )
            rows = cursor.fetchall()
            return {row["log_date"]: (row["cnt"] / total_active) for row in rows}
        except sqlite3.Error as e:
            logger.error(f"Error computing heatmap data: {e}")
            return {}

    def get_category_breakdown(self, start_date: str, end_date: str) -> Dict[str, int]:
        """Returns total completion counts grouped by track/category name."""
        try:
            conn = self.get_connection()
            cursor = conn.execute(
                """
                SELECT COALESCE(t.name, 'Other') as track_name, COUNT(d.id) as completions
                FROM daily_logs d
                JOIN habits h ON d.habit_id = h.id
                LEFT JOIN tracks t ON h.track_id = t.id
                WHERE d.completed = 1 AND d.log_date BETWEEN ? AND ?
                GROUP BY track_name
                ORDER BY completions DESC
                """,
                (start_date, end_date),
            )
            rows = cursor.fetchall()
            return {row["track_name"]: row["completions"] for row in rows}
        except sqlite3.Error as e:
            logger.error(f"Error getting category breakdown: {e}")
            return {}

    def get_weekly_completion_counts(self, start_date: str, end_date: str) -> List[Tuple[str, int]]:
        """Returns list of (log_date, completed_count) pairs for the given range."""
        try:
            conn = self.get_connection()
            cursor = conn.execute(
                """
                SELECT d.log_date, COUNT(d.id) as cnt
                FROM daily_logs d
                JOIN habits h ON d.habit_id = h.id
                WHERE h.is_active = 1 AND d.completed = 1 AND d.log_date BETWEEN ? AND ?
                GROUP BY d.log_date
                ORDER BY d.log_date ASC
                """,
                (start_date, end_date),
            )
            rows = cursor.fetchall()
            counts_map = {row["log_date"]: row["cnt"] for row in rows}

            # Fill missing days with 0
            cur = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
            result = []
            while cur <= end:
                iso = cur.isoformat()
                result.append((iso, counts_map.get(iso, 0)))
                cur += timedelta(days=1)
            return result
        except sqlite3.Error as e:
            logger.error(f"Error getting weekly completion counts: {e}")
            return []

    def get_monthly_trend(self, num_months: int = 4) -> List[Tuple[str, float]]:
        """Returns list of (month_label, completion_ratio) over the last N months."""
        today = date.today()
        trend = []
        active_habits = self.get_active_habits()
        num_habits = len(active_habits)
        if num_habits == 0:
            return []

        for m_offset in range(num_months - 1, -1, -1):
            # calculate year and month
            total_m = today.year * 12 + (today.month - 1) - m_offset
            yr = total_m // 12
            mo = (total_m % 12) + 1
            start_d = f"{yr:04d}-{mo:02d}-01"
            if mo == 12:
                next_m = date(yr + 1, 1, 1)
            else:
                next_m = date(yr, mo + 1, 1)
            end_d = (next_m - timedelta(days=1)).strftime("%Y-%m-%d")
            total_days_in_m = (next_m - timedelta(days=1)).day

            potential = num_habits * total_days_in_m
            try:
                conn = self.get_connection()
                cursor = conn.execute(
                    """
                    SELECT COUNT(d.id) as cnt
                    FROM daily_logs d
                    JOIN habits h ON d.habit_id = h.id
                    WHERE h.is_active = 1 AND d.completed = 1 AND d.log_date BETWEEN ? AND ?
                    """,
                    (start_d, end_d),
                )
                row = cursor.fetchone()
                cnt = row["cnt"] if row else 0
                ratio = min(1.0, cnt / potential) if potential > 0 else 0.0
                month_name = date(yr, mo, 1).strftime("%b %y")
                trend.append((month_name, ratio))
            except sqlite3.Error:
                month_name = date(yr, mo, 1).strftime("%b %y")
                trend.append((month_name, 0.0))

        return trend

    def get_top_and_lowest_habits(self, start_date: str, end_date: str) -> Tuple[List[Tuple[Habit, float]], List[Tuple[Habit, float]]]:
        """Returns (top_performing_habits, needs_attention_habits) with completion % for the date range."""
        habits = self.get_active_habits()
        if not habits:
            return ([], [])

        habit_rates = []
        for h in habits:
            rate = self.get_completion_percentage(h.id, start_date, end_date)
            habit_rates.append((h, rate))

        # Sort descending by completion rate
        habit_rates.sort(key=lambda x: x[1], reverse=True)
        top = habit_rates[:3]
        lowest = sorted(habit_rates, key=lambda x: x[1])[:3]
        return (top, lowest)

    # ==========================================
    # Reset All Data
    # ==========================================

    def reset_all_data(self) -> None:
        """Wipes all data from tables and re-initializes clean schema."""
        try:
            conn = self.get_connection()
            with conn:
                conn.execute("PRAGMA foreign_keys = OFF;")
                conn.execute("DELETE FROM daily_logs;")
                conn.execute("DELETE FROM tasks;")
                conn.execute("DELETE FROM plans;")
                conn.execute("DELETE FROM habits;")
                conn.execute("DELETE FROM tracks;")
                conn.execute("PRAGMA foreign_keys = ON;")
        except sqlite3.Error as e:
            logger.error(f"Error resetting database: {e}")
            raise DatabaseError("Failed to reset application data.") from e
