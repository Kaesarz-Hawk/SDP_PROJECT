"""
Momentum — app entry point.

Creates the root window (via App controller), initializes the database,
seeds sample data on first run, shows a brief splash, then runs the Tk mainloop.
"""
from __future__ import annotations

import sys
import os
import traceback

# Ensure the momentum/ project root is importable when launched from anywhere
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    # 1) Path helper — correct in dev AND as a PyInstaller-frozen .exe
    from utils.path_helper import get_db_path

    # 2) Database — creates the file + schema automatically on first run
    from database.db_manager import DBManager, DatabaseError

    # Detect a brand-new database file so we seed exactly once (after
    # "Reset all data", restarting the app must NOT resurrect sample data)
    db_path = get_db_path()
    first_run = not os.path.exists(db_path)

    try:
        db = DBManager(db_path)
    except DatabaseError as exc:
        # Friendly failure only — no raw traceback to the user
        print(f"[Momentum] Could not start: {exc.friendly}")
        print(f"[Momentum] technical: {exc.technical}")
        try:
            from tkinter import messagebox
            messagebox.showerror("Momentum — data error", exc.friendly)
        except Exception:
            pass
        return 1

    # 3) Seed realistic sample data on first run only
    try:
        from utils.seed_data import seed_if_empty, ensure_recent_rollover
        if first_run:
            seeded = seed_if_empty(db, force=True)
            if seeded:
                print("[Momentum] first run — sample data seeded")
        ensure_recent_rollover(db)  # roll overdue pending tasks into today
    except Exception as exc:
        print(f"[Momentum] seed/rollover step failed: {exc}")
        traceback.print_exc()

    # 4) Splash + app shell (frame-switching controller)
    import customtkinter as ctk
    from utils.theme import Colors, ThemeConfig
    from ui.app_controller import App

    ctk.set_appearance_mode(ThemeConfig.mode)
    app = App(db)

    # 5) Mainloop
    try:
        app.mainloop()
    finally:
        # Guarantee the connection is closed even if close-event flow is skipped
        try:
            db.close()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
