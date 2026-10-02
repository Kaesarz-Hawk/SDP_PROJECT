"""Sidebar navigation component for Momentum.

Provides a persistent modern sidebar on the left with brand identity,
styled navigation buttons, and visual active state indication.
"""

from typing import Callable, Dict
import customtkinter as ctk

from utils.theme import (
    COLOR_ACCENT,
    COLOR_BG_CARD_HOVER,
    COLOR_BG_SIDEBAR,
    COLOR_BORDER,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    CORNER_MD,
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


class Sidebar(ctk.CTkFrame):
    """Persistent sidebar navigation frame."""

    NAV_ITEMS = [
        ("dashboard", "⚡ Dashboard"),
        ("habit_tracker", "📋 Habit Tracker"),
        ("calendar", "📅 Calendar"),
        ("todo", "✅ To-Do Tasks"),
        ("analytics", "📊 Analytics"),
        ("plan_builder", "🎯 Plan Builder"),
        ("settings", "⚙️ Settings"),
    ]

    def __init__(self, master, on_navigate: Callable[[str], None], **kwargs):
        super().__init__(
            master,
            width=230,
            fg_color=COLOR_BG_SIDEBAR,
            corner_radius=0,
            border_width=1,
            border_color=COLOR_BORDER,
            **kwargs,
        )
        self.on_navigate = on_navigate
        self.nav_buttons: Dict[str, ctk.CTkButton] = {}
        self.current_screen = "dashboard"

        self._build_sidebar()

    def _build_sidebar(self) -> None:
        # Prevent auto-shrinking
        self.pack_propagate(False)

        # 1. Header & Logo
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=PAD_MD, pady=(PAD_LG, PAD_MD))

        logo_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        logo_row.pack(fill="x")

        ctk.CTkLabel(
            logo_row,
            text="🔥 Momentum",
            font=FONT_TITLE,
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(side="left")

        ctk.CTkLabel(
            header_frame,
            text="Consistency OS",
            font=FONT_CAPTION,
            text_color=COLOR_ACCENT,
        ).pack(anchor="w", pady=(2, 0))

        # Divider
        divider = ctk.CTkFrame(self, height=1, fg_color=COLOR_BORDER)
        divider.pack(fill="x", padx=PAD_MD, pady=(PAD_SM, PAD_MD))

        # 2. Navigation items
        nav_container = ctk.CTkFrame(self, fg_color="transparent")
        nav_container.pack(fill="both", expand=True, padx=PAD_SM)

        ctk.CTkLabel(
            nav_container,
            text="MENU",
            font=FONT_CAPTION,
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w", padx=PAD_SM, pady=(0, PAD_SM))

        for key, label in self.NAV_ITEMS:
            btn = ctk.CTkButton(
                nav_container,
                text=label,
                font=FONT_BODY_BOLD,
                anchor="w",
                height=42,
                corner_radius=CORNER_MD,
                fg_color="transparent",
                hover_color=COLOR_BG_CARD_HOVER,
                text_color=COLOR_TEXT_SECONDARY,
                command=lambda k=key: self._handle_click(k),
            )
            btn.pack(fill="x", pady=PAD_XS)
            self.nav_buttons[key] = btn

        # 3. Bottom Footer
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", side="bottom", padx=PAD_MD, pady=PAD_MD)

        ctk.CTkLabel(
            footer,
            text="v1.0.0 • Offline Ready",
            font=FONT_CAPTION,
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w")

        # Set default active
        self.set_active("dashboard")

    def _handle_click(self, key: str) -> None:
        self.set_active(key)
        if self.on_navigate:
            self.on_navigate(key)

    def set_active(self, key: str) -> None:
        self.current_screen = key
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(
                    fg_color=COLOR_ACCENT,
                    text_color=COLOR_TEXT_PRIMARY,
                    hover_color=COLOR_ACCENT,
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLOR_TEXT_SECONDARY,
                    hover_color=COLOR_BG_CARD_HOVER,
                )
