"""
Screen 4: To-Do / Tasks.

- Daily task list, default view = today, with date navigation
- Full CRUD: add / edit / delete / mark-complete
- Priority pills (Low/Medium/High colored tags), status, optional track link
- Undone tasks roll over to the next day with a "carried over" badge
- Filter/sort controls: status, priority
"""
from __future__ import annotations

from datetime import date, timedelta

import customtkinter as ctk

try:
    from utils.theme import Colors, Fonts, Spacing
except ImportError:  # pragma: no cover
    from ..utils.theme import Colors, Fonts, Spacing

from .components.modal_dialog import ConfirmModal, FormModal, show_message, show_error

PRIORITY_COLORS = {"Low": Colors.PRI_LOW, "Medium": Colors.PRI_MEDIUM, "High": Colors.PRI_HIGH}


class TodoFrame(ctk.CTkFrame):
    def __init__(self, master, db, app):
        super().__init__(master, fg_color=Colors.BG_BASE, corner_radius=0)
        self.db = db
        self.app = app
        self.view_date: date = date.today()
        self.status_filter = "All"
        self.sort_by = "Priority"

        # ---- Header ----
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=Spacing.XL, pady=(Spacing.LG, Spacing.MD))
        ctk.CTkLabel(head, text="To-Do", font=Fonts.title(),
                     text_color=Colors.TEXT_PRIMARY).pack(side="left")

        # ---- Date navigation ----
        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.pack(fill="x", padx=Spacing.XL, pady=(0, Spacing.SM))
        self.date_lbl = ctk.CTkLabel(nav, text="", font=Fonts.subtitle(),
                                     text_color=Colors.TEXT_PRIMARY, width=280)
        self.date_lbl.pack(side="left")
        ctk.CTkButton(nav, text="◀", width=40, height=30,
                      fg_color=Colors.BG_ELEVATED, hover_color=Colors.BG_HOVER,
                      text_color=Colors.TEXT_PRIMARY,
                      command=lambda: self._shift_day(-1)).pack(side="right", padx=Spacing.XS)
        ctk.CTkButton(nav, text="Today", width=80, height=30,
                      fg_color=Colors.BG_ELEVATED, hover_color=Colors.BG_HOVER,
                      text_color=Colors.TEXT_PRIMARY,
                      command=self._go_today).pack(side="right", padx=Spacing.XS)
        ctk.CTkButton(nav, text="▶", width=40, height=30,
                      fg_color=Colors.BG_ELEVATED, hover_color=Colors.BG_HOVER,
                      text_color=Colors.TEXT_PRIMARY,
                      command=lambda: self._shift_day(1)).pack(side="right", padx=Spacing.XS)

        # ---- Quick add row ----
        add_row = ctk.CTkFrame(self, fg_color=Colors.BG_CARD,
                               corner_radius=Spacing.CARD_RADIUS)
        add_row.pack(fill="x", padx=Spacing.XL, pady=(0, Spacing.SM))
        inner = ctk.CTkFrame(add_row, fg_color="transparent")
        inner.pack(fill="x", padx=Spacing.MD, pady=Spacing.MD)
        self.title_entry = ctk.CTkEntry(
            inner, placeholder_text="Add a task for this day…", height=36,
            fg_color=Colors.BG_INPUT, border_color=Colors.BG_ELEVATED,
            text_color=Colors.TEXT_PRIMARY, font=Fonts.body(),
            corner_radius=Spacing.BUTTON_RADIUS)
        self.title_entry.pack(side="left", fill="x", expand=True, padx=(0, Spacing.SM))
        self.title_entry.bind("<Return>", lambda e: self._add_task())

        self.pri_var = ctk.StringVar(value="Medium")
        ctk.CTkOptionMenu(inner, values=["Low", "Medium", "High"], variable=self.pri_var,
                          width=100, height=36, fg_color=Colors.BG_ELEVATED,
                          button_color=Colors.ACCENT, button_hover_color=Colors.ACCENT_HOVER,
                          dropdown_fg_color=Colors.BG_ELEVATED,
                          font=Fonts.body()).pack(side="left", padx=Spacing.XS)

        self.track_var = ctk.StringVar(value="(none)")
        ctk.CTkOptionMenu(inner, values=["(none)"] + self._track_labels(),
                          variable=self.track_var, width=150, height=36,
                          fg_color=Colors.BG_ELEVATED, button_color=Colors.ACCENT,
                          button_hover_color=Colors.ACCENT_HOVER,
                          dropdown_fg_color=Colors.BG_ELEVATED,
                          font=Fonts.body()).pack(side="left", padx=Spacing.XS)

        ctk.CTkButton(inner, text="＋ Add", width=90, height=36,
                      fg_color=Colors.ACCENT, hover_color=Colors.ACCENT_HOVER,
                      font=Fonts.body_bold(), corner_radius=Spacing.BUTTON_RADIUS,
                      command=self._add_task).pack(side="left", padx=Spacing.XS)

        # ---- Filter / sort row ----
        filters = ctk.CTkFrame(self, fg_color="transparent")
        filters.pack(fill="x", padx=Spacing.XL, pady=(Spacing.XS, 0))
        self.status_seg = ctk.CTkSegmentedButton(
            filters, values=["All", "Pending", "Done"], font=Fonts.small_bold(),
            selected_color=Colors.ACCENT, selected_hover_color=Colors.ACCENT_HOVER,
            unselected_color=Colors.BG_ELEVATED, unselected_hover_color=Colors.BG_HOVER,
            fg_color=Colors.BG_ELEVATED, text_color=Colors.TEXT_SECONDARY,
            command=self._on_status_filter)
        self.status_seg.set("All")
        self.status_seg.pack(side="left")
        ctk.CTkLabel(filters, text="Sort:", font=Fonts.small(),
                     text_color=Colors.TEXT_MUTED).pack(side="left", padx=(Spacing.MD, Spacing.XS))
        ctk.CTkOptionMenu(filters, values=["Priority", "Date", "Title"],
                          variable=ctk.StringVar(value=self.sort_by),
                          width=110, height=28, fg_color=Colors.BG_ELEVATED,
                          button_color=Colors.BG_HOVER,
                          button_hover_color=Colors.BG_INPUT,
                          dropdown_fg_color=Colors.BG_ELEVATED, font=Fonts.small(),
                          command=self._on_sort).pack(side="left")

        # ---- List ----
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=Spacing.XL, pady=(Spacing.MD, Spacing.LG))

    # ------------------------------------------------------------------ #
    def _track_labels(self) -> list[str]:
        return [f"{t.icon} {t.name}" for t in self.db.get_all_tracks()]

    def _track_id_by_label(self, label: str):
        for t in self.db.get_all_tracks():
            if f"{t.icon} {t.name}" == label:
                return t.id
        return None

    def _shift_day(self, delta: int) -> None:
        self.view_date += timedelta(days=delta)
        self.refresh()

    def _go_today(self) -> None:
        self.view_date = date.today()
        self.refresh()

    def _on_status_filter(self, value: str) -> None:
        self.status_filter = value
        self.refresh()

    def _on_sort(self, value: str) -> None:
        self.sort_by = value
        self.refresh()

    # ------------------------------------------------------------------ #
    def refresh(self) -> None:
        try:
            self.track_var.set("(none)")
            try:
                self.status_seg.set(self.status_filter)
            except Exception:
                pass
            iso = self.view_date.isoformat()
            if self.view_date == date.today():
                self.date_lbl.configure(text=f"Today · {self.view_date.strftime('%A, %d %b %Y')}")
            else:
                self.date_lbl.configure(text=self.view_date.strftime("%A, %d %b %Y"))

            # Roll overdue pending tasks into today's view (only when viewing today)
            if self.view_date == date.today():
                self.db.roll_over_incomplete_tasks(
                    (self.view_date - timedelta(days=1)).isoformat(), iso)

            tasks = self.db.get_tasks_for_date(iso)
            if self.status_filter != "All":
                tasks = [t for t in tasks if t.status == self.status_filter]
            if self.sort_by == "Priority":
                tasks.sort(key=lambda t: (t.priority_rank(), t.id or 0))
            elif self.sort_by == "Title":
                tasks.sort(key=lambda t: t.display_title().lower())
            else:
                tasks.sort(key=lambda t: t.due_date)

            for child in self.scroll.winfo_children():
                child.destroy()

            if not tasks:
                self._build_empty()
                return
            for task in tasks:
                self._build_row(task)
        except Exception as exc:
            print(f"[Momentum:Todo] refresh failed: {exc}")
            import traceback
            traceback.print_exc()

    def _build_empty(self) -> None:
        box = ctk.CTkFrame(self.scroll, fg_color="transparent")
        box.pack(fill="both", expand=True, pady=Spacing.XXL)
        if self.view_date == date.today():
            emoji = "🌤"
            title = "All clear for today"
            sub = "Add a task above to plan your day ✍️"
        else:
            emoji = "🗓"
            title = "No tasks on this date"
            sub = "Use the box above to add one."
        ctk.CTkLabel(box, text=emoji, font=(Fonts.FAMILY, 56)).pack(pady=(Spacing.XL, Spacing.XS))
        ctk.CTkLabel(box, text=title, font=Fonts.subtitle(),
                     text_color=Colors.TEXT_PRIMARY).pack()
        ctk.CTkLabel(box, text=sub, font=Fonts.body(),
                     text_color=Colors.TEXT_SECONDARY).pack(pady=(Spacing.XS, 0))

    def _build_row(self, task) -> None:
        row = ctk.CTkFrame(self.scroll, fg_color=Colors.BG_CARD,
                           corner_radius=Spacing.CARD_RADIUS, height=58)
        row.pack(fill="x", pady=Spacing.SM)
        row.pack_propagate(False)

        accent = task.track_color or Colors.BG_ELEVATED

        # Status toggle
        check = ctk.CTkButton(
            row, text="✓" if task.is_done else "○", width=34, height=34,
            corner_radius=17,
            fg_color=Colors.SUCCESS if task.is_done else Colors.BG_ELEVATED,
            hover_color=Colors.SUCCESS_DARK if task.is_done else Colors.BG_HOVER,
            text_color=Colors.TEXT_INVERSE if task.is_done else Colors.TEXT_SECONDARY,
            font=Fonts.body_bold(),
            command=lambda: self._toggle_task(task))
        check.pack(side="left", padx=(Spacing.MD, Spacing.SM))

        # Text block
        text_col = ctk.CTkFrame(row, fg_color="transparent")
        text_col.pack(side="left", fill="both", expand=True, pady=Spacing.SM)
        title_row = ctk.CTkFrame(text_col, fg_color="transparent")
        title_row.pack(fill="x")
        title_lbl = ctk.CTkLabel(
            title_row, text=task.display_title(), font=Fonts.body_bold(),
            text_color=Colors.TEXT_MUTED if task.is_done else Colors.TEXT_PRIMARY,
            anchor="w")
        title_lbl.pack(side="left")
        if task.is_done:
            title_lbl.configure(font=Fonts.body())
        if task.is_carried_over:
            badge = ctk.CTkLabel(title_row, text=" carried over ",
                                 font=(Fonts.FAMILY, 9, "bold"),
                                 text_color=Colors.WARNING,
                                 fg_color=Colors.BG_ELEVATED, corner_radius=6)
            badge.pack(side="left", padx=Spacing.SM)
        if task.linked_track_id and task.track_name:
            chip = ctk.CTkLabel(text_col,
                                text=f"{task.track_name}",
                                font=(Fonts.FAMILY, 9, "bold"), text_color=accent,
                                fg_color=Colors.BG_ELEVATED, corner_radius=6)
            chip.pack(side="left", padx=(0, Spacing.XS), pady=(3, 0))

        # Priority pill
        pill = ctk.CTkLabel(
            row, text=f" {task.priority} ", font=(Fonts.FAMILY, 10, "bold"),
            text_color=PRIORITY_COLORS.get(task.priority, Colors.PRI_MEDIUM),
            fg_color=Colors.BG_ELEVATED, corner_radius=8, width=70)
        pill.pack(side="right", padx=Spacing.XS)

        # Edit / delete
        ctk.CTkButton(row, text="✎", width=32, height=32,
                      fg_color="transparent", hover_color=Colors.BG_ELEVATED,
                      text_color=Colors.TEXT_SECONDARY, font=Fonts.body(),
                      command=lambda: self._edit_task(task)).pack(
            side="right", padx=2, pady=Spacing.SM)
        ctk.CTkButton(row, text="🗑", width=32, height=32,
                      fg_color="transparent", hover_color=Colors.BG_ELEVATED,
                      text_color=Colors.DANGER, font=Fonts.body(),
                      command=lambda: self._delete_task(task)).pack(
            side="right", padx=2, pady=Spacing.SM)

    # ------------------------------------------------------------------ #
    def _toggle_task(self, task) -> None:
        try:
            new_status = "Done" if task.status == "Pending" else "Pending"
            self.db.update_task_status(task.id, new_status)
            self.refresh()
        except Exception as exc:
            show_error(self.winfo_toplevel(), "Could not update task",
                       "Your change didn't stick. Please try again.",
                       technical=str(exc))

    def _add_task(self) -> None:
        try:
            title = self.title_entry.get().strip()
            if not title:
                self.title_entry.configure(border_color=Colors.DANGER)
                self.title_entry.after(
                    1200, lambda: self.title_entry.configure(border_color=Colors.BG_ELEVATED))
                return
            if len(title) > 140:
                show_message(self.winfo_toplevel(), "Title too long",
                             "Task titles are capped at 140 characters.")
                return
            track_id = self._track_id_by_label(self.track_var.get())
            self.db.create_task(title, self.view_date.isoformat(),
                                self.pri_var.get(), track_id)
            self.title_entry.delete(0, "end")
            self.refresh()
        except Exception as exc:
            show_error(self.winfo_toplevel(), "Could not add task",
                       "The task could not be saved.", technical=str(exc))

    def _edit_task(self, task) -> None:
        tracks = self._track_labels()
        fields = [
            {"key": "title", "label": "Title", "type": "entry",
             "initial": task.title, "max_length": 140},
            {"key": "due_date", "label": "Due date", "type": "entry",
             "initial": task.due_date, "placeholder": "YYYY-MM-DD"},
            {"key": "priority", "label": "Priority", "type": "option",
             "options": ["Low", "Medium", "High"], "initial": task.priority},
            {"key": "status", "label": "Status", "type": "option",
             "options": ["Pending", "Done"], "initial": task.status},
            {"key": "track", "label": "Track", "type": "option",
             "options": ["(none)"] + tracks,
             "initial": self._label_for_track(task.linked_track_id)},
        ]

        def validate(values: dict) -> str | None:
            title = (values.get("title") or "").strip()
            if not title:
                return "Task title cannot be empty."
            try:
                date.fromisoformat((values.get("due_date") or "").strip())
            except ValueError:
                return "Due date must be a valid date (YYYY-MM-DD)."
            return None

        def submit(values: dict) -> None:
            try:
                track_id = None
                if values["track"] != "(none)":
                    track_id = self._track_id_by_label(values["track"])
                self.db.update_task(
                    task.id, title=values["title"].strip(),
                    due_date=values["due_date"].strip(),
                    priority=values["priority"], status=values["status"],
                    linked_track_id=track_id)
                self.refresh()
            except Exception as exc:
                show_error(self.winfo_toplevel(), "Could not update task",
                           "The task could not be saved.", technical=str(exc))

        FormModal(self.winfo_toplevel(), "Edit task", fields, submit,
                  validate=validate, submit_text="Save changes")

    def _label_for_track(self, track_id) -> str:
        if not track_id:
            return "(none)"
        t = self.db.get_track(track_id)
        return f"{t.icon} {t.name}" if t else "(none)"

    def _delete_task(self, task) -> None:
        def do_delete():
            try:
                self.db.delete_task(task.id)
                self.refresh()
            except Exception as exc:
                show_error(self.winfo_toplevel(), "Could not delete",
                           "The task could not be removed.", technical=str(exc))

        ConfirmModal(self.winfo_toplevel(), "Delete this task?",
                     f"\"{task.display_title()}\" will be permanently removed.",
                     on_confirm=do_delete, confirm_text="Delete")
