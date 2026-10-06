"""
Reusable calendar-heatmap widgets (GitHub-contributions style).

- HeatmapStrip     : compact horizontal strip of the last N days (Dashboard)
- HeatmapCalendar  : full month grid with day numbers + click (Calendar screen)

Color intensity maps to that day's overall completion % via Colors.heat_color().
Renders cleanly when a month has ZERO logged data (no crash, flat empty cells).
"""
from __future__ import annotations

import tkinter as tk
from datetime import date, timedelta
from typing import Callable, Optional

try:
    from utils.theme import Colors, Fonts, Spacing
except ImportError:  # pragma: no cover
    from ...utils.theme import Colors, Fonts, Spacing


def _safe_ratio(value) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


class HeatmapStrip(tk.Canvas):
    """
    Last `days` days as small squares in a single/double row.
    ratios: {iso_date: 0..1} — missing dates render as HEAT_0 (empty).
    """

    def __init__(self, master, days: int = 30, cell: int = 16, gap: int = 4,
                 ratios: Optional[dict] = None, bg: str = Colors.BG_CARD, **kwargs):
        self.days = days
        self.cell = cell
        self.gap = gap
        width = days * (cell + gap) + gap
        height = cell + gap * 2 + 14
        super().__init__(master, width=width, height=height, highlightthickness=0,
                         bd=0, bg=bg, **kwargs)
        self._ratios: dict[str, float] = ratios or {}
        self.redraw()

    def set_ratios(self, ratios: dict[str, float]) -> None:
        self._ratios = ratios or {}
        self.redraw()

    def redraw(self) -> None:
        self.delete("all")
        today = date.today()
        x = self.gap
        y = self.gap
        for i in range(self.days, -1, -1):
            day = today - timedelta(days=i)
            iso = day.isoformat()
            ratio = _safe_ratio(self._ratios.get(iso, 0.0))
            color = Colors.heat_color(ratio)
            self.create_rectangle(x, y, x + self.cell, y + self.cell,
                                  fill=color, outline=Colors.BG_BASE, width=1)
            if day.day in (1, 15) or i == 0:
                label = (f"{day.strftime('%b')} {day.day}") if i == 0 else str(day.day)
                self.create_text(x + self.cell // 2, y + self.cell + 8,
                                 text=label,
                                 fill=Colors.TEXT_MUTED,
                                 font=(Fonts.FAMILY, 8))
            x += self.cell + self.gap


class HeatmapCalendar(tk.Canvas):
    """
    Full month grid (Mon–Sun rows per design preference, columns = weekdays).
    Each cell background = that day's overall completion heatmap color.
    Click a day → on_click(date) callback (Calendar screen detail panel).
    """

    WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def __init__(self, master, year: int, month: int,
                 ratios: Optional[dict[str, float]] = None,
                 selected: Optional[date] = None,
                 on_click: Optional[Callable[[date], None]] = None,
                 cell_w: int = 96, cell_h: int = 74, **kwargs):
        self.year = year
        self.month = month
        self._ratios: dict[str, float] = ratios or {}
        self.selected = selected
        self.on_click = on_click
        self.cell_w = cell_w
        self.cell_h = cell_h
        cols = 7
        rows = 7  # header + up to 6 week rows
        width = cols * cell_w + 8
        height = rows * cell_h + 26
        bg = kwargs.pop("bg", Colors.BG_CARD)
        super().__init__(master, width=width, height=height, highlightthickness=0,
                         bd=0, bg=bg, **kwargs)
        self.bind("<Button-1>", self._handle_click)
        self._hitboxes: list[tuple[int, int, int, int, date]] = []
        self.redraw()

    def set_month(self, year: int, month: int, ratios: dict[str, float],
                  selected: Optional[date] = None) -> None:
        self.year = year
        self.month = month
        self._ratios = ratios or {}
        self.selected = selected
        self.redraw()

    def set_ratios(self, ratios: dict[str, float]) -> None:
        self._ratios = ratios or {}
        self.redraw()

    def _cell_color(self, day: date) -> str:
        return Colors.heat_color(_safe_ratio(self._ratios.get(day.isoformat(), 0.0)))

    def redraw(self) -> None:
        self.delete("all")
        self._hitboxes.clear()
        # Weekday header
        for col, label in enumerate(self.WEEKDAYS):
            x0 = 4 + col * self.cell_w
            self.create_text(x0 + self.cell_w // 2, 14, text=label,
                             fill=Colors.TEXT_MUTED, font=(Fonts.FAMILY, 11, "bold"))
        # First day of month
        first = date(self.year, self.month, 1)
        if self.month == 12:
            nxt = date(self.year + 1, 1, 1)
        else:
            nxt = date(self.year, self.month + 1, 1)
        last_day = (nxt - timedelta(days=1)).day
        # Monday=0 offset
        offset = (first.weekday()) % 7

        row, col = 0, offset
        y_top = 26
        for day_num in range(1, last_day + 1):
            day = date(self.year, self.month, day_num)
            x0 = 4 + col * self.cell_w
            y0 = y_top + row * self.cell_h
            x1 = x0 + self.cell_w - 4
            y1 = y0 + self.cell_h - 4
            color = self._cell_color(day)
            is_today = day == date.today()
            is_sel = self.selected == day
            outline = Colors.ACCENT if is_sel else (Colors.TEXT_SECONDARY if is_today else Colors.BG_BASE)
            self.create_rectangle(x0, y0, x1, y1, fill=color, outline=outline,
                                  width=2 if (is_sel or is_today) else 1)
            # Day number
            text_color = Colors.TEXT_PRIMARY if color in (Colors.HEAT_4, Colors.HEAT_5) else Colors.TEXT_SECONDARY
            self.create_text(x0 + 10, y0 + 11, text=str(day_num), anchor="nw",
                             fill=text_color, font=(Fonts.FAMILY, 11, "bold"))
            # Completion label inside cell (only when data exists)
            ratio = _safe_ratio(self._ratios.get(day.isoformat(), 0.0))
            if ratio > 0:
                pct = int(round(ratio * 100))
                self.create_text(x1 - 8, y1 - 8, text=f"{pct}%", anchor="se",
                                 fill=text_color, font=(Fonts.FAMILY, 10))
            else:
                # subtle empty-day marker so zero-data months still read as a calendar
                self.create_text(x0 + (self.cell_w - 4) // 2, y0 + (self.cell_h - 4) // 2 + 6,
                                 text="·", fill=Colors.HEAT_1, font=(Fonts.FAMILY, 16))
            self._hitboxes.append((x0, y0, x1, y1, day))
            col += 1
            if col > 6:
                col = 0
                row += 1

    def _handle_click(self, event) -> None:
        for x0, y0, x1, y1, day in self._hitboxes:
            if x0 <= event.x <= x1 and y0 <= event.y <= y1:
                if self.on_click:
                    self.on_click(day)
                return
