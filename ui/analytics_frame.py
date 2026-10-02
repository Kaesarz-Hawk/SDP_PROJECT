"""Analytics Screen (Screen 6) for Momentum.

Provides rich visual analytics:
- Weekly Bar Chart: daily completion counts over current week
- Monthly Trend Line: overall consistency percentage over the last 4-6 months
- Category Breakdown Donut / Pie Chart: distribution of effort across life tracks
- Auto-generated Insights: "Top Performing Habits" and "Needs Attention"
All matplotlib charts are dark-themed and safely wrapped in try-except fallbacks.
"""

from datetime import date, timedelta
import logging
from typing import Dict, List, Optional, Tuple
import customtkinter as ctk

from database.db_manager import DBManager
from models.habit import Habit
from utils.theme import (
    CATEGORY_COLORS,
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

logger = logging.getLogger(__name__)

# Safe Matplotlib import
try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except Exception as e:
    logger.error(f"Failed to import matplotlib: {e}")
    MATPLOTLIB_AVAILABLE = False


class AnalyticsFrame(ctk.CTkFrame):
    """Deep analytics screen with embedded matplotlib figures."""

    def __init__(self, master, db: DBManager, **kwargs):
        super().__init__(master, fg_color=COLOR_BG_BASE, **kwargs)
        self.db = db
        self.canvases = []  # Keep references to avoid garbage collection

        self._build_screen()

    def refresh(self) -> None:
        self._build_screen()

    def _build_screen(self) -> None:
        self._dispose_charts()
        for widget in self.winfo_children():
            widget.destroy()
        self.canvases.clear()

        # Header Bar
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=PAD_LG, pady=(PAD_MD, PAD_SM))

        ctk.CTkLabel(header, text="Performance & Analytics", font=FONT_TITLE, text_color=COLOR_TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(
            header,
            text="Consistency metrics, trends & habit health diagnostics",
            font=FONT_BODY,
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(side="left", padx=PAD_MD)

        # Scrollable container for charts and insights
        scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_container.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_SM)

        # Row 1: Insights Cards (Top Habits vs Needs Attention)
        self._render_insights_row(scroll_container)

        # Row 2: Weekly Bar Chart + Category Distribution Donut
        row2 = ctk.CTkFrame(scroll_container, fg_color="transparent")
        row2.pack(fill="x", pady=(0, PAD_MD))

        chart1_frame = ctk.CTkFrame(row2, fg_color=COLOR_BG_CARD, corner_radius=CORNER_MD, border_width=1, border_color=COLOR_BORDER)
        chart1_frame.pack(side="left", fill="both", expand=True, padx=(0, PAD_SM))

        chart2_frame = ctk.CTkFrame(row2, fg_color=COLOR_BG_CARD, corner_radius=CORNER_MD, border_width=1, border_color=COLOR_BORDER)
        chart2_frame.pack(side="left", fill="both", expand=True, padx=(PAD_SM, 0))

        self._render_weekly_bar_chart(chart1_frame)
        self._render_category_donut(chart2_frame)

        # Row 3: Monthly Trend Line Chart (Full Width)
        trend_card = ctk.CTkFrame(scroll_container, fg_color=COLOR_BG_CARD, corner_radius=CORNER_MD, border_width=1, border_color=COLOR_BORDER)
        trend_card.pack(fill="x", pady=(0, PAD_MD))
        self._render_monthly_trend_chart(trend_card)

    def _dispose_charts(self) -> None:
        """Release Tk and Matplotlib resources before rebuilding the screen."""
        for canvas in self.canvases:
            try:
                canvas.get_tk_widget().destroy()
                canvas.figure.clear()
                plt.close(canvas.figure)
            except (AttributeError, RuntimeError):
                # The parent may already be closing; there is nothing left to release.
                pass
        self.canvases.clear()

    def _render_insights_row(self, parent) -> None:
        today = date.today()
        month_start = f"{today.year:04d}-{today.month:02d}-01"
        month_end = today.isoformat()

        top_habits, lowest_habits = self.db.get_top_and_lowest_habits(month_start, month_end)

        insights_row = ctk.CTkFrame(parent, fg_color="transparent")
        insights_row.pack(fill="x", pady=(0, PAD_MD))

        # Top Performing Card
        top_card = ctk.CTkFrame(insights_row, fg_color=COLOR_BG_CARD, corner_radius=CORNER_MD, border_width=1, border_color=COLOR_BORDER)
        top_card.pack(side="left", fill="both", expand=True, padx=(0, PAD_SM))

        t_inner = ctk.CTkFrame(top_card, fg_color="transparent")
        t_inner.pack(fill="both", expand=True, padx=PAD_MD, pady=PAD_MD)

        ctk.CTkLabel(t_inner, text="🏆 Top Performing Habits (This Month)", font=FONT_SUBTITLE, text_color=COLOR_SUCCESS).pack(anchor="w", pady=(0, PAD_SM))

        if not top_habits or all(rate == 0.0 for _, rate in top_habits):
            ctk.CTkLabel(t_inner, text="Log more habit check-ins to reveal top performers.", font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(anchor="w")
        else:
            for habit, rate in top_habits:
                h_row = ctk.CTkFrame(t_inner, fg_color="#1E1E2A", corner_radius=6)
                h_row.pack(fill="x", pady=2)
                ctk.CTkLabel(h_row, text=f"{habit.icon} {habit.name}", font=FONT_BODY_BOLD, text_color=COLOR_TEXT_PRIMARY).pack(side="left", padx=PAD_SM, pady=4)
                ctk.CTkLabel(h_row, text=f"{int(rate * 100)}%", font=FONT_BODY_BOLD, text_color=COLOR_SUCCESS).pack(side="right", padx=PAD_SM)

        # Needs Attention Card
        low_card = ctk.CTkFrame(insights_row, fg_color=COLOR_BG_CARD, corner_radius=CORNER_MD, border_width=1, border_color=COLOR_BORDER)
        low_card.pack(side="left", fill="both", expand=True, padx=(PAD_SM, 0))

        l_inner = ctk.CTkFrame(low_card, fg_color="transparent")
        l_inner.pack(fill="both", expand=True, padx=PAD_MD, pady=PAD_MD)

        ctk.CTkLabel(l_inner, text="⚠️ Needs Attention / Building Up", font=FONT_SUBTITLE, text_color=COLOR_WARNING).pack(anchor="w", pady=(0, PAD_SM))

        if not lowest_habits:
            ctk.CTkLabel(l_inner, text="No habits currently lagging behind.", font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(anchor="w")
        else:
            for habit, rate in lowest_habits:
                h_row = ctk.CTkFrame(l_inner, fg_color="#1E1E2A", corner_radius=6)
                h_row.pack(fill="x", pady=2)
                ctk.CTkLabel(h_row, text=f"{habit.icon} {habit.name}", font=FONT_BODY_BOLD, text_color=COLOR_TEXT_PRIMARY).pack(side="left", padx=PAD_SM, pady=4)
                ctk.CTkLabel(h_row, text=f"{int(rate * 100)}%", font=FONT_BODY_BOLD, text_color=COLOR_WARNING).pack(side="right", padx=PAD_SM)

    def _render_weekly_bar_chart(self, container) -> None:
        ctk.CTkLabel(container, text="Weekly Check-in Volume", font=FONT_SUBTITLE, text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=PAD_MD, pady=(PAD_MD, 2))
        ctk.CTkLabel(container, text="Total habits completed per day this week", font=FONT_CAPTION, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w", padx=PAD_MD, pady=(0, PAD_SM))

        today = date.today()
        start_week = today - timedelta(days=6)
        daily_counts = self.db.get_weekly_completion_counts(start_week.isoformat(), today.isoformat())

        if not MATPLOTLIB_AVAILABLE or not daily_counts:
            self._render_chart_placeholder(container, "Weekly data unavailable.")
            return

        try:
            days = [date.fromisoformat(d).strftime("%a\n%b %d") for d, _ in daily_counts]
            counts = [c for _, c in daily_counts]

            fig = Figure(figsize=(5, 3.2), dpi=100, facecolor=COLOR_BG_CARD)
            ax = fig.add_subplot(111)
            ax.set_facecolor(COLOR_BG_CARD)

            bars = ax.bar(days, counts, color=COLOR_ACCENT, width=0.55, edgecolor="none", zorder=3)
            # Highlight max bar
            if max(counts) > 0:
                max_val = max(counts)
                for b, c in zip(bars, counts):
                    if c == max_val:
                        b.set_color(COLOR_SUCCESS)

            ax.grid(axis="y", color="#2A2A3A", linestyle="--", alpha=0.7, zorder=0)
            ax.tick_params(colors=COLOR_TEXT_SECONDARY, labelsize=8)
            for spine in ax.spines.values():
                spine.set_color(COLOR_BORDER)

            # Set integer y-ticks
            max_y = max(counts) if counts and max(counts) > 0 else 5
            ax.set_ylim(0, max_y + 1)
            ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))

            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=PAD_MD, pady=(0, PAD_MD))
            self.canvases.append(canvas)
        except Exception as e:
            logger.error(f"Error drawing weekly bar chart: {e}")
            self._render_chart_placeholder(container, "Not enough data for weekly chart yet.")

    def _render_category_donut(self, container) -> None:
        ctk.CTkLabel(container, text="Track Effort Allocation", font=FONT_SUBTITLE, text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=PAD_MD, pady=(PAD_MD, 2))
        ctk.CTkLabel(container, text="Proportion of total completions by life track", font=FONT_CAPTION, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w", padx=PAD_MD, pady=(0, PAD_SM))

        today = date.today()
        start_month = (today - timedelta(days=30)).isoformat()
        breakdown = self.db.get_category_breakdown(start_month, today.isoformat())

        if not MATPLOTLIB_AVAILABLE or not breakdown or sum(breakdown.values()) == 0:
            self._render_chart_placeholder(container, "No category completions logged yet.")
            return

        try:
            labels = list(breakdown.keys())
            values = list(breakdown.values())
            colors = [CATEGORY_COLORS.get(l, COLOR_ACCENT) for l in labels]

            fig = Figure(figsize=(5, 3.2), dpi=100, facecolor=COLOR_BG_CARD)
            ax = fig.add_subplot(111)
            ax.set_facecolor(COLOR_BG_CARD)

            wedges, texts, autotexts = ax.pie(
                values,
                labels=labels,
                autopct="%1.0f%%",
                startangle=140,
                colors=colors,
                textprops=dict(color=COLOR_TEXT_PRIMARY, size=8),
                wedgeprops=dict(width=0.45, edgecolor=COLOR_BG_CARD, linewidth=2),
                pctdistance=0.75,
            )
            for autotext in autotexts:
                autotext.set_color("#FFFFFF")
                autotext.set_weight("bold")

            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=PAD_MD, pady=(0, PAD_MD))
            self.canvases.append(canvas)
        except Exception as e:
            logger.error(f"Error drawing category donut: {e}")
            self._render_chart_placeholder(container, "Not enough data for track breakdown.")

    def _render_monthly_trend_chart(self, container) -> None:
        ctk.CTkLabel(container, text="Long-Term Consistency Trend", font=FONT_SUBTITLE, text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", padx=PAD_MD, pady=(PAD_MD, 2))
        ctk.CTkLabel(container, text="Overall consistency percentage trajectory across months", font=FONT_CAPTION, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w", padx=PAD_MD, pady=(0, PAD_SM))

        monthly_data = self.db.get_monthly_trend(num_months=5)

        if not MATPLOTLIB_AVAILABLE or not monthly_data:
            self._render_chart_placeholder(container, "Not enough historical data for trendline.")
            return

        try:
            months = [m for m, _ in monthly_data]
            pcts = [p * 100 for _, p in monthly_data]

            fig = Figure(figsize=(10, 2.8), dpi=100, facecolor=COLOR_BG_CARD)
            ax = fig.add_subplot(111)
            ax.set_facecolor(COLOR_BG_CARD)

            # Trend line with gradient glow effect
            ax.plot(months, pcts, color=COLOR_ACCENT, marker="o", linewidth=2.5, markersize=6, zorder=4)
            ax.fill_between(months, pcts, color=COLOR_ACCENT, alpha=0.15, zorder=2)

            ax.grid(axis="both", color="#2A2A3A", linestyle="--", alpha=0.7, zorder=0)
            ax.tick_params(colors=COLOR_TEXT_SECONDARY, labelsize=9)
            for spine in ax.spines.values():
                spine.set_color(COLOR_BORDER)

            ax.set_ylim(0, 105)
            ax.set_ylabel("Consistency %", color=COLOR_TEXT_MUTED, fontsize=9)
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=PAD_MD, pady=(0, PAD_MD))
            self.canvases.append(canvas)
        except Exception as e:
            logger.error(f"Error drawing monthly trend chart: {e}")
            self._render_chart_placeholder(container, "Not enough data for trend analysis.")

    def _render_chart_placeholder(self, parent, message: str) -> None:
        ph = ctk.CTkFrame(parent, fg_color="#181822", height=180, corner_radius=CORNER_SM)
        ph.pack(fill="both", expand=True, padx=PAD_MD, pady=PAD_MD)
        ctk.CTkLabel(ph, text="📊", font=("Segoe UI", 32)).pack(expand=True, pady=(PAD_MD, 2))
        ctk.CTkLabel(ph, text=message, font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(expand=True, pady=(0, PAD_MD))
