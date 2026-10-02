"""Habit Tracker Screen (Screen 3) for Momentum.

Detailed grid matrix view:
- Rows = Habits, Columns = Days of the selected month
- Click any day cell to toggle complete/incomplete instantly
- Month/Year navigation
- Per-habit stats pane (completion %, current streak, best streak, total completions)
- Full CRUD for habits: Add, Edit, Soft-delete with confirmation modal
"""

import calendar
from datetime import date, timedelta
from typing import Dict, List, Optional
import customtkinter as ctk

from database.db_manager import DBManager
from models.habit import Habit
from models.track import Track
from ui.components.modal_dialog import BaseModal, ConfirmModal, InfoModal
from utils.theme import (
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_BG_BASE,
    COLOR_BG_CARD,
    COLOR_BG_INPUT,
    COLOR_BORDER,
    COLOR_DANGER,
    COLOR_DANGER_HOVER,
    COLOR_SUCCESS,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
    CORNER_MD,
    CORNER_SM,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_CAPTION,
    FONT_DISPLAY_LARGE,
    FONT_SECTION_HEADER,
    FONT_STAT_VALUE,
    FONT_SUBTITLE,
    FONT_TITLE,
    PAD_LG,
    PAD_MD,
    PAD_SM,
    PAD_XS,
    TRACK_ICONS,
)


