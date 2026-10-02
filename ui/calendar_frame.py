"""Calendar Screen (Screen 5) for Momentum.

Full month calendar view with heatmap-colored cells representing overall consistency.
Includes:
- Interactive month grid with color intensity mapping to daily completion ratio
- Month / Year navigation controls
- Side inspector panel displaying detailed habit check-ins and tasks for the clicked day
"""

import calendar
from datetime import date, timedelta
from typing import Dict, List, Optional
import customtkinter as ctk

from database.db_manager import DBManager
from models.habit import Habit
from models.task import Task
from models.track import Track
from ui.components.heatmap_grid import MonthHeatmapGrid
from utils.theme import (
    COLOR_ACCENT,
    COLOR_BG_BASE,
    COLOR_BG_CARD,
    COLOR_BORDER,
    COLOR_DANGER,
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
    FONT_SECTION_HEADER,
    FONT_SUBTITLE,
    FONT_TITLE,
    PAD_LG,
    PAD_MD,
    PAD_SM,
    PAD_XS,
)


class CalendarFrame(ctk.CTkFrame):
    """Unified Calendar Screen with consistency heatmap and day inspection."""

    def __init__(self, master, db: DBManager, **kwargs):
        super().__init__(master, fg_color=COLOR_BG_BASE, **kwargs)
        self.db = db

        today = date.today()
        self.selected_year = today.year
        self.selected_month = today.month
        self.active_day_iso = today.isoformat()

        self._build_screen()

    def refresh(self) -> None:
        self._build_screen()

    def _build_screen(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()

        # Header Bar
        header_bar = ctk.CTkFrame(self, fg_color="transparent")
        header_bar.pack(fill="x", padx=PAD_LG, pady=(PAD_MD, PAD_SM))

        left_header = ctk.CTkFrame(header_bar, fg_color="transparent")
        left_header.pack(side="left")

        ctk.CTkLabel(left_header, text="Consistency Calendar", font=FONT_TITLE, text_color=COLOR_TEXT_PRIMARY).pack(side="left", padx=(0, PAD_LG))

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

        month_name = date(self.selected_year, self.selected_month, 1).strftime("%B %Y")
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

        ctk.CTkButton(
            header_bar,
            text="Today",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_BG_CARD,
            hover_color=COLOR_BORDER,
            command=self._jump_to_today,
            width=80,
        ).pack(side="right")

        # Two-Column Layout: Calendar Grid on Left, Day Inspector on Right
        body_frame = ctk.CTkFrame(self, fg_color="transparent")
        body_frame.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_SM)

        left_col = ctk.CTkFrame(body_frame, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, PAD_MD))

        # Query month heatmap ratios
        num_days = calendar.monthrange(self.selected_year, self.selected_month)[1]
        start_d = f"{self.selected_year:04d}-{self.selected_month:02d}-01"
        end_d = f"{self.selected_year:04d}-{self.selected_month:02d}-{num_days:02d}"
        heatmap_ratios = self.db.get_overall_heatmap_data(start_d, end_d)

        # Heatmap Calendar Grid
        self.cal_widget = MonthHeatmapGrid(
            left_col,
            year=self.selected_year,
            month=self.selected_month,
            daily_ratios=heatmap_ratios,
            on_day_click=self._handle_day_click,
        )
        self.cal_widget.selected_date = self.active_day_iso
        self.cal_widget.pack(fill="both", expand=True)

        # Right Column: Day Inspector Side Panel
        right_col = ctk.CTkScrollableFrame(
            body_frame,
            width=340,
            fg_color=COLOR_BG_CARD,
            corner_radius=CORNER_MD,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        right_col.pack(side="right", fill="both", expand=False)

        self._render_day_inspector(right_col)

    def _render_day_inspector(self, panel) -> None:
        try:
            target_date = date.fromisoformat(self.active_day_iso)
            date_display = target_date.strftime("%A, %b %d")
        except ValueError:
            date_display = self.active_day_iso

        # Inspector Title
        ctk.CTkLabel(
            panel,
            text=date_display,
            font=FONT_SUBTITLE,
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", padx=PAD_MD, pady=(PAD_MD, 2))

        # Day overall completion ratio
        day_ratio = self.db.get_overall_completion_for_date(self.active_day_iso)
        ratio_lbl = f"{int(day_ratio * 100)}% Habit Consistency"
        ctk.CTkLabel(
            panel,
            text=ratio_lbl,
            font=FONT_BODY_BOLD,
            text_color=COLOR_SUCCESS if day_ratio >= 0.7 else (COLOR_WARNING if day_ratio > 0 else COLOR_TEXT_MUTED),
        ).pack(anchor="w", padx=PAD_MD, pady=(0, PAD_MD))

        # Divider
        ctk.CTkFrame(panel, height=1, fg_color=COLOR_BORDER).pack(fill="x", padx=PAD_MD, pady=(0, PAD_MD))

        # Section 1: Habits Logged on This Day
        ctk.CTkLabel(
            panel,
            text="HABITS RECORD",
            font=FONT_SECTION_HEADER,
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w", padx=PAD_MD, pady=(0, PAD_SM))

        active_habits = self.db.get_active_habits()
        if not active_habits:
            ctk.CTkLabel(panel, text="No habits configured.", font=FONT_CAPTION, text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=PAD_MD)
        else:
            for h in active_habits:
                is_done = self.db.is_habit_completed(h.id, self.active_day_iso)
                row = ctk.CTkFrame(panel, fg_color="#1E1E2A", corner_radius=6)
                row.pack(fill="x", padx=PAD_MD, pady=3)

                status_icon = "✅" if is_done else "⚪"
                status_color = COLOR_SUCCESS if is_done else COLOR_TEXT_MUTED

                ctk.CTkLabel(
                    row,
                    text=f"{status_icon} {h.icon} {h.name}",
                    font=FONT_BODY,
                    text_color=COLOR_TEXT_PRIMARY if is_done else COLOR_TEXT_SECONDARY,
                ).pack(side="left", padx=PAD_SM, pady=6)

        # Divider
        ctk.CTkFrame(panel, height=1, fg_color=COLOR_BORDER).pack(fill="x", padx=PAD_MD, pady=PAD_MD)

        # Section 2: Tasks Due on This Day
        ctk.CTkLabel(
            panel,
            text="TASKS SCHEDULED",
            font=FONT_SECTION_HEADER,
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w", padx=PAD_MD, pady=(0, PAD_SM))

        tasks = self.db.get_tasks_for_date(self.active_day_iso)
        if not tasks:
            ctk.CTkLabel(
                panel,
                text="No tasks scheduled for this day.",
                font=FONT_CAPTION,
                text_color=COLOR_TEXT_MUTED,
            ).pack(anchor="w", padx=PAD_MD, pady=(0, PAD_MD))
        else:
            for t in tasks:
                t_row = ctk.CTkFrame(panel, fg_color="#1E1E2A", corner_radius=6)
                t_row.pack(fill="x", padx=PAD_MD, pady=3)

                t_done = (t.status == "Done")
                status_ico = "☑" if t_done else "☐"

                ctk.CTkLabel(
                    t_row,
                    text=f"{status_ico} {t.title}",
                    font=FONT_BODY,
                    text_color=COLOR_TEXT_MUTED if t_done else COLOR_TEXT_PRIMARY,
                ).pack(side="left", padx=PAD_SM, pady=6)

                if t.carried_over:
                    badge = ctk.CTkFrame(t_row, fg_color=COLOR_WARNING, corner_radius=4)
                    badge.pack(side="right", padx=PAD_SM)
                    ctk.CTkLabel(badge, text="rolled", font=FONT_CAPTION, text_color="#000000").pack(padx=3, pady=1)

    def _handle_day_click(self, d_iso: str) -> None:
        self.active_day_iso = d_iso
        self.refresh()

    def _prev_month(self) -> None:
        if self.selected_month == 1:
            self.selected_month = 12
            self.selected_year -= 1
        else:
            self.selected_month -= 1
        self.refresh()

    def _next_month(self) -> None:
        if self.selected_month == 12:
            self.selected_month = 1
            self.selected_year += 1
        else:
            self.selected_month += 1
        self.refresh()

    def _jump_to_today(self) -> None:
        today = date.today()
        self.selected_year = today.year
        self.selected_month = today.month
        self.active_day_iso = today.isoformat()
        self.refresh()
