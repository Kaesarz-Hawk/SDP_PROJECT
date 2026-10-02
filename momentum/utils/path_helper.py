"""
Path resolution for Momentum — critical for PyInstaller frozen builds.

Bundled read-only assets live under sys._MEIPASS when frozen.
Writable data (the SQLite DB) must NEVER be written into the bundle.
"""
from __future__ import annotations

import os
import sys


def get_base_path() -> str:
    """
    Returns the base path for bundled read-only assets.
    Works both in dev mode (project root) and frozen .exe mode (temp extract dir).
    """
    if getattr(sys, "frozen", False):
        # Running as a PyInstaller bundle — temp extraction directory
        return sys._MEIPASS  # type: ignore[attr-defined]
    # Dev mode: project root (parent of utils/)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_writable_data_path() -> str:
    """
    Returns a writable location for the database file.
    Never write the database inside the bundled/frozen read-only location.
    """
    if getattr(sys, "frozen", False):
        # User-writable AppData folder next to the user profile
        app_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Momentum")
    else:
        # Dev mode: project root
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


def get_db_path() -> str:
    """Absolute path to the Momentum SQLite database file."""
    return os.path.join(get_writable_data_path(), "momentum.db")


def get_asset_path(relative_path: str) -> str:
    """Absolute path to a bundled asset (icon, images, fonts)."""
    return os.path.join(get_base_path(), "assets", relative_path)


def get_log_path() -> str:
    """Optional internal log file location (writable)."""
    return os.path.join(get_writable_data_path(), "momentum.log")
