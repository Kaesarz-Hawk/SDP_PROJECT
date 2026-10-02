"""Dashboard Screen (Screen 2) for Momentum.

Centerpiece screen featuring:
- Top aggregate summary bar with large Donut Progress Ring, active streaks count, and best streak
- Timeframe filter segmented button (Daily / Weekly / Monthly / Yearly)
- 30-day horizontal consistency heatmap strip
- Interactive grid of HabitCards with instant completion toggles, streaks, and sparklines
- Designed empty state for zero habits
"""

from datetime import date, timedelta
from typing import Dict, List, Optional
import customtkinter as ctk

from database.db_manager import DBManager
from models.habit import Habit
from models.track import Track
from ui.components.habit_card import HabitCard
from ui.components.heatmap_grid import HeatmapStrip
from ui.components.progress_ring import ProgressRing
from utils.theme import (
    COLOR_ACCENT,
    COLOR_BG_BASE,
    COLOR_BG_CARD,
    COLOR_BORDER,
    COLOR_SUCCESS,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
    CORNER_MD,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_CAPTION,
    FONT_DISPLAY_LARGE,
    FONT_SECTION_HEADER,
    FONT_STAT_LABEL,
    FONT_STAT_VALUE,
    FONT_SUBTITLE,
    FONT_TITLE,
    PAD_LG,
    PAD_MD,
    PAD_SM,
    PAD_XS,
    PAD_XL,
)


