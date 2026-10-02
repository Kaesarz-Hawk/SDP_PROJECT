"""
Single source of truth for every color, font, and spacing value in Momentum.
UI files must import from here — never hardcode hex colors or font tuples elsewhere.
"""
from __future__ import annotations


class Spacing:
    """Consistent spacing system — use multiples of 8 only."""
    XS = 4
    SM = 8
    MD = 16
    LG = 24
    XL = 32
    XXL = 48
    PADDING = 16  # primary padding unit from design spec
    CARD_RADIUS = 14
    BUTTON_RADIUS = 10
    SIDEBAR_WIDTH = 220
    SIDEBAR_COLLAPSED = 72
    MIN_WINDOW_W = 1100
    MIN_WINDOW_H = 700


class Fonts:
    """Clean modern hierarchy. Segoe UI preferred, with safe fallbacks."""
    FAMILY = "Segoe UI"
    FALLBACKS = ("Helvetica", "Arial")

    @classmethod
    def get(cls, size: int = 14, weight: str = "normal") -> tuple:
        """Return a Tk font tuple: (family, size, weight)."""
        return (cls.FAMILY, size, weight)

    # Named styles used across the app
    @classmethod
    def title(cls) -> tuple:
        return cls.get(26, "bold")

    @classmethod
    def subtitle(cls) -> tuple:
        return cls.get(18, "bold")

    @classmethod
    def section(cls) -> tuple:
        return cls.get(15, "bold")

    @classmethod
    def body(cls) -> tuple:
        return cls.get(14, "normal")

    @classmethod
    def body_bold(cls) -> tuple:
        return cls.get(14, "bold")

    @classmethod
    def small(cls) -> tuple:
        return cls.get(12, "normal")

    @classmethod
    def small_bold(cls) -> tuple:
        return cls.get(12, "bold")

    @classmethod
    def caption(cls) -> tuple:
        return cls.get(11, "normal")

    @classmethod
    def stat_number(cls) -> tuple:
        """Large bold number for streak counts, completion %, etc."""
        return cls.get(28, "bold")

    @classmethod
    def nav(cls) -> tuple:
        return cls.get(14, "normal")

    @classmethod
    def nav_active(cls) -> tuple:
        return cls.get(14, "bold")


