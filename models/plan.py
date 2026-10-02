"""Plan model representing a decomposed long-term goal for a Track."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Plan:
    id: Optional[int]
    track_id: int
    start_date: str
    end_date: str
    weekly_target: Optional[int]
    notes: Optional[str] = ""
