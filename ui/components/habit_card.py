"""Reusable Habit Card component for the Dashboard.

Displays habit metadata, category accent stripe, today's toggle switch,
streak count with intensifying flame, 7-day mini trend sparkline, and donut progress ring.
"""

from datetime import date, timedelta
import tkinter as tk
from typing import Callable, List, Optional
import customtkinter as ctk

from models.habit import Habit
from models.track import Track
from ui.components.progress_ring import ProgressRing
from utils.streak_calculator import get_streak_flame_level
from utils.theme import (
    COLOR_ACCENT,
    COLOR_BG_CARD,
    COLOR_BG_CARD_HOVER,
    COLOR_BORDER,
    COLOR_SUCCESS,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    CORNER_MD,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_CAPTION,
    FONT_SECTION_HEADER,
    PAD_MD,
    PAD_SM,
    PAD_XS,
)


class HabitCard(ctk.CTkFrame):
    """Modern dashboard habit card."""

    def __init__(
        self,
        master,
        habit: Habit,
        track: Optional[Track],
        is_completed_today: bool,
        current_streak: int,
        completion_ratio: float,
        last_7_days_completed: List[bool],
        on_toggle: Callable[[int, bool], None],
        **kwargs,
    ):
        super().__init__(
            master,
            fg_color=COLOR_BG_CARD,
            corner_radius=CORNER_MD,
            border_width=1,
            border_color=COLOR_BORDER,
            **kwargs,
        )
        self.habit = habit
        self.track = track
        self.is_completed_today = is_completed_today
        self.current_streak = current_streak
        self.completion_ratio = completion_ratio
        self.last_7_days_completed = last_7_days_completed
        self.on_toggle = on_toggle

        self._build_card()

    def _build_card(self) -> None:
        track_color = self.track.color_hex if self.track else COLOR_ACCENT
        track_name = self.track.name if self.track else "General"

        # Main horizontal layout: Left Accent Stripe + Content Box
        main_layout = ctk.CTkFrame(self, fg_color="transparent")
        main_layout.pack(fill="both", expand=True)

        # 1. Left Color Stripe
        stripe = ctk.CTkFrame(
            main_layout,
            width=6,
            fg_color=track_color,
            corner_radius=2,
        )
        stripe.pack(side="left", fill="y", padx=(PAD_SM, 0), pady=PAD_SM)

        # 2. Content Container
        content = ctk.CTkFrame(main_layout, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=PAD_MD, pady=PAD_MD)

        # Header: Icon + Name + Category Tag
        header_row = ctk.CTkFrame(content, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, PAD_SM))

        icon_lbl = ctk.CTkLabel(
            header_row,
            text=self.habit.icon or "⚡",
            font=("Segoe UI", 20),
        )
        icon_lbl.pack(side="left", padx=(0, PAD_SM))

        name_col = ctk.CTkFrame(header_row, fg_color="transparent")
        name_col.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            name_col,
            text=self.habit.name,
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            name_col,
            text=track_name,
            font=FONT_CAPTION,
            text_color=track_color,
            anchor="w",
        ).pack(fill="x")

        # Middle Row: Mini 7-day sparkline + Streak badge + Donut progress
        mid_row = ctk.CTkFrame(content, fg_color="transparent")
        mid_row.pack(fill="x", pady=(PAD_SM, PAD_SM))

        # 7-day sparkline mini indicators
        spark_frame = ctk.CTkFrame(mid_row, fg_color="transparent")
        spark_frame.pack(side="left", anchor="w")

        ctk.CTkLabel(
            spark_frame,
            text="Last 7 Days:",
            font=FONT_CAPTION,
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w", pady=(0, 2))

        dots_row = ctk.CTkFrame(spark_frame, fg_color="transparent")
        dots_row.pack(anchor="w")

        for done in self.last_7_days_completed:
            dot = ctk.CTkFrame(
                dots_row,
                width=10,
                height=10,
                corner_radius=5,
                fg_color=COLOR_SUCCESS if done else "#262636",
            )
            dot.pack(side="left", padx=2)

        # Streak indicator
        flame_icon, flame_color = get_streak_flame_level(self.current_streak)
        streak_frame = ctk.CTkFrame(mid_row, fg_color="#222230", corner_radius=8)
        streak_frame.pack(side="left", padx=PAD_MD)

        streak_lbl = ctk.CTkLabel(
            streak_frame,
            text=f"{flame_icon} {self.current_streak}d streak",
            font=FONT_BODY_BOLD,
            text_color=flame_color,
            padx=8,
            pady=4,
        )
        streak_lbl.pack()

        # Mini Progress Ring on the right
        self.ring = ProgressRing(
            mid_row,
            size=46,
            thickness=5,
            progress=self.completion_ratio,
            color=track_color,
            bg_color=COLOR_BG_CARD,
        )
        self.ring.pack(side="right")

        # Bottom Row: CTkSwitch for Today's Completion Toggle
        bottom_row = ctk.CTkFrame(content, fg_color="transparent")
        bottom_row.pack(fill="x", pady=(PAD_SM, 0))

        self.switch_var = ctk.BooleanVar(value=self.is_completed_today)
        self.switch = ctk.CTkSwitch(
            bottom_row,
            text="Completed Today" if self.is_completed_today else "Mark as Done",
            variable=self.switch_var,
            command=self._handle_switch,
            font=FONT_BODY,
            progress_color=COLOR_SUCCESS,
            button_color=COLOR_TEXT_PRIMARY,
            button_hover_color=COLOR_ACCENT,
        )
        self.switch.pack(side="left")

    def _handle_switch(self) -> None:
        val = self.switch_var.get()
        self.switch.configure(text="Completed Today" if val else "Mark as Done")
        if self.on_toggle:
            self.on_toggle(self.habit.id, val)
