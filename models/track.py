"""Track model representing a life category / track."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Track:
    id: Optional[int]
    name: str
    category: str
    color_hex: str
    icon: str
    created_date: str

    def display_name(self) -> str:
        """Returns friendly icon + name display string."""
        return f"{self.icon} {self.name}" if self.icon else self.name
