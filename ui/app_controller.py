"""App Controller and Main Window manager for Momentum.

Owns:
- Root CTk window and global styling
- Persistent Sidebar navigation
- Centralized frame-switching controller pattern
- Shared DBManager instance
- Graceful shutdown lifecycle closing SQLite connection
"""

import os
import customtkinter as ctk

from database.db_manager import DBManager
from ui.analytics_frame import AnalyticsFrame
from ui.calendar_frame import CalendarFrame
from ui.dashboard_frame import DashboardFrame
from ui.habit_tracker_frame import HabitTrackerFrame
from ui.onboarding_frame import OnboardingFrame
from ui.settings_frame import SettingsFrame
from ui.sidebar import Sidebar
from ui.todo_frame import TodoFrame
from utils.path_helper import get_asset_path
from utils.theme import (
    APP_NAME,
    COLOR_BG_BASE,
    WINDOW_DEFAULT_HEIGHT,
    WINDOW_DEFAULT_WIDTH,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
)


class AppController:
    """Central controller coordinating navigation and views."""

    def __init__(self, root: ctk.CTk, db: DBManager):
        self.root = root
        self.db = db
        self._is_closing = False
        self._is_navigating = False

        # Configure root window
        self.root.title(APP_NAME)
        self.root.geometry(f"{WINDOW_DEFAULT_WIDTH}x{WINDOW_DEFAULT_HEIGHT}")
        self.root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.root.configure(fg_color=COLOR_BG_BASE)

        # Set custom window icon if available
        icon_path = get_asset_path("icon.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

        # Protocol for clean exit
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Main Layout: Sidebar on Left, Content Area on Right
        self.sidebar = Sidebar(self.root, on_navigate=self.show_frame)
        self.sidebar.pack(side="left", fill="y")

        self.content_area = ctk.CTkFrame(self.root, fg_color=COLOR_BG_BASE, corner_radius=0)
        self.content_area.pack(side="right", fill="both", expand=True)

        # Instantiate all frames with shared DBManager
        self.frames = {
            "dashboard": DashboardFrame(
                self.content_area,
                db=self.db,
                on_navigate_to_onboarding=lambda: self.show_frame("plan_builder"),
            ),
            "habit_tracker": HabitTrackerFrame(self.content_area, db=self.db),
            "calendar": CalendarFrame(self.content_area, db=self.db),
            "todo": TodoFrame(self.content_area, db=self.db),
            "analytics": AnalyticsFrame(self.content_area, db=self.db),
            "plan_builder": OnboardingFrame(
                self.content_area,
                db=self.db,
                on_plan_created=lambda: self.show_frame("dashboard"),
            ),
            "settings": SettingsFrame(
                self.content_area,
                db=self.db,
                on_data_reset=self._handle_global_reset,
            ),
        }

        # Pack frames into content area (stacked)
        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        # Start on dashboard
        self.active_frame_name = "dashboard"
        self.show_frame("dashboard")

    def show_frame(self, name: str) -> None:
        """Raises and refreshes the chosen frame."""
        if name in self.frames and not self._is_closing and not self._is_navigating:
            self._is_navigating = True
            target_frame = self.frames[name]
            try:
                if hasattr(target_frame, "refresh"):
                    target_frame.refresh()
                target_frame.tkraise()
                self.active_frame_name = name
                self.sidebar.set_active(name)
            finally:
                self._is_navigating = False

    def _handle_global_reset(self) -> None:
        """Called when data is wiped in settings to refresh all frames."""
        for frame in self.frames.values():
            if hasattr(frame, "refresh"):
                frame.refresh()
        self.show_frame("dashboard")

    def _on_close(self) -> None:
        """Ensures database connection is cleanly closed upon application exit."""
        if self._is_closing:
            return
        self._is_closing = True
        if self.db:
            self.db.close()
        self.root.destroy()
