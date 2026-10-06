"""Track data model — a custom life category (Fitness, Academics, etc.)."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Track:
    """Represents one row of the tracks table."""
    id: Optional[int] = None
    name: str = ""
    category: str = ""
    color_hex: str = "#7C5CFC"
    icon: str = "📁"
    created_date: str = ""
    habit_count: int = field(default=0, compare=False)

    def display_name(self) -> str:
        """Human-readable label with emoji icon."""
        icon = self.icon.strip() if self.icon else ""
        name = self.name.strip() if self.name else "Untitled"
        return f"{icon} {name}" if icon else name

    def __str__(self) -> str:
        return self.display_name()
