"""
Reusable modal dialogs — styled to match Momentum's dark design system.
NO default tkinter.messagebox anywhere in the app (file 07 requirement):
all confirmations, forms, and friendly errors go through these modals.

- show_message()  : informational modal (OK)
- show_error()    : friendly error modal (technical details stay in console log)
- ConfirmModal    : confirm-before-delete (double-confirm supported for Reset)
- FormModal       : generic input form with validation + safe submit
"""
from __future__ import annotations

import tkinter as tk
import customtkinter as ctk
from typing import Callable, Optional

try:
    from utils.theme import Colors, Fonts, Spacing
except ImportError:  # pragma: no cover
    from ...utils.theme import Colors, Fonts, Spacing


class _BaseModal(ctk.CTkToplevel):
    """Shared chrome: dimmed focus, Escape-to-close, centered placement."""

    def __init__(self, master, title: str, width: int = 420, height: int = 220):
        super().__init__(master)
        self.title(title)
        self.configure(fg_color=Colors.BG_MODAL)
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.grab_set()              # block interaction with the main window
        self._on_close: Optional[Callable] = None
        self._resolved = False
        self._width = width
        self._height = height
        self.protocol("WM_DELETE_WINDOW", self._handle_close)
        self.bind("<Escape>", lambda e: self._handle_close())

    def _place_centered(self) -> None:
        self.update_idletasks()
        parent = self.master.winfo_toplevel()
        x = parent.winfo_rootx() + (parent.winfo_width() - self._width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self._height) // 2
        self.geometry(f"{self._width}x{self._height}+{max(0, x)}+{max(0, y)}")

    def _handle_close(self) -> None:
        if not self._resolved:
            self._resolved = True
            if self._on_close:
                try:
                    self._on_close()
                except Exception:
                    pass
        self._safe_destroy()

    def _finish(self) -> None:
        self._resolved = True
        self._safe_destroy()

    def _safe_destroy(self) -> None:
        """
        customtkinter (Windows) may schedule `after(10, focused_widget.focus)`
        for focus restoration; neutralize it so it can never target a widget
        that our refresh cycle destroys immediately after the modal closes.
        """
        try:
            self.focused_widget_before_widthdraw = None
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass

    def set_close_callback(self, cb: Callable) -> None:
        """Called when the user dismisses without deciding (X / Escape / Cancel)."""
        self._on_close = cb


def show_message(parent, title: str, message: str, on_ok: Optional[Callable] = None) -> None:
    """Friendly informational modal (styled, not messagebox)."""
    modal = _BaseModal(parent, title, 440, 200)

    def _ok():
        if on_ok:
            on_ok()
        modal._finish()

    ctk.CTkLabel(modal, text=title, font=Fonts.subtitle(),
                 text_color=Colors.TEXT_PRIMARY).pack(padx=Spacing.XL, pady=(Spacing.XL, Spacing.SM))
    ctk.CTkLabel(modal, text=message, font=Fonts.body(),
                 text_color=Colors.TEXT_SECONDARY, wraplength=380, justify="left").pack(
        padx=Spacing.XL, pady=(0, Spacing.MD))
    ctk.CTkButton(modal, text="Got it", width=120, corner_radius=Spacing.BUTTON_RADIUS,
                  fg_color=Colors.ACCENT, hover_color=Colors.ACCENT_HOVER,
                  font=Fonts.body_bold(), command=_ok).pack(pady=(0, Spacing.XL))
    modal._place_centered()
    modal.wait_window()


def show_error(parent, title: str, friendly_message: str, technical: str = "") -> None:
    """Clean error modal. Technical detail is logged to console, never shown raw."""
    if technical:
        print(f"[Momentum:Error] {title}: {technical}")
    modal = _BaseModal(parent, title, 460, 220)
    ctk.CTkLabel(modal, text=f"⚠️  {title}", font=Fonts.subtitle(),
                 text_color=Colors.WARNING).pack(padx=Spacing.XL, pady=(Spacing.XL, Spacing.SM))
    ctk.CTkLabel(modal, text=friendly_message, font=Fonts.body(),
                 text_color=Colors.TEXT_SECONDARY, wraplength=400, justify="left").pack(
        padx=Spacing.XL, pady=(0, Spacing.MD))
    ctk.CTkButton(modal, text="OK", width=120, corner_radius=Spacing.BUTTON_RADIUS,
                  fg_color=Colors.ACCENT, hover_color=Colors.ACCENT_HOVER,
                  font=Fonts.body_bold(),
                  command=modal._finish).pack(pady=(0, Spacing.XL))
    modal._place_centered()
    modal.wait_window()


