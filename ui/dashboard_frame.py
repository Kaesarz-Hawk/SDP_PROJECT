"""
Screen 2: Dashboard — the centerpiece.

- Top summary bar: large "Today's Progress" donut, active streaks count, single best streak
- Segmented control: Daily / Weekly / Monthly / Yearly aggregate view
- Grid of habit cards (icon, accent stripe, modern toggle, ring, streak, sparkline)
- 30-day overall completion heatmap strip
- Designed empty state when zero habits exist
"""
from __future__ import annotations

import tkinter as tk
from datetime import date, timedelta
from typing import Optional

import customtkinter as ctk

try:
    from utils.theme import Colors, Fonts, Spacing
except ImportError:  # pragma: no cover
    from ..utils.theme import Colors, Fonts, Spacing

from .components.habit_card import HabitCard
from .components.progress_ring import ProgressRing
from .components.heatmap_grid import HeatmapStrip
from .components.modal_dialog import show_message, show_error


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master, db, app):
        super().__init__(master, fg_color=Colors.BG_BASE, corner_radius=0)
        self.db = db
        self.app = app
        self.timeframe = "Daily"

        # ---- Header (built once) ----
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=Spacing.XL, pady=(Spacing.LG, Spacing.MD))
        left = ctk.CTkFrame(head, fg_color="transparent")
        left.pack(side="left")
        ctk.CTkLabel(left, text="Dashboard", font=Fonts.title(),
                     text_color=Colors.TEXT_PRIMARY).pack(anchor="w")
        self.date_lbl = ctk.CTkLabel(
            left, text=date.today().strftime("%A, %d %B %Y"),
            font=Fonts.body(), text_color=Colors.TEXT_SECONDARY)
        self.date_lbl.pack(anchor="w", pady=(2, 0))

        self.segment = ctk.CTkSegmentedButton(
            head, values=["Daily", "Weekly", "Monthly", "Yearly"],
            font=Fonts.small_bold(), selected_color=Colors.ACCENT,
            selected_hover_color=Colors.ACCENT_HOVER,
            unselected_color=Colors.BG_ELEVATED,
            unselected_hover_color=Colors.BG_HOVER,
            fg_color=Colors.BG_ELEVATED, text_color=Colors.TEXT_SECONDARY,
            command=self._on_timeframe_change)
        self.segment.set("Daily")
        self.segment.pack(side="right")

        # ---- Scrollable content (rebuilt on refresh) ----
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=Spacing.XS, pady=(0, Spacing.MD))

    # ------------------------------------------------------------------ #
    def _on_timeframe_change(self, value: str) -> None:
        self.timeframe = value
        self.after(10, self.refresh)

    def refresh(self) -> None:
        """Rebuild all dynamic content from the database."""
        try:
            for child in self.scroll.winfo_children():
                child.destroy()
            self.segment.set(self.timeframe)
            habits = self.db.get_active_habits()
            if not habits:
                self._build_empty_state()
                return
            self._build_summary()
            self._build_heatmap_strip()
            self._build_habit_grid(habits)
        except Exception as exc:
            print(f"[Momentum:Dashboard] refresh failed: {exc}")
            import traceback
            traceback.print_exc()
            self._build_error_state()

    # ------------------------------------------------------------------ #
    def _build_empty_state(self) -> None:
        box = ctk.CTkFrame(self.scroll, fg_color="transparent")
        box.pack(fill="both", expand=True, pady=Spacing.XXL)
        ctk.CTkLabel(box, text="🚀", font=(Fonts.FAMILY, 64)).pack(pady=(Spacing.XXL, Spacing.SM))
        ctk.CTkLabel(box, text="No habits yet",
                     font=Fonts.subtitle(), text_color=Colors.TEXT_PRIMARY).pack()
        ctk.CTkLabel(box, text="Create your first track to start your streak 🔥",
                     font=Fonts.body(), text_color=Colors.TEXT_SECONDARY).pack(pady=(Spacing.XS, Spacing.LG))
        ctk.CTkButton(box, text="Open Plan Builder", width=200,
                      fg_color=Colors.ACCENT, hover_color=Colors.ACCENT_HOVER,
                      corner_radius=Spacing.BUTTON_RADIUS, font=Fonts.body_bold(),
                      command=lambda: self.app.show_frame("onboarding")).pack()

    def _build_error_state(self) -> None:
        ctk.CTkLabel(self.scroll, text="😅 Couldn't load your dashboard.\nPlease go back to this screen.",
                     font=Fonts.body(), text_color=Colors.TEXT_SECONDARY,
                     justify="center").pack(pady=Spacing.XXL)

    # ------------------------------------------------------------------ #
    def _build_summary(self) -> None:
        """Top summary: donut + active streaks + best streak."""
        row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        row.pack(fill="x", padx=Spacing.MD, pady=(0, Spacing.MD))

        stats = self.db.get_today_progress()

        # Card 1 — Today's Progress donut
        c1 = ctk.CTkFrame(row, fg_color=Colors.BG_CARD,
                          corner_radius=Spacing.CARD_RADIUS)
        c1.pack(side="left", expand=True, fill="both", padx=(0, Spacing.SM))
        ctk.CTkLabel(c1, text="TODAY'S PROGRESS", font=(Fonts.FAMILY, 10, "bold"),
                     text_color=Colors.TEXT_MUTED).pack(anchor="w",
                                                        padx=Spacing.MD, pady=(Spacing.MD, 0))
        mid = ctk.CTkFrame(c1, fg_color="transparent")
        mid.pack(fill="x", padx=Spacing.MD, pady=(Spacing.SM, 0))
        ring = ProgressRing(mid, value=stats["percent"], size=118, width=12,
                            fill_color=Colors.ACCENT, track_color=Colors.BG_ELEVATED,
                            text_color=Colors.TEXT_PRIMARY, font_size=22)
        ring.pack(side="left", padx=(0, Spacing.MD))
        info = ctk.CTkFrame(mid, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(info, text=f"{stats['done']} / {stats['total']}",
                     font=Fonts.stat_number(), text_color=Colors.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(info, text="habits completed today",
                     font=Fonts.small(), text_color=Colors.TEXT_SECONDARY).pack(anchor="w")

        # Card 2 — active streaks
        c2 = ctk.CTkFrame(row, fg_color=Colors.BG_CARD,
                          corner_radius=Spacing.CARD_RADIUS)
        c2.pack(side="left", expand=True, fill="both", padx=Spacing.SM)
        ctk.CTkLabel(c2, text="ACTIVE STREAKS", font=(Fonts.FAMILY, 10, "bold"),
                     text_color=Colors.TEXT_MUTED).pack(anchor="w",
                                                        padx=Spacing.MD, pady=(Spacing.MD, 0))
        streak_val = stats["active_streaks"]
        ctk.CTkLabel(c2, text=f"🔥 {streak_val}", font=Fonts.stat_number(),
                     text_color=Colors.streak_color(streak_val)).pack(anchor="w",
                                                                      padx=Spacing.MD, pady=(Spacing.SM, 0))
        ctk.CTkLabel(c2, text=f"habits on a streak right now",
                     font=Fonts.small(), text_color=Colors.TEXT_SECONDARY).pack(
            anchor="w", padx=Spacing.MD, pady=(0, Spacing.MD))

        # Card 3 — best streak highlighted
        c3 = ctk.CTkFrame(row, fg_color=Colors.BG_CARD,
                          corner_radius=Spacing.CARD_RADIUS)
        c3.pack(side="left", expand=True, fill="both", padx=(Spacing.SM, 0))
        ctk.CTkLabel(c3, text="BEST STREAK", font=(Fonts.FAMILY, 10, "bold"),
                     text_color=Colors.TEXT_MUTED).pack(anchor="w",
                                                        padx=Spacing.MD, pady=(Spacing.MD, 0))
        best = stats["best_streak"]
        ctk.CTkLabel(c3, text=f"🏆 {best}", font=Fonts.stat_number(),
                     text_color=Colors.streak_color(best)).pack(anchor="w",
                                                                padx=Spacing.MD, pady=(Spacing.SM, 0))
        best_habit = stats["best_habit"]
        label = best_habit.display_name() if best_habit else "Keep going!"
        ctk.CTkLabel(c3, text=label, font=Fonts.small(),
                     text_color=Colors.TEXT_SECONDARY).pack(anchor="w",
                                                            padx=Spacing.MD, pady=(0, Spacing.MD))

    def _build_heatmap_strip(self) -> None:
        """Last 30 days of OVERALL (all habits combined) daily completion."""
        card = ctk.CTkFrame(self.scroll, fg_color=Colors.BG_CARD,
                            corner_radius=Spacing.CARD_RADIUS)
        card.pack(fill="x", padx=Spacing.MD, pady=(0, Spacing.MD))
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=Spacing.MD, pady=(Spacing.MD, 0))
        ctk.CTkLabel(top, text="LAST 30 DAYS · OVERALL COMPLETION",
                     font=(Fonts.FAMILY, 10, "bold"),
                     text_color=Colors.TEXT_MUTED).pack(side="left")
        ctk.CTkLabel(top, text="less ■ ■ ■ ■ ■ more",
                     font=Fonts.caption(), text_color=Colors.TEXT_MUTED).pack(side="right")
        ratios = {}
        today = date.today()
        for i in range(30, -1, -1):
            day = today - timedelta(days=i)
            ratios[day.isoformat()] = self.db.get_daily_overall_completion(day.isoformat())
        strip = HeatmapStrip(card, days=30, cell=18, ratios=ratios, bg=Colors.BG_CARD)
        strip.pack(anchor="w", padx=Spacing.MD, pady=(Spacing.SM, Spacing.MD))

    # ------------------------------------------------------------------ #
    def _build_habit_grid(self, habits: list) -> None:
        """2-column grid of habit cards."""
        grid = ctk.CTkFrame(self.scroll, fg_color="transparent")
        grid.pack(fill="x", padx=Spacing.MD, pady=(0, Spacing.LG))
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        for i, habit in enumerate(habits):
            row, col = divmod(i, 2)
            card = HabitCard(
                grid, habit, self.db, timeframe=self.timeframe,
                on_toggle=self._on_toggle, on_details=self._show_details)
            card.grid(row=row, column=col, sticky="nsew",
                      padx=(0, Spacing.SM) if col == 0 else (Spacing.SM, 0),
                      pady=Spacing.SM)

    # ------------------------------------------------------------------ #
    def _on_toggle(self, habit_id: int, completed: bool) -> None:
        """User toggled today's completion → write, then refresh (deferred)."""
        try:
            self.db.toggle_completion(habit_id, date.today().isoformat(), completed)
        except Exception as exc:
            print(f"[Momentum:Dashboard] toggle failed: {exc}")
            show_error(self.winfo_toplevel(), "Could not save",
                       "Your change didn't stick. Please try again.",
                       technical=str(exc))
        # Deferred rebuild — never destroy the switch mid-command
        self.after(30, self.refresh)

    def _show_details(self, habit_id: int) -> None:
        """Per-habit stats pop-over from a card click."""
        try:
            stats = self.db.get_habit_stats(habit_id)
            if not stats.get("exists"):
                show_message(self.winfo_toplevel(), "Habit", "This habit no longer exists.")
                return
            habit = stats["habit"]
            text = (
                f"{habit.display_name()}\n\n"
                f"• Today: {'✓ done' if stats['today_done'] else 'not yet'}\n"
                f"• Current streak: {stats['current_streak']} days\n"
                f"• Best streak ever: {stats['best_streak']} days\n"
                f"• This month: {stats['month_pct']}%\n"
                f"• All-time completions: {stats['all_time_completions']}\n"
                f"• Target: {habit.weekly_target()}× per week\n"
                f"• Track: {habit.track_name or 'None'}"
            )
            show_message(self.winfo_toplevel(), "Habit details", text)
        except Exception as exc:
            print(f"[Momentum:Dashboard] details failed: {exc}")
            show_error(self.winfo_toplevel(), "Could not load details",
                       "Stats for this habit are unavailable right now.", technical=str(exc))