class DashboardFrame(ctk.CTkFrame):
    """Main Dashboard screen frame."""

    def __init__(self, master, db: DBManager, on_navigate_to_onboarding=None, **kwargs):
        super().__init__(master, fg_color=COLOR_BG_BASE, **kwargs)
        self.db = db
        self.on_navigate_to_onboarding = on_navigate_to_onboarding
        self.selected_timeframe = "Weekly"  # Daily, Weekly, Monthly, Yearly

        self._build_screen()

    def refresh(self) -> None:
        """Reloads all data from DB and re-renders the dashboard widgets."""
        self._build_screen()

    def _build_screen(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()

        today = date.today()
        today_iso = today.isoformat()

        # Query all active habits & tracks
        habits = self.db.get_active_habits()
        tracks = {t.id: t for t in self.db.get_all_tracks()}

        # Main scrollable canvas container to support arbitrary screen heights
        scroll_container = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )
        scroll_container.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_MD)

        # 1. Header Bar: Date & Title
        header_frame = ctk.CTkFrame(scroll_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, PAD_MD))

        title_col = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_col.pack(side="left")

        ctk.CTkLabel(
            title_col,
            text=f"Welcome back! 👋",
            font=FONT_TITLE,
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_col,
            text=f"{today.strftime('%A, %B %d, %Y')} • Keep your momentum burning",
            font=FONT_BODY,
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(anchor="w")

        # Timeframe Segmented Control on top-right
        tf_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        tf_frame.pack(side="right", anchor="e")

        ctk.CTkLabel(
            tf_frame,
            text="View Range:",
            font=FONT_CAPTION,
            text_color=COLOR_TEXT_MUTED,
        ).pack(side="left", padx=(0, PAD_SM))

        self.seg_btn = ctk.CTkSegmentedButton(
            tf_frame,
            values=["Daily", "Weekly", "Monthly", "Yearly"],
            command=self._on_timeframe_change,
            selected_color=COLOR_ACCENT,
            selected_hover_color=COLOR_ACCENT,
            font=FONT_BODY,
        )
        self.seg_btn.set(self.selected_timeframe)
        self.seg_btn.pack(side="left")

        # 2. Zero-data empty state handling
        if not habits:
            self._render_empty_state(scroll_container)
            return

        # 3. Calculate Overall Metrics
        total_active_habits = len(habits)
        completed_today_count = 0
        active_streaks_count = 0
        best_streak_overall = 0
        best_streak_habit_name = "None"

        # Determine date range for timeframe completion rates
        if self.selected_timeframe == "Daily":
            range_start = today_iso
        elif self.selected_timeframe == "Weekly":
            range_start = (today - timedelta(days=6)).isoformat()
        elif self.selected_timeframe == "Monthly":
            range_start = (today - timedelta(days=29)).isoformat()
        else:  # Yearly
            range_start = (today - timedelta(days=364)).isoformat()
        range_end = today_iso

        habit_details = []
        for h in habits:
            is_done_today = self.db.is_habit_completed(h.id, today_iso)
            if is_done_today:
                completed_today_count += 1

            curr_streak = self.db.get_current_streak(h.id)
            if curr_streak > 0:
                active_streaks_count += 1

            best_s = self.db.get_best_streak(h.id)
            if best_s > best_streak_overall:
                best_streak_overall = best_s
                best_streak_habit_name = h.name

            # Last 7 days boolean list
            last_7 = []
            for i in range(6, -1, -1):
                d = (today - timedelta(days=i)).isoformat()
                last_7.append(self.db.is_habit_completed(h.id, d))

            ratio = self.db.get_completion_percentage(h.id, range_start, range_end)
            track = tracks.get(h.track_id)
            habit_details.append((h, track, is_done_today, curr_streak, ratio, last_7))

        today_ratio = completed_today_count / total_active_habits if total_active_habits > 0 else 0.0

        # 4. Top Summary Banner (Glassmorphism-inspired card)
        summary_card = ctk.CTkFrame(
            scroll_container,
            fg_color=COLOR_BG_CARD,
            corner_radius=CORNER_MD,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        summary_card.pack(fill="x", pady=(0, PAD_MD))

        sum_inner = ctk.CTkFrame(summary_card, fg_color="transparent")
        sum_inner.pack(fill="x", padx=PAD_LG, pady=PAD_LG)

        # Left: Large Donut Ring for Today's Overall Completion
        donut_col = ctk.CTkFrame(sum_inner, fg_color="transparent")
        donut_col.pack(side="left", padx=(0, PAD_XL))

        overall_ring = ProgressRing(
            donut_col,
            size=96,
            thickness=10,
            progress=today_ratio,
            color=COLOR_SUCCESS if today_ratio >= 0.7 else COLOR_ACCENT,
            bg_color=COLOR_BG_CARD,
        )
        overall_ring.pack(side="left", padx=(0, PAD_MD))

        donut_text_col = ctk.CTkFrame(donut_col, fg_color="transparent")
        donut_text_col.pack(side="left")

        ctk.CTkLabel(
            donut_text_col,
            text=f"{completed_today_count} of {total_active_habits}",
            font=FONT_DISPLAY_LARGE,
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w")

        ctk.CTkLabel(
            donut_text_col,
            text="Habits Completed Today",
            font=FONT_BODY,
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(anchor="w")

        # Vertical Divider
        ctk.CTkFrame(sum_inner, width=1, fg_color=COLOR_BORDER).pack(side="left", fill="y", padx=PAD_LG)

        # Metric 2: Active Streaks
        streak_col = ctk.CTkFrame(sum_inner, fg_color="transparent")
        streak_col.pack(side="left", padx=(PAD_MD, PAD_XL))

        ctk.CTkLabel(
            streak_col,
            text=f"🔥 {active_streaks_count}",
            font=FONT_DISPLAY_LARGE,
            text_color=COLOR_WARNING,
        ).pack(anchor="w")

        ctk.CTkLabel(
            streak_col,
            text="Active Streaks Maintained",
            font=FONT_BODY,
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(anchor="w")

        # Vertical Divider
        ctk.CTkFrame(sum_inner, width=1, fg_color=COLOR_BORDER).pack(side="left", fill="y", padx=PAD_LG)

        # Metric 3: Best Streak Highlight
        best_col = ctk.CTkFrame(sum_inner, fg_color="transparent")
        best_col.pack(side="left", padx=(PAD_MD, 0))

        ctk.CTkLabel(
            best_col,
            text=f"⭐ {best_streak_overall} Days",
            font=FONT_DISPLAY_LARGE,
            text_color="#EC4899",
        ).pack(anchor="w")

        ctk.CTkLabel(
            best_col,
            text=f"Record: {best_streak_habit_name}",
            font=FONT_BODY,
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(anchor="w")

        # 5. Horizontal Mini Heatmap Strip (Last 30 days)
        thirty_days_ago = (today - timedelta(days=29)).isoformat()
        heatmap_data = self.db.get_overall_heatmap_data(thirty_days_ago, today_iso)
        strip = HeatmapStrip(scroll_container, data=heatmap_data, days=30)
        strip.pack(fill="x", pady=(0, PAD_LG))

        # 6. Section Header for Habit Cards
        habits_header = ctk.CTkFrame(scroll_container, fg_color="transparent")
        habits_header.pack(fill="x", pady=(0, PAD_SM))

        ctk.CTkLabel(
            habits_header,
            text=f"ACTIVE HABITS ({total_active_habits})",
            font=FONT_SECTION_HEADER,
            text_color=COLOR_TEXT_MUTED,
        ).pack(side="left")

        # 7. Grid of Habit Cards (2 columns layout)
        cards_container = ctk.CTkFrame(scroll_container, fg_color="transparent")
        cards_container.pack(fill="both", expand=True)

        col_left = ctk.CTkFrame(cards_container, fg_color="transparent")
        col_left.pack(side="left", fill="both", expand=True, padx=(0, PAD_SM))

        col_right = ctk.CTkFrame(cards_container, fg_color="transparent")
        col_right.pack(side="left", fill="both", expand=True, padx=(PAD_SM, 0))

        for idx, (h, track, is_done, streak, ratio, last_7) in enumerate(habit_details):
            parent_col = col_left if (idx % 2 == 0) else col_right
            card = HabitCard(
                parent_col,
                habit=h,
                track=track,
                is_completed_today=is_done,
                current_streak=streak,
                completion_ratio=ratio,
                last_7_days_completed=last_7,
                on_toggle=self._handle_habit_toggle,
            )
            card.pack(fill="x", pady=(0, PAD_MD))

    def _handle_habit_toggle(self, habit_id: int, completed: bool) -> None:
        today_iso = date.today().isoformat()
        self.db.log_daily_completion(habit_id, today_iso, completed)
        # Immediate refresh to reflect new streak & summary percentage
        self.refresh()

    def _on_timeframe_change(self, val: str) -> None:
        self.selected_timeframe = val
        self.refresh()

    def _render_empty_state(self, container) -> None:
        empty_box = ctk.CTkFrame(container, fg_color=COLOR_BG_CARD, corner_radius=CORNER_MD)
        empty_box.pack(fill="both", expand=True, padx=PAD_XL, pady=PAD_XL)

        inner = ctk.CTkFrame(empty_box, fg_color="transparent")
        inner.pack(expand=True, pady=PAD_XL)

        ctk.CTkLabel(inner, text="🌱", font=("Segoe UI", 48)).pack(pady=(0, PAD_MD))
        ctk.CTkLabel(inner, text="No Habits Tracked Yet", font=FONT_TITLE, text_color=COLOR_TEXT_PRIMARY).pack(pady=(0, PAD_SM))
        ctk.CTkLabel(
            inner,
            text="Define your first track and build habits to spark your consistency streak 🔥",
            font=FONT_BODY,
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(pady=(0, PAD_LG))

        if self.on_navigate_to_onboarding:
            ctk.CTkButton(
                inner,
                text="Create First Goal Plan 🚀",
                font=FONT_BODY_BOLD,
                fg_color=COLOR_ACCENT,
                command=self.on_navigate_to_onboarding,
            ).pack()
