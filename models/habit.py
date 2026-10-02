"""Habit model representing a trackable recurring habit or skill."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Habit:
    id: Optional[int]
    track_id: Optional[int]
    name: str
    icon: str
    target_frequency: int
    created_date: str
    is_active: int = 1

    def display_name(self) -> str:
        """Returns friendly icon + name display string."""
        return f"{self.icon} {self.name}" if self.icon else self.name
