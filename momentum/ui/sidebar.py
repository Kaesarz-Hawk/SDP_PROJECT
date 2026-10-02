"""
Sidebar — persistent left navigation (logo + icon/label nav items).
Active item is highlighted with the accent color + left indicator bar.
"""
from __future__ import annotations

import customtkinter as ctk
from typing import Callable, Optional

try:
    from utils.theme import Colors, Fonts, Spacing
except ImportError:  # pragma: no cover
    from ..utils.theme import Colors, Fonts, Spacing


NAV_ITEMS = [
    ("dashboard", "📊", "Dashboard"),
    ("habits", "✅", "Habit Tracker"),
    ("todo", "☑", "To-Do"),
    ("calendar", "📅", "Calendar"),
    ("analytics", "📈", "Analytics"),
    ("onboarding", "🎯", "Plan Builder"),
    ("settings", "⚙", "Settings"),
]


class Sidebar(ctk.CTkFrame):
    """Navigation rail. Owns no data — just raises navigation events."""

    def __init__(self, master, on_navigate: Callable[[str], None]):
        super().__init__(master, width=Spacing.SIDEBAR_WIDTH, corner_radius=0,
                         fg_color=Colors.BG_SIDEBAR)
        self.on_navigate = on_navigate
        self.active_key: str = "dashboard"
        self._buttons: dict[str, ctk.CTkButton] = {}

        # Logo
        logo = ctk.CTkLabel(self, text="🎯 Momentum", font=(Fonts.FAMILY, 22, "bold"),
                            text_color=Colors.TEXT_PRIMARY)
        logo.pack(anchor="w", padx=Spacing.MD, pady=(Spacing.LG, Spacing.XL))

        # Nav buttons
        for key, icon, label in NAV_ITEMS:
            btn = ctk.CTkButton(
                self, text=f"  {icon}  {label}", anchor="w",
                font=Fonts.nav(), height=42, corner_radius=Spacing.BUTTON_RADIUS,
                fg_color="transparent", hover_color=Colors.BG_ELEVATED,
                text_color=Colors.TEXT_SECONDARY,
                command=lambda k=key: self._click(k))
            btn.pack(fill="x", padx=Spacing.SM, pady=2)
            self._buttons[key] = btn

        # Footer hint
        ctk.CTkLabel(self, text="100% offline\nSingle user",
                     font=Fonts.caption(), text_color=Colors.TEXT_MUTED,
                     justify="left").pack(side="bottom", anchor="w",
                                          padx=Spacing.MD, pady=Spacing.MD)

        self.set_active("dashboard")

    def _click(self, key: str):
        if key == self.active_key:
            return
        self.set_active(key)
        self.on_navigate(key)

    def set_active(self, key: str) -> None:
        self.active_key = key
        for k, btn in self._buttons.items():
            if k == key:
                btn.configure(fg_color=Colors.ACCENT,
                              hover_color=Colors.ACCENT_HOVER,
                              text_color=Colors.TEXT_PRIMARY,
                              font=Fonts.nav_active())
            else:
                btn.configure(fg_color="transparent",
                              hover_color=Colors.BG_ELEVATED,
                              text_color=Colors.TEXT_SECONDARY,
                              font=Fonts.nav())
