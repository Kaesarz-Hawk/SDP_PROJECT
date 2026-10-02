"""
Screen 1: Onboarding / Plan Builder — step-by-step goal decomposition wizard.

Step 1 — Name the Track: name, category, color, icon
Step 2 — Add Habits/Skills under it
Step 3 — Set Timeframe & Goal: duration + target frequency → computed weekly plan
Step 4 — Confirm & Create: summary, then saves Track + Habits + Plan

Also accessible any time to add NEW tracks/plans. Existing tracks & plans are
shown alongside so the Plan Builder's output is always visible.
"""
from __future__ import annotations

from datetime import date, timedelta

import tkinter as tk
import customtkinter as ctk

try:
    from utils.theme import Colors, Fonts, Spacing
except ImportError:  # pragma: no cover
    from ..utils.theme import Colors, Fonts, Spacing

from .components.modal_dialog import ConfirmModal, FormModal, show_message, show_error

# Smart default color palette (design doc category families + extras)
SWATCH_COLORS = [
    Colors.ACCENT, Colors.CAT_FITNESS, Colors.CAT_ACADEMICS,
    Colors.CAT_PRODUCTIVITY, Colors.CAT_READING, Colors.CAT_HEALTH,
    "#F472B6", "#F0435C", "#4ADE80",
]
EMOJI_CHOICES = ["🎯", "📚", "💪", "💻", "🧘", "🌱", "⚡", "🎨",
                 "🎵", "🏃", "🧠", "💼", "📈", "💧", "😴", "📖"]
CATEGORIES = ["Productivity", "Academics", "Fitness", "Reading",
              "Health & Sleep", "Custom"]
DURATIONS = {
    "1 week": 7,
    "1 month": 30,
    "2 months": 61,
    "3 months": 90,
    "6 months": 183,
    "1 year": 365,
    "2 years": 730,
}
STEP_TITLES = [
    "Step 1 · Name the track",
    "Step 2 · Add habits / skills",
    "Step 3 · Timeframe & goal",
    "Step 4 · Confirm & create",
]


