"""Reusable circular / donut progress ring widget for Momentum.

Implemented via Tkinter Canvas for high-performance, flicker-free rendering
in dark and light modes without heavy matplotlib overhead for small cards.
"""

import tkinter as tk
from typing import Optional
import customtkinter as ctk

from utils.theme import (
    COLOR_ACCENT,
    COLOR_BG_CARD,
    COLOR_BORDER,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY,
)


class ProgressRing(ctk.CTkFrame):
    """Circular donut progress ring that visualizes a percentage value (0.0 to 1.0)."""

    def __init__(
        self,
        master,
        size: int = 60,
        thickness: int = 6,
        progress: float = 0.0,
        color: str = COLOR_ACCENT,
        track_color: str = COLOR_BORDER,
        bg_color: str = COLOR_BG_CARD,
        show_text: bool = True,
        text_font: Optional[tuple] = None,
        custom_text: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color=bg_color, bg_color=bg_color, **kwargs)
        self.size = size
        self.thickness = thickness
        self.progress = max(0.0, min(1.0, progress))
        self.color = color
        self.track_color = track_color
        self.surface_color = bg_color
        self.show_text = show_text
        self.custom_text = custom_text
        self.text_font = text_font or (FONT_FAMILY, max(8, int(size * 0.2)), "bold")

        self.canvas = tk.Canvas(
            self,
            width=self.size,
            height=self.size,
            bg=self.surface_color,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True)
        self.draw()

    def set_progress(self, progress: float, custom_text: Optional[str] = None) -> None:
        """Updates the progress percentage and redraws."""
        self.progress = max(0.0, min(1.0, progress))
        if custom_text is not None:
            self.custom_text = custom_text
        self.draw()

    def set_color(self, color: str) -> None:
        self.color = color
        self.draw()

    def draw(self) -> None:
        self.canvas.delete("all")
        pad = self.thickness // 2 + 2
        bbox = (pad, pad, self.size - pad, self.size - pad)

        # 1. Background full track ring
        self.canvas.create_oval(
            bbox,
            outline=self.track_color,
            width=self.thickness,
        )

        # 2. Foreground progress arc
        extent = -1 * (self.progress * 359.9)
        if self.progress > 0.001:
            self.canvas.create_arc(
                bbox,
                start=90,
                extent=extent,
                outline=self.color,
                width=self.thickness,
                style=tk.ARC,
            )

        # 3. Center text
        if self.show_text:
            display_str = self.custom_text if self.custom_text is not None else f"{int(self.progress * 100)}%"
            self.canvas.create_text(
                self.size // 2,
                self.size // 2,
                text=display_str,
                fill=COLOR_TEXT_PRIMARY,
                font=self.text_font,
            )
