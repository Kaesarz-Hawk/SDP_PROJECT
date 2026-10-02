"""Calendar heatmap widgets for Momentum.

Provides:
1. HeatmapStrip: Horizontal 30-day consistency strip for the Dashboard.
2. MonthHeatmapGrid: Full month calendar heatmap grid with interactive day cells.
"""

import calendar
from datetime import date, timedelta
from typing import Callable, Dict, Optional
import customtkinter as ctk

from utils.theme import (
    COLOR_ACCENT,
    COLOR_BG_CARD,
    COLOR_BORDER,
    COLOR_SUCCESS,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    CORNER_SM,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_CAPTION,
    FONT_FAMILY,
    FONT_SECTION_HEADER,
    PAD_SM,
    PAD_XS,
)


def get_heatmap_color(completion_ratio: float) -> str:
    """Maps a 0.0-1.0 completion ratio to a dark-mode heatmap cell hex color."""
    if completion_ratio <= 0.0:
        return "#1E1E28"       # Base empty slot
    elif completion_ratio < 0.25:
        return "#064E3B"       # Subtle deep emerald
    elif completion_ratio < 0.50:
        return "#047857"       # Medium emerald
    elif completion_ratio < 0.80:
        return "#059669"       # Bright emerald
    else:
        return "#10B981"       # Vivid glowing emerald


class HeatmapStrip(ctk.CTkFrame):
    """Horizontal 30-day overall consistency strip for the Dashboard."""

    def __init__(
        self,
        master,
        data: Optional[Dict[str, float]] = None,
        days: int = 30,
        **kwargs,
    ):
        super().__init__(
            master,
            fg_color=COLOR_BG_CARD,
            corner_radius=CORNER_SM,
            border_width=1,
            border_color=COLOR_BORDER,
            **kwargs,
        )
        self.days_count = days
        self.data: Dict[str, float] = data or {}
        self._build_ui()

    def update_data(self, data: Dict[str, float]) -> None:
        self.data = data
        self._build_ui()

    def _build_ui(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=PAD_SM, pady=(PAD_SM, 2))

        ctk.CTkLabel(
            header_frame,
            text=f"Last {self.days_count} Days Consistency Strip",
            font=FONT_SECTION_HEADER,
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(side="left")

        # Legend on the right
        legend_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        legend_frame.pack(side="right")
        ctk.CTkLabel(legend_frame, text="Less", font=FONT_CAPTION, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=2)
        for val in [0.0, 0.25, 0.5, 0.8, 1.0]:
            swatch = ctk.CTkFrame(
                legend_frame,
                width=10,
                height=10,
                corner_radius=2,
                fg_color=get_heatmap_color(val),
            )
            swatch.pack(side="left", padx=2)
        ctk.CTkLabel(legend_frame, text="More", font=FONT_CAPTION, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=2)

        # Grid of days strip
        strip_container = ctk.CTkFrame(self, fg_color="transparent")
        strip_container.pack(fill="x", padx=PAD_SM, pady=(PAD_XS, PAD_SM))

        today = date.today()
        start_date = today - timedelta(days=self.days_count - 1)

        for col_idx in range(self.days_count):
            day_d = start_date + timedelta(days=col_idx)
            iso = day_d.isoformat()
            ratio = self.data.get(iso, 0.0)
            cell_color = get_heatmap_color(ratio)

            # Tooltip text
            percent_str = f"{int(ratio * 100)}%"
            tooltip = f"{day_d.strftime('%b %d')}: {percent_str}"

            cell = ctk.CTkButton(
                strip_container,
                text="",
                width=24,
                height=24,
                corner_radius=4,
                fg_color=cell_color,
                hover_color=COLOR_ACCENT,
                border_width=1 if iso == today.isoformat() else 0,
                border_color=COLOR_TEXT_PRIMARY if iso == today.isoformat() else cell_color,
            )
            cell.pack(side="left", padx=2, expand=True)


class MonthHeatmapGrid(ctk.CTkFrame):
    """Full month calendar grid with day cells shaded by completion ratio."""

    def __init__(
        self,
        master,
        year: int,
        month: int,
        daily_ratios: Optional[Dict[str, float]] = None,
        on_day_click: Optional[Callable[[str], None]] = None,
        **kwargs,
    ):
        super().__init__(
            master,
            fg_color=COLOR_BG_CARD,
            corner_radius=CORNER_SM,
            border_width=1,
            border_color=COLOR_BORDER,
            **kwargs,
        )
        self.year = year
        self.month = month
        self.daily_ratios = daily_ratios or {}
        self.on_day_click = on_day_click
        self.selected_date: Optional[str] = None
        self._build_grid()

    def set_month_data(self, year: int, month: int, daily_ratios: Dict[str, float]) -> None:
        self.year = year
        self.month = month
        self.daily_ratios = daily_ratios
        self._build_grid()

    def _build_grid(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()

        # Day-of-week column headers
        days_header = ctk.CTkFrame(self, fg_color="transparent")
        days_header.pack(fill="x", padx=PAD_SM, pady=(PAD_SM, PAD_XS))

        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, wd in enumerate(weekdays):
            lbl = ctk.CTkLabel(
                days_header,
                text=wd,
                font=FONT_BODY_BOLD,
                text_color=COLOR_TEXT_SECONDARY,
                width=64,
            )
            lbl.pack(side="left", expand=True, fill="x")

        # Weeks matrix
        month_cal = calendar.monthcalendar(self.year, self.month)
        today_iso = date.today().isoformat()

        cal_body = ctk.CTkFrame(self, fg_color="transparent")
        cal_body.pack(fill="both", expand=True, padx=PAD_SM, pady=(0, PAD_SM))

        for week in month_cal:
            week_row = ctk.CTkFrame(cal_body, fg_color="transparent")
            week_row.pack(fill="x", pady=2, expand=True)

            for day_num in week:
                if day_num == 0:
                    # Empty cell padding
                    empty_box = ctk.CTkFrame(week_row, fg_color="transparent", width=64, height=54)
                    empty_box.pack(side="left", padx=2, expand=True, fill="both")
                else:
                    d_iso = f"{self.year:04d}-{self.month:02d}-{day_num:02d}"
                    ratio = self.daily_ratios.get(d_iso, 0.0)
                    bg_col = get_heatmap_color(ratio)

                    is_today = (d_iso == today_iso)
                    is_selected = (d_iso == self.selected_date)

                    cell_text = f"{day_num}\n{int(ratio * 100)}%" if ratio > 0 else f"{day_num}\n—"

                    btn = ctk.CTkButton(
                        week_row,
                        text=cell_text,
                        font=FONT_BODY,
                        width=64,
                        height=54,
                        corner_radius=8,
                        fg_color=bg_col,
                        hover_color=COLOR_ACCENT,
                        text_color=COLOR_TEXT_PRIMARY,
                        border_width=2 if (is_selected or is_today) else 0,
                        border_color=COLOR_ACCENT if is_selected else (COLOR_SUCCESS if is_today else bg_col),
                        command=lambda d=d_iso: self._handle_click(d),
                    )
                    btn.pack(side="left", padx=2, expand=True, fill="both")

    def _handle_click(self, d_iso: str) -> None:
        self.selected_date = d_iso
        self._build_grid()
        if self.on_day_click:
            self.on_day_click(d_iso)
