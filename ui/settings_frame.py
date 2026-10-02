"""Settings Screen (Screen 7) for Momentum.

Provides:
- Application version & runtime environment information
- Theme mode selector (Dark / Light mode) with live switching
- Database statistics & storage location (using path_helper)
- Option to re-populate realistic demo seed data
- Danger Zone: Double-confirmation "Reset All Data" feature
- About Momentum architectural overview
"""

import os
import customtkinter as ctk

from database.db_manager import DBManager
from ui.components.modal_dialog import ConfirmModal, InfoModal
from utils.path_helper import get_db_path
from utils.seed_data import populate_seed_data_if_empty
from utils.theme import (
    APP_NAME,
    APP_SUBTITLE,
    APP_VERSION,
    COLOR_ACCENT,
    COLOR_BG_BASE,
    COLOR_BG_CARD,
    COLOR_BG_INPUT,
    COLOR_BORDER,
    COLOR_DANGER,
    COLOR_DANGER_HOVER,
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


class SettingsFrame(ctk.CTkFrame):
    """Settings and configuration screen."""

    def __init__(self, master, db: DBManager, on_data_reset=None, **kwargs):
        super().__init__(master, fg_color=COLOR_BG_BASE, **kwargs)
        self.db = db
        self.on_data_reset = on_data_reset

        self._build_screen()

    def refresh(self) -> None:
        self._build_screen()

    def _build_screen(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()

        # Header Bar
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=PAD_LG, pady=(PAD_MD, PAD_SM))

        ctk.CTkLabel(header, text="Application Settings", font=FONT_TITLE, text_color=COLOR_TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(header, text="Preferences, database management & diagnostics", font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY).pack(side="left", padx=PAD_MD)

        scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_container.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_SM)

        # 1. Appearance / Theme Card
        theme_card = ctk.CTkFrame(scroll_container, fg_color=COLOR_BG_CARD, corner_radius=CORNER_MD, border_width=1, border_color=COLOR_BORDER)
        theme_card.pack(fill="x", pady=(0, PAD_MD))

        t_inner = ctk.CTkFrame(theme_card, fg_color="transparent")
        t_inner.pack(fill="x", padx=PAD_LG, pady=PAD_MD)

        ctk.CTkLabel(t_inner, text="Visual Appearance", font=FONT_SUBTITLE, text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(t_inner, text="Toggle between Dark (primary target) and Light user interface styles.", font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w", pady=(0, PAD_MD))

        mode_row = ctk.CTkFrame(t_inner, fg_color="transparent")
        mode_row.pack(fill="x")

        ctk.CTkLabel(mode_row, text="Theme Mode:", font=FONT_BODY_BOLD, text_color=COLOR_TEXT_PRIMARY).pack(side="left", padx=(0, PAD_MD))

        current_mode = ctk.get_appearance_mode()
        self.theme_seg = ctk.CTkSegmentedButton(
            mode_row,
            values=["Dark", "Light"],
            command=self._on_theme_change,
            selected_color=COLOR_ACCENT,
            font=FONT_BODY,
        )
        self.theme_seg.set("Dark" if current_mode.lower() == "dark" else "Light")
        self.theme_seg.pack(side="left")

        # 2. Database & Storage Diagnostics Card
        db_card = ctk.CTkFrame(scroll_container, fg_color=COLOR_BG_CARD, corner_radius=CORNER_MD, border_width=1, border_color=COLOR_BORDER)
        db_card.pack(fill="x", pady=(0, PAD_MD))

        d_inner = ctk.CTkFrame(db_card, fg_color="transparent")
        d_inner.pack(fill="x", padx=PAD_LG, pady=PAD_MD)

        ctk.CTkLabel(d_inner, text="Data & Local Storage", font=FONT_SUBTITLE, text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(d_inner, text="All application state is stored locally and securely in an offline SQLite database.", font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w", pady=(0, PAD_MD))

        db_path = get_db_path()
        db_size_kb = 0
        if os.path.exists(db_path):
            db_size_kb = os.path.getsize(db_path) / 1024

        tracks_count = len(self.db.get_all_tracks())
        habits_count = len(self.db.get_active_habits())

        info_text = (
            f"• Database File: {db_path}\n"
            f"• Storage Size: {db_size_kb:.1f} KB\n"
            f"• Configured Tracks: {tracks_count}\n"
            f"• Active Habits: {habits_count}\n"
            f"• Storage Engine: SQLite3 (WAL mode, Foreign Keys Enforced)"
        )

        stat_box = ctk.CTkFrame(d_inner, fg_color="#181822", corner_radius=CORNER_SM)
        stat_box.pack(fill="x", pady=(0, PAD_MD))
        ctk.CTkLabel(stat_box, text=info_text, font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY, justify="left").pack(padx=PAD_MD, pady=PAD_MD, anchor="w")

        # Seed data trigger if needed
        btn_reseed = ctk.CTkButton(
            d_inner,
            text="🌱 Re-seed Demo Sample Data",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_BG_INPUT,
            hover_color=COLOR_BORDER,
            command=self._handle_reseed,
            width=210,
        )
        btn_reseed.pack(anchor="w")

        # 3. About & Engineering Stack Card
        about_card = ctk.CTkFrame(scroll_container, fg_color=COLOR_BG_CARD, corner_radius=CORNER_MD, border_width=1, border_color=COLOR_BORDER)
        about_card.pack(fill="x", pady=(0, PAD_MD))

        a_inner = ctk.CTkFrame(about_card, fg_color="transparent")
        a_inner.pack(fill="x", padx=PAD_LG, pady=PAD_MD)

        ctk.CTkLabel(a_inner, text=f"About {APP_NAME}", font=FONT_SUBTITLE, text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(a_inner, text=f"{APP_NAME} v{APP_VERSION} — {APP_SUBTITLE}", font=FONT_BODY_BOLD, text_color=COLOR_ACCENT).pack(anchor="w", pady=(0, PAD_SM))

        about_desc = (
            "Momentum is an offline personal consistency and habit tracking desktop operating system.\n"
            "Built with strict modular OOP architecture: separated database queries, data models, and UI shell.\n"
            "Technology Stack: Python 3.10+, CustomTkinter, SQLite3, Matplotlib (TkAgg).\n"
            "Designed and engineered for maximum responsiveness, zero network latency, and high visual feedback."
        )
        ctk.CTkLabel(a_inner, text=about_desc, font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY, justify="left").pack(anchor="w")

        # 4. Danger Zone Card (Double confirmation reset)
        danger_card = ctk.CTkFrame(scroll_container, fg_color="#241416", corner_radius=CORNER_MD, border_width=1, border_color=COLOR_DANGER)
        danger_card.pack(fill="x", pady=PAD_MD)

        dang_inner = ctk.CTkFrame(danger_card, fg_color="transparent")
        dang_inner.pack(fill="x", padx=PAD_LG, pady=PAD_MD)

        ctk.CTkLabel(dang_inner, text="⚠️ Danger Zone", font=FONT_SUBTITLE, text_color=COLOR_DANGER).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(
            dang_inner,
            text="Permanently clear all user records, tracks, habits, daily logs, tasks, and plans.",
            font=FONT_BODY,
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(anchor="w", pady=(0, PAD_MD))

        ctk.CTkButton(
            dang_inner,
            text="Reset All Application Data",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_DANGER,
            hover_color=COLOR_DANGER_HOVER,
            command=self._handle_first_reset_warning,
            width=220,
        ).pack(anchor="w")

    def _on_theme_change(self, mode: str) -> None:
        ctk.set_appearance_mode(mode.lower())

    def _handle_reseed(self) -> None:
        def confirm_reseed():
            populate_seed_data_if_empty(self.db)
            InfoModal(self, title="Demo Data Seeded", message="Sample tracks, habits, 30 days of logs, and tasks have been verified.")
            self.refresh()
            if self.on_data_reset:
                self.on_data_reset()

        ConfirmModal(
            self,
            title="Seed Sample Data",
            message="Populate realistic demonstration data if database is empty?",
            confirm_text="Seed Data",
            on_confirm=confirm_reseed,
        )

    def _handle_first_reset_warning(self) -> None:
        """First confirmation dialog."""
        ConfirmModal(
            self,
            title="Reset All Data (Step 1/2)",
            message="Are you sure you want to reset all data? This will erase all tracks, habits, check-ins, tasks, and plans.",
            confirm_text="Continue to Final Warning",
            is_danger=True,
            on_confirm=self._handle_second_reset_warning,
        )

    def _handle_second_reset_warning(self) -> None:
        """Second (final) confirmation dialog for irreversible action."""
        ConfirmModal(
            self,
            title="FINAL WARNING (Step 2/2)",
            message="THIS ACTION CANNOT BE UNDONE. All streaks and historical statistics will be permanently destroyed. Confirm reset?",
            confirm_text="Permanently Wipe Everything",
            is_danger=True,
            on_confirm=self._execute_full_reset,
        )

    def _execute_full_reset(self) -> None:
        try:
            self.db.reset_all_data()
            InfoModal(
                self,
                title="Data Cleared",
                message="All database records have been wiped. You now have a clean slate.",
            )
            self.refresh()
            if self.on_data_reset:
                self.on_data_reset()
        except Exception as e:
            InfoModal(self, title="Reset Failed", message=str(e), is_error=True)
