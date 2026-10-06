"""DailyLog data model — one completion record per habit per day."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class DailyLog:
    """Represents one row of the daily_logs table."""
    id: Optional[int] = None
    habit_id: int = 0
    log_date: str = ""  # ISO YYYY-MM-DD
    completed: int = 0  # 0 or 1
    value: Optional[float] = None  # optional metric (hours, steps, etc.)

    @property
    def is_completed(self) -> bool:
        return bool(self.completed)
