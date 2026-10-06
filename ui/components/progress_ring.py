"""
Circular / donut progress ring widget.
Drawn with Tkinter Canvas arc drawing (explicitly allowed by the design doc) —
lightweight enough to show many rings on the Dashboard at once.
"""
from __future__ import annotations

import math
import tkinter as tk
from typing import Optional

try:
    from utils.theme import Fonts, Colors
except ImportError:  # pragma: no cover
    from ...utils.theme import Fonts, Colors


def _resolve_bg(master) -> str:
    """
    Best-effort parent background:
    CTk widgets expose fg_color (NOT bg), plain tk widgets expose bg.
    """
    try:
        fg = master.cget("fg_color")
        if isinstance(fg, str) and fg not in ("", "transparent"):
            return fg
    except Exception:
        pass
    try:
        bg = master.cget("bg")
        if isinstance(bg, str) and bg:
            return bg
    except Exception:
        pass
    return Colors.BG_CARD


class ProgressRing(tk.Canvas):
    """
    A circular progress indicator.
      value      : 0..100 percent
      track_color: background ring
      fill_color : progress arc color
      width      : ring thickness in px
      show_pct   : draw percentage text in the center
    """

    def __init__(
        self,
        master,
        value: float = 0.0,
        size: int = 90,
        width: int = 9,
        track_color: str = "#24242E",
        fill_color: str = "#7C5CFC",
        text_color: str = "#F4F4F8",
        font_size: int = 14,
        show_pct: bool = True,
        center_text: Optional[str] = None,
        **kwargs,
    ):
        bg = kwargs.pop("bg", None) or _resolve_bg(master)
        super().__init__(
            master,
            width=size,
            height=size,
            highlightthickness=0,
            bd=0,
            bg=bg,
            **kwargs,
        )
        self.size = size
        self.thickness = width
        self.track_color = track_color
        self.fill_color = fill_color
        self.text_color = text_color
        self.font_size = font_size
        self.show_pct = show_pct
        self.center_text_override = center_text
        self._value = 0.0
        self._text_id = None
        self.draw(value)

    def _clamp(self, value) -> float:
        try:
            return max(0.0, min(100.0, float(value)))
        except (TypeError, ValueError):
            return 0.0

    def set_colors(self, track_color: str, fill_color: str) -> None:
        self.track_color = track_color
        self.fill_color = fill_color

    def draw(self, value: float) -> None:
        """Render ring at the given percentage (0..100)."""
        self._value = self._clamp(value)
        self.delete("all")
        pad = self.thickness // 2 + 2
        bbox = (pad, pad, self.size - pad, self.size - pad)
        # Background track (full circle)
        self.create_arc(*bbox, start=90, extent=360,
                        style=tk.ARC, outline=self.track_color, width=self.thickness)
        # Progress arc — clockwise from 12 o'clock
        extent = -360.0 * (self._value / 100.0)
        if self._value > 0:
            if self._value >= 99.95:
                extent = -359.9  # avoid full-circle arc rendering quirk
            self.create_arc(*bbox, start=90, extent=extent,
                            style=tk.ARC, outline=self.fill_color, width=self.thickness)
        if self.center_text_override is not None:
            label = self.center_text_override
        elif self.show_pct:
            label = f"{int(round(self._value))}%"
        else:
            label = ""
        if label:
            cx = self.size // 2
            self._text_id = self.create_text(
                cx, cx, text=label, fill=self.text_color,
                font=(Fonts.FAMILY, self.font_size, "bold"),
            )

    def set_value(self, value: float) -> None:
        self.draw(value)

    @property
    def value(self) -> float:
        return self._value
