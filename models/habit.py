"""Habit data model — a trackable item under a Track."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Habit:
    """Represents one row of the habits table."""
    id: Optional[int] = None
    track_id: Optional[int] = None
    name: str = ""
    icon: str = "✅"
    target_frequency: int = 7  # completions per week
    created_date: str = ""
    is_active: int = 1  # soft-delete flag
    track_name: str = field(default="", compare=False)
    track_color: str = field(default="#7C5CFC", compare=False)

    @property
    def active(self) -> bool:
        return bool(self.is_active)

    def display_name(self) -> str:
        icon = self.icon.strip() if self.icon else ""
        name = self.name.strip() if self.name else "Untitled habit"
        return f"{icon} {name}" if icon else name

    def weekly_target(self) -> int:
        """Sanitized weekly target (never below 1, never above 7)."""
        try:
            value = int(self.target_frequency)
        except (TypeError, ValueError):
            return 7
        return max(1, min(7, value))

    def __str__(self) -> str:
        return self.display_name()
