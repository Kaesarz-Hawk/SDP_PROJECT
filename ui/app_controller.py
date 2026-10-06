"""
App — the main application controller (owns the single root window).

Responsibilities:
- create shared DBManager reference (passed in, never re-instantiated per screen)
- build sidebar + one instance of each frame, switch visibility (pack/forget + refresh)
- startup splash ("Loading your data...")
- theme switching (rebuild frames with the new palette)
- custom title/icon, minimum window size, clean DB close on exit
"""
from __future__ import annotations

import os
import tkinter as tk
from typing import Optional

import customtkinter as ctk

try:
    from utils.theme import Colors, Fonts, Spacing, set_theme_mode, ThemeConfig
    from utils.path_helper import get_asset_path
except ImportError:  # pragma: no cover
    from ..utils.theme import Colors, Fonts, Spacing, set_theme_mode, ThemeConfig
    from ..utils.path_helper import get_asset_path

from .sidebar import Sidebar, NAV_ITEMS

APP_NAME = "Momentum"
APP_VERSION = "1.0.0"

# Screen keys in sidebar order
FRAME_KEYS = [item[0] for item in NAV_ITEMS]


class App(ctk.CTk):
    """Central controller: one root, sidebar, stacked screens, frame switching."""

    def __init__(self, db, splash_ms: int = 700):
        super().__init__()
        self.db = db
        self.current_key: Optional[str] = None
        self.frames: dict[str, ctk.CTkFrame] = {}
        self.sidebar: Optional[Sidebar] = None
        self.content: Optional[ctk.CTkFrame] = None

        # --- window chrome ------------------------------------------------
        self.title(APP_NAME)
        self.configure(fg_color=Colors.BG_BASE)
        self.minsize(Spacing.MIN_WINDOW_W, Spacing.MIN_WINDOW_H)
        self._apply_window_icon()

        ctk.set_appearance_mode(ThemeConfig.mode)

        # --- splash --------------------------------------------------------
        self._splash = self._build_splash()

        # Defer heavy UI build so "Loading your data..." is actually visible.
        # Track after-jobs so they can be cancelled when the splash is destroyed.
        self._splash_jobs = []
        self._splash_jobs.append(self.after(300, lambda: self._splash_bar(0.85)))
        self._splash_jobs.append(self.after(splash_ms, self._build_ui))

        # Clean DB close on X button / quit
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _splash_bar(self, value: float) -> None:
        """Advance splash progress only if the splash still exists (no stale callbacks)."""
        try:
            if self._splash is not None and self._splash.winfo_exists():
                for child in self._splash.winfo_children():
                    if isinstance(child, ctk.CTkProgressBar):
                        child.set(value)
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    def _apply_window_icon(self) -> None:
        """Custom window icon (never the default Tk feather)."""
        icon_path = get_asset_path("icon.ico")
        try:
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as exc:
            # icon failures are cosmetic — never crash over them
            print(f"[Momentum] window icon not applied: {exc}")

    def _build_splash(self) -> ctk.CTkFrame:
        splash = ctk.CTkFrame(self, fg_color=Colors.BG_BASE, corner_radius=0)
        splash.pack(fill="both", expand=True)
        ctk.CTkLabel(splash, text="🎯", font=(Fonts.FAMILY, 64),
                     text_color=Colors.ACCENT).pack(pady=(Spacing.XXL, Spacing.SM))
        ctk.CTkLabel(splash, text=APP_NAME, font=(Fonts.FAMILY, 34, "bold"),
                     text_color=Colors.TEXT_PRIMARY).pack()
        ctk.CTkLabel(splash, text="Loading your data...",
                     font=Fonts.body(), text_color=Colors.TEXT_SECONDARY).pack(pady=(Spacing.SM, Spacing.MD))
        try:
            bar = ctk.CTkProgressBar(splash, width=220, fg_color=Colors.BG_ELEVATED,
                                     progress_color=Colors.ACCENT)
            bar.pack()
            bar.set(0.35)
        except Exception:
            pass
        self.update()
        return splash

    def _build_ui(self) -> None:
        """Create sidebar + all screens after the splash."""
        for job in getattr(self, "_splash_jobs", []):
            try:
                self.after_cancel(job)
            except Exception:
                pass
        self._splash_jobs = []
        try:
            self._splash.destroy()
        except Exception:
            pass
        self._splash = None

        self.sidebar = Sidebar(self, on_navigate=self.show_frame)
        self.sidebar.grid(row=0, column=0, sticky="nsw")

        self.content = ctk.CTkFrame(self, fg_color=Colors.BG_BASE, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._create_frames()
        self.show_frame("dashboard")

    def _create_frames(self) -> None:
        """Instantiate every screen once. Screens receive the shared db instance."""
        from .dashboard_frame import DashboardFrame
        from .habit_tracker_frame import HabitTrackerFrame
        from .todo_frame import TodoFrame
        from .calendar_frame import CalendarFrame
        from .analytics_frame import AnalyticsFrame
        from .onboarding_frame import OnboardingFrame
        from .settings_frame import SettingsFrame

        factories = {
            "dashboard": DashboardFrame,
            "habits": HabitTrackerFrame,
            "todo": TodoFrame,
            "calendar": CalendarFrame,
            "analytics": AnalyticsFrame,
            "onboarding": OnboardingFrame,
            "settings": SettingsFrame,
        }
        for key, cls in factories.items():
            try:
                frame = cls(self.content, self.db, self)
                frame.place(relx=0, rely=0, relwidth=1, relheight=1)
                frame.lower()
                self.frames[key] = frame
            except Exception as exc:
                print(f"[Momentum] failed to build screen '{key}': {exc}")
                import traceback
                traceback.print_exc()  # console only — never shown in UI
                self.frames[key] = self._error_frame(key, exc)

    def _error_frame(self, key: str, exc: Exception) -> ctk.CTkFrame:
        """Fallback screen if a frame fails to build (never a blank window)."""
        frame = ctk.CTkFrame(self.content, fg_color=Colors.BG_BASE, corner_radius=0)
        frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        ctk.CTkLabel(frame, text="😅", font=(Fonts.FAMILY, 56)).pack(pady=(Spacing.XXL, Spacing.SM))
        ctk.CTkLabel(frame, text=f"Couldn't load {key}",
                     font=Fonts.subtitle(), text_color=Colors.TEXT_PRIMARY).pack()
        ctk.CTkLabel(frame, text="Something went wrong while preparing this screen.\nThe rest of the app still works.",
                     font=Fonts.body(), text_color=Colors.TEXT_SECONDARY).pack(pady=Spacing.SM)
        print(f"[Momentum] frame '{key}' fallback: {exc}")
        return frame

    # ------------------------------------------------------------------ #
    def show_frame(self, key: str) -> None:
        """Switch the visible screen (single content area)."""
        if key not in self.frames:
            print(f"[Momentum] unknown frame: {key}")
            return
        frame = self.frames[key]
        try:
            # Refresh data on every visit so screens are never stale
            refresh = getattr(frame, "refresh", None)
            if callable(refresh):
                refresh()
        except Exception as exc:
            print(f"[Momentum] refresh failed for '{key}': {exc}")
        frame.lift()
        self.current_key = key
        if self.sidebar and self.sidebar.active_key != key:
            self.sidebar.set_active(key)

    def refresh_current(self) -> None:
        """Called by screens after data mutations to repaint the visible frame."""
        if self.current_key:
            frame = self.frames.get(self.current_key)
            refresh = getattr(frame, "refresh", None)
            if callable(refresh):
                try:
                    refresh()
                except Exception as exc:
                    print(f"[Momentum] refresh_current failed: {exc}")

    def refresh_all(self) -> None:
        """Re-run refresh on every built frame (used after theme change)."""
        for key, frame in self.frames.items():
            refresh = getattr(frame, "refresh", None)
            if callable(refresh):
                try:
                    refresh()
                except Exception as exc:
                    print(f"[Momentum] refresh_all '{key}' failed: {exc}")

    # ------------------------------------------------------------------ #
    def set_theme(self, mode: str) -> None:
        """
        Switch dark/light: update palette + rebuild every screen.

        NOTE: customtkinter's Windows titlebar-color flow withdraws the root and
        schedules `after(1, previously_focused_widget.focus)`. If we destroyed the
        frames synchronously, that callback would hit a dead widget (TclError in
        console). Deferring the rebuild ~100ms lets those callbacks fire first
        while all widgets still exist.
        """
        if mode not in ("dark", "light"):
            mode = "dark"
        set_theme_mode(mode)
        ctk.set_appearance_mode(mode)
        self._pending_theme = mode
        if getattr(self, "_theme_job", None):
            try:
                self.after_cancel(self._theme_job)
            except Exception:
                pass
        self._theme_job = self.after(100, self._do_rebuild)

    def _do_rebuild(self) -> None:
        self._theme_job = None
        mode = getattr(self, "_pending_theme", "dark")
        self.configure(fg_color=Colors.BG_BASE)
        # Rebuild whole UI so all colors created at widget-construction re-apply
        for frame in list(self.frames.values()):
            try:
                frame.destroy()
            except Exception:
                pass
        self.frames.clear()
        if self.sidebar:
            self.sidebar.destroy()
            self.sidebar = None
        if self.content:
            self.content.destroy()
            self.content = None
        self.sidebar = Sidebar(self, on_navigate=self.show_frame)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.content = ctk.CTkFrame(self, fg_color=Colors.BG_BASE, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self._create_frames()
        self.show_frame("settings")

    # ------------------------------------------------------------------ #
    def on_close(self) -> None:
        """Window X — close SQLite cleanly to avoid lock files/corruption."""
        try:
            self.db.close()
        except Exception as exc:
            print(f"[Momentum] DB close on exit failed: {exc}")
        try:
            self.destroy()
        except Exception:
            pass
