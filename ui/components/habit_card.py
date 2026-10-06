"""
HabitCard — the reusable Dashboard card:
  • category color accent stripe + emoji icon + name
  • today's status as a modern toggle switch (not a plain checkbox)
  • small circular progress ring (completion % for selected timeframe)
  • streak count with flame that intensifies as it grows
  • 7-day sparkline mini trend (matplotlib, minimal axes)
  • debounce so rapid double-clicks cannot double-write the DB
"""
from __future__ import annotations

import tkinter as tk
from datetime import date, timedelta
from typing import Callable, Optional

import customtkinter as ctk

try:
    from utils.theme import Colors, Fonts, Spacing
except ImportError:  # pragma: no cover
    from ...utils.theme import Colors, Fonts, Spacing

from .progress_ring import ProgressRing


class Sparkline(tk.Canvas):
    """Tiny trend line of the last N days — matplotlib Figure (no pyplot global state)."""

    def __init__(self, master, width: int = 150, height: int = 40,
                 line_color: str = Colors.CHART_LINE, bg: str = Colors.BG_CARD, **kwargs):
        super().__init__(master, width=width, height=height, highlightthickness=0,
                         bd=0, bg=bg, **kwargs)
        # NOTE: never name attributes "_w"/"_h" — those are Tk's internal widget path!
        self._px_w = width
        self._px_h = height
        self._color = line_color
        self._values: list[float] = []
        # Use a plain Figure (never pyplot) — safe to create/destroy repeatedly
        self._fig = None
        self._canvas_widget = None
        try:
            from matplotlib.figure import Figure
            self._Figure = Figure
            self._fig = Figure(figsize=(width / 100, height / 100), dpi=100,
                               facecolor=self.cget("bg"))
        except Exception as exc:  # matplotlib missing/broken → Canvas fallback
            print(f"[Momentum:Sparkline] matplotlib unavailable ({exc}); using Canvas line")
            self._Figure = None

    def set_values(self, values: list[float]) -> None:
        self._values = [float(v) for v in values]
        self.redraw()

    def redraw(self) -> None:
        if self._fig is None:
            self._draw_fallback()
            return
        try:
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            self._fig.clf()
            ax = self._fig.add_subplot(111)
            ax.set_facecolor(self.cget("bg"))
            values = self._values
            if not values:
                ax.text(0.5, 0.5, "no data", ha="center", va="center",
                        color=Colors.TEXT_MUTED, fontsize=7)
                ax.axis("off")
            else:
                xs = list(range(len(values)))
                ax.plot(xs, values, color=self._color, linewidth=1.8)
                ax.fill_between(xs, values, alpha=0.15, color=self._color)
                ax.set_xlim(0, max(xs))
                ax.set_ylim(min(min(values), 0) - 0.2, max(max(values), 1.0) + 0.2)
                ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
                for spine in ax.spines.values():
                    spine.set_visible(False)
            self._fig.tight_layout(pad=0.2)
            if self._canvas_widget is not None:
                self._canvas_widget.get_tk_widget().destroy()
                self._canvas_widget = None
            self._canvas_widget = FigureCanvasTkAgg(self._fig, master=self)
            self._canvas_widget.draw()
            self._canvas_widget.get_tk_widget().place(x=0, y=0)
        except Exception as exc:
            # File 07: rendering failure must not crash the screen
            print(f"[Momentum:Sparkline] render failed: {exc}")
            self._fig = None
            self._draw_fallback()

    def _draw_fallback(self) -> None:
        self.delete("all")
        values = self._values
        if len(values) < 2:
            self.create_text(self._px_w // 2, self._px_h // 2, text="–",
                             fill=Colors.TEXT_MUTED, font=(Fonts.FAMILY, 10))
            return
        lo, hi = min(values), max(values)
        span = (hi - lo) or 1.0
        pts = []
        for i, v in enumerate(values):
            x = 4 + i * ((self._px_w - 8) / (len(values) - 1))
            y = (self._px_h - 6) - ((v - lo) / span) * (self._px_h - 12)
            pts.extend([x, y])
        self.create_line(*pts, fill=self._color, width=2, smooth=True)


