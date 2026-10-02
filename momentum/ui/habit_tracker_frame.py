"""
Screen 3: Habit Tracker — deep/detailed matrix view.

- Rows = habits, columns = days of the selected month
- Click any cell → toggle complete/incomplete (instant green check feedback)
- Month/year navigation (past & future)
- Per-habit stats panel: completion %, current streak, best streak, total completions
- Full CRUD: Add / Edit / Delete (delete = confirm dialog + soft delete)
"""
from __future__ import annotations

import tkinter as tk
from datetime import date, timedelta
import calendar as calendar_mod

import customtkinter as ctk

try:
    from utils.theme import Colors, Fonts, Spacing
except ImportError:  # pragma: no cover
    from ..utils.theme import Colors, Fonts, Spacing

from .components.modal_dialog import ConfirmModal, FormModal, show_message, show_error

LABEL_W = 170     # habit name column width on the grid canvas
CELL_H = 30       # row height
TOP_PAD = 26      # weekday header space


class HabitTrackerFrame(ctk.CTkFrame):
    def __init__(self, master, db, app):
        super().__init__(master, fg_color=Colors.BG_BASE, corner_radius=0)
        self.db = db
        self.app = app
        today = date.today()
        self.year = today.year
        self.month = today.month
        self.selected_habit_id: int | None = None

        # ---- Header ----
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=Spacing.XL, pady=(Spacing.LG, Spacing.MD))
        ctk.CTkLabel(head, text="Habit Tracker", font=Fonts.title(),
                     text_color=Colors.TEXT_PRIMARY).pack(side="left")
        ctk.CTkButton(
            head, text="＋ Add habit", width=130, height=34,
            fg_color=Colors.ACCENT, hover_color=Colors.ACCENT_HOVER,
            corner_radius=Spacing.BUTTON_RADIUS, font=Fonts.body_bold(),
            command=self._add_habit).pack(side="right")

        # ---- Month navigation ----
        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.pack(fill="x", padx=Spacing.XL, pady=(0, Spacing.SM))
        self.month_lbl = ctk.CTkLabel(nav, text="", font=Fonts.subtitle(),
                                      text_color=Colors.TEXT_PRIMARY, width=240)
        self.month_lbl.pack(side="left")
        ctk.CTkButton(nav, text="◀", width=40, height=30,
                      fg_color=Colors.BG_ELEVATED, hover_color=Colors.BG_HOVER,
                      text_color=Colors.TEXT_PRIMARY,
                      command=lambda: self._shift_month(-1)).pack(side="right", padx=Spacing.XS)
        ctk.CTkButton(nav, text="Today", width=80, height=30,
                      fg_color=Colors.BG_ELEVATED, hover_color=Colors.BG_HOVER,
                      text_color=Colors.TEXT_PRIMARY,
                      command=self._go_today).pack(side="right", padx=Spacing.XS)
        ctk.CTkButton(nav, text="▶", width=40, height=30,
                      fg_color=Colors.BG_ELEVATED, hover_color=Colors.BG_HOVER,
                      text_color=Colors.TEXT_PRIMARY,
                      command=lambda: self._shift_month(1)).pack(side="right", padx=Spacing.XS)

        # ---- Main: grid canvas + stats side panel ----
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=Spacing.XL, pady=(0, Spacing.LG))

        grid_card = ctk.CTkFrame(body, fg_color=Colors.BG_CARD,
                                 corner_radius=Spacing.CARD_RADIUS)
        grid_card.pack(side="left", fill="both", expand=True, padx=(0, Spacing.MD))
        self.canvas = tk.Canvas(grid_card, bg=Colors.BG_CARD, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True, padx=Spacing.SM, pady=Spacing.SM)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        self.side = ctk.CTkFrame(body, fg_color=Colors.BG_CARD,
                                 corner_radius=Spacing.CARD_RADIUS, width=260)
        self.side.pack(side="right", fill="y")
        self.side.pack_propagate(False)

    # ------------------------------------------------------------------ #
    def _shift_month(self, delta: int) -> None:
        self.month += delta
        if self.month > 12:
            self.month, self.year = 1, self.year + 1
        elif self.month < 1:
            self.month, self.year = 12, self.year - 1
        self.refresh()

    def _go_today(self) -> None:
        today = date.today()
        self.year, self.month = today.year, today.month
        self.refresh()

    # ------------------------------------------------------------------ #
    def refresh(self) -> None:
        try:
            for child in self.side.winfo_children():
                child.destroy()
            self.month_lbl.configure(
                text=f"{calendar_mod.month_name[self.month]} {self.year}")
            self._draw_grid()
            self._draw_side_panel()
        except Exception as exc:
            print(f"[Momentum:HabitTracker] refresh failed: {exc}")
            import traceback
            traceback.print_exc()

    # ------------------------------------------------------------------ #
    def _draw_grid(self) -> None:
        self.canvas.delete("all")
        habits = self.db.get_active_habits()
        if not habits:
            self.canvas.configure(height=320)
            self.canvas.create_text(
                self.canvas.winfo_width() // 2 or 400, 140,
                text="🌱 No habits yet",
                font=(Fonts.FAMILY, 22, "bold"), fill=Colors.TEXT_PRIMARY)
            self.canvas.create_text(
                self.canvas.winfo_width() // 2 or 400, 180,
                text="Click '+ Add habit' to start your first streak 🔥",
                font=(Fonts.FAMILY, 13), fill=Colors.TEXT_SECONDARY)
            self._hit_cells = []
            self._habit_rows = []
            return

        if self.selected_habit_id is None or \
                self.selected_habit_id not in [h.id for h in habits]:
            self.selected_habit_id = habits[0].id

        days_in_month = calendar_mod.monthrange(self.year, self.month)[1]
        width = max(self.canvas.winfo_width(), LABEL_W + days_in_month * 24 + 10)
        height = TOP_PAD + len(habits) * CELL_H + 10
        self.canvas.configure(height=height)

        # Weekday header
        for d in range(1, days_in_month + 1):
            x = LABEL_W + (d - 1) * self.cell_w(days_in_month, width)
            wd = date(self.year, self.month, d).strftime("%a")[0]
            self.canvas.create_text(x + self.cell_w(days_in_month, width) // 2, 12,
                                    text=wd, fill=Colors.TEXT_MUTED,
                                    font=(Fonts.FAMILY, 9))

        # Month logs for hit-testing + painting
        logs = self.db.get_logs_for_month(self.year, self.month)
        done_map: dict[tuple[int, str], bool] = {}
        for log in logs:
            done_map[(log.habit_id, log.log_date)] = bool(log.completed)

        self._hit_cells = []       # (x0,y0,x1,y1, habit_id, iso_date)
        self._habit_rows = []      # (y0, y1, habit)

        for r, habit in enumerate(habits):
            y0 = TOP_PAD + r * CELL_H
            y1 = y0 + CELL_H
            self._habit_rows.append((y0, y1, habit))
            selected = habit.id == self.selected_habit_id
            # Row label background
            self.canvas.create_rectangle(
                0, y0, LABEL_W - 6, y1 - 2,
                fill=Colors.BG_ELEVATED if selected else Colors.BG_INPUT,
                outline=Colors.ACCENT if selected else Colors.BG_CARD,
                width=2 if selected else 1)
            # Color stripe + icon + name
            self.canvas.create_rectangle(0, y0, 5, y1 - 2,
                                         fill=habit.track_color or Colors.CAT_DEFAULT,
                                         outline="")
            self.canvas.create_text(
                14, (y0 + y1) // 2, anchor="w",
                text=f"{habit.icon} {habit.name[:16]}{'…' if len(habit.name) > 16 else ''}",
                fill=Colors.TEXT_PRIMARY, font=(Fonts.FAMILY, 11, "bold"))

            cw = self.cell_w(days_in_month, width)
            for d in range(1, days_in_month + 1):
                iso = f"{self.year:04d}-{self.month:02d}-{d:02d}"
                x0 = LABEL_W + (d - 1) * cw
                x1 = x0 + cw - 2
                done = done_map.get((habit.id, iso), False)
                fill = Colors.SUCCESS if done else Colors.BG_INPUT
                self.canvas.create_rectangle(x0, y0, x1, y1 - 2,
                                             fill=fill, outline=Colors.BG_CARD, width=1)
                if done:
                    self.canvas.create_text((x0 + x1) // 2, (y0 + y1) // 2,
                                            text="✓", fill="#0B3B2E",
                                            font=(Fonts.FAMILY, 11, "bold"))
                self._hit_cells.append((x0, y0, x1, y1 - 2, habit.id, iso))

    @staticmethod
    def cell_w(days_in_month: int, width: int) -> int:
        return max(14, (width - LABEL_W - 8) // days_in_month)

    def _on_canvas_click(self, event) -> None:
        try:
            # Row-label click → select habit
            for y0, y1, habit in getattr(self, "_habit_rows", []):
                if y0 <= event.y <= y1 and event.x <= LABEL_W - 6:
                    if habit.id != self.selected_habit_id:
                        self.selected_habit_id = habit.id
                        self.refresh()
                    return
            # Cell click → toggle completion
            for x0, y0, x1, y1, habit_id, iso in getattr(self, "_hit_cells", []):
                if x0 <= event.x <= x1 and y0 <= event.y <= y1:
                    self._toggle_cell(habit_id, iso)
                    return
        except Exception as exc:
            print(f"[Momentum:HabitTracker] click failed: {exc}")

    def _toggle_cell(self, habit_id: int, iso: str) -> None:
        """Toggle one cell: filled green check ↔ empty cell (instant feedback)."""
        try:
            logs = self.db.get_logs_for_habit(habit_id, iso, iso)
            currently_done = any(l.completed for l in logs)
            self.db.toggle_completion(habit_id, iso, not currently_done)
            # repaint immediately
            self._draw_grid()
            self._draw_side_panel()
        except Exception as exc:
            print(f"[Momentum:HabitTracker] toggle failed: {exc}")
            show_error(self.winfo_toplevel(), "Could not save",
                       "That day could not be updated. Please try again.",
                       technical=str(exc))

    # ------------------------------------------------------------------ #
    def _draw_side_panel(self) -> None:
        for child in self.side.winfo_children():
            child.destroy()

        if not self.db.get_active_habits():
            ctk.CTkLabel(self.side, text="Stats", font=Fonts.subtitle(),
                         text_color=Colors.TEXT_PRIMARY).pack(
                anchor="w", padx=Spacing.MD, pady=Spacing.MD)
            ctk.CTkLabel(self.side, text="No habit selected.\nAdd a habit to see stats here.",
                         font=Fonts.small(), text_color=Colors.TEXT_MUTED,
                         wraplength=210, justify="left").pack(
                anchor="w", padx=Spacing.MD, pady=Spacing.SM)
            return

        habit = self.db.get_habit(self.selected_habit_id)
        if habit is None:
            return
        stats = self.db.get_habit_stats(habit.id)

        ctk.CTkLabel(self.side, text="HABIT DETAILS", font=(Fonts.FAMILY, 10, "bold"),
                     text_color=Colors.TEXT_MUTED).pack(
            anchor="w", padx=Spacing.MD, pady=(Spacing.MD, Spacing.XS))
        ctk.CTkLabel(self.side, text=habit.display_name(), font=Fonts.body_bold(),
                     text_color=Colors.TEXT_PRIMARY, wraplength=220,
                     justify="left").pack(anchor="w", padx=Spacing.MD)

        stats_box = [
            ("Completion (month)", f"{stats['month_pct']}%"),
            ("Current streak", f"🔥 {stats['current_streak']} days"),
            ("Best streak ever", f"🏆 {stats['best_streak']} days"),
            ("Total completions", f"{stats['all_time_completions']}"),
            ("Weekly target", f"{habit.weekly_target()}× / week"),
        ]
        for label, value in stats_box:
            row = ctk.CTkFrame(self.side, fg_color="transparent")
            row.pack(fill="x", padx=Spacing.MD, pady=(Spacing.SM, 0))
            ctk.CTkLabel(row, text=label, font=Fonts.caption(),
                         text_color=Colors.TEXT_MUTED).pack(anchor="w")
            ctk.CTkLabel(row, text=value, font=Fonts.body_bold(),
                         text_color=Colors.TEXT_PRIMARY).pack(anchor="w")

        btns = ctk.CTkFrame(self.side, fg_color="transparent")
        btns.pack(fill="x", padx=Spacing.MD, pady=Spacing.LG)
        ctk.CTkButton(btns, text="✎ Edit", width=100, height=32,
                      fg_color=Colors.BG_ELEVATED, hover_color=Colors.BG_HOVER,
                      text_color=Colors.TEXT_PRIMARY, font=Fonts.small_bold(),
                      command=lambda: self._edit_habit(habit)).pack(
            side="left", padx=(0, Spacing.SM))
        ctk.CTkButton(btns, text="🗑 Delete", width=100, height=32,
                      fg_color=Colors.DANGER, hover_color=Colors.DANGER_HOVER,
                      font=Fonts.small_bold(),
                      command=lambda: self._delete_habit(habit)).pack(side="left")

    # ------------------------------------------------------------------ #
    # CRUD
    # ------------------------------------------------------------------ #
    def _track_options(self) -> list[str]:
        tracks = self.db.get_all_tracks()
        return [f"{t.icon} {t.name}" for t in tracks] or ["(no tracks)"]

    def _track_id_by_label(self, label: str):
        for t in self.db.get_all_tracks():
            if f"{t.icon} {t.name}" == label:
                return t.id
        return None

    def _add_habit(self) -> None:
        tracks = self.db.get_all_tracks()
        if not tracks:
            show_message(self.winfo_toplevel(), "No tracks yet",
                         "Create a track first in the Plan Builder, then add habits to it.",
                         on_ok=lambda: self.app.show_frame("onboarding"))
            return

        fields = [
            {"key": "name", "label": "Habit name", "type": "entry",
             "placeholder": "e.g. Morning Workout", "max_length": 60},
            {"key": "track", "label": "Track / category", "type": "option",
             "options": self._track_options(),
             "initial": tracks[0].icon + " " + tracks[0].name},
            {"key": "icon", "label": "Icon (emoji)", "type": "entry", "initial": "✅",
             "max_length": 4},
            {"key": "freq", "label": "Target / week", "type": "option",
             "options": ["1", "2", "3", "4", "5", "6", "7"], "initial": "5"},
        ]

        def validate(values: dict) -> str | None:
            name = (values.get("name") or "").strip()
            if not name:
                return "Habit name cannot be empty."
            if len(name) > 60:
                return "Habit name is too long (max 60 characters)."
            track_id = self._track_id_by_label(values.get("track", ""))
            if self.db.habit_name_in_track_exists(name, track_id):
                return (f"\"{name}\" already exists in this track. "
                        "Please choose a different name.")
            return None

        def submit(values: dict) -> None:
            try:
                track_id = self._track_id_by_label(values["track"])
                icon = (values.get("icon") or "✅").strip() or "✅"
                self.db.create_habit(track_id, values["name"].strip(), icon,
                                     int(values["freq"]))
                self.refresh()
            except Exception as exc:
                show_error(self.winfo_toplevel(), "Could not save habit",
                           "The habit could not be created.", technical=str(exc))

        FormModal(self.winfo_toplevel(), "Add habit", fields, submit,
                  validate=validate, submit_text="Create")

    def _edit_habit(self, habit) -> None:
        tracks = self.db.get_all_tracks()
        track_labels = ["(none)"] + self._track_options()
        current_label = "(none)"
        if habit.track_id:
            for t in tracks:
                if t.id == habit.track_id:
                    current_label = f"{t.icon} {t.name}"
                    break
        fields = [
            {"key": "name", "label": "Habit name", "type": "entry",
             "initial": habit.name, "max_length": 60},
            {"key": "track", "label": "Track / category", "type": "option",
             "options": track_labels, "initial": current_label},
            {"key": "icon", "label": "Icon (emoji)", "type": "entry",
             "initial": habit.icon, "max_length": 4},
            {"key": "freq", "label": "Target / week", "type": "option",
             "options": ["1", "2", "3", "4", "5", "6", "7"],
             "initial": str(habit.weekly_target())},
        ]

        def validate(values: dict) -> str | None:
            name = (values.get("name") or "").strip()
            if not name:
                return "Habit name cannot be empty."
            track_id = None
            if values.get("track") != "(none)":
                track_id = self._track_id_by_label(values.get("track"))
            if self.db.habit_name_in_track_exists(name, track_id,
                                                  exclude_habit_id=habit.id):
                return f"\"{name}\" already exists in this track. Choose another name."
            return None

        def submit(values: dict) -> None:
            try:
                track_id = None
                if values.get("track") != "(none)":
                    track_id = self._track_id_by_label(values["track"])
                self.db.update_habit(
                    habit.id, name=values["name"].strip(),
                    track_id=track_id, icon=(values.get("icon") or "✅").strip() or "✅",
                    target_frequency=int(values["freq"]))
                self.refresh()
            except Exception as exc:
                show_error(self.winfo_toplevel(), "Could not update habit",
                           "The habit could not be saved.", technical=str(exc))

        FormModal(self.winfo_toplevel(), "Edit habit", fields, submit,
                  validate=validate, submit_text="Save changes")

    def _delete_habit(self, habit) -> None:
        """Confirm-before-delete → soft delete (keeps history for analytics)."""
        def do_delete():
            try:
                self.db.deactivate_habit(habit.id)
                if self.selected_habit_id == habit.id:
                    self.selected_habit_id = None
                self.refresh()
            except Exception as exc:
                show_error(self.winfo_toplevel(), "Could not delete",
                           "The habit could not be removed.", technical=str(exc))

        ConfirmModal(
            self.winfo_toplevel(), "Delete this habit?",
            f"\"{habit.name}\" will be hidden from tracking.\n"
            "Its history is kept for analytics (soft delete).",
            on_confirm=do_delete, confirm_text="Delete habit")
