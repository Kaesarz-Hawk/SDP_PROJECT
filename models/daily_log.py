"""DailyLog model representing a habit completion status for a specific date."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DailyLog:
    id: Optional[int]
    habit_id: int
    log_date: str
    completed: int  # 0 or 1
    value: Optional[float] = None
