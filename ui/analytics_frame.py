"""
Screen 6: Analytics — embedded matplotlib charts + computed insights.

- Weekly bar chart: habit completion count per day (current week)
- Monthly trend line: overall consistency % (last 6 months)
- Per-category donut: proportion of completions by track (last 30 days)
- Auto-generated insight lists: "Top performing" + "Needs attention" (this month)
- Every chart has a clean "Not enough data yet" placeholder for empty datasets
- ALL matplotlib rendering wrapped in try/except (never crashes the screen)
"""
from __future__ import annotations

from datetime import date, timedelta

import customtkinter as ctk

try:
    from utils.theme import Colors, Fonts, Spacing
except ImportError:  # pragma: no cover
    from ..utils.theme import Colors, Fonts, Spacing


class AnalyticsFrame(ctk.CTkFrame):
    def __init__(self, master, db, app):
        super().__init__(master, fg_color=Colors.BG_BASE, corner_radius=0)
        self.db = db
        self.app = app
        self._canvases = []

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=Spacing.XL, pady=(Spacing.LG, Spacing.MD))
        ctk.CTkLabel(head, text="Analytics", font=Fonts.title(),
                     text_color=Colors.TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(head, text="Your consistency, quantified",
                     font=Fonts.body(), text_color=Colors.TEXT_SECONDARY).pack(
            side="left", padx=Spacing.MD)

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=Spacing.XL, pady=(0, Spacing.LG))
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)
        grid.grid_rowconfigure(0, weight=1)
        grid.grid_rowconfigure(1, weight=1)

        # Each chart card = title label + content holder (holder is rebuilt freely)
        self.h_week = self._make_card(grid, "THIS WEEK · COMPLETIONS PER DAY")
        self.h_week.grid(row=0, column=0, sticky="nsew",
                         padx=(0, Spacing.SM), pady=(0, Spacing.SM))
        self.h_trend = self._make_card(grid, "CONSISTENCY TREND · LAST 6 MONTHS")
        self.h_trend.grid(row=0, column=1, sticky="nsew",
                          padx=(Spacing.SM, 0), pady=(0, Spacing.SM))
        self.h_donut = self._make_card(grid, "COMPLETIONS BY TRACK · LAST 30 DAYS")
        self.h_donut.grid(row=1, column=0, sticky="nsew",
                          padx=(0, Spacing.SM), pady=(Spacing.SM, 0))
        self.h_insight = self._make_card(grid, "INSIGHTS · THIS MONTH")
        self.h_insight.grid(row=1, column=1, sticky="nsew",
                            padx=(Spacing.SM, 0), pady=(Spacing.SM, 0))

    def _make_card(self, parent, title: str) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent, fg_color=Colors.BG_CARD,
                            corner_radius=Spacing.CARD_RADIUS)
        ctk.CTkLabel(card, text=title, font=(Fonts.FAMILY, 10, "bold"),
                     text_color=Colors.TEXT_MUTED).pack(
            anchor="w", padx=Spacing.MD, pady=(Spacing.MD, Spacing.XS))
        holder = ctk.CTkFrame(card, fg_color="transparent")
        holder.pack(fill="both", expand=True, padx=Spacing.XS, pady=(0, Spacing.SM))
        card.holder = holder
        return card

    # ------------------------------------------------------------------ #
    def refresh(self) -> None:
        try:
            self._destroy_charts()
            self._clear(self.h_week)
            self._clear(self.h_trend)
            self._clear(self.h_donut)
            self._clear(self.h_insight)
            self._placeholder(self.h_week, "📊", "Building chart…")
            self._placeholder(self.h_trend, "📈", "Building chart…")
            self._placeholder(self.h_donut, "🍩", "Building chart…")
            self._render_insights()
            # Render after layout settles (avases zero-size figure canvases)
            self.after(60, self._render_charts)
        except Exception as exc:
            print(f"[Momentum:Analytics] refresh failed: {exc}")
            import traceback
            traceback.print_exc()

    @staticmethod
    def _clear(card) -> None:
        holder = card.holder
        for child in holder.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass

    def _destroy_charts(self) -> None:
        for canvas in self._canvases:
            try:
                canvas.get_tk_widget().destroy()
            except Exception:
                pass
        self._canvases.clear()

    @staticmethod
    def _placeholder(card, emoji: str, text: str) -> ctk.CTkLabel:
        lbl = ctk.CTkLabel(card.holder, text=f"{emoji}\n{text}",
                           font=Fonts.body(), text_color=Colors.TEXT_MUTED,
                           justify="center")
        lbl.pack(fill="both", expand=True, pady=Spacing.LG)
        return lbl

    # ------------------------------------------------------------------ #
    def _render_charts(self) -> None:
        for fn, card, emoji in (
            (self._render_weekly_bar, self.h_week, "📊"),
            (self._render_trend_line, self.h_trend, "📈"),
            (self._render_category_donut, self.h_donut, "🍩"),
        ):
            try:
                self._clear(card)
                fn(card)
            except Exception as exc:
                # File 07: chart failure → clean text fallback, never a crash
                print(f"[Momentum:Analytics] chart failed: {exc}")
                import traceback
                traceback.print_exc()
                self._clear(card)
                self._placeholder(card, "📉", "Chart unavailable right now")

    def _new_canvas(self, card, figsize=(4.4, 2.7)):
        """Create a matplotlib Figure + TkAgg canvas inside the card holder."""
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        fig = Figure(figsize=figsize, dpi=100, facecolor=Colors.BG_CARD)
        ax = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, master=card.holder)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.configure(bg=Colors.BG_CARD, highlightthickness=0)
        widget.pack(fill="both", expand=True)
        self._canvases.append(canvas)
        return fig, ax, canvas

    # ---- individual charts ------------------------------------------------
    def _render_weekly_bar(self, card) -> None:
        """Bar chart: completions per day across the current week."""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        data = self.db.get_weekly_bar_data(week_start.isoformat(), today.isoformat())
        if not data:
            self._placeholder(card, "📊", "Not enough data yet")
            return
        fig, ax, canvas = self._new_canvas(card)
        days = [week_start + timedelta(days=i) for i in range(7)]
        labels = [d.strftime("%a") for d in days]
        values = [data.get(d.isoformat(), 0) for d in days]
        bars = ax.bar(labels, values, color=Colors.CHART_BAR, width=0.6,
                      edgecolor="none", zorder=3)
        for rect, v in zip(bars, values):
            if v > 0:
                ax.text(rect.get_x() + rect.get_width() / 2, v + 0.15, str(v),
                        ha="center", va="bottom", color=Colors.TEXT_SECONDARY, fontsize=8)
        ax.set_facecolor(Colors.BG_CARD)
        ax.tick_params(colors=Colors.TEXT_SECONDARY, labelsize=9)
        ax.set_ylim(0, max(max(values), 1) + 1.5)
        ax.grid(axis="y", color=Colors.CHART_GRID, linewidth=0.7, zorder=0)
        for spine in ax.spines.values():
            spine.set_visible(False)
        fig.tight_layout(pad=0.6)
        canvas.draw()

    def _render_trend_line(self, card) -> None:
        """Line chart: overall consistency % over the last 6 months."""
        data = self.db.get_monthly_trend(months=6)
        if not data:
            self._placeholder(card, "📈", "Not enough data yet")
            return
        fig, ax, canvas = self._new_canvas(card)
        labels = [d[0] for d in data]
        values = [d[1] for d in data]
        ax.plot(labels, values, color=Colors.CHART_LINE, linewidth=2.4,
                marker="o", markersize=5, zorder=3)
        ax.fill_between(range(len(values)), values, alpha=0.12, color=Colors.CHART_LINE)
        ax.set_ylim(0, 105)
        ax.set_ylabel("%", color=Colors.TEXT_MUTED, fontsize=9)
        ax.set_facecolor(Colors.BG_CARD)
        ax.tick_params(colors=Colors.TEXT_SECONDARY, labelsize=9)
        ax.grid(axis="y", color=Colors.CHART_GRID, linewidth=0.7, zorder=0)
        for spine in ax.spines.values():
            spine.set_visible(False)
        fig.tight_layout(pad=0.6)
        canvas.draw()

    def _render_category_donut(self, card) -> None:
        """Donut/pie: proportion of completions by track (last 30 days)."""
        end = date.today()
        start = end - timedelta(days=29)
        breakdown = self.db.get_category_breakdown(start.isoformat(), end.isoformat())
        breakdown = {k: v for k, v in breakdown.items() if v > 0}
        if not breakdown:
            self._placeholder(card, "🍩", "Not enough data yet")
            return
        fig, ax, canvas = self._new_canvas(card, figsize=(4.4, 2.9))
        track_colors = self.db.get_category_colors()
        labels = list(breakdown.keys())
        sizes = list(breakdown.values())
        colors = [track_colors.get(lbl, Colors.CAT_DEFAULT) for lbl in labels]
        wedges, _ = ax.pie(sizes, colors=colors, startangle=90,
                           wedgeprops=dict(width=0.42, edgecolor=Colors.BG_CARD,
                                           linewidth=2))
        total = sum(sizes) or 1
        ax.text(0, 0, f"{total}\nlogs", ha="center", va="center",
                color=Colors.TEXT_PRIMARY, fontsize=11, fontweight="bold")
        ax.legend(wedges,
                  [f"{lbl} ({int(v / total * 100)}%)" for lbl, v in zip(labels, sizes)],
                  loc="center left", bbox_to_anchor=(0.96, 0.5),
                  frameon=False, fontsize=8, labelcolor=Colors.TEXT_SECONDARY)
        fig.tight_layout(pad=0.4)
        canvas.draw()

    # ------------------------------------------------------------------ #
    def _render_insights(self) -> None:
        """Top performing + Needs attention (simple computed logic, no AI)."""
        start = date.today().replace(day=1).isoformat()
        end = date.today().isoformat()
        try:
            top, needs = self.db.get_top_and_needs_attention(start, end)
        except Exception as exc:
            print(f"[Momentum:Analytics] insights failed: {exc}")
            self._placeholder(self.h_insight, "⚠️", "Insights unavailable")
            return

        if not top and not needs:
            self._placeholder(self.h_insight, "🌱", "Not enough data yet")
            return

        body = ctk.CTkFrame(self.h_insight.holder, fg_color="transparent")
        body.pack(fill="both", expand=True)
        left = ctk.CTkFrame(body, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=(Spacing.XS, Spacing.SM))
        right = ctk.CTkFrame(body, fg_color="transparent")
        right.pack(side="right", fill="both", expand=True, padx=(Spacing.SM, Spacing.XS))

        ctk.CTkLabel(left, text="🏆 Top performing", font=Fonts.small_bold(),
                     text_color=Colors.SUCCESS).pack(anchor="w", pady=(0, Spacing.XS))
        if top:
            for habit, pct in top:
                ctk.CTkLabel(left, text=f"{habit.display_name()}  ·  {pct}%",
                             font=Fonts.small(), text_color=Colors.TEXT_SECONDARY,
                             anchor="w").pack(fill="x", pady=2)
        else:
            ctk.CTkLabel(left, text="No completions yet",
                         font=Fonts.small(), text_color=Colors.TEXT_MUTED).pack(anchor="w")

        ctk.CTkLabel(right, text="⚠️ Needs attention", font=Fonts.small_bold(),
                     text_color=Colors.WARNING).pack(anchor="w", pady=(0, Spacing.XS))
        if needs:
            for habit, pct in needs:
                ctk.CTkLabel(right, text=f"{habit.display_name()}  ·  {pct}%",
                             font=Fonts.small(), text_color=Colors.TEXT_SECONDARY,
                             anchor="w").pack(fill="x", pady=2)
        else:
            ctk.CTkLabel(right, text="Everything looks great!",
                         font=Fonts.small(), text_color=Colors.TEXT_MUTED).pack(anchor="w")