class HabitCard(ctk.CTkFrame):
    """
    One habit card on the Dashboard.
    callbacks:
      on_toggle(habit_id, completed_bool)
      on_details(habit_id)  — optional, click habit name for stats
    """

    def __init__(self, master, habit, db, timeframe: str = "Daily",
                 on_toggle: Optional[Callable] = None,
                 on_details: Optional[Callable] = None):
        super().__init__(master, fg_color=Colors.BG_CARD,
                         corner_radius=Spacing.CARD_RADIUS, height=170)
        self.habit = habit
        self.db = db
        self.timeframe = timeframe
        self.on_toggle = on_toggle
        self.on_details = on_details
        self._debounce_job = None
        self._building = True

        accent = habit.track_color or Colors.CAT_DEFAULT

        # Left accent stripe
        stripe = tk.Canvas(self, width=5, height=170, highlightthickness=0, bd=0,
                           bg=Colors.BG_CARD)
        stripe.place(x=0, y=0, relheight=1)
        stripe.create_rectangle(0, 0, 5, 170, fill=accent, outline="")

        # Header: icon + name (clickable) + category chip
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=(Spacing.MD, Spacing.MD), pady=(Spacing.MD, 0))
        name_btn = ctk.CTkButton(
            head, text=f"{habit.icon} {habit.name}", font=Fonts.body_bold(),
            fg_color="transparent", hover_color=Colors.BG_ELEVATED,
            text_color=Colors.TEXT_PRIMARY, anchor="w", cursor="hand2",
            height=26, command=self._open_details)
        name_btn.pack(side="left", fill="x", expand=True)
        cat = ctk.CTkLabel(head, text=(habit.track_name or "No track").upper(),
                           font=(Fonts.FAMILY, 9, "bold"), text_color=accent)
        cat.pack(side="right")

        # Middle row: ring + streak + sparkline
        mid = ctk.CTkFrame(self, fg_color="transparent")
        mid.pack(fill="x", padx=Spacing.MD, pady=Spacing.SM)

        ring_val = self._timeframe_pct()
        self.ring = ProgressRing(mid, value=ring_val, size=64, width=7,
                                 fill_color=accent, track_color=Colors.BG_ELEVATED,
                                 text_color=Colors.TEXT_PRIMARY, font_size=11)
        self.ring.pack(side="left")

        info = ctk.CTkFrame(mid, fg_color="transparent")
        info.pack(side="left", padx=Spacing.SM, fill="x", expand=True)
        streak = int(self.db.get_current_streak(habit.id) or 0)
        self.streak_color = Colors.streak_color(streak)
        flame = "🔥" if streak >= 3 else "✨" if streak > 0 else "·"
        self.streak_lbl = ctk.CTkLabel(
            info, text=f"{flame} {streak} day streak",
            font=(Fonts.FAMILY, 13, "bold"), text_color=self.streak_color, anchor="w")
        self.streak_lbl.pack(anchor="w")
        done = self._today_done()
        self.sub_lbl = ctk.CTkLabel(
            info,
            text=f"target {habit.weekly_target()}×/week · " + ("done today ✓" if done else "not yet today"),
            font=Fonts.caption(), text_color=Colors.TEXT_MUTED, anchor="w")
        self.sub_lbl.pack(anchor="w", pady=(2, 0))

        # Sparkline (last 7 days)
        try:
            self.sparkline = Sparkline(mid, width=140, height=44, line_color=accent,
                                       bg=Colors.BG_CARD)
            self.sparkline.pack(side="right", padx=(Spacing.SM, 0))
            self.sparkline.set_values(self._last_7_values())
        except Exception as exc:
            print(f"[Momentum:HabitCard] sparkline init failed: {exc}")
            self.sparkline = None

        # Footer: toggle switch (modern, not checkbox)
        foot = ctk.CTkFrame(self, fg_color="transparent")
        foot.pack(fill="x", padx=Spacing.MD, pady=(0, Spacing.MD))
        self.toggle = ctk.CTkSwitch(
            foot, text="Done today" if True else "", font=Fonts.small(),
            progress_color=accent, button_color=Colors.TEXT_SECONDARY,
            button_hover_color=accent,
            fg_color=Colors.BG_ELEVATED, text_color=Colors.TEXT_SECONDARY,
            command=self._on_toggle_click)
        if done:
            self.toggle.select()
        self.toggle.pack(side="left")
        pct_lbl = ctk.CTkLabel(foot, text=f"{ring_val:.0f}% {timeframe.lower()}",
                               font=Fonts.caption(), text_color=Colors.TEXT_MUTED)
        pct_lbl.pack(side="right")

        self._building = False

    # ------------------------------------------------------------------ #
    def _today_done(self) -> bool:
        today = date.today().isoformat()
        logs = self.db.get_logs_for_habit(self.habit.id, today, today)
        return any(l.completed for l in logs)

    def _timeframe_pct(self) -> float:
        today = date.today()
        if self.timeframe == "Daily":
            return 100.0 if self._today_done() else 0.0
        if self.timeframe == "Weekly":
            start = today - timedelta(days=today.weekday())
            return self.db.get_completion_percentage(self.habit.id, start.isoformat(), today.isoformat(),
                                                     expected_days=self.habit.weekly_target())
        if self.timeframe == "Monthly":
            start = today.replace(day=1)
            return self.db.get_completion_percentage(self.habit.id, start.isoformat(), today.isoformat())
        # Yearly
        start = today.replace(month=1, day=1)
        return self.db.get_completion_percentage(self.habit.id, start.isoformat(), today.isoformat())

    def _last_7_values(self) -> list[float]:
        today = date.today()
        start = today - timedelta(days=6)
        completion = self.db.get_completion_map(self.habit.id, start.isoformat(), today.isoformat())
        return [1.0 if completion.get((today - timedelta(days=i)).isoformat(), 0) else 0.0
                for i in range(6, -1, -1)]

    def _open_details(self):
        if self.on_details:
            self.on_details(self.habit.id)

    def _on_toggle_click(self):
        """Debounced toggle — rapid clicks must not create duplicate DB writes."""
        if self._building:
            return
        if self._debounce_job is not None:
            return
        completed = bool(self.toggle.get())
        self._debounce_job = self.after(350, lambda: setattr(self, "_debounce_job", None))
        try:
            if self.on_toggle:
                self.on_toggle(self.habit.id, completed)
            else:
                self.db.toggle_completion(self.habit.id, date.today().isoformat(), completed)
        except Exception as exc:
            # Never show a traceback — flip UI back and show friendly message
            print(f"[Momentum:HabitCard] toggle failed: {exc}")
            try:
                if completed:
                    self.toggle.deselect()
                else:
                    self.toggle.select()
            except Exception:
                pass
            parent = self.winfo_toplevel()
            try:
                from .modal_dialog import show_error
                show_error(parent, "Could not save",
                           "That update didn't stick. Please try again.")
            except Exception:
                pass

    def refresh(self, timeframe: Optional[str] = None) -> None:
        """Recompute ring/streak/sparkline after data changes."""
        if timeframe:
            self.timeframe = timeframe
        try:
            self._building = True
            done = self._today_done()
            if done:
                self.toggle.select()
            else:
                self.toggle.deselect()
            self.ring.set_value(self._timeframe_pct())
            streak = int(self.db.get_current_streak(self.habit.id) or 0)
            flame = "🔥" if streak >= 3 else "✨" if streak > 0 else "·"
            color = Colors.streak_color(streak)
            self.streak_lbl.configure(text=f"{flame} {streak} day streak", text_color=color)
            self.sub_lbl.configure(
                text=f"target {self.habit.weekly_target()}×/week · "
                     + ("done today ✓" if done else "not yet today"))
            if self.sparkline:
                self.sparkline.set_values(self._last_7_values())
        finally:
            self._building = False
