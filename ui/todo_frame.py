"""To-Do & Tasks Screen (Screen 4) for Momentum.

Provides:
- Daily task list with date navigation (previous day, today, next day)
- Full CRUD for tasks: Add, Edit, Delete, Toggle Complete
- Automated rollover of overdue pending tasks to today with "carried over" badges
- Filter controls: Status (All/Pending/Done), Priority (All/High/Medium/Low), Track category
"""

from datetime import date, timedelta
from typing import List, Optional
import customtkinter as ctk

from database.db_manager import DBManager
from models.task import Task
from models.track import Track
from ui.components.modal_dialog import BaseModal, ConfirmModal
from utils.theme import (
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_BG_BASE,
    COLOR_BG_CARD,
    COLOR_BG_INPUT,
    COLOR_BORDER,
    COLOR_DANGER,
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


class TaskFormModal(BaseModal):
    """Modal dialog for creating or editing a task."""

    def __init__(
        self,
        parent,
        tracks: List[Track],
        task: Optional[Task] = None,
        default_date: Optional[str] = None,
        on_save=None,
    ):
        title = "Edit Task" if task else "Create New Task"
        super().__init__(parent, title=title, width=460, height=420)
        self.tracks = tracks
        self.task = task
        self.default_date = default_date or date.today().isoformat()
        self.on_save = on_save

        self._build_form()

    def _build_form(self) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_LG)

        ctk.CTkLabel(
            container,
            text="Task Details",
            font=FONT_SUBTITLE,
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, PAD_MD))

        # Title
        ctk.CTkLabel(container, text="Task Title*", font=FONT_BODY_BOLD, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")
        self.title_entry = ctk.CTkEntry(
            container,
            placeholder_text="e.g. Submit project milestone report",
            fg_color=COLOR_BG_INPUT,
            border_color=COLOR_BORDER,
        )
        self.title_entry.pack(fill="x", pady=(2, PAD_SM))
        if self.task:
            self.title_entry.insert(0, self.task.title)

        # Due Date
        ctk.CTkLabel(container, text="Due Date (YYYY-MM-DD)*", font=FONT_BODY_BOLD, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")
        self.date_entry = ctk.CTkEntry(
            container,
            fg_color=COLOR_BG_INPUT,
            border_color=COLOR_BORDER,
        )
        self.date_entry.insert(0, self.task.due_date if self.task else self.default_date)
        self.date_entry.pack(fill="x", pady=(2, PAD_SM))

        # Priority & Track Row
        opts_row = ctk.CTkFrame(container, fg_color="transparent")
        opts_row.pack(fill="x", pady=(2, PAD_SM))

        # Priority
        pri_col = ctk.CTkFrame(opts_row, fg_color="transparent")
        pri_col.pack(side="left", fill="x", expand=True, padx=(0, PAD_SM))
        ctk.CTkLabel(pri_col, text="Priority", font=FONT_BODY_BOLD, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")
        self.pri_menu = ctk.CTkOptionMenu(
            pri_col,
            values=["High", "Medium", "Low"],
            fg_color=COLOR_BG_INPUT,
            button_color=COLOR_BORDER,
            dropdown_fg_color=COLOR_BG_CARD,
        )
        self.pri_menu.set(self.task.priority if self.task else "Medium")
        self.pri_menu.pack(fill="x", pady=(2, 0))

        # Track Category
        trk_col = ctk.CTkFrame(opts_row, fg_color="transparent")
        trk_col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(trk_col, text="Track (Optional)", font=FONT_BODY_BOLD, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")
        trk_names = ["None"] + [f"{t.icon} {t.name}" for t in self.tracks]
        self.trk_menu = ctk.CTkOptionMenu(
            trk_col,
            values=trk_names,
            fg_color=COLOR_BG_INPUT,
            button_color=COLOR_BORDER,
            dropdown_fg_color=COLOR_BG_CARD,
        )
        cur_track_str = "None"
        if self.task and self.task.linked_track_id:
            for t in self.tracks:
                if t.id == self.task.linked_track_id:
                    cur_track_str = f"{t.icon} {t.name}"
                    break
        self.trk_menu.set(cur_track_str)
        self.trk_menu.pack(fill="x", pady=(2, 0))

        # Error text
        self.error_label = ctk.CTkLabel(container, text="", font=FONT_CAPTION, text_color=COLOR_DANGER)
        self.error_label.pack(anchor="w", pady=(PAD_SM, 0))

        # Buttons
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom")

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            fg_color=COLOR_BG_INPUT,
            hover_color=COLOR_BORDER,
            command=self.destroy,
            width=90,
        ).pack(side="right", padx=(PAD_SM, 0))

        ctk.CTkButton(
            btn_row,
            text="Save Task",
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            command=self._save,
            width=110,
        ).pack(side="right")

    def _save(self) -> None:
        title = self.title_entry.get().strip()
        if not title:
            self.error_label.configure(text="Please provide a task title.")
            return

        due = self.date_entry.get().strip()
        try:
            date.fromisoformat(due)
        except ValueError:
            self.error_label.configure(text="Invalid date format. Use YYYY-MM-DD.")
            return

        priority = self.pri_menu.get()
        track_str = self.trk_menu.get()
        track_id = None
        if track_str != "None":
            for t in self.tracks:
                if f"{t.icon} {t.name}" == track_str:
                    track_id = t.id
                    break

        self.destroy()
        if self.on_save:
            self.on_save(title, due, priority, track_id)


class TodoFrame(ctk.CTkFrame):
    """Daily To-Do screen with filters and automated task rollover."""

    def __init__(self, master, db: DBManager, **kwargs):
        super().__init__(master, fg_color=COLOR_BG_BASE, **kwargs)
        self.db = db

        self.current_date = date.today()
        self.filter_status = "All"
        self.filter_priority = "All"

        # Trigger automatic rollover on load for tasks before today
        self.db.roll_over_incomplete_tasks(to_date=date.today().isoformat())

        self._build_screen()

    def refresh(self) -> None:
        self._build_screen()

    def _build_screen(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()

        tracks = {t.id: t for t in self.db.get_all_tracks()}
        all_tracks_list = self.db.get_all_tracks()
        date_iso = self.current_date.isoformat()
        is_today = (self.current_date == date.today())

        # Top Bar: Date controls & Add Task
        header_bar = ctk.CTkFrame(self, fg_color="transparent")
        header_bar.pack(fill="x", padx=PAD_LG, pady=(PAD_MD, PAD_SM))

        left_header = ctk.CTkFrame(header_bar, fg_color="transparent")
        left_header.pack(side="left")

        ctk.CTkLabel(left_header, text="To-Do & Tasks", font=FONT_TITLE, text_color=COLOR_TEXT_PRIMARY).pack(side="left", padx=(0, PAD_LG))

        # Date Navigator
        nav_box = ctk.CTkFrame(left_header, fg_color=COLOR_BG_CARD, corner_radius=CORNER_SM)
        nav_box.pack(side="left")

        ctk.CTkButton(
            nav_box,
            text="◀",
            width=32,
            height=28,
            fg_color="transparent",
            hover_color=COLOR_BORDER,
            command=self._prev_day,
        ).pack(side="left", padx=2)

        date_display = f"{'Today: ' if is_today else ''}{self.current_date.strftime('%a, %b %d')}"
        ctk.CTkLabel(
            nav_box,
            text=date_display,
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_PRIMARY,
            width=160,
        ).pack(side="left", padx=PAD_SM)

        ctk.CTkButton(
            nav_box,
            text="▶",
            width=32,
            height=28,
            fg_color="transparent",
            hover_color=COLOR_BORDER,
            command=self._next_day,
        ).pack(side="left", padx=2)

        if not is_today:
            ctk.CTkButton(
                left_header,
                text="Jump to Today",
                font=FONT_BODY,
                fg_color=COLOR_BG_CARD,
                hover_color=COLOR_BORDER,
                command=self._jump_today,
                width=110,
            ).pack(side="left", padx=PAD_MD)

        # Add Task Button
        ctk.CTkButton(
            header_bar,
            text="+ Add Task",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            command=lambda: self._show_add_modal(all_tracks_list),
        ).pack(side="right")

        # Filters Bar
        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.pack(fill="x", padx=PAD_LG, pady=(0, PAD_SM))

        # Status filter
        ctk.CTkLabel(filter_bar, text="Status:", font=FONT_CAPTION, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=(0, PAD_XS))
        self.status_seg = ctk.CTkSegmentedButton(
            filter_bar,
            values=["All", "Pending", "Done"],
            command=self._on_status_filter,
            selected_color=COLOR_ACCENT,
            font=FONT_BODY,
        )
        self.status_seg.set(self.filter_status)
        self.status_seg.pack(side="left", padx=(0, PAD_LG))

        # Priority filter
        ctk.CTkLabel(filter_bar, text="Priority:", font=FONT_CAPTION, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=(0, PAD_XS))
        self.pri_seg = ctk.CTkSegmentedButton(
            filter_bar,
            values=["All", "High", "Medium", "Low"],
            command=self._on_pri_filter,
            selected_color=COLOR_ACCENT,
            font=FONT_BODY,
        )
        self.pri_seg.set(self.filter_priority)
        self.pri_seg.pack(side="left")

        # Fetch tasks for currently navigated date
        tasks = self.db.get_tasks_for_date(date_iso)

        # Apply client filters
        filtered_tasks = []
        for t in tasks:
            if self.filter_status != "All" and t.status != self.filter_status:
                continue
            if self.filter_priority != "All" and t.priority != self.filter_priority:
                continue
            filtered_tasks.append(t)

        # Task List Container
        scroll_list = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_list.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_SM)

        if not filtered_tasks:
            self._render_empty_state(scroll_list, len(tasks) == 0)
            return

        for t in filtered_tasks:
            self._render_task_item(scroll_list, t, tracks.get(t.linked_track_id), all_tracks_list)

    def _render_task_item(self, parent, task: Task, track: Optional[Track], all_tracks: List[Track]) -> None:
        card = ctk.CTkFrame(
            parent,
            fg_color=COLOR_BG_CARD,
            corner_radius=CORNER_SM,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        card.pack(fill="x", pady=4)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=PAD_MD, pady=PAD_SM)

        is_done = (task.status == "Done")

        # Checkbox / Toggle
        cb = ctk.CTkCheckBox(
            inner,
            text="",
            width=24,
            checkbox_width=20,
            checkbox_height=20,
            corner_radius=4,
            fg_color=COLOR_SUCCESS,
            border_color=COLOR_BORDER,
            command=lambda tid=task.id, cur=is_done: self._toggle_task(tid, cur),
        )
        if is_done:
            cb.select()
        else:
            cb.deselect()
        cb.pack(side="left", padx=(0, PAD_SM))

        # Title & Rollover Tag
        title_box = ctk.CTkFrame(inner, fg_color="transparent")
        title_box.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            title_box,
            text=task.title,
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_MUTED if is_done else COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(side="left")

        if task.carried_over and not is_done:
            carry_badge = ctk.CTkFrame(title_box, fg_color="#3B2610", corner_radius=4)
            carry_badge.pack(side="left", padx=PAD_SM)
            ctk.CTkLabel(
                carry_badge,
                text="↻ Carried Over",
                font=FONT_CAPTION,
                text_color=COLOR_WARNING,
            ).pack(padx=6, pady=2)

        # Track Category Badge
        if track:
            t_badge = ctk.CTkFrame(inner, fg_color="#20202E", corner_radius=4)
            t_badge.pack(side="left", padx=PAD_SM)
            ctk.CTkLabel(
                t_badge,
                text=f"{track.icon} {track.name}",
                font=FONT_CAPTION,
                text_color=track.color_hex,
            ).pack(padx=6, pady=2)

        # Priority Pill
        pri_col_map = {
            "High": COLOR_DANGER,
            "Medium": COLOR_WARNING,
            "Low": "#3B82F6",
        }
        pri_badge = ctk.CTkFrame(
            inner,
            fg_color=pri_col_map.get(task.priority, COLOR_BORDER),
            corner_radius=4,
        )
        pri_badge.pack(side="left", padx=PAD_SM)
        ctk.CTkLabel(
            pri_badge,
            text=task.priority,
            font=FONT_CAPTION,
            text_color="#FFFFFF" if task.priority != "Medium" else "#000000",
        ).pack(padx=6, pady=2)

        # Actions: Edit & Delete
        actions_frame = ctk.CTkFrame(inner, fg_color="transparent")
        actions_frame.pack(side="right")

        ctk.CTkButton(
            actions_frame,
            text="✏️",
            width=28,
            height=26,
            fg_color="transparent",
            hover_color=COLOR_BORDER,
            command=lambda: self._show_edit_modal(task, all_tracks),
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            actions_frame,
            text="🗑️",
            width=28,
            height=26,
            fg_color="transparent",
            hover_color=COLOR_DANGER,
            command=lambda: self._show_delete_modal(task.id, task.title),
        ).pack(side="left", padx=2)

    def _toggle_task(self, task_id: int, current_status: bool) -> None:
        new_status = "Pending" if current_status else "Done"
        self.db.update_task_status(task_id, new_status)
        self.refresh()

    def _prev_day(self) -> None:
        self.current_date -= timedelta(days=1)
        self.refresh()

    def _next_day(self) -> None:
        self.current_date += timedelta(days=1)
        self.refresh()

    def _jump_today(self) -> None:
        self.current_date = date.today()
        self.refresh()

    def _on_status_filter(self, val: str) -> None:
        self.filter_status = val
        self.refresh()

    def _on_pri_filter(self, val: str) -> None:
        self.filter_priority = val
        self.refresh()

    def _show_add_modal(self, tracks: List[Track]) -> None:
        def handle_save(title, due, pri, trk_id):
            self.db.create_task(title=title, due_date=due, priority=pri, linked_track_id=trk_id)
            self.refresh()

        TaskFormModal(
            self,
            tracks=tracks,
            default_date=self.current_date.isoformat(),
            on_save=handle_save,
        )

    def _show_edit_modal(self, task: Task, tracks: List[Track]) -> None:
        def handle_save(title, due, pri, trk_id):
            self.db.update_task(task.id, title=title, due_date=due, priority=pri, linked_track_id=trk_id)
            self.refresh()

        TaskFormModal(self, tracks=tracks, task=task, on_save=handle_save)

    def _show_delete_modal(self, task_id: int, task_title: str) -> None:
        def handle_delete():
            self.db.delete_task(task_id)
            self.refresh()

        ConfirmModal(
            self,
            title="Delete Task",
            message=f"Are you sure you want to delete '{task_title}'?",
            confirm_text="Delete",
            is_danger=True,
            on_confirm=handle_delete,
        )

    def _render_empty_state(self, parent, truly_empty: bool) -> None:
        empty = ctk.CTkFrame(parent, fg_color=COLOR_BG_CARD, corner_radius=CORNER_MD)
        empty.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_LG)

        inner = ctk.CTkFrame(empty, fg_color="transparent")
        inner.pack(expand=True, pady=PAD_LG)

        icon = "🎉" if truly_empty else "🔍"
        title = "All Clear!" if truly_empty else "No Tasks Matching Filter"
        subtitle = "No tasks scheduled for this day." if truly_empty else "Try adjusting your status or priority filter."

        ctk.CTkLabel(inner, text=icon, font=("Segoe UI", 42)).pack(pady=(0, PAD_SM))
        ctk.CTkLabel(inner, text=title, font=FONT_TITLE, text_color=COLOR_TEXT_PRIMARY).pack(pady=(0, PAD_XS))
        ctk.CTkLabel(inner, text=subtitle, font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY).pack(pady=(0, PAD_MD))
