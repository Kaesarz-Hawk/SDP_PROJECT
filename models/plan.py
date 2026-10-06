"""Plan data model — a goal decomposition window for a Track."""
from dataclasses import dataclass
from typing import Optional
from datetime import date


@dataclass
class Plan:
    """Represents one row of the plans table."""
    id: Optional[int] = None
    track_id: int = 0
    start_date: str = ""  # ISO YYYY-MM-DD
    end_date: str = ""    # ISO YYYY-MM-DD
    weekly_target: int = 3
    notes: str = ""
    track_name: str = ""
    track_color: str = "#7C5CFC"
    track_icon: str = "📁"

    def total_weeks(self) -> float:
        """Weeks covered by the plan (at least 1 to avoid divide-by-zero)."""
        try:
            start = date.fromisoformat(self.start_date)
            end = date.fromisoformat(self.end_date)
        except (TypeError, ValueError):
            return 1.0
        days = (end - start).days + 1
        return max(days / 7.0, 1.0)

    def duration_label(self) -> str:
        """Human-readable duration, e.g. '3 months' / '12 weeks'."""
        try:
            start = date.fromisoformat(self.start_date)
            end = date.fromisoformat(self.end_date)
        except (TypeError, ValueError):
            return "Custom range"
        days = (end - start).days + 1
        if days <= 0:
            return "Invalid range"
        weeks = days / 7.0
        if weeks < 4:
            return f"{weeks:.0f} week{'s' if abs(weeks - 1) > 0.01 else ''}"
        if weeks < 8:
            return f"{weeks / 4.345:.1f} months"
        if weeks < 52:
            return f"{weeks / 4.345:.1f} months"
        years = weeks / 52.0
        return f"{years:.1f} year{'s' if abs(years - 1) > 0.01 else ''}"

    @staticmethod
    def calculate_weekly_target(start_date: str, end_date: str, times_per_week: int) -> int:
        """
        Suggested weekly target from user goal frequency.
        Clamps nonsense inputs (short/long timeframes, zero/negative frequency).
        """
        try:
            freq = int(times_per_week)
        except (TypeError, ValueError):
            freq = 3
        freq = max(1, min(7, freq))
        try:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
        except (TypeError, ValueError):
            return freq
        if end < start:
            return freq
        days = (end - start).days + 1
        weeks = days / 7.0
        if weeks < 1:
            # Very short timeframe: keep the stated frequency, no extrapolation blow-up
            return freq
        # Scale gently with plan length but stay within 1..7 per day-cap and user intent
        suggested = freq
        # Longer plans: slight boost if user asked for more frequent habits
        if weeks >= 4 and freq < 7:
            suggested = min(7, freq)
        return max(1, min(7, int(round(suggested))))

    def summary(self) -> str:
        weeks = self.total_weeks()
        return (
            f"{self.start_date} → {self.end_date} · "
            f"{weeks:.1f} weeks · {self.weekly_target}× / week"
        )