class ConfirmModal(_BaseModal):
    """
    Confirm-before-delete modal (never silent delete on single click).
    double_confirm=True adds a SECOND confirmation step for irreversible actions
    (Settings → Reset all data).
    """

    def __init__(self, master, title: str, message: str,
                 on_confirm: Callable, on_cancel: Optional[Callable] = None,
                 confirm_text: str = "Delete", danger: bool = True,
                 double_confirm: bool = False):
        super().__init__(master, title, 480, 260 if not double_confirm else 300)
        self._on_confirm = on_confirm
        self._stage = 1
        self._double = double_confirm
        self.set_close_callback(on_cancel)

        self._title_lbl = ctk.CTkLabel(self, text=title, font=Fonts.subtitle(),
                                       text_color=Colors.DANGER if danger else Colors.TEXT_PRIMARY)
        self._title_lbl.pack(padx=Spacing.XL, pady=(Spacing.XL, Spacing.SM))
        self._msg_lbl = ctk.CTkLabel(self, text=message, font=Fonts.body(),
                                     text_color=Colors.TEXT_SECONDARY, wraplength=420, justify="left")
        self._msg_lbl.pack(padx=Spacing.XL, pady=(0, Spacing.MD))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=(0, Spacing.XL))
        self._cancel_btn = ctk.CTkButton(
            btn_row, text="Cancel", width=110, corner_radius=Spacing.BUTTON_RADIUS,
            fg_color=Colors.BG_ELEVATED, hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_PRIMARY, font=Fonts.body(),
            command=self._cancel)
        self._cancel_btn.pack(side="left", padx=Spacing.SM)
        self._confirm_btn = ctk.CTkButton(
            btn_row, text=confirm_text, width=130, corner_radius=Spacing.BUTTON_RADIUS,
            fg_color=Colors.DANGER if danger else Colors.ACCENT,
            hover_color=Colors.DANGER_HOVER if danger else Colors.ACCENT_HOVER,
            font=Fonts.body_bold(), command=self._confirm)
        self._confirm_btn.pack(side="left", padx=Spacing.SM)
        self._place_centered()
        self.wait_window()

    def _confirm(self):
        if self._double and self._stage == 1:
            self._stage = 2
            self._title_lbl.configure(text="Are you absolutely sure?",
                                      text_color=Colors.DANGER)
            self._msg_lbl.configure(
                text=("This is your LAST warning. All tracks, habits, history, "
                      "tasks and plans will be permanently deleted.\nThis cannot be undone."))
            self._confirm_btn.configure(text="Yes, erase everything")
            return
        cb = self._on_confirm
        self._finish()
        if cb:
            cb()

    def _cancel(self):
        cb = self._on_close
        self._finish()
        if cb:
            cb()


class FormModal(_BaseModal):
    """
    Generic form modal.

    fields: list of dicts:
        {"key", "label", "type": "entry"|"option"|"date",
         "initial"?, "placeholder"?, "options"?, "max_length"?}
    validate(values) -> Optional[str]: return an error message to block submit.
    on_submit(values): called with clean values after validation passes.
    """

    def __init__(self, master, title: str, fields: list[dict],
                 on_submit: Callable, validate: Optional[Callable] = None,
                 submit_text: str = "Save", width: int = 460):
        height = 150 + 74 * len(fields)
        super().__init__(master, title, width, height)
        self._fields = fields
        self._on_submit = on_submit
        self._validate = validate
        self._entries: dict[str, tk.Variable] = {}
        self._error_lbl = None

        ctk.CTkLabel(self, text=title, font=Fonts.subtitle(),
                     text_color=Colors.TEXT_PRIMARY).pack(
            padx=Spacing.XL, pady=(Spacing.XL, Spacing.SM))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=Spacing.XL, pady=0)
        for spec in fields:
            row = ctk.CTkFrame(form, fg_color="transparent")
            row.pack(fill="x", pady=Spacing.SM)
            ctk.CTkLabel(row, text=spec["label"], font=Fonts.small(),
                         text_color=Colors.TEXT_SECONDARY, width=130, anchor="w").pack(
                side="left", padx=(0, Spacing.SM))
            ftype = spec.get("type", "entry")
            if ftype == "option":
                var = tk.StringVar(value=str(spec.get("initial") or spec["options"][0]))
                widget = ctk.CTkOptionMenu(
                    row, values=list(spec.get("options", [])), variable=var,
                    width=200, fg_color=Colors.BG_ELEVATED,
                    button_color=Colors.ACCENT, button_hover_color=Colors.ACCENT_HOVER,
                    dropdown_fg_color=Colors.BG_ELEVATED,
                    font=Fonts.body())
                widget.pack(side="left", fill="x", expand=True)
            else:
                var = tk.StringVar(value=str(spec.get("initial") or ""))
                widget = ctk.CTkEntry(
                    row, textvariable=var, height=34,
                    placeholder_text=spec.get("placeholder", ""),
                    fg_color=Colors.BG_INPUT, border_color=Colors.BG_ELEVATED,
                    text_color=Colors.TEXT_PRIMARY, font=Fonts.body(),
                    corner_radius=Spacing.BUTTON_RADIUS)
                if spec.get("max_length"):
                    # Cap input length in the form itself (file 07)
                    widget.configure(validate="key",
                                     validatecommand=(self.register(
                                         lambda v, m=spec["max_length"]: len(v) <= m), "%P"))
                widget.pack(side="left", fill="x", expand=True)
            self._entries[spec["key"]] = var

        self._error_lbl = ctk.CTkLabel(self, text="", font=Fonts.small(),
                                       text_color=Colors.DANGER, wraplength=400)
        self._error_lbl.pack(padx=Spacing.XL, pady=(Spacing.SM, 0))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=Spacing.MD)
        ctk.CTkButton(btn_row, text="Cancel", width=110,
                      corner_radius=Spacing.BUTTON_RADIUS,
                      fg_color=Colors.BG_ELEVATED, hover_color=Colors.BG_HOVER,
                      text_color=Colors.TEXT_PRIMARY, font=Fonts.body(),
                      command=self._handle_close).pack(side="left", padx=Spacing.SM)
        ctk.CTkButton(btn_row, text=submit_text, width=140,
                      corner_radius=Spacing.BUTTON_RADIUS,
                      fg_color=Colors.ACCENT, hover_color=Colors.ACCENT_HOVER,
                      font=Fonts.body_bold(), command=self._submit).pack(
            side="left", padx=Spacing.SM)
        self._place_centered()
        self.wait_window()

    def _values(self) -> dict:
        return {k: v.get() for k, v in self._entries.items()}

    def _submit(self):
        values = self._values()
        if self._validate:
            try:
                error = self._validate(values)
            except Exception as exc:  # validation itself must never crash
                error = str(exc)
            if error:
                self._error_lbl.configure(text=error)
                return
        cb = self._on_submit
        self._finish()
        if cb:
            cb(values)
