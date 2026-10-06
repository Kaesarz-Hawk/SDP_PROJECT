"""
Screen 5: Calendar — unified consistency heatmap calendar.

- Full month grid (Mon–Sun rows), heatmap intensity = overall completion % that day
- Month/year navigation
- Click a day → side panel showing exactly which habits were done/missed
  and which tasks were completed/pending that day
- Zero-data months render cleanly (empty cells, no errors)
"""
from __future__ import annotations

from datetime import date

import customtkinter as ctk

try:
    from utils.theme import Colors, Fonts, Spacing
except ImportError:  # pragma: no cover
    from ..utils.theme import Colors, Fonts, Spacing

from .components.heatmap_grid import HeatmapCalendar


class CalendarFrame(ctk.CTkFrame):
    def __init__(self, master, db, app):
        super().__init__(master, fg_color=Colors.BG_BASE, corner_radius=0)
        self.db = db
        self.app = app
        today = date.today()
        self.year = today.year
        self.month = today.month
        self.selected_day: date = today

        # ---- Header ----
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=Spacing.XL, pady=(Spacing.LG, Spacing.MD))
        ctk.CTkLabel(head, text="Calendar", font=Fonts.title(),
                     text_color=Colors.TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(head, text="Color = overall completion that day",
                     font=Fonts.small(), text_color=Colors.TEXT_MUTED).pack(
            side="left", padx=Spacing.MD)

        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.pack(fill="x", padx=Spacing.XL, pady=(0, Spacing.SM))
        self.month_lbl = ctk.CTkLabel(nav, text="", font=Fonts.subtitle(),
                                      text_color=Colors.TEXT_PRIMARY, width=220)
        self.month_lbl.pack(side="left")
        ctk.CTkButton(nav, text="◀", width=40, height=30,
                      fg_color=Colors.BG_ELEVATED, hover_color=Colors.BG_HOVER,
                      text_color=Colors.TEXT_PRIMARY,
                      command=lambda: self._shift(-1)).pack(side="right", padx=Spacing.XS)
        ctk.CTkButton(nav, text="Today", width=80, height=30,
                      fg_color=Colors.BG_ELEVATED, hover_color=Colors.BG_HOVER,
                      text_color=Colors.TEXT_PRIMARY,
                      command=self._go_today).pack(side="right", padx=Spacing.XS)
        ctk.CTkButton(nav, text="▶", width=40, height=30,
                      fg_color=Colors.BG_ELEVATED, hover_color=Colors.BG_HOVER,
                      text_color=Colors.TEXT_PRIMARY,
                      command=lambda: self._shift(1)).pack(side="right", padx=Spacing.XS)

        # ---- Body: heatmap + day detail panel ----
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=Spacing.XL, pady=(0, Spacing.LG))

        left = ctk.CTkFrame(body, fg_color=Colors.BG_CARD,
                            corner_radius=Spacing.CARD_RADIUS)
        left.pack(side="left", fill="both", expand=True, padx=(0, Spacing.MD))
        self.cal_holder = ctk.CTkFrame(left, fg_color="transparent")
        self.cal_holder.pack(fill="both", expand=True, padx=Spacing.SM, pady=Spacing.SM)

        self.panel = ctk.CTkFrame(body, fg_color=Colors.BG_CARD,
                                  corner_radius=Spacing.CARD_RADIUS, width=300)
        self.panel.pack(side="right", fill="y")
        self.panel.pack_propagate(False)

        self.cal: HeatmapCalendar | None = None

    # ------------------------------------------------------------------ #
    def _shift(self, delta: int) -> None:
        self.month += delta
        if self.month > 12:
            self.month, self.year = 1, self.year + 1
        elif self.month < 1:
            self.month, self.year = 12, self.year - 1
        # keep selected day inside a valid nearby date
        self.selected_day = date(self.year, self.month, min(self.selected_day.day, 28))
        self.refresh()

    def _go_today(self) -> None:
        today = date.today()
        self.year, self.month = today.year, today.month
        self.selected_day = today
        self.refresh()

    # ------------------------------------------------------------------ #
    def refresh(self) -> None:
        try:
            import calendar as calendar_mod
            self.month_lbl.configure(
                text=f"{calendar_mod.month_name[self.month]} {self.year}")

            ratios = {}
            last = calendar_mod.monthrange(self.year, self.month)[1]
            for d in range(1, last + 1):
                iso = f"{self.year:04d}-{self.month:02d}-{d:02d}"
                ratios[iso] = self.db.get_daily_overall_completion(iso)

            for child in self.cal_holder.winfo_children():
                child.destroy()
            self.cal = HeatmapCalendar(
                self.cal_holder, self.year, self.month, ratios=ratios,
                selected=self.selected_day, on_click=self._on_day_click,
                cell_w=92, cell_h=72, bg=Colors.BG_CARD)
            self.cal.pack(anchor="n")

            self._render_day_panel()
        except Exception as exc:
            print(f"[Momentum:Calendar] refresh failed: {exc}")
            import traceback
            traceback.print_exc()

    def _on_day_click(self, day: date) -> None:
        self.selected_day = day
        if self.cal:
            self.cal.selected = day
            self.cal.redraw()
        self._render_day_panel()

    # ------------------------------------------------------------------ #
    def _render_day_panel(self) -> None:
        for child in self.panel.winfo_children():
            child.destroy()
        day = self.selected_day
        iso = day.isoformat()

        ctk.CTkLabel(self.panel, text="DAY DETAIL", font=(Fonts.FAMILY, 10, "bold"),
                     text_color=Colors.TEXT_MUTED).pack(
            anchor="w", padx=Spacing.MD, pady=(Spacing.MD, 2))
        ctk.CTkLabel(self.panel, text=day.strftime("%A, %d %B %Y"),
                     font=Fonts.body_bold(), text_color=Colors.TEXT_PRIMARY).pack(
            anchor="w", padx=Spacing.MD)

        ratio = self.db.get_daily_overall_completion(iso)
        ctk.CTkLabel(self.panel, text=f"Overall: {int(ratio * 100)}% complete",
                     font=Fonts.small(),
                     text_color=Colors.SUCCESS if ratio >= 0.99 else Colors.WARNING).pack(
            anchor="w", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))

        # Habits done / missed
        ctk.CTkLabel(self.panel, text="HABITS", font=(Fonts.FAMILY, 10, "bold"),
                     text_color=Colors.TEXT_MUTED).pack(anchor="w", padx=Spacing.MD)
        habits = self.db.get_active_habits()
        if not habits:
            ctk.CTkLabel(self.panel, text="No habits yet.",
                         font=Fonts.small(), text_color=Colors.TEXT_MUTED).pack(
                anchor="w", padx=Spacing.MD, pady=Spacing.XS)
        else:
            done_ids = {l.habit_id for l in self.db.get_logs_for_day(iso) if l.completed}
            for h in habits:
                done = h.id in done_ids
                mark = "✅" if done else "❌"
                ctk.CTkLabel(self.panel, text=f"{mark} {h.display_name()}",
                             font=Fonts.small(),
                             text_color=Colors.TEXT_SECONDARY,
                             anchor="w", wraplength=250, justify="left").pack(
                    fill="x", padx=Spacing.MD, pady=1)

        # Tasks for that day
        ctk.CTkLabel(self.panel, text="TASKS", font=(Fonts.FAMILY, 10, "bold"),
                     text_color=Colors.TEXT_MUTED).pack(
            anchor="w", padx=Spacing.MD, pady=(Spacing.MD, 0))
        tasks = self.db.get_tasks_for_date(iso)
        if not tasks:
            ctk.CTkLabel(self.panel, text="No tasks scheduled.",
                         font=Fonts.small(), text_color=Colors.TEXT_MUTED).pack(
                anchor="w", padx=Spacing.MD, pady=Spacing.XS)
        else:
            for t in tasks:
                mark = "☑" if t.is_done else "☐"
                ctk.CTkLabel(self.panel, text=f"{mark} {t.display_title()}",
                             font=Fonts.small(),
                             text_color=Colors.TEXT_SECONDARY if not t.is_done else Colors.TEXT_MUTED,
                             anchor="w", wraplength=250, justify="left").pack(
                    fill="x", padx=Spacing.MD, pady=1)

        ctk.CTkLabel(self.panel, text="Click any day on the calendar",
                     font=Fonts.caption(), text_color=Colors.TEXT_MUTED).pack(
            side="bottom", anchor="w", padx=Spacing.MD, pady=Spacing.MD)
