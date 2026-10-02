"""Modern reusable modal dialog components for Momentum.

Provides custom-styled confirmation and form dialogs matching the dark UI theme,
preventing raw Tkinter default system popups.
"""

from typing import Callable, Optional
import customtkinter as ctk

from utils.theme import (
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_BG_CARD,
    COLOR_BG_INPUT,
    COLOR_BORDER,
    COLOR_DANGER,
    COLOR_DANGER_HOVER,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    CORNER_MD,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_FAMILY,
    FONT_SUBTITLE,
    PAD_LG,
    PAD_MD,
    PAD_SM,
)


class BaseModal(ctk.CTkToplevel):
    """Base modal window with darkened backdrop styling and grab focus."""

    def __init__(self, parent, title: str = "Dialog", width: int = 440, height: int = 280):
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG_CARD)

        # Center on parent
        self.transient(parent)
        self.grab_set()

        # Center positioning calculation
        parent.update_idletasks()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        x = px + (pw - width) // 2
        y = py + (ph - height) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")


class ConfirmModal(BaseModal):
    """Modern confirmation dialog for destructive or critical actions."""

    def __init__(
        self,
        parent,
        title: str = "Confirm Action",
        message: str = "Are you sure you want to proceed?",
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        is_danger: bool = False,
        on_confirm: Optional[Callable[[], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
        width: int = 420,
        height: int = 220,
    ):
        super().__init__(parent, title=title, width=width, height=height)
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_LG)

        ctk.CTkLabel(
            container,
            text=title,
            font=FONT_SUBTITLE,
            text_color=COLOR_DANGER if is_danger else COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, PAD_SM))

        ctk.CTkLabel(
            container,
            text=message,
            font=FONT_BODY,
            text_color=COLOR_TEXT_SECONDARY,
            wraplength=width - 60,
            justify="left",
        ).pack(anchor="w", pady=(0, PAD_LG))

        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom")

        btn_cancel = ctk.CTkButton(
            btn_row,
            text=cancel_text,
            fg_color=COLOR_BG_INPUT,
            hover_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            command=self._cancel,
            width=100,
        )
        btn_cancel.pack(side="right", padx=(PAD_SM, 0))

        btn_confirm = ctk.CTkButton(
            btn_row,
            text=confirm_text,
            fg_color=COLOR_DANGER if is_danger else COLOR_ACCENT,
            hover_color=COLOR_DANGER_HOVER if is_danger else COLOR_ACCENT_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            command=self._confirm,
            width=110,
        )
        btn_confirm.pack(side="right")

    def _confirm(self):
        self.destroy()
        if self.on_confirm:
            self.on_confirm()

    def _cancel(self):
        self.destroy()
        if self.on_cancel:
            self.on_cancel()


class InfoModal(BaseModal):
    """Information or notification modal."""

    def __init__(
        self,
        parent,
        title: str = "Notice",
        message: str = "",
        is_error: bool = False,
        width: int = 400,
        height: int = 200,
    ):
        super().__init__(parent, title=title, width=width, height=height)
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_LG)

        header_icon = "⚠️" if is_error else "ℹ️"
        ctk.CTkLabel(
            container,
            text=f"{header_icon} {title}",
            font=FONT_SUBTITLE,
            text_color=COLOR_DANGER if is_error else COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, PAD_SM))

        ctk.CTkLabel(
            container,
            text=message,
            font=FONT_BODY,
            text_color=COLOR_TEXT_SECONDARY,
            wraplength=width - 60,
            justify="left",
        ).pack(anchor="w", pady=(0, PAD_LG))

        btn_ok = ctk.CTkButton(
            container,
            text="OK",
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            command=self.destroy,
            width=90,
        )
        btn_ok.pack(side="bottom", anchor="e")
