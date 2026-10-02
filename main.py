"""Main entry point for Momentum: Personal Consistency & Productivity Tracker.

Handles:
- High-DPI and dark mode appearance initialization
- Database connection and schema verification
- Sample data seeding on first run
- Splash loading screen transition
- AppController launch and mainloop
"""

import sys
import customtkinter as ctk

from database.db_manager import DBManager, DatabaseError
from ui.app_controller import AppController
from ui.components.modal_dialog import InfoModal
from utils.path_helper import get_asset_path, get_db_path
from utils.seed_data import populate_seed_data_if_empty
from utils.theme import (
    APP_NAME,
    COLOR_ACCENT,
    COLOR_BG_BASE,
    COLOR_BG_CARD,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    CORNER_MD,
    FONT_BODY,
    FONT_CAPTION,
    FONT_DISPLAY_LARGE,
    FONT_SUBTITLE,
    FONT_TITLE,
    PAD_LG,
    PAD_MD,
)


def run_app() -> None:
    # 1. Set global styling
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title(APP_NAME)
    root.geometry("640x400")
    root.configure(fg_color=COLOR_BG_BASE)
    root.resizable(False, False)

    # Center splash window on screen
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = (screen_w - 640) // 2
    y = (screen_h - 400) // 2
    root.geometry(f"+{x}+{y}")

    # Set icon
    icon_path = get_asset_path("icon.ico")
    try:
        root.iconbitmap(icon_path)
    except Exception:
        pass

    # 2. Splash Container
    splash_frame = ctk.CTkFrame(root, fg_color=COLOR_BG_CARD, corner_radius=CORNER_MD)
    splash_frame.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_LG)

    inner = ctk.CTkFrame(splash_frame, fg_color="transparent")
    inner.pack(expand=True)

    ctk.CTkLabel(inner, text="🔥 Momentum", font=FONT_DISPLAY_LARGE, text_color=COLOR_TEXT_PRIMARY).pack(pady=(0, 4))
    ctk.CTkLabel(inner, text="Personal Consistency & Productivity Operating System", font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY).pack(pady=(0, PAD_LG))

    progress_bar = ctk.CTkProgressBar(inner, width=280, height=8, corner_radius=4, progress_color=COLOR_ACCENT)
    progress_bar.set(0.2)
    progress_bar.pack(pady=(0, PAD_MD))

    status_lbl = ctk.CTkLabel(inner, text="Initializing database & storage...", font=FONT_CAPTION, text_color=COLOR_TEXT_MUTED)
    status_lbl.pack()

    root.update()

    # 3. Initialize Database & Seed Data
    try:
        db_path = get_db_path()
        db = DBManager(db_path)
        progress_bar.set(0.6)
        status_lbl.configure(text="Verifying tracks and habits...")
        root.update()

        populate_seed_data_if_empty(db)
        progress_bar.set(0.9)
        status_lbl.configure(text="Launching workspace...")
        root.update()
    except DatabaseError as dbe:
        InfoModal(root, title="Storage Error", message=str(dbe), is_error=True)
        root.destroy()
        sys.exit(1)
    except Exception as exc:
        InfoModal(root, title="Startup Error", message=f"Unexpected error initializing: {exc}", is_error=True)
        root.destroy()
        sys.exit(1)

    # 4. Transition from Splash to Full Main Workspace
    launch_after_id = None
    splash_closed = False

    def launch_main_ui():
        if splash_closed or not root.winfo_exists():
            return
        splash_frame.destroy()
        root.resizable(True, True)
        AppController(root, db)

    def close_splash():
        nonlocal splash_closed
        splash_closed = True
        if launch_after_id is not None:
            root.after_cancel(launch_after_id)
        db.close()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", close_splash)
    launch_after_id = root.after(600, launch_main_ui)
    root.mainloop()


if __name__ == "__main__":
    run_app()