class Colors:
    """Palette — dark mode primary. Light overrides applied via ThemeConfig."""
    # Surfaces
    BG_BASE = "#0F0F14"
    BG_CARD = "#1A1A22"
    BG_ELEVATED = "#24242E"
    BG_HOVER = "#2A2A36"
    BG_INPUT = "#16161E"
    BG_SIDEBAR = "#12121A"
    BG_MODAL = "#1E1E28"

    # Text
    TEXT_PRIMARY = "#F4F4F8"
    TEXT_SECONDARY = "#A0A0B0"
    TEXT_MUTED = "#6B6B7B"
    TEXT_INVERSE = "#0F0F14"

    # Accent — deep purple (spec recommendation)
    ACCENT = "#7C5CFC"
    ACCENT_HOVER = "#8F74FF"
    ACCENT_DARK = "#5A3FD6"
    ACCENT_SOFT = "#7C5CFC33"

    # Semantic
    SUCCESS = "#2DD4A7"
    SUCCESS_DARK = "#1FA882"
    WARNING = "#F5A524"
    DANGER = "#F0435C"
    DANGER_HOVER = "#FF5A72"
    INFO = "#38BDF8"

    # Category accents (harmonious families)
    CAT_FITNESS = "#2DD4A7"       # green
    CAT_ACADEMICS = "#38BDF8"     # blue
    CAT_PRODUCTIVITY = "#F5A524"  # amber/orange
    CAT_READING = "#A78BFA"       # purple
    CAT_HEALTH = "#22D3EE"        # teal
    CAT_DEFAULT = "#7C5CFC"

    # Streak gradient endpoints (cool → warm as streak grows)
    STREAK_COOL = "#38BDF8"
    STREAK_MID = "#F5A524"
    STREAK_HOT = "#F97316"
    STREAK_FIRE = "#EF4444"

    # Heatmap ramp (0% → 100% completion)
    HEAT_0 = "#1A1A22"
    HEAT_1 = "#2A2450"
    HEAT_2 = "#3D3480"
    HEAT_3 = "#5A3FD6"
    HEAT_4 = "#7C5CFC"
    HEAT_5 = "#2DD4A7"

    # Chart / viz
    CHART_GRID = "#2A2A36"
    CHART_LINE = "#7C5CFC"
    CHART_BAR = "#38BDF8"
    CHART_BAR_ALT = "#2DD4A7"
    CHART_FIGURE_BG = "none"
    CHART_AXES_BG = "none"

    # Priority pills
    PRI_LOW = "#38BDF8"
    PRI_MEDIUM = "#F5A524"
    PRI_HIGH = "#F0435C"

    @classmethod
    def priority_color(cls, priority: str) -> str:
        mapping = {
            "Low": cls.PRI_LOW,
            "Medium": cls.PRI_MEDIUM,
            "High": cls.PRI_HIGH,
        }
        return mapping.get(priority, cls.PRI_MEDIUM)

    @classmethod
    def category_color(cls, category: str | None) -> str:
        if not category:
            return cls.CAT_DEFAULT
        key = str(category).strip().lower()
        mapping = {
            "fitness": cls.CAT_FITNESS,
            "health": cls.CAT_HEALTH,
            "health/sleep": cls.CAT_HEALTH,
            "sleep": cls.CAT_HEALTH,
            "academics": cls.CAT_ACADEMICS,
            "school": cls.CAT_ACADEMICS,
            "productivity": cls.CAT_PRODUCTIVITY,
            "productivity/skills": cls.CAT_PRODUCTIVITY,
            "skills": cls.CAT_PRODUCTIVITY,
            "coding": cls.CAT_PRODUCTIVITY,
            "reading": cls.CAT_READING,
            "learning": cls.CAT_READING,
        }
        return mapping.get(key, cls.CAT_DEFAULT)

    @classmethod
    def streak_color(cls, streak: int) -> str:
        """Warmth scales with streak length — rewards consistency visually."""
        if streak <= 0:
            return cls.TEXT_MUTED
        if streak < 3:
            return cls.STREAK_COOL
        if streak < 7:
            return cls.STREAK_MID
        if streak < 14:
            return cls.STREAK_HOT
        return cls.STREAK_FIRE

    @classmethod
    def heat_color(cls, ratio: float) -> str:
        """Map 0..1 completion ratio to heatmap intensity."""
        try:
            r = max(0.0, min(1.0, float(ratio)))
        except (TypeError, ValueError):
            r = 0.0
        if r <= 0.0:
            return cls.HEAT_0
        if r < 0.2:
            return cls.HEAT_1
        if r < 0.4:
            return cls.HEAT_2
        if r < 0.6:
            return cls.HEAT_3
        if r < 0.85:
            return cls.HEAT_4
        return cls.HEAT_5


class ThemeConfig:
    """Current theme mode holder (dark default)."""
    mode: str = "dark"  # "dark" | "light"

    # Light-mode overrides (applied when mode == "light")
    LIGHT = {
        "BG_BASE": "#F4F4F7",
        "BG_CARD": "#FFFFFF",
        "BG_ELEVATED": "#FFFFFF",
        "BG_HOVER": "#ECECF2",
        "BG_INPUT": "#FFFFFF",
        "BG_SIDEBAR": "#EBEBF2",
        "BG_MODAL": "#FFFFFF",
        "TEXT_PRIMARY": "#14141C",
        "TEXT_SECONDARY": "#4A4A5A",
        "TEXT_MUTED": "#8A8A9A",
        "TEXT_INVERSE": "#FFFFFF",
        "ACCENT": "#6B4CF6",
        "ACCENT_HOVER": "#7C5CFC",
        "ACCENT_DARK": "#5A3FD6",
        "CHART_GRID": "#E2E2EA",
    }


# Snapshot of the original dark palette so mode switching can always revert cleanly
_DARK_SNAPSHOT = {
    k: v for k, v in vars(Colors).items()
    if k.isupper() and isinstance(v, str)
}


def current_theme() -> type:
    """Return the active Colors class (mutated to the current mode)."""
    return Colors


def set_theme_mode(mode: str) -> None:
    """
    Set global theme mode ('dark' or 'light').
    Mutates Colors class attributes in place — frames rebuilt afterwards pick
    up the new palette (all UI files reference Colors.ATTRIBUTE at creation time).
    """
    ThemeConfig.mode = mode if mode in ("dark", "light") else "dark"
    # Always restore dark defaults first...
    for key, value in _DARK_SNAPSHOT.items():
        setattr(Colors, key, value)
    # ...then apply light overrides on top
    if ThemeConfig.mode == "light":
        for key, value in ThemeConfig.LIGHT.items():
            setattr(Colors, key, value)
