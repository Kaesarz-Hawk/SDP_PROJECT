"""Task data model — a daily to-do item with priority and optional track link."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Task:
    """Represents one row of the tasks table."""
    id: Optional[int] = None
    title: str = ""
    due_date: str = ""  # ISO YYYY-MM-DD
    priority: str = "Medium"  # Low | Medium | High
    status: str = "Pending"  # Pending | Done
    linked_track_id: Optional[int] = None
    carried_over: int = 0
    created_date: str = ""
    track_name: str = ""
    track_color: str = ""

    @property
    def is_done(self) -> bool:
        return self.status == "Done"

    @property
    def is_carried_over(self) -> bool:
        return bool(self.carried_over)

    def priority_rank(self) -> int:
        """Lower number = higher priority for sorting."""
        order = {"High": 0, "Medium": 1, "Low": 2}
        return order.get(self.priority, 1)

    def display_title(self) -> str:
        return self.title.strip() if self.title else "Untitled task"
