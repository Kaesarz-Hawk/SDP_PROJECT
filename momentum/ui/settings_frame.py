"""
Screen 7: Settings — minimal but present.

- App version display
- Theme toggle (dark/light) — functional; rebuilds the UI with the new palette
- "Reset all data" with DOUBLE confirm (irreversible)
- About section
"""
from __future__ import annotations

import customtkinter as ctk

try:
    from utils.theme import Colors, Fonts, Spacing, ThemeConfig
except ImportError:  # pragma: no cover
    from ..utils.theme import Colors, Fonts, Spacing, ThemeConfig

from .components.modal_dialog import ConfirmModal, show_message, show_error

APP_VERSION = "1.0.0"
APP_ABOUT = ("Momentum — a personal consistency & productivity tracker. "
             "100% offline, single-user, built with Python + Tkinter + SQLite.")


class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master, db, app):
        super().__init__(master, fg_color=Colors.BG_BASE, corner_radius=0)
        self.db = db
        self.app = app

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=Spacing.XL, pady=(Spacing.LG, Spacing.MD))
        ctk.CTkLabel(head, text="Settings", font=Fonts.title(),
                     text_color=Colors.TEXT_PRIMARY).pack(side="left")

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=Spacing.XL, pady=(0, Spacing.LG))

        # ---- Appearance ----
        appearance = self._card("🎨 Appearance")
        row = ctk.CTkFrame(appearance, fg_color="transparent")
        row.pack(fill="x", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))
        ctk.CTkLabel(row, text="Theme", font=Fonts.body(),
                     text_color=Colors.TEXT_SECONDARY).pack(side="left")
        self.theme_seg = ctk.CTkSegmentedButton(
            row, values=["Dark", "Light"], font=Fonts.small_bold(),
            selected_color=Colors.ACCENT, selected_hover_color=Colors.ACCENT_HOVER,
            unselected_color=Colors.BG_ELEVATED, unselected_hover_color=Colors.BG_HOVER,
            fg_color=Colors.BG_ELEVATED, text_color=Colors.TEXT_SECONDARY,
            command=self._on_theme_change)
        self.theme_seg.set("Dark" if ThemeConfig.mode != "light" else "Light")
        self.theme_seg.pack(side="right")

        # ---- About ----
        about = self._card("ℹ️ About")
        ctk.CTkLabel(about, text=f"Momentum v{APP_VERSION}",
                     font=Fonts.subtitle(), text_color=Colors.TEXT_PRIMARY).pack(
            anchor="w", padx=Spacing.MD, pady=(Spacing.XS, 2))
        ctk.CTkLabel(about, text=APP_ABOUT, font=Fonts.body(),
                     text_color=Colors.TEXT_SECONDARY, wraplength=640,
                     justify="left").pack(anchor="w", padx=Spacing.MD, pady=(0, Spacing.MD))

        # ---- Data ----
        data = self._card("💾 Data")
        info = ctk.CTkLabel(
            data,
            text="Momentum stores everything locally in momentum.db on this computer.\n"
                 "There is no cloud, no account, and no network involved.",
            font=Fonts.small(), text_color=Colors.TEXT_MUTED,
            wraplength=640, justify="left")
        info.pack(anchor="w", padx=Spacing.MD, pady=(Spacing.XS, Spacing.SM))
        btn_row = ctk.CTkFrame(data, fg_color="transparent")
        btn_row.pack(anchor="w", padx=Spacing.MD, pady=(0, Spacing.MD))
        ctk.CTkButton(btn_row, text="Reset all data…", width=160, height=36,
                      fg_color=Colors.DANGER, hover_color=Colors.DANGER_HOVER,
                      font=Fonts.body_bold(),
                      corner_radius=Spacing.BUTTON_RADIUS,
                      command=self._reset_all_data).pack(side="left")
        ctk.CTkButton(btn_row, text="What's included?", width=150, height=36,
                      fg_color=Colors.BG_ELEVATED, hover_color=Colors.BG_HOVER,
                      text_color=Colors.TEXT_PRIMARY, font=Fonts.body(),
                      corner_radius=Spacing.BUTTON_RADIUS,
                      command=self._show_about).pack(side="left", padx=Spacing.SM)

    # ------------------------------------------------------------------ #
    def _card(self, title: str) -> ctk.CTkFrame:
        card = ctk.CTkFrame(self.scroll, fg_color=Colors.BG_CARD,
                            corner_radius=Spacing.CARD_RADIUS)
        card.pack(fill="x", pady=(0, Spacing.MD))
        ctk.CTkLabel(card, text=title.upper(), font=(Fonts.FAMILY, 10, "bold"),
                     text_color=Colors.TEXT_MUTED).pack(
            anchor="w", padx=Spacing.MD, pady=(Spacing.MD, 0))
        return card

    def refresh(self) -> None:
        try:
            self.theme_seg.set("Dark" if ThemeConfig.mode != "light" else "Light")
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    def _on_theme_change(self, value: str) -> None:
        mode = "light" if value == "Light" else "dark"
        if mode == ThemeConfig.mode:
            return
        # Rebuild every screen with the new palette (controller handles it)
        self.app.set_theme(mode)

    def _show_about(self) -> None:
        show_message(
            self.winfo_toplevel(), "About Momentum",
            f"Momentum v{APP_VERSION}\n\n{APP_ABOUT}\n\n"
            "Built with Python, Tkinter (customtkinter), SQLite and matplotlib.")

    def _reset_all_data(self) -> None:
        """Irreversible → DOUBLE confirmation (file 04 + 07)."""
        def do_reset():
            try:
                self.db.reset_all_data()
                self.app.refresh_all()
                show_message(
                    self.winfo_toplevel(), "All data erased",
                    "Every track, habit, log, task and plan has been deleted.\n"
                    "Momentum is now empty — use the Plan Builder to start fresh.")
            except Exception as exc:
                show_error(self.winfo_toplevel(), "Could not reset",
                           "Your data was not fully cleared. Please try again.",
                           technical=str(exc))

        ConfirmModal(
            self.winfo_toplevel(), "Reset ALL data?",
            "This deletes every track, habit, completion history, task and plan.\n"
            "This action is irreversible.",
            on_confirm=do_reset, confirm_text="Continue…",
            double_confirm=True)