class OnboardingFrame(ctk.CTkFrame):
    def __init__(self, master, db, app):
        super().__init__(master, fg_color=Colors.BG_BASE, corner_radius=0)
        self.db = db
        self.app = app
        self.step = 1
        self._reset_wizard_state()

        # ---- Header ----
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=Spacing.XL, pady=(Spacing.LG, Spacing.MD))
        ctk.CTkLabel(head, text="Plan Builder", font=Fonts.title(),
                     text_color=Colors.TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(head, text="Turn a long-term goal into daily trackable habits",
                     font=Fonts.body(), text_color=Colors.TEXT_SECONDARY).pack(
            side="left", padx=Spacing.MD)

        # ---- Body: wizard card + existing data panel ----
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=Spacing.XL, pady=(0, Spacing.LG))

        left = ctk.CTkFrame(body, fg_color=Colors.BG_CARD,
                            corner_radius=Spacing.CARD_RADIUS)
        left.pack(side="left", fill="both", expand=True, padx=(0, Spacing.MD))
        self.left = left

        # Step indicator
        indicator = ctk.CTkFrame(left, fg_color="transparent")
        indicator.pack(fill="x", padx=Spacing.LG, pady=(Spacing.MD, 0))
        self.step_labels = []
        for i in range(4):
            lbl = ctk.CTkLabel(indicator, text=f"{i + 1}  ", width=34, height=34,
                               corner_radius=17, font=Fonts.small_bold(),
                               fg_color=Colors.BG_ELEVATED,
                               text_color=Colors.TEXT_MUTED)
            lbl.pack(side="left", padx=(0, Spacing.SM))
            self.step_labels.append(lbl)
        self.step_title = ctk.CTkLabel(left, text=STEP_TITLES[0],
                                       font=Fonts.subtitle(),
                                       text_color=Colors.TEXT_PRIMARY)
        self.step_title.pack(anchor="w", padx=Spacing.LG, pady=(Spacing.MD, 0))

        self.step_holder = ctk.CTkFrame(left, fg_color="transparent")
        self.step_holder.pack(fill="both", expand=True, padx=Spacing.LG,
                              pady=Spacing.MD)

        # Wizard navigation
        nav = ctk.CTkFrame(left, fg_color="transparent")
        nav.pack(fill="x", padx=Spacing.LG, pady=(0, Spacing.LG))
        self.back_btn = ctk.CTkButton(
            nav, text="← Back", width=110, height=38,
            fg_color=Colors.BG_ELEVATED, hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_PRIMARY, font=Fonts.body(),
            command=self._go_back)
        self.back_btn.pack(side="left")
        self.next_btn = ctk.CTkButton(
            nav, text="Next →", width=130, height=38,
            fg_color=Colors.ACCENT, hover_color=Colors.ACCENT_HOVER,
            font=Fonts.body_bold(), command=self._go_next)
        self.next_btn.pack(side="right")

        # Existing tracks & plans (Plan Builder output visible)
        self.side = ctk.CTkFrame(body, fg_color=Colors.BG_CARD,
                                 corner_radius=Spacing.CARD_RADIUS, width=310)
        self.side.pack(side="right", fill="y")
        self.side.pack_propagate(False)

        self._render_step()

    def _reset_wizard_state(self) -> None:
        self.wiz = {
            "name": "",
            "category": CATEGORIES[0],
            "color": SWATCH_COLORS[0],
            "icon": EMOJI_CHOICES[0],
            "habits": [],           # [(name, icon)]
            "duration": "3 months",
            "freq": "5",
            "start": date.today(),
        }

    # ------------------------------------------------------------------ #
    def refresh(self) -> None:
        try:
            self._render_step()
            self._render_side_panel()
        except Exception as exc:
            print(f"[Momentum:PlanBuilder] refresh failed: {exc}")
            import traceback
            traceback.print_exc()

    # ------------------------------------------------------------------ #
    def _render_step(self) -> None:
        for child in self.step_holder.winfo_children():
            child.destroy()
        self.step_title.configure(text=STEP_TITLES[self.step - 1])
        for i, lbl in enumerate(self.step_labels):
            if i + 1 < self.step:
                lbl.configure(fg_color=Colors.ACCENT, text_color=Colors.TEXT_PRIMARY,
                              text=f"✓")
            elif i + 1 == self.step:
                lbl.configure(fg_color=Colors.ACCENT, text_color=Colors.TEXT_PRIMARY,
                              text=str(i + 1))
            else:
                lbl.configure(fg_color=Colors.BG_ELEVATED,
                              text_color=Colors.TEXT_MUTED, text=str(i + 1))
        self.back_btn.configure(state="disabled" if self.step == 1 else "normal")
        self.next_btn.configure(text="Create 🎉" if self.step == 4 else "Next →")

        renderer = {
            1: self._render_step1,
            2: self._render_step2,
            3: self._render_step3,
            4: self._render_step4,
        }[self.step]
        renderer()

    def _render_step1(self) -> None:
        holder = self.step_holder
        ctk.CTkLabel(holder, text="Track name", font=Fonts.small(),
                     text_color=Colors.TEXT_SECONDARY).pack(anchor="w")
        self.name_entry = ctk.CTkEntry(
            holder, placeholder_text="e.g. Productivity, Academics, Fitness",
            height=36, fg_color=Colors.BG_INPUT, border_color=Colors.BG_ELEVATED,
            text_color=Colors.TEXT_PRIMARY, font=Fonts.body(),
            corner_radius=Spacing.BUTTON_RADIUS)
        self.name_entry.pack(fill="x", pady=(Spacing.XS, Spacing.MD))
        self.name_entry.insert(0, self.wiz["name"])

        ctk.CTkLabel(holder, text="Category", font=Fonts.small(),
                     text_color=Colors.TEXT_SECONDARY).pack(anchor="w")
        ctk.CTkOptionMenu(holder, values=CATEGORIES, variable=tk.StringVar(value=self.wiz["category"]),
                          height=32, fg_color=Colors.BG_ELEVATED,
                          button_color=Colors.ACCENT, button_hover_color=Colors.ACCENT_HOVER,
                          dropdown_fg_color=Colors.BG_ELEVATED, font=Fonts.body(),
                          command=self._set_category).pack(fill="x",
                                                           pady=(Spacing.XS, Spacing.MD))

        ctk.CTkLabel(holder, text="Color", font=Fonts.small(),
                     text_color=Colors.TEXT_SECONDARY).pack(anchor="w")
        swatches = ctk.CTkFrame(holder, fg_color="transparent")
        swatches.pack(anchor="w", pady=(Spacing.XS, Spacing.MD))
        for color in SWATCH_COLORS:
            btn = ctk.CTkButton(swatches, text="", width=34, height=34,
                                corner_radius=17, fg_color=color,
                                hover_color=color,
                                border_width=3 if color == self.wiz["color"] else 0,
                                border_color=Colors.TEXT_PRIMARY,
                                command=lambda c=color: self._set_color(c))
            btn.pack(side="left", padx=3)

        ctk.CTkLabel(holder, text="Icon (emoji)", font=Fonts.small(),
                     text_color=Colors.TEXT_SECONDARY).pack(anchor="w")
        icon_row = ctk.CTkFrame(holder, fg_color="transparent")
        icon_row.pack(anchor="w", pady=(Spacing.XS, 0))
        self.icon_var = tk.StringVar(value=self.wiz["icon"])
        for emoji in EMOJI_CHOICES[:8]:
            btn = ctk.CTkButton(
                icon_row, text=emoji, width=34, height=34,
                corner_radius=Spacing.BUTTON_RADIUS,
                fg_color=Colors.BG_ELEVATED if emoji != self.wiz["icon"] else Colors.ACCENT,
                hover_color=Colors.BG_HOVER,
                font=(Fonts.FAMILY, 15),
                command=lambda e=emoji: self._set_icon(e))
            btn.pack(side="left", padx=2)

    def _set_category(self, value: str) -> None:
        self.wiz["category"] = value

    def _set_color(self, color: str) -> None:
        self.wiz["color"] = color
        self._stash_step1()
        self._render_step()

    def _set_icon(self, emoji: str) -> None:
        self.wiz["icon"] = emoji
        self._stash_step1()
        self._render_step()

    def _stash_step1(self) -> None:
        try:
            if hasattr(self, "name_entry"):
                self.wiz["name"] = self.name_entry.get().strip()
        except Exception:
            pass

    def _render_step2(self) -> None:
        holder = self.step_holder
        ctk.CTkLabel(holder, text=f"Habits under “{self.wiz['name'] or 'this track'}”",
                     font=Fonts.small(), text_color=Colors.TEXT_SECONDARY).pack(
            anchor="w")
        row = ctk.CTkFrame(holder, fg_color="transparent")
        row.pack(fill="x", pady=(Spacing.XS, Spacing.SM))
        self.habit_entry = ctk.CTkEntry(
            row, placeholder_text="e.g. CP problems", height=34,
            fg_color=Colors.BG_INPUT, border_color=Colors.BG_ELEVATED,
            text_color=Colors.TEXT_PRIMARY, font=Fonts.body(),
            corner_radius=Spacing.BUTTON_RADIUS)
        self.habit_entry.pack(side="left", fill="x", expand=True, padx=(0, Spacing.SM))
        self.habit_icon = ctk.CTkEntry(
            row, placeholder_text="emoji", width=54, height=34,
            fg_color=Colors.BG_INPUT, border_color=Colors.BG_ELEVATED,
            text_color=Colors.TEXT_PRIMARY, font=Fonts.body(),
            corner_radius=Spacing.BUTTON_RADIUS, justify="center")
        self.habit_icon.pack(side="left", padx=(0, Spacing.SM))
        self.habit_icon.insert(0, "✅")
        ctk.CTkButton(row, text="＋ Add", width=80, height=34,
                      fg_color=Colors.ACCENT, hover_color=Colors.ACCENT_HOVER,
                      font=Fonts.body_bold(),
                      command=self._add_wiz_habit).pack(side="left")
        self.habit_entry.bind("<Return>", lambda e: self._add_wiz_habit())

        list_holder = ctk.CTkScrollableFrame(holder, fg_color=Colors.BG_INPUT,
                                             corner_radius=Spacing.BUTTON_RADIUS,
                                             height=210)
        list_holder.pack(fill="both", expand=True, pady=(0, Spacing.XS))
        if not self.wiz["habits"]:
            ctk.CTkLabel(list_holder, text="No habits added yet — add at least one.",
                         font=Fonts.small(), text_color=Colors.TEXT_MUTED).pack(
                pady=Spacing.MD)
        else:
            for i, (hname, hicon) in enumerate(self.wiz["habits"]):
                r = ctk.CTkFrame(list_holder, fg_color="transparent")
                r.pack(fill="x", padx=Spacing.XS, pady=2)
                ctk.CTkLabel(r, text=f"{hicon}  {hname}", font=Fonts.body(),
                             text_color=Colors.TEXT_PRIMARY).pack(side="left")
                ctk.CTkButton(r, text="✕", width=30, height=26, corner_radius=8,
                              fg_color="transparent", hover_color=Colors.DANGER_HOVER,
                              text_color=Colors.DANGER,
                              command=lambda idx=i: self._remove_wiz_habit(idx)).pack(
                    side="right")

        ctk.CTkLabel(holder, text="💡 Add the sub-skills of your goal — e.g. CP, SQL, React, JS, Java, MongoDB",
                     font=Fonts.caption(), text_color=Colors.TEXT_MUTED,
                     wraplength=520, justify="left").pack(anchor="w", pady=(Spacing.XS, 0))

    def _add_wiz_habit(self) -> None:
        name = self.habit_entry.get().strip()
        icon = (self.habit_icon.get().strip() or "✅")
        if not name:
            self.habit_entry.configure(border_color=Colors.DANGER)
            self.habit_entry.after(
                1200, lambda: self.habit_entry.configure(border_color=Colors.BG_ELEVATED))
            return
        if len(name) > 60:
            show_message(self.winfo_toplevel(), "Too long",
                         "Habit names are capped at 60 characters.")
            return
        if any(name.lower() == h[0].lower() for h in self.wiz["habits"]):
            show_message(self.winfo_toplevel(), "Duplicate",
                         f"\"{name}\" is already in this list.")
            return
        if len(self.wiz["habits"]) >= 12:
            show_message(self.winfo_toplevel(), "That's plenty",
                         "Keep it focused: 12 habits per track is the max.")
            return
        self.wiz["habits"].append((name, icon))
        self.habit_entry.delete(0, "end")
        self._render_step()
        self.habit_entry.focus_set()

    def _remove_wiz_habit(self, index: int) -> None:
        if 0 <= index < len(self.wiz["habits"]):
            self.wiz["habits"].pop(index)
            self._render_step()

    def _render_step3(self) -> None:
        holder = self.step_holder
        start = self.wiz["start"]

        ctk.CTkLabel(holder, text="Duration", font=Fonts.small(),
                     text_color=Colors.TEXT_SECONDARY).pack(anchor="w")
        ctk.CTkOptionMenu(holder, values=list(DURATIONS.keys()),
                          variable=tk.StringVar(value=self.wiz["duration"]),
                          height=32, fg_color=Colors.BG_ELEVATED,
                          button_color=Colors.ACCENT, button_hover_color=Colors.ACCENT_HOVER,
                          dropdown_fg_color=Colors.BG_ELEVATED, font=Fonts.body(),
                          command=self._set_duration).pack(fill="x",
                                                           pady=(Spacing.XS, Spacing.MD))

        ctk.CTkLabel(holder, text="Target frequency", font=Fonts.small(),
                     text_color=Colors.TEXT_SECONDARY).pack(anchor="w")
        ctk.CTkOptionMenu(holder, values=["1", "2", "3", "4", "5", "6", "7"],
                          variable=tk.StringVar(value=self.wiz["freq"]),
                          height=32, fg_color=Colors.BG_ELEVATED,
                          button_color=Colors.ACCENT, button_hover_color=Colors.ACCENT_HOVER,
                          dropdown_fg_color=Colors.BG_ELEVATED, font=Fonts.body(),
                          command=self._set_freq).pack(fill="x",
                                                       pady=(Spacing.XS, Spacing.MD))

        # Computed plan preview
        days = DURATIONS[self.wiz["duration"]]
        end = start + timedelta(days=days)
        weeks = max(days / 7.0, 1.0)
        from models.plan import Plan
        target = Plan.calculate_weekly_target(
            start.isoformat(), end.isoformat(), int(self.wiz["freq"]))

        preview = ctk.CTkFrame(holder, fg_color=Colors.BG_INPUT,
                               corner_radius=Spacing.CARD_RADIUS)
        preview.pack(fill="x", pady=Spacing.MD)
        ctk.CTkLabel(preview, text="CALCULATED PLAN", font=(Fonts.FAMILY, 10, "bold"),
                     text_color=Colors.TEXT_MUTED).pack(
            anchor="w", padx=Spacing.MD, pady=(Spacing.MD, Spacing.XS))
        rows = [
            ("Start date", start.isoformat()),
            ("End date", end.isoformat()),
            ("Total weeks", f"{weeks:.1f} weeks"),
            ("Suggested weekly target", f"{target} completions / week"),
            ("Daily suggestion", f"~{max(1, round(target / 7))} habit check-ins / day"),
        ]
        for label, value in rows:
            r = ctk.CTkFrame(preview, fg_color="transparent")
            r.pack(fill="x", padx=Spacing.MD, pady=2)
            ctk.CTkLabel(r, text=label, font=Fonts.small(),
                         text_color=Colors.TEXT_SECONDARY).pack(side="left")
            ctk.CTkLabel(r, text=value, font=Fonts.body_bold(),
                         text_color=Colors.TEXT_PRIMARY).pack(side="right")
        ctk.CTkLabel(preview, text=" ", font=Fonts.caption()).pack(pady=(0, Spacing.SM))

    def _set_duration(self, value: str) -> None:
        self.wiz["duration"] = value
        self._render_step()

    def _set_freq(self, value: str) -> None:
        self.wiz["freq"] = value
        self._render_step()

    def _render_step4(self) -> None:
        from models.plan import Plan
        holder = self.step_holder
        days = DURATIONS[self.wiz["duration"]]
        end = self.wiz["start"] + timedelta(days=days)
        weeks = max(days / 7.0, 1.0)
        target = Plan.calculate_weekly_target(
            self.wiz["start"].isoformat(), end.isoformat(), int(self.wiz["freq"]))

        summary = ctk.CTkFrame(holder, fg_color=Colors.BG_INPUT,
                               corner_radius=Spacing.CARD_RADIUS)
        summary.pack(fill="x")
        ctk.CTkLabel(summary, text="SUMMARY", font=(Fonts.FAMILY, 10, "bold"),
                     text_color=Colors.TEXT_MUTED).pack(
            anchor="w", padx=Spacing.MD, pady=(Spacing.MD, Spacing.XS))
        ctk.CTkLabel(summary, text=f"{self.wiz['icon']}  {self.wiz['name']}",
                     font=Fonts.subtitle(), text_color=self.wiz["color"]).pack(
            anchor="w", padx=Spacing.MD)
        ctk.CTkLabel(summary, text=f"Category: {self.wiz['category']}",
                     font=Fonts.small(), text_color=Colors.TEXT_SECONDARY).pack(
            anchor="w", padx=Spacing.MD, pady=(2, 0))
        ctk.CTkLabel(summary, text=f"Timeframe: {self.wiz['duration']} "
                                   f"({self.wiz['start'].isoformat()} → {end.isoformat()}, "
                                   f"{weeks:.1f} weeks)",
                     font=Fonts.small(), text_color=Colors.TEXT_SECONDARY).pack(
            anchor="w", padx=Spacing.MD, pady=(2, 0))
        ctk.CTkLabel(summary, text=f"Weekly target: {target} completions / week",
                     font=Fonts.small_bold(), text_color=Colors.TEXT_PRIMARY).pack(
            anchor="w", padx=Spacing.MD, pady=(2, 0))
        ctk.CTkLabel(summary, text=" ", font=Fonts.caption()).pack()

        ctk.CTkLabel(holder, text=f"Habits to create ({len(self.wiz['habits'])}):",
                     font=Fonts.small_bold(), text_color=Colors.TEXT_PRIMARY).pack(
            anchor="w", pady=(Spacing.MD, Spacing.XS))
        if not self.wiz["habits"]:
            ctk.CTkLabel(holder, text="None — go back and add at least one habit.",
                         font=Fonts.small(), text_color=Colors.DANGER).pack(anchor="w")
        else:
            for hname, hicon in self.wiz["habits"]:
                ctk.CTkLabel(holder, text=f"   {hicon} {hname}",
                             font=Fonts.body(), text_color=Colors.TEXT_SECONDARY).pack(
                    anchor="w", pady=1)

        ctk.CTkLabel(holder,
                     text="This creates: 1 Track · {} Habits · 1 Plan (with weekly target)".format(
                         len(self.wiz["habits"])),
                     font=Fonts.caption(), text_color=Colors.TEXT_MUTED).pack(
            anchor="w", pady=(Spacing.MD, 0))

    # ------------------------------------------------------------------ #
    def _go_back(self) -> None:
        if self.step > 1:
            if self.step == 2:
                self._stash_step2_input()
            self.step -= 1
            self._render_step()

    def _stash_step2_input(self) -> None:
        pass  # step-2 additions are committed immediately on Add

    def _go_next(self) -> None:
        if self.step == 1:
            if not self._validate_step1():
                return
            self.step = 2
            self._render_step()
        elif self.step == 2:
            self._stash_step2_input()
            if not self.wiz["habits"]:
                show_message(self.winfo_toplevel(), "Add a habit",
                             "Add at least one habit before continuing.")
                return
            self.step = 3
            self._render_step()
        elif self.step == 3:
            self.step = 4
            self._render_step()
        elif self.step == 4:
            self._create_everything()

    def _validate_step1(self) -> bool:
        name = ""
        try:
            name = self.name_entry.get().strip()
        except Exception:
            pass
        if not name:
            show_message(self.winfo_toplevel(), "Name required",
                         "Give your track a name (e.g. Productivity).")
            return False
        if len(name) > 50:
            show_message(self.winfo_toplevel(), "Name too long",
                         "Track names are capped at 50 characters.")
            return False
        if self.db.track_exists(name):
            show_message(self.winfo_toplevel(), "Track exists",
                         f"A track called \"{name}\" already exists. Pick another name.")
            return False
        self.wiz["name"] = name
        return True

    # ------------------------------------------------------------------ #
    def _create_everything(self) -> None:
        if not self.wiz["habits"]:
            show_message(self.winfo_toplevel(), "Nothing to create",
                         "Add at least one habit first.")
            return
        try:
            tid = self.db.create_track(
                self.wiz["name"], self.wiz["category"],
                self.wiz["color"], self.wiz["icon"])
            for hname, hicon in self.wiz["habits"]:
                self.db.create_habit(tid, hname, hicon, int(self.wiz["freq"]))

            days = DURATIONS[self.wiz["duration"]]
            end = self.wiz["start"] + timedelta(days=days)
            from models.plan import Plan
            target = Plan.calculate_weekly_target(
                self.wiz["start"].isoformat(), end.isoformat(), int(self.wiz["freq"]))
            self.db.create_plan(
                tid, self.wiz["start"].isoformat(), end.isoformat(), target,
                f"{self.wiz['duration']} plan: {self.wiz['name']}")

            name = self.wiz["name"]
            self._reset_wizard_state()
            self.step = 1
            self.refresh()
            show_message(
                self.winfo_toplevel(), "Plan created 🎉",
                f"Track “{name}” with its habits and plan is ready.\n"
                "Your Dashboard and Calendar now include them.")
        except Exception as exc:
            show_error(self.winfo_toplevel(), "Could not create plan",
                       "Something went wrong while saving. Nothing was half-saved "
                       "except partial rows if an error occurred mid-way — please "
                       "check Plan Builder list.", technical=str(exc))
            self._render_side_panel()

    # ------------------------------------------------------------------ #
    def _render_side_panel(self) -> None:
        for child in self.side.winfo_children():
            child.destroy()
        ctk.CTkLabel(self.side, text="YOUR TRACKS & PLANS", font=(Fonts.FAMILY, 10, "bold"),
                     text_color=Colors.TEXT_MUTED).pack(
            anchor="w", padx=Spacing.MD, pady=(Spacing.MD, Spacing.XS))

        tracks = self.db.get_all_tracks()
        if not tracks:
            ctk.CTkLabel(self.side, text="Nothing yet — build your first plan →",
                         font=Fonts.small(), text_color=Colors.TEXT_MUTED,
                         wraplength=260, justify="left").pack(
                anchor="w", padx=Spacing.MD, pady=Spacing.XS)
            return

        scroll = ctk.CTkScrollableFrame(self.side, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=Spacing.XS, pady=(0, Spacing.XS))

        for track in tracks:
            card = ctk.CTkFrame(scroll, fg_color=Colors.BG_INPUT,
                                corner_radius=Spacing.BUTTON_RADIUS)
            card.pack(fill="x", padx=Spacing.XS, pady=Spacing.XS)
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=Spacing.SM, pady=(Spacing.SM, 0))
            ctk.CTkLabel(top, text=track.display_name(), font=Fonts.body_bold(),
                         text_color=track.color_hex).pack(side="left")
            ctk.CTkLabel(top, text=f"{track.habit_count} habits",
                         font=Fonts.caption(),
                         text_color=Colors.TEXT_MUTED).pack(side="right")

            plans = self.db.get_plans_for_track(track.id)
            if plans:
                for plan in plans[:2]:
                    ctk.CTkLabel(
                        card, text=f"🗓 {plan.start_date} → {plan.end_date} · "
                                   f"{plan.weekly_target}×/week",
                        font=Fonts.caption(), text_color=Colors.TEXT_SECONDARY,
                        anchor="w").pack(fill="x", padx=Spacing.SM, pady=(2, 0))
            else:
                ctk.CTkLabel(card, text="No plan yet",
                             font=Fonts.caption(), text_color=Colors.TEXT_MUTED,
                             anchor="w").pack(fill="x", padx=Spacing.SM, pady=(2, 0))

            btns = ctk.CTkFrame(card, fg_color="transparent")
            btns.pack(fill="x", padx=Spacing.SM, pady=(Spacing.XS, Spacing.SM))
            ctk.CTkButton(btns, text="✎ Edit", width=66, height=24,
                          corner_radius=7, fg_color=Colors.BG_ELEVATED,
                          hover_color=Colors.BG_HOVER, text_color=Colors.TEXT_PRIMARY,
                          font=Fonts.caption(),
                          command=lambda t=track: self._edit_track(t)).pack(
                side="left", padx=(0, 4))
            ctk.CTkButton(btns, text="🗑 Delete", width=74, height=24,
                          corner_radius=7, fg_color=Colors.BG_ELEVATED,
                          hover_color=Colors.BG_HOVER, text_color=Colors.DANGER,
                          font=Fonts.caption(),
                          command=lambda t=track: self._delete_track(t)).pack(side="left")

    def _edit_track(self, track) -> None:
        fields = [
            {"key": "name", "label": "Track name", "type": "entry",
             "initial": track.name, "max_length": 50},
            {"key": "category", "label": "Category", "type": "option",
             "options": CATEGORIES,
             "initial": track.category if track.category in CATEGORIES else CATEGORIES[0]},
            {"key": "icon", "label": "Icon (emoji)", "type": "entry",
             "initial": track.icon, "max_length": 4},
            {"key": "color", "label": "Color hex", "type": "entry",
             "initial": track.color_hex, "max_length": 7},
        ]

        def validate(values: dict) -> str | None:
            name = (values.get("name") or "").strip()
            if not name:
                return "Track name cannot be empty."
            color = (values.get("color") or "").strip()
            if not (color.startswith("#") and len(color) == 7):
                return "Color must be a hex value like #7C5CFC."
            existing = [t for t in self.db.get_all_tracks()
                        if t.id != track.id and t.name.lower() == name.lower()]
            if existing:
                return f"A track named \"{name}\" already exists."
            return None

        def submit(values: dict) -> None:
            try:
                self.db.update_track(
                    track.id, name=values["name"].strip(),
                    category=values["category"],
                    icon=(values.get("icon") or "📁").strip() or "📁",
                    color_hex=values["color"].strip())
                self.refresh()
            except Exception as exc:
                show_error(self.winfo_toplevel(), "Could not update track",
                           "The track could not be saved.", technical=str(exc))

        FormModal(self.winfo_toplevel(), f"Edit “{track.name}”", fields, submit,
                  validate=validate, submit_text="Save changes")

    def _delete_track(self, track) -> None:
        def do_delete():
            try:
                self.db.delete_track(track.id)
                self.refresh()
            except Exception as exc:
                show_error(self.winfo_toplevel(), "Could not delete track",
                           "The track could not be removed.", technical=str(exc))

        ConfirmModal(
            self.winfo_toplevel(), "Delete this track?",
            f"\"{track.name}\" and its plans will be removed.\n"
            "Its habits are hidden (soft-deleted) but their history is kept for analytics.",
            on_confirm=do_delete, confirm_text="Delete track")
