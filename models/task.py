"""Task model representing a to-do item."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Task:
    id: Optional[int]
    title: str
    due_date: str
    priority: str = "Medium"  # 'Low' | 'Medium' | 'High'
    status: str = "Pending"   # 'Pending' | 'Done'
    linked_track_id: Optional[int] = None
    carried_over: int = 0     # 0 or 1
    created_date: str = ""
