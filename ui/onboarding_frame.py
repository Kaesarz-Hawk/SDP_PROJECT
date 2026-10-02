"""Onboarding / Plan Builder Screen (Screen 1) for Momentum.

Provides a 4-step wizard to decompose long-term goals into trackable categories and habits:
- Step 1: Name the Track, pick category, custom color, and emoji icon
- Step 2: Add individual habits/skills under the track
- Step 3: Set timeframe (e.g. 3 months) & target frequency with auto-calculated targets
- Step 4: Review summary and confirm creation into database
Also displays currently active goal plans.
"""

from datetime import date, timedelta
from typing import Callable, List, Optional
import customtkinter as ctk

from database.db_manager import DBManager
from models.plan import Plan
from models.track import Track
from ui.components.modal_dialog import ConfirmModal, InfoModal
from utils.theme import (
    CATEGORY_COLORS,
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
    CORNER_MD,
    CORNER_SM,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_CAPTION,
    FONT_DISPLAY_LARGE,
    FONT_SECTION_HEADER,
    FONT_SUBTITLE,
    FONT_TITLE,
    PAD_LG,
    PAD_MD,
    PAD_SM,
    PAD_XS,
    TRACK_ICONS,
    TRACK_PALETTE,
)


class OnboardingFrame(ctk.CTkFrame):
    """Wizard flow for goal decomposition and track building."""

    def __init__(self, master, db: DBManager, on_plan_created: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(master, fg_color=COLOR_BG_BASE, **kwargs)
        self.db = db
        self.on_plan_created = on_plan_created

        # Wizard state
        self.current_step = 1
        self.track_name = ""
        self.track_category = "Productivity"
        self.track_color = TRACK_PALETTE[2]  # Amber default
        self.track_icon = "💻"
        self.habits_list: List[str] = []
        self.duration_months = 3
        self.target_frequency = 5
        self.plan_notes = ""

        self._build_screen()

    def refresh(self) -> None:
        self._build_screen()

    def _reset_wizard(self) -> None:
        self.current_step = 1
        self.track_name = ""
        self.track_category = "Productivity"
        self.track_color = TRACK_PALETTE[2]
        self.track_icon = "💻"
        self.habits_list = []
        self.duration_months = 3
        self.target_frequency = 5
        self.plan_notes = ""
        self._build_screen()

    def _build_screen(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()

        # Header Bar
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=PAD_LG, pady=(PAD_MD, PAD_SM))

        ctk.CTkLabel(header, text="Goal Decomposition & Plan Builder", font=FONT_TITLE, text_color=COLOR_TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(header, text="Turn high-level ambitions into daily trackable momentum", font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY).pack(side="left", padx=PAD_MD)

        # Main scrollable canvas
        scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_container.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_SM)

        # Wizard Stepper Progress Bar
        stepper_card = ctk.CTkFrame(scroll_container, fg_color=COLOR_BG_CARD, corner_radius=CORNER_MD, border_width=1, border_color=COLOR_BORDER)
        stepper_card.pack(fill="x", pady=(0, PAD_MD))

        steps = [
            (1, "1. Track Category"),
            (2, "2. Habits & Skills"),
            (3, "3. Goal Timeframe"),
            (4, "4. Review & Confirm"),
        ]

        step_bar = ctk.CTkFrame(stepper_card, fg_color="transparent")
        step_bar.pack(fill="x", padx=PAD_LG, pady=PAD_MD)

        for step_num, step_title in steps:
            is_active = (step_num == self.current_step)
            is_done = (step_num < self.current_step)

            step_box = ctk.CTkFrame(step_bar, fg_color="transparent")
            step_box.pack(side="left", expand=True)

            color = COLOR_ACCENT if is_active else (COLOR_SUCCESS if is_done else COLOR_TEXT_MUTED)
            indicator = "✓" if is_done else str(step_num)

            ctk.CTkLabel(
                step_box,
                text=f"[{indicator}] {step_title}",
                font=FONT_BODY_BOLD,
                text_color=color,
            ).pack()

        # Step Content Container
        self.step_content_frame = ctk.CTkFrame(
            scroll_container,
            fg_color=COLOR_BG_CARD,
            corner_radius=CORNER_MD,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.step_content_frame.pack(fill="both", expand=True, pady=(0, PAD_MD))

        if self.current_step == 1:
            self._render_step_1()
        elif self.current_step == 2:
            self._render_step_2()
        elif self.current_step == 3:
            self._render_step_3()
        elif self.current_step == 4:
            self._render_step_4()

        # Existing Plans Section Below
        self._render_existing_plans_section(scroll_container)

    # -------------------------------------------------------------
    # Step 1: Name the Track
    # -------------------------------------------------------------
    def _render_step_1(self) -> None:
        container = ctk.CTkFrame(self.step_content_frame, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_LG)

        ctk.CTkLabel(container, text="Step 1 — Define Your Track Category", font=FONT_SUBTITLE, text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(container, text="Choose a broad life area to organize your consistency goals.", font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w", pady=(0, PAD_MD))

        # Track Name
        ctk.CTkLabel(container, text="Track Name*", font=FONT_BODY_BOLD, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")
        self.name_input = ctk.CTkEntry(
            container,
            placeholder_text="e.g. 3 Months of Productivity, Full-Stack Mastery, Marathon Prep",
            fg_color=COLOR_BG_INPUT,
            border_color=COLOR_BORDER,
        )
        if self.track_name:
            self.name_input.insert(0, self.track_name)
        self.name_input.pack(fill="x", pady=(2, PAD_MD))

        # Category Preset
        ctk.CTkLabel(container, text="Category Category Family", font=FONT_BODY_BOLD, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")
        cat_options = ["Productivity", "Academics", "Fitness", "Reading", "Health", "Personal"]
        self.cat_menu = ctk.CTkOptionMenu(
            container,
            values=cat_options,
            command=self._on_category_select,
            fg_color=COLOR_BG_INPUT,
            button_color=COLOR_ACCENT,
            dropdown_fg_color=COLOR_BG_CARD,
        )
        self.cat_menu.set(self.track_category)
        self.cat_menu.pack(anchor="w", pady=(2, PAD_MD))

        # Color Palette Picker
        ctk.CTkLabel(container, text="Color Accent Stripe", font=FONT_BODY_BOLD, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")
        palette_frame = ctk.CTkFrame(container, fg_color="transparent")
        palette_frame.pack(anchor="w", pady=(4, PAD_MD))

        self.color_buttons = []
        for col_hex in TRACK_PALETTE:
            is_cur = (col_hex == self.track_color)
            btn = ctk.CTkButton(
                palette_frame,
                text="✓" if is_cur else "",
                width=34,
                height=34,
                corner_radius=17,
                fg_color=col_hex,
                hover_color=col_hex,
                border_width=2 if is_cur else 0,
                border_color="#FFFFFF",
                command=lambda c=col_hex: self._select_color(c),
            )
            btn.pack(side="left", padx=4)
            self.color_buttons.append((col_hex, btn))

        # Icon Picker
        ctk.CTkLabel(container, text="Track Icon", font=FONT_BODY_BOLD, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")
        icon_frame = ctk.CTkFrame(container, fg_color="transparent")
        icon_frame.pack(anchor="w", pady=(4, PAD_MD))

        self.icon_buttons = []
        for ico in TRACK_ICONS:
            is_cur = (ico == self.track_icon)
            btn = ctk.CTkButton(
                icon_frame,
                text=ico,
                width=36,
                height=36,
                corner_radius=8,
                fg_color=COLOR_ACCENT if is_cur else COLOR_BG_INPUT,
                hover_color=COLOR_BORDER,
                font=("Segoe UI", 16),
                command=lambda ic=ico: self._select_icon(ic),
            )
            btn.pack(side="left", padx=3)
            self.icon_buttons.append((ico, btn))

        self.step1_error = ctk.CTkLabel(container, text="", font=FONT_CAPTION, text_color=COLOR_DANGER)
        self.step1_error.pack(anchor="w", pady=(PAD_SM, 0))

        # Next Button
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom", pady=(PAD_MD, 0))

        ctk.CTkButton(
            btn_row,
            text="Next: Add Habits ➔",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            command=self._submit_step_1,
            width=160,
        ).pack(side="right")

    def _on_category_select(self, val: str) -> None:
        self.track_category = val
        if val in CATEGORY_COLORS:
            self._select_color(CATEGORY_COLORS[val])

    def _select_color(self, hex_val: str) -> None:
        self.track_color = hex_val
        for c, btn in self.color_buttons:
            if c == hex_val:
                btn.configure(text="✓", border_width=2)
            else:
                btn.configure(text="", border_width=0)

    def _select_icon(self, ico: str) -> None:
        self.track_icon = ico
        for ic, btn in self.icon_buttons:
            btn.configure(fg_color=COLOR_ACCENT if ic == ico else COLOR_BG_INPUT)

    def _submit_step_1(self) -> None:
        name = self.name_input.get().strip()
        if not name:
            self.step1_error.configure(text="Please give this track a name.")
            return
        self.track_name = name
        self.current_step = 2
        self._build_screen()

    # -------------------------------------------------------------
    # Step 2: Add Habits / Skills
    # -------------------------------------------------------------
    def _render_step_2(self) -> None:
        container = ctk.CTkFrame(self.step_content_frame, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_LG)

        ctk.CTkLabel(container, text="Step 2 — Add Habits & Sub-Skills", font=FONT_SUBTITLE, text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(
            container,
            text=f"List individual trackable items under '{self.track_name}' (e.g. CP, SQL, React, JS, Java, MongoDB).",
            font=FONT_BODY,
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(anchor="w", pady=(0, PAD_MD))

        # Add habit input row
        add_row = ctk.CTkFrame(container, fg_color="transparent")
        add_row.pack(fill="x", pady=(0, PAD_SM))

        self.habit_entry = ctk.CTkEntry(
            add_row,
            placeholder_text="Enter habit or skill name...",
            fg_color=COLOR_BG_INPUT,
            border_color=COLOR_BORDER,
        )
        self.habit_entry.pack(side="left", fill="x", expand=True, padx=(0, PAD_SM))
        self.habit_entry.bind("<Return>", lambda e: self._add_habit_item())

        ctk.CTkButton(
            add_row,
            text="+ Add Item",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_ACCENT,
            command=self._add_habit_item,
            width=100,
        ).pack(side="left")

        # Quick preset pills
        presets_row = ctk.CTkFrame(container, fg_color="transparent")
        presets_row.pack(fill="x", pady=(0, PAD_MD))

        ctk.CTkLabel(presets_row, text="Quick suggestions:", font=FONT_CAPTION, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=(0, PAD_SM))
        suggestions = ["Competitive Programming", "SQL Database Queries", "React Components", "Data Structures", "Daily 5km Run", "Read 20 Pages"]
        for sug in suggestions:
            ctk.CTkButton(
                presets_row,
                text=f"+ {sug}",
                font=FONT_CAPTION,
                fg_color=COLOR_BG_INPUT,
                hover_color=COLOR_BORDER,
                height=22,
                command=lambda s=sug: self._add_habit_string(s),
            ).pack(side="left", padx=2)

        # Habit list display
        self.habits_box = ctk.CTkScrollableFrame(container, height=180, fg_color="#181822", corner_radius=CORNER_SM)
        self.habits_box.pack(fill="both", expand=True, pady=(0, PAD_MD))
        self._refresh_habit_tags()

        self.step2_error = ctk.CTkLabel(container, text="", font=FONT_CAPTION, text_color=COLOR_DANGER)
        self.step2_error.pack(anchor="w", pady=(0, PAD_SM))

        # Stepper Navigation Buttons
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom")

        ctk.CTkButton(
            btn_row,
            text="◀ Back",
            fg_color=COLOR_BG_INPUT,
            hover_color=COLOR_BORDER,
            command=self._back_step,
            width=90,
        ).pack(side="left")

        ctk.CTkButton(
            btn_row,
            text="Next: Timeframe & Goal ➔",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            command=self._submit_step_2,
            width=200,
        ).pack(side="right")

    def _add_habit_item(self) -> None:
        name = self.habit_entry.get().strip()
        if name:
            self._add_habit_string(name)
            self.habit_entry.delete(0, "end")

    def _add_habit_string(self, text: str) -> None:
        if text not in self.habits_list:
            self.habits_list.append(text)
            self._refresh_habit_tags()

    def _remove_habit_string(self, text: str) -> None:
        if text in self.habits_list:
            self.habits_list.remove(text)
            self._refresh_habit_tags()

    def _refresh_habit_tags(self) -> None:
        for w in self.habits_box.winfo_children():
            w.destroy()

        if not self.habits_list:
            ctk.CTkLabel(
                self.habits_box,
                text="No habits added yet. Type a skill or habit above and click Add.",
                font=FONT_BODY,
                text_color=COLOR_TEXT_MUTED,
            ).pack(expand=True, pady=PAD_LG)
            return

        for idx, h in enumerate(self.habits_list, 1):
            row = ctk.CTkFrame(self.habits_box, fg_color=COLOR_BG_CARD, corner_radius=6)
            row.pack(fill="x", pady=2, padx=PAD_XS)

            ctk.CTkLabel(row, text=f"{idx}. {self.track_icon} {h}", font=FONT_BODY_BOLD, text_color=COLOR_TEXT_PRIMARY).pack(side="left", padx=PAD_SM, pady=4)
            ctk.CTkButton(
                row,
                text="✕",
                width=24,
                height=22,
                fg_color="transparent",
                hover_color=COLOR_DANGER,
                text_color=COLOR_TEXT_MUTED,
                command=lambda s=h: self._remove_habit_string(s),
            ).pack(side="right", padx=PAD_SM)

    def _submit_step_2(self) -> None:
        if not self.habits_list:
            self.step2_error.configure(text="Please add at least one habit or skill under this track.")
            return
        self.current_step = 3
        self._build_screen()

    # -------------------------------------------------------------
    # Step 3: Timeframe & Goal Frequency
    # -------------------------------------------------------------
    def _render_step_3(self) -> None:
        container = ctk.CTkFrame(self.step_content_frame, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_LG)

        ctk.CTkLabel(container, text="Step 3 — Set Timeframe & Target Frequency", font=FONT_SUBTITLE, text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(container, text="The goal decomposition engine calculates weekly and total check-in targets.", font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w", pady=(0, PAD_MD))

        # Timeframe Selector
        ctk.CTkLabel(container, text="Target Duration", font=FONT_BODY_BOLD, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")
        dur_frame = ctk.CTkFrame(container, fg_color="transparent")
        dur_frame.pack(anchor="w", pady=(2, PAD_MD))

        durations = [(1, "1 Month (4 wks)"), (3, "3 Months (13 wks)"), (6, "6 Months (26 wks)"), (12, "1 Year (52 wks)")]
        for m_count, m_label in durations:
            is_cur = (m_count == self.duration_months)
            ctk.CTkButton(
                dur_frame,
                text=m_label,
                font=FONT_BODY,
                fg_color=COLOR_ACCENT if is_cur else COLOR_BG_INPUT,
                hover_color=COLOR_BORDER,
                command=lambda mc=m_count: self._set_duration(mc),
            ).pack(side="left", padx=4)

        # Target Frequency Selector
        ctk.CTkLabel(container, text="Target Frequency (Days Per Week)", font=FONT_BODY_BOLD, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")
        freq_frame = ctk.CTkFrame(container, fg_color="transparent")
        freq_frame.pack(anchor="w", pady=(2, PAD_MD))

        for f in [3, 4, 5, 6, 7]:
            is_cur = (f == self.target_frequency)
            ctk.CTkButton(
                freq_frame,
                text=f"{f}x / week",
                font=FONT_BODY,
                fg_color=COLOR_ACCENT if is_cur else COLOR_BG_INPUT,
                hover_color=COLOR_BORDER,
                width=80,
                command=lambda fr=f: self._set_frequency(fr),
            ).pack(side="left", padx=3)

        # Decomposed Calculation Banner
        total_weeks = int(self.duration_months * 4.33)
        total_targets = total_weeks * self.target_frequency

        calc_card = ctk.CTkFrame(container, fg_color="#181822", corner_radius=CORNER_SM, border_width=1, border_color=COLOR_BORDER)
        calc_card.pack(fill="x", pady=PAD_MD)

        calc_inner = ctk.CTkFrame(calc_card, fg_color="transparent")
        calc_inner.pack(fill="x", padx=PAD_MD, pady=PAD_MD)

        ctk.CTkLabel(calc_inner, text="⚡ Auto-Calculated Goal Plan Target:", font=FONT_BODY_BOLD, text_color=COLOR_SUCCESS).pack(anchor="w", pady=(0, 4))
        calc_text = (
            f"• Duration: {self.duration_months} Months ({total_weeks} weeks)\n"
            f"• Target Cadence: {self.target_frequency} days/week per habit\n"
            f"• Total Target Check-ins: ~{total_targets} completions per habit over the plan duration"
        )
        ctk.CTkLabel(calc_inner, text=calc_text, font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY, justify="left").pack(anchor="w")

        # Plan Notes
        ctk.CTkLabel(container, text="Plan Focus & Notes (Optional)", font=FONT_BODY_BOLD, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w", pady=(PAD_SM, 2))
        self.notes_entry = ctk.CTkEntry(
            container,
            placeholder_text="e.g. Master algorithms and build 3 full-stack portfolio apps",
            fg_color=COLOR_BG_INPUT,
            border_color=COLOR_BORDER,
        )
        if self.plan_notes:
            self.notes_entry.insert(0, self.plan_notes)
        self.notes_entry.pack(fill="x", pady=(2, PAD_MD))

        # Navigation
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom")

        ctk.CTkButton(
            btn_row,
            text="◀ Back",
            fg_color=COLOR_BG_INPUT,
            hover_color=COLOR_BORDER,
            command=self._back_step,
            width=90,
        ).pack(side="left")

        ctk.CTkButton(
            btn_row,
            text="Next: Review & Confirm ➔",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            command=self._submit_step_3,
            width=200,
        ).pack(side="right")

    def _set_duration(self, mc: int) -> None:
        self.duration_months = mc
        self._build_screen()

    def _set_frequency(self, fr: int) -> None:
        self.target_frequency = fr
        self._build_screen()

    def _submit_step_3(self) -> None:
        self.plan_notes = self.notes_entry.get().strip()
        self.current_step = 4
        self._build_screen()

    # -------------------------------------------------------------
    # Step 4: Confirm & Launch
    # -------------------------------------------------------------
    def _render_step_4(self) -> None:
        container = ctk.CTkFrame(self.step_content_frame, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_LG)

        ctk.CTkLabel(container, text="Step 4 — Review & Launch Plan", font=FONT_SUBTITLE, text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(container, text="Verify details below. Upon confirmation, the Track, Habits, and Plan will be saved.", font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w", pady=(0, PAD_MD))

        summary_box = ctk.CTkFrame(container, fg_color="#181822", corner_radius=CORNER_SM, border_width=1, border_color=COLOR_BORDER)
        summary_box.pack(fill="both", expand=True, padx=PAD_MD, pady=PAD_MD)

        s_inner = ctk.CTkFrame(summary_box, fg_color="transparent")
        s_inner.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_LG)

        # Track Summary
        t_row = ctk.CTkFrame(s_inner, fg_color="transparent")
        t_row.pack(fill="x", pady=(0, PAD_SM))
        ctk.CTkLabel(t_row, text=f"{self.track_icon} {self.track_name}", font=FONT_TITLE, text_color=self.track_color).pack(side="left")
        ctk.CTkLabel(t_row, text=f"Category: {self.track_category}", font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY).pack(side="right")

        # Plan Scope
        ctk.CTkLabel(
            s_inner,
            text=f"Timeframe: {self.duration_months} Months • Weekly Target: {self.target_frequency} days/week",
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, PAD_SM))

        if self.plan_notes:
            ctk.CTkLabel(s_inner, text=f"Focus: {self.plan_notes}", font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(anchor="w", pady=(0, PAD_SM))

        # Habits to be created
        ctk.CTkLabel(s_inner, text=f"Habits / Skills Included ({len(self.habits_list)}):", font=FONT_SECTION_HEADER, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w", pady=(PAD_SM, 2))
        for h in self.habits_list:
            ctk.CTkLabel(s_inner, text=f"  • {self.track_icon} {h}", font=FONT_BODY, text_color=COLOR_TEXT_PRIMARY).pack(anchor="w")

        # Navigation
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom")

        ctk.CTkButton(
            btn_row,
            text="◀ Back",
            fg_color=COLOR_BG_INPUT,
            hover_color=COLOR_BORDER,
            command=self._back_step,
            width=90,
        ).pack(side="left")

        ctk.CTkButton(
            btn_row,
            text="🚀 Confirm & Launch Plan",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_SUCCESS,
            hover_color="#059669",
            command=self._confirm_and_create,
            width=200,
        ).pack(side="right")

    def _back_step(self) -> None:
        self.current_step = max(1, self.current_step - 1)
        self._build_screen()

    def _confirm_and_create(self) -> None:
        try:
            # 1. Create Track
            track_id = self.db.create_track(
                name=self.track_name,
                category=self.track_category,
                color_hex=self.track_color,
                icon=self.track_icon,
            )

            # 2. Create Habits under track
            for h_name in self.habits_list:
                self.db.create_habit(
                    track_id=track_id,
                    name=h_name,
                    icon=self.track_icon,
                    target_frequency=self.target_frequency,
                )

            # 3. Create Plan
            today = date.today()
            start_date = today.isoformat()
            end_date = (today + timedelta(days=self.duration_months * 30)).isoformat()
            self.db.create_plan(
                track_id=track_id,
                start_date=start_date,
                end_date=end_date,
                weekly_target=self.target_frequency,
                notes=self.plan_notes,
            )

            # Success modal
            InfoModal(
                self,
                title="Plan Created!",
                message=f"'{self.track_name}' and its {len(self.habits_list)} habits have been successfully registered.",
            )
            self._reset_wizard()
            if self.on_plan_created:
                self.on_plan_created()
        except Exception as e:
            InfoModal(self, title="Error Creating Plan", message=str(e), is_error=True)

    def _render_existing_plans_section(self, parent) -> None:
        plans = self.db.get_all_plans()
        tracks = {t.id: t for t in self.db.get_all_tracks()}

        plans_card = ctk.CTkFrame(parent, fg_color=COLOR_BG_CARD, corner_radius=CORNER_MD, border_width=1, border_color=COLOR_BORDER)
        plans_card.pack(fill="x", pady=PAD_MD)

        p_inner = ctk.CTkFrame(plans_card, fg_color="transparent")
        p_inner.pack(fill="x", padx=PAD_LG, pady=PAD_MD)

        ctk.CTkLabel(p_inner, text="Active Long-Term Plans", font=FONT_SUBTITLE, text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", pady=(0, PAD_SM))

        if not plans:
            ctk.CTkLabel(p_inner, text="No long-term plans created yet.", font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(anchor="w")
            return

        for p in plans:
            tr = tracks.get(p.track_id)
            tr_name = tr.name if tr else "Track"
            tr_color = tr.color_hex if tr else COLOR_ACCENT
            tr_ico = tr.icon if tr else "🎯"

            row = ctk.CTkFrame(p_inner, fg_color="#1E1E2A", corner_radius=6)
            row.pack(fill="x", pady=3)

            left_box = ctk.CTkFrame(row, fg_color="transparent")
            left_box.pack(side="left", padx=PAD_MD, pady=PAD_SM)

            ctk.CTkLabel(left_box, text=f"{tr_ico} {tr_name}", font=FONT_BODY_BOLD, text_color=tr_color).pack(anchor="w")
            ctk.CTkLabel(left_box, text=f"Target: {p.weekly_target}x/wk • Range: {p.start_date} to {p.end_date}", font=FONT_CAPTION, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")
            if p.notes:
                ctk.CTkLabel(left_box, text=f"Focus: {p.notes}", font=FONT_CAPTION, text_color=COLOR_TEXT_MUTED).pack(anchor="w")

            ctk.CTkButton(
                row,
                text="Delete Plan",
                width=90,
                height=26,
                fg_color="transparent",
                hover_color=COLOR_DANGER,
                text_color=COLOR_TEXT_MUTED,
                command=lambda pid=p.id, pname=tr_name: self._confirm_delete_plan(pid, pname),
            ).pack(side="right", padx=PAD_MD)

    def _confirm_delete_plan(self, plan_id: int, plan_name: str) -> None:
        def handle_delete():
            self.db.delete_plan(plan_id)
            self.refresh()

        ConfirmModal(
            self,
            title="Delete Plan",
            message=f"Are you sure you want to remove the plan for '{plan_name}'? The track and habits will remain intact.",
            confirm_text="Delete",
            is_danger=True,
            on_confirm=handle_delete,
        )
