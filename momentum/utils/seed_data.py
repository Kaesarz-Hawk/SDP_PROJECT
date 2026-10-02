"""
Seed data — populates the database with realistic sample data on first run
(or after "Reset all data"), so every screen looks alive immediately.

Design goal: charts/heatmaps must look INTERESTING, not uniformly 100% or 0%.
Includes: strong recent streaks, historic gaps, partial weeks, a carried-over task,
mixed priorities, and one 3-month Productivity plan.
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Optional

try:
    from database.db_manager import DBManager
except ImportError:  # pragma: no cover
    from ..database.db_manager import DBManager

# Fixed seed => deterministic, demo-friendly history every fresh install
_RANDOM = random.Random(42)


def _d(days_ago: int) -> str:
    return (date.today() - timedelta(days=days_ago)).isoformat()


# Reliability profile per habit: probability of completion per day, plus
# special recent-behavior so the demo shows a live streak on the dashboard.
_SEED_TRACKS = [
    # (name, category, color, icon, habits[(name, icon, target, profile)])
    {
        "name": "Fitness",
        "category": "fitness",
        "color": "#2DD4A7",
        "icon": "\U0001F3CB",
        "habits": [
            ("Morning Workout", "\U0001F3CB", 5, {"p": 0.72, "recent_streak": 6}),
            ("10k Steps", "\U0001F43F", 6, {"p": 0.60, "recent_streak": 3}),
            ("Stretching", "\U0001F9D8", 4, {"p": 0.45, "recent_streak": 0}),
        ],
    },
    {
        "name": "Academics",
        "category": "academics",
        "color": "#38BDF8",
        "icon": "\U0001F4DA",
        "habits": [
            ("SQL Practice", "\U0001F4BE", 5, {"p": 0.78, "recent_streak": 9}),
            ("Lecture Notes", "\U0001F4DD", 6, {"p": 0.65, "recent_streak": 2}),
            ("Past Paper Drill", "\U0001F9F3", 3, {"p": 0.40, "recent_streak": 0}),
        ],
    },
    {
        "name": "Productivity",
        "category": "productivity/skills",
        "color": "#F5A524",
        "icon": "\U0001F4A1",
        "habits": [
            ("CP Problems", "\U0001F9E9", 5, {"p": 0.70, "recent_streak": 4}),
            ("React Study", "\U0001F7E9", 4, {"p": 0.55, "recent_streak": 1}),
            ("Java Refactor", "\U0001F41E", 3, {"p": 0.35, "recent_streak": 0}),
        ],
    },
    {
        "name": "Reading",
        "category": "reading",
        "color": "#A78BFA",
        "icon": "\U0001F4D6",
        "habits": [
            ("Read 30 min", "\U0001F4D6", 6, {"p": 0.68, "recent_streak": 5}),
            ("Kindle Highlights", "\U0001F4F1", 3, {"p": 0.38, "recent_streak": 0}),
        ],
    },
]

_SEED_TASKS = [
    # (title, days_offset, priority, status, track_index)
    ("Finish DB schema diagram", 0, "High", "Pending", 1),
    ("Review lecture 4 notes", 0, "Medium", "Pending", 1),
    ("Buy protein powder", 0, "Low", "Done", 0),
    ("Solve 2 array problems", 1, "High", "Pending", 2),
    ("Water the plants", 1, "Low", "Pending", 3),
    ("Submit assignment draft", -1, "High", "Pending", 1),   # carried over
    ("Outline blog post", 2, "Medium", "Pending", None),
    ("Weekly review", 3, "Medium", "Pending", None),
]

_SEED_PLAN = {
    "track": "Productivity",
    "days": 90,           # ~3 months
    "times_per_week": 5,
    "notes": "3-month focus: CP, SQL, React, JS, Java, MongoDB",
}


def _pattern_done(profile: dict, days_ago: int) -> bool:
    """
    Decide if a habit was completed days_ago.
    - days_ago < recent_streak => guaranteed done (fresh live streak)
    - otherwise roll dice against p, with occasional planned gaps so history
      shows streaks AND resets.
    """
    recent = int(profile.get("recent_streak", 0))
    if days_ago < recent:
        return True
    if days_ago == recent and recent > 0:
        # day right before the streak started: usually missed (streak boundary)
        return False
    p = float(profile.get("p", 0.5))
    # Occasional vacation gap: whole week off roughly every 5 weeks
    week = days_ago // 7
    if week % 5 == 4 and 14 <= days_ago <= 20:
        return False
    return _RANDOM.random() < p


def seed_if_empty(db: DBManager, force: bool = False) -> bool:
    """
    Populate sample data when the tracks table is empty (first run / post-reset).
    Returns True if seeding happened.
    """
    try:
        if not force and not db.is_empty():
            return False
        _populate(db)
        return True
    except Exception as exc:  # never let seeding crash the app
        print(f"[Momentum:Seed] seeding failed: {exc}")
        return False


def _populate(db: DBManager) -> None:
    """Insert tracks, habits, ~5 weeks of logs, tasks, and one plan."""
    history_days = 35  # ~5 weeks of history

    track_ids: list[int] = []
    habit_rows: list[tuple[int, dict]] = []  # (habit_id, profile)

    for spec in _SEED_TRACKS:
        tid = db.create_track(spec["name"], spec["category"], spec["color"], spec["icon"])
        track_ids.append(tid)
        for hname, hicon, hfreq, profile in spec["habits"]:
            hid = db.create_habit(tid, hname, hicon, hfreq)
            # Habits "existed" since the start of the seeded history window
            db.update_habit(hid, created_date=_d(history_days))
            habit_rows.append((hid, profile))

    # Daily logs — varied history with streaks, gaps, partial weeks
    for habit_id, profile in habit_rows:
        for days_ago in range(history_days, -1, -1):
            done = _pattern_done(profile, days_ago)
            # Weekend softness for a couple of habits makes charts less flat
            day = date.today() - timedelta(days=days_ago)
            if day.weekday() >= 5 and profile.get("p", 0.5) < 0.6:
                done = done and _RANDOM.random() < 0.6
            db.toggle_completion(habit_id, day.isoformat(), done)

    # Tasks — mixed priorities, some done, one/two carried over from past dates
    for title, offset, priority, status, track_idx in _SEED_TASKS:
        due = (date.today() + timedelta(days=offset)).isoformat()
        linked = track_ids[track_idx] if track_idx is not None else None
        carried = 1 if offset < 0 and status == "Pending" else 0
        db.create_task(title, due, priority, linked, status=status,
                       carried_over=carried, created_date=_d(max(0, -offset + 2)))

    # Sample plan — 3-month Productivity plan
    plan_spec = _SEED_PLAN
    p_idx = next(i for i, t in enumerate(_SEED_TRACKS) if t["name"] == plan_spec["track"])
    start = date.today() - timedelta(days=7)   # started last week, looks "in progress"
    end = start + timedelta(days=plan_spec["days"])
    weekly_target = 5
    db.create_plan(track_ids[p_idx], start.isoformat(), end.isoformat(),
                   weekly_target, plan_spec["notes"])


def ensure_recent_rollover(db: DBManager) -> int:
    """Auto-roll pending overdue tasks into today (screen-4 behavior). Called on launch."""
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    return db.roll_over_incomplete_tasks(yesterday, today)
