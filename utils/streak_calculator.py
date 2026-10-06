"""
Pure streak & completion logic.
No UI code, no SQL — takes plain date strings / log lists and returns numbers.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable, Optional, Sequence, Set


def _to_date(value: str | date) -> Optional[date]:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _completed_set(daily_logs: Iterable) -> Set[date]:
    """Extract the set of dates marked completed from DailyLog objects or (date, completed) pairs."""
    completed: Set[date] = set()
    for item in daily_logs:
        if item is None:
            continue
        if isinstance(item, tuple) and len(item) >= 2:
            d = _to_date(item[0])
            flag = item[1]
        else:
            d = _to_date(getattr(item, "log_date", None))
            flag = getattr(item, "completed", 0)
        if d is None:
            continue
        if bool(flag):
            completed.add(d)
    return completed


def compute_current_streak(daily_logs: Iterable, today: Optional[date] = None) -> int:
    """
    Current consecutive-day streak ending today (or yesterday if today not logged yet).

    Rules:
    - Habit never completed → 0
    - Completed every day since creation → correct count, no off-by-one
    - Gap in the middle → streak resets after the gap
    - If today has no log yet but yesterday does, streak is still alive (grace for same-day tracking)
    """
    completed = _completed_set(daily_logs)
    if not completed:
        return 0

    if today is None:
        today = date.today()

    # If today is completed, streak walks back from today
    if today in completed:
        cursor = today
    elif (today - timedelta(days=1)) in completed:
        # Grace: user can still complete today without breaking yesterday's streak
        cursor = today - timedelta(days=1)
    else:
        return 0

    streak = 0
    while cursor in completed:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def compute_best_streak(daily_logs: Iterable) -> int:
    """Longest consecutive run of completed days in the entire history."""
    completed = _completed_set(daily_logs)
    if not completed:
        return 0
    ordered = sorted(completed)
    best = 1
    run = 1
    for i in range(1, len(ordered)):
        if ordered[i] - ordered[i - 1] == timedelta(days=1):
            run += 1
            if run > best:
                best = run
        else:
            run = 1
    return best


def compute_completion_percentage(
    daily_logs: Iterable,
    start_date: str | date,
    end_date: str | date,
    expected_days: Optional[int] = None,
) -> float:
    """
    Completion percentage over [start_date, end_date] inclusive.

    expected_days: optional override (e.g. target frequency-based days).
    Default denominator = calendar days in range (min 1).
    """
    completed = _completed_set(daily_logs)
    start = _to_date(start_date)
    end = _to_date(end_date)
    if start is None or end is None:
        return 0.0
    if end < start:
        start, end = end, start

    if expected_days is not None:
        try:
            denom = int(expected_days)
        except (TypeError, ValueError):
            denom = 0
        if denom <= 0:
            # Fall back to calendar days
            denom = (end - start).days + 1
    else:
        denom = (end - start).days + 1

    if denom <= 0:
        return 0.0

    hits = sum(1 for d in completed if start <= d <= end)
    return round(min(100.0, (hits / denom) * 100.0), 1)


def compute_daily_overall_completion(
    habit_logs_by_habit: dict[int, Sequence],
    habits: Sequence,
    day: date,
) -> float:
    """
    Overall completion ratio for one calendar day across all active habits.
    habit_logs_by_habit: {habit_id: [DailyLog, ...]} or {habit_id: [(date_str, completed), ...]}
    """
    active = [h for h in habits if bool(getattr(h, "is_active", 1))]
    if not active:
        return 0.0
    done = 0
    for habit in active:
        logs = habit_logs_by_habit.get(getattr(habit, "id", None), [])
        completed = _completed_set(logs)
        if day in completed:
            done += 1
    return done / len(active)
