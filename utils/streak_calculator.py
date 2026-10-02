"""Streak calculation logic for Momentum habits.

Pure business logic module: computes current and all-time best streaks
given a collection of completed daily logs or completed date strings.
Contains no UI, database, or network code.
"""

from datetime import date, datetime, timedelta
from typing import Iterable, Sequence, Set, Union


def _normalize_date(d: Union[str, date, datetime]) -> date:
    """Normalizes input to a datetime.date object."""
    if isinstance(d, datetime):
        return d.date()
    elif isinstance(d, date):
        return d
    elif isinstance(d, str):
        return date.fromisoformat(d.strip())
    raise ValueError(f"Unsupported date format: {d}")


def compute_current_streak(
    completed_dates: Iterable[Union[str, date, datetime]],
    reference_date: Union[str, date, datetime, None] = None,
) -> int:
    """Calculates the current streak of consecutive days up to reference_date (defaults to today).

    If the habit is completed today, streak counts today + unbroken consecutive preceding days.
    If not completed today, but completed yesterday, streak is still active (unbroken from yesterday).
    Otherwise, current streak is 0.

    Args:
        completed_dates: Iterable of date objects or 'YYYY-MM-DD' strings where habit was completed.
        reference_date: Target reference date (defaults to date.today()).

    Returns:
        int: Length of current streak in consecutive days (0 if never or lost).
    """
    if reference_date is None:
        ref = date.today()
    else:
        ref = _normalize_date(reference_date)

    dates_set: Set[date] = set()
    for item in completed_dates:
        try:
            dates_set.add(_normalize_date(item))
        except (ValueError, TypeError):
            continue

    if not dates_set:
        return 0

    # Check starting anchor: today or yesterday
    if ref in dates_set:
        curr = ref
    elif (ref - timedelta(days=1)) in dates_set:
        curr = ref - timedelta(days=1)
    else:
        return 0

    streak = 0
    while curr in dates_set:
        streak += 1
        curr -= timedelta(days=1)

    return streak


def compute_best_streak(
    completed_dates: Iterable[Union[str, date, datetime]],
) -> int:
    """Calculates the longest unbroken sequence of consecutive completed days in history.

    Args:
        completed_dates: Iterable of date objects or 'YYYY-MM-DD' strings where habit was completed.

    Returns:
        int: Longest consecutive streak count (0 if no completed dates).
    """
    parsed_dates: list[date] = []
    for item in completed_dates:
        try:
            parsed_dates.append(_normalize_date(item))
        except (ValueError, TypeError):
            continue

    if not parsed_dates:
        return 0

    unique_sorted = sorted(set(parsed_dates))
    max_streak = 1
    current_run = 1

    for i in range(1, len(unique_sorted)):
        prev = unique_sorted[i - 1]
        curr = unique_sorted[i]
        if curr - prev == timedelta(days=1):
            current_run += 1
            if current_run > max_streak:
                max_streak = current_run
        else:
            current_run = 1

    return max_streak


def get_streak_flame_level(streak_count: int) -> tuple[str, str]:
    """Returns visual flame icon and hex color representing streak intensity.

    Returns:
        (emoji, hex_color)
    """
    if streak_count <= 0:
        return ("⚡", "#64748B")  # Muted grey when 0
    elif streak_count < 3:
        return ("🔥", "#F59E0B")  # Amber for starting streak
    elif streak_count < 7:
        return ("🔥", "#F97316")  # Orange for building streak
    elif streak_count < 21:
        return ("🔥", "#EF4444")  # Bright red for solid habit
    else:
        return ("🔥", "#EC4899")  # Pink/purple super flame for 3+ weeks
