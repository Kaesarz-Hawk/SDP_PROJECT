"""Path helper module for Momentum.

Provides correct file paths for both standard Python execution
and PyInstaller frozen standalone .exe environments.
"""

import os
import sys


def get_base_path() -> str:
    """Returns the base directory for read-only bundled assets (works in dev and PyInstaller bundle)."""
    if getattr(sys, "frozen", False):
        # Running as a PyInstaller bundle
        return sys._MEIPASS
    else:
        # Running as normal script: project root is parent of utils/
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_writable_data_path() -> str:
    """Returns a user-writable directory for database and mutable state.

    In frozen mode, writes to %LOCALAPPDATA%/Momentum.
    In dev mode, writes directly inside the project root directory.
    """
    if getattr(sys, "frozen", False):
        app_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Momentum")
    else:
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


def get_db_path() -> str:
    """Returns absolute path to the SQLite database file."""
    return os.path.join(get_writable_data_path(), "momentum.db")


def get_asset_path(relative_path: str) -> str:
    """Returns absolute path to an asset file in the assets folder."""
    return os.path.join(get_base_path(), "assets", relative_path)