class HabitFormModal(BaseModal):
    """Modal dialog for creating or editing a habit."""

    def __init__(
        self,
        parent,
        tracks: List[Track],
        habit: Optional[Habit] = None,
        on_save=None,
    ):
        title = "Edit Habit" if habit else "Create New Habit"
        super().__init__(parent, title=title, width=480, height=440)
        self.tracks = tracks
        self.habit = habit
        self.on_save = on_save

        self._build_form()

    def _build_form(self) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_LG)

        ctk.CTkLabel(
            container,
            text="Habit Details",
            font=FONT_SUBTITLE,
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, PAD_MD))

        # Habit Name
        ctk.CTkLabel(container, text="Habit Name*", font=FONT_BODY_BOLD, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")
        self.name_entry = ctk.CTkEntry(
            container,
            placeholder_text="e.g. Daily LeetCode Problem",
            fg_color=COLOR_BG_INPUT,
            border_color=COLOR_BORDER,
        )
        self.name_entry.pack(fill="x", pady=(2, PAD_SM))
        if self.habit:
            self.name_entry.insert(0, self.habit.name)

        # Track Category Dropdown
        ctk.CTkLabel(container, text="Track / Life Category*", font=FONT_BODY_BOLD, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")
        self.track_names = [f"{t.icon} {t.name}" for t in self.tracks]
        default_track = self.track_names[0] if self.track_names else "General"
        if self.habit and self.habit.track_id:
            for t in self.tracks:
                if t.id == self.habit.track_id:
                    default_track = f"{t.icon} {t.name}"
                    break

        self.track_menu = ctk.CTkOptionMenu(
            container,
            values=self.track_names if self.track_names else ["General"],
            fg_color=COLOR_BG_INPUT,
            button_color=COLOR_ACCENT,
            dropdown_fg_color=COLOR_BG_CARD,
        )
        self.track_menu.set(default_track)
        self.track_menu.pack(fill="x", pady=(2, PAD_SM))

        # Icon and Target Frequency Row
        row2 = ctk.CTkFrame(container, fg_color="transparent")
        row2.pack(fill="x", pady=(2, PAD_SM))

        # Icon Picker
        icon_col = ctk.CTkFrame(row2, fg_color="transparent")
        icon_col.pack(side="left", fill="x", expand=True, padx=(0, PAD_SM))
        ctk.CTkLabel(icon_col, text="Icon", font=FONT_BODY_BOLD, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")
        self.icon_menu = ctk.CTkOptionMenu(
            icon_col,
            values=TRACK_ICONS,
            fg_color=COLOR_BG_INPUT,
            button_color=COLOR_BORDER,
            dropdown_fg_color=COLOR_BG_CARD,
            width=80,
        )
        self.icon_menu.set(self.habit.icon if self.habit and self.habit.icon else "⚡")
        self.icon_menu.pack(anchor="w", pady=(2, 0))

        # Target Frequency
        freq_col = ctk.CTkFrame(row2, fg_color="transparent")
        freq_col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(freq_col, text="Target Days / Week", font=FONT_BODY_BOLD, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")
        self.freq_menu = ctk.CTkOptionMenu(
            freq_col,
            values=["1", "2", "3", "4", "5", "6", "7"],
            fg_color=COLOR_BG_INPUT,
            button_color=COLOR_BORDER,
            dropdown_fg_color=COLOR_BG_CARD,
            width=80,
        )
        self.freq_menu.set(str(self.habit.target_frequency) if self.habit else "7")
        self.freq_menu.pack(anchor="w", pady=(2, 0))

        # Error label
        self.error_label = ctk.CTkLabel(
            container,
            text="",
            font=FONT_CAPTION,
            text_color=COLOR_DANGER,
        )
        self.error_label.pack(anchor="w", pady=(PAD_SM, 0))

        # Action Buttons
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom")

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            fg_color=COLOR_BG_INPUT,
            hover_color=COLOR_BORDER,
            command=self.destroy,
            width=90,
        ).pack(side="right", padx=(PAD_SM, 0))

        ctk.CTkButton(
            btn_row,
            text="Save Habit",
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            command=self._save,
            width=110,
        ).pack(side="right")

    def _save(self) -> None:
        name = self.name_entry.get().strip()
        if not name:
            self.error_label.configure(text="Please provide a habit name.")
            return

        selected_track_str = self.track_menu.get()
        track_id = None
        for t in self.tracks:
            if f"{t.icon} {t.name}" == selected_track_str:
                track_id = t.id
                break

        icon = self.icon_menu.get()
        try:
            freq = int(self.freq_menu.get())
        except ValueError:
            freq = 7

        self.destroy()
        if self.on_save:
            self.on_save(name, track_id, icon, freq)


class HabitTrackerFrame(ctk.CTkFrame):
    """Deep monthly habit matrix view."""

    def __init__(self, master, db: DBManager, **kwargs):
        super().__init__(master, fg_color=COLOR_BG_BASE, **kwargs)
        self.db = db

        today = date.today()
        self.current_year = today.year
        self.current_month = today.month
        self.selected_habit_id: Optional[int] = None

        self._build_screen()

    def refresh(self) -> None:
        self._build_screen()

    def _build_screen(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()

        tracks = {t.id: t for t in self.db.get_all_tracks()}
        habits = self.db.get_active_habits()

        if not self.selected_habit_id and habits:
            self.selected_habit_id = habits[0].id

        # Main layout: Top Bar + Matrix Table + Bottom/Side Stats Pane
        header_bar = ctk.CTkFrame(self, fg_color="transparent")
        header_bar.pack(fill="x", padx=PAD_LG, pady=(PAD_MD, PAD_SM))

        # Title & Month Selector
        left_header = ctk.CTkFrame(header_bar, fg_color="transparent")
        left_header.pack(side="left")

        ctk.CTkLabel(left_header, text="Habit Matrix", font=FONT_TITLE, text_color=COLOR_TEXT_PRIMARY).pack(side="left", padx=(0, PAD_LG))

        nav_box = ctk.CTkFrame(left_header, fg_color=COLOR_BG_CARD, corner_radius=CORNER_SM)
        nav_box.pack(side="left")

        ctk.CTkButton(
            nav_box,
            text="◀",
            width=32,
            height=28,
            fg_color="transparent",
            hover_color=COLOR_BORDER,
            command=self._prev_month,
        ).pack(side="left", padx=2)

        month_name = date(self.current_year, self.current_month, 1).strftime("%B %Y")
        ctk.CTkLabel(
            nav_box,
            text=month_name,
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_PRIMARY,
            width=130,
        ).pack(side="left", padx=PAD_SM)

        ctk.CTkButton(
            nav_box,
            text="▶",
            width=32,
            height=28,
            fg_color="transparent",
            hover_color=COLOR_BORDER,
            command=self._next_month,
        ).pack(side="left", padx=2)

        # Right Action: Add Habit
        ctk.CTkButton(
            header_bar,
            text="+ Add Habit",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            command=self._show_add_modal,
        ).pack(side="right")

        if not habits:
            self._render_empty_state()
            return

        # Days in current month
        num_days = calendar.monthrange(self.current_year, self.current_month)[1]
        today = date.today()

        # Build Month Logs Map: (habit_id, day) -> completed
        month_logs = self.db.get_logs_for_month(self.current_year, self.current_month)
        log_lookup = set()
        for l in month_logs:
            if l.completed:
                day_int = int(l.log_date.split("-")[2])
                log_lookup.add((l.habit_id, day_int))

        # Main split: Matrix on top, Stats panel at bottom
        main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_scroll.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_SM)

        # Matrix Table Card
        matrix_card = ctk.CTkFrame(
            main_scroll,
            fg_color=COLOR_BG_CARD,
            corner_radius=CORNER_MD,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        matrix_card.pack(fill="x", pady=(0, PAD_MD))

        # Horizontal scroll or packed columns
        # Column headers: Habit Info (fixed width 180), then 1..num_days, then Actions (60)
        table_header = ctk.CTkFrame(matrix_card, fg_color="transparent")
        table_header.pack(fill="x", padx=PAD_SM, pady=(PAD_SM, PAD_XS))

        ctk.CTkLabel(
            table_header,
            text="Habit / Category",
            font=FONT_SECTION_HEADER,
            text_color=COLOR_TEXT_MUTED,
            width=180,
            anchor="w",
        ).pack(side="left", padx=(PAD_SM, 0))

        days_frame = ctk.CTkFrame(table_header, fg_color="transparent")
        days_frame.pack(side="left", fill="x", expand=True)

        for d in range(1, num_days + 1):
            day_date = date(self.current_year, self.current_month, d)
            is_today = (day_date == today)
            weekday_str = day_date.strftime("%a")[0]

            hdr_col = ctk.CTkFrame(days_frame, fg_color="transparent", width=24)
            hdr_col.pack(side="left", expand=True, fill="both")

            ctk.CTkLabel(
                hdr_col,
                text=f"{weekday_str}\n{d}",
                font=FONT_CAPTION,
                text_color=COLOR_SUCCESS if is_today else COLOR_TEXT_MUTED,
            ).pack()

        ctk.CTkLabel(table_header, text="Actions", font=FONT_SECTION_HEADER, text_color=COLOR_TEXT_MUTED, width=70).pack(side="right", padx=PAD_SM)

        # Divider
        ctk.CTkFrame(matrix_card, height=1, fg_color=COLOR_BORDER).pack(fill="x", padx=PAD_SM, pady=(0, PAD_XS))

        # Habit Rows
        for h in habits:
            track = tracks.get(h.track_id)
            track_col = track.color_hex if track else COLOR_ACCENT
            is_selected = (h.id == self.selected_habit_id)

            row_frame = ctk.CTkFrame(
                matrix_card,
                fg_color="#222230" if is_selected else "transparent",
                corner_radius=6,
            )
            row_frame.pack(fill="x", padx=PAD_SM, pady=2)

            # Left habit name click selects habit for stats panel
            left_btn = ctk.CTkButton(
                row_frame,
                text=f"{h.icon} {h.name}",
                font=FONT_BODY_BOLD,
                anchor="w",
                width=180,
                fg_color="transparent",
                hover_color=COLOR_BORDER,
                text_color=track_col if is_selected else COLOR_TEXT_PRIMARY,
                command=lambda hid=h.id: self._select_habit(hid),
            )
            left_btn.pack(side="left", padx=(PAD_SM, 0))

            # Days checkboxes/buttons
            cells_row = ctk.CTkFrame(row_frame, fg_color="transparent")
            cells_row.pack(side="left", fill="x", expand=True)

            for d in range(1, num_days + 1):
                is_done = (h.id, d) in log_lookup
                day_d = date(self.current_year, self.current_month, d)
                is_today = (day_d == today)

                btn = ctk.CTkButton(
                    cells_row,
                    text="✓" if is_done else "",
                    width=22,
                    height=24,
                    corner_radius=4,
                    fg_color=COLOR_SUCCESS if is_done else "#1C1C26",
                    hover_color=COLOR_ACCENT,
                    text_color="#FFFFFF",
                    font=FONT_CAPTION,
                    border_width=1 if is_today else 0,
                    border_color=COLOR_TEXT_PRIMARY if is_today else (COLOR_SUCCESS if is_done else "#1C1C26"),
                    command=lambda hid=h.id, dnum=d, cur=is_done: self._toggle_day(hid, dnum, cur),
                )
                btn.pack(side="left", expand=True, padx=1)

            # Row Action Buttons: Edit & Delete
            actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=70)
            actions_frame.pack(side="right", padx=PAD_SM)

            ctk.CTkButton(
                actions_frame,
                text="✏️",
                width=26,
                height=24,
                fg_color="transparent",
                hover_color=COLOR_BORDER,
                command=lambda hb=h: self._show_edit_modal(hb),
            ).pack(side="left", padx=1)

            ctk.CTkButton(
                actions_frame,
                text="🗑️",
                width=26,
                height=24,
                fg_color="transparent",
                hover_color=COLOR_DANGER,
                command=lambda hid=h.id, hname=h.name: self._show_delete_modal(hid, hname),
            ).pack(side="left", padx=1)

        # Stats Panel for currently selected habit
        if self.selected_habit_id:
            sel_habit = self.db.get_habit_by_id(self.selected_habit_id)
            if sel_habit:
                self._render_stats_pane(main_scroll, sel_habit, tracks.get(sel_habit.track_id), num_days)

    def _render_stats_pane(self, parent, habit: Habit, track: Optional[Track], num_days: int) -> None:
        stats_card = ctk.CTkFrame(
            parent,
            fg_color=COLOR_BG_CARD,
            corner_radius=CORNER_MD,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        stats_card.pack(fill="x", pady=(0, PAD_MD))

        inner = ctk.CTkFrame(stats_card, fg_color="transparent")
        inner.pack(fill="x", padx=PAD_LG, pady=PAD_MD)

        # Header
        track_name = track.name if track else "General"
        track_color = track.color_hex if track else COLOR_ACCENT

        title_frame = ctk.CTkFrame(inner, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, PAD_MD))

        ctk.CTkLabel(
            title_frame,
            text=f"{habit.icon} {habit.name}",
            font=FONT_TITLE,
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(side="left")

        ctk.CTkLabel(
            title_frame,
            text=f"• {track_name} (Target: {habit.target_frequency}x/week)",
            font=FONT_BODY,
            text_color=track_color,
        ).pack(side="left", padx=(PAD_SM, 0))

        # Metrics columns
        metrics_row = ctk.CTkFrame(inner, fg_color="transparent")
        metrics_row.pack(fill="x")

        # Current streak
        curr_streak = self.db.get_current_streak(habit.id)
        best_streak = self.db.get_best_streak(habit.id)
        total_completions = self.db.get_total_completions(habit.id)

        start_of_month = f"{self.current_year:04d}-{self.current_month:02d}-01"
        end_of_month = f"{self.current_year:04d}-{self.current_month:02d}-{num_days:02d}"
        month_rate = self.db.get_completion_percentage(habit.id, start_of_month, end_of_month)

        stat_items = [
            ("Monthly Rate", f"{int(month_rate * 100)}%", COLOR_ACCENT),
            ("Current Streak", f"🔥 {curr_streak} Days", COLOR_WARNING),
            ("Best Streak", f"⭐ {best_streak} Days", "#EC4899"),
            ("Total Check-ins", f"✨ {total_completions}", COLOR_SUCCESS),
        ]

        for label, val, color in stat_items:
            box = ctk.CTkFrame(metrics_row, fg_color="#222230", corner_radius=CORNER_SM)
            box.pack(side="left", expand=True, fill="both", padx=PAD_XS)
            ctk.CTkLabel(box, text=val, font=FONT_STAT_VALUE, text_color=color).pack(pady=(PAD_SM, 2))
            ctk.CTkLabel(box, text=label, font=FONT_CAPTION, text_color=COLOR_TEXT_SECONDARY).pack(pady=(0, PAD_SM))

    def _select_habit(self, habit_id: int) -> None:
        self.selected_habit_id = habit_id
        self.refresh()

    def _toggle_day(self, habit_id: int, day_num: int, current_status: bool) -> None:
        log_date = f"{self.current_year:04d}-{self.current_month:02d}-{day_num:02d}"
        self.db.toggle_completion(habit_id, log_date, not current_status)
        self.refresh()

    def _prev_month(self) -> None:
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.refresh()

    def _next_month(self) -> None:
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.refresh()

    def _show_add_modal(self) -> None:
        tracks = self.db.get_all_tracks()
        if not tracks:
            InfoModal(self, title="No Tracks", message="Please create at least one Track category before creating habits.")
            return

        def handle_save(name, track_id, icon, freq):
            self.db.create_habit(track_id=track_id, name=name, icon=icon, target_frequency=freq)
            self.refresh()

        HabitFormModal(self, tracks=tracks, on_save=handle_save)

    def _show_edit_modal(self, habit: Habit) -> None:
        tracks = self.db.get_all_tracks()

        def handle_save(name, track_id, icon, freq):
            self.db.update_habit(habit.id, name=name, track_id=track_id, icon=icon, target_frequency=freq)
            self.refresh()

        HabitFormModal(self, tracks=tracks, habit=habit, on_save=handle_save)

    def _show_delete_modal(self, habit_id: int, habit_name: str) -> None:
        def handle_delete():
            self.db.deactivate_habit(habit_id)
            if self.selected_habit_id == habit_id:
                self.selected_habit_id = None
            self.refresh()

        ConfirmModal(
            self,
            title="Deactivate Habit",
            message=f"Are you sure you want to remove '{habit_name}'? Historical completion records will be safely retained.",
            confirm_text="Remove",
            is_danger=True,
            on_confirm=handle_delete,
        )

    def _render_empty_state(self) -> None:
        empty = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=CORNER_MD)
        empty.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_LG)

        inner = ctk.CTkFrame(empty, fg_color="transparent")
        inner.pack(expand=True)

        ctk.CTkLabel(inner, text="📋", font=("Segoe UI", 48)).pack(pady=(0, PAD_MD))
        ctk.CTkLabel(inner, text="No Habits Found", font=FONT_TITLE, text_color=COLOR_TEXT_PRIMARY).pack(pady=(0, PAD_SM))
        ctk.CTkLabel(
            inner,
            text="Add your first habit using the button above to begin filling the consistency grid.",
            font=FONT_BODY,
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(pady=(0, PAD_LG))
        ctk.CTkButton(
            inner,
            text="+ Add Habit",
            fg_color=COLOR_ACCENT,
            command=self._show_add_modal,
        ).pack()
