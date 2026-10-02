"""Theme and design system constants for Momentum.

Defines the single source of truth for colors, fonts, dimensions,
and layout padding used across all UI frames and widgets.
"""

# App Identity
APP_NAME = "Momentum"
APP_VERSION = "1.0.0"
APP_SUBTITLE = "Personal Consistency & Productivity Tracker"

# Window defaults
WINDOW_MIN_WIDTH = 1080
WINDOW_MIN_HEIGHT = 680
WINDOW_DEFAULT_WIDTH = 1240
WINDOW_DEFAULT_HEIGHT = 780

# Dark Theme Color Palette
COLOR_BG_BASE = "#0F0F14"        # Deep near-black background
COLOR_BG_SIDEBAR = "#14141C"     # Slightly lighter navigation layer
COLOR_BG_CARD = "#1A1A24"        # Elevated card surface
COLOR_BG_CARD_HOVER = "#242432"  # Hover state for interactive cards
COLOR_BG_INPUT = "#1E1E2A"       # Input field background
COLOR_BORDER = "#2A2A3A"         # Subtle card and divider border

# Text Palette
COLOR_TEXT_PRIMARY = "#F8FAFC"   # Bright crisp text for headers & main content
COLOR_TEXT_SECONDARY = "#94A3B8" # Subtle text for subheaders & metadata
COLOR_TEXT_MUTED = "#64748B"     # Muted text for captions and empty hints

# Brand & System Accents
COLOR_ACCENT = "#7C5CFC"         # Modern vibrant violet/purple
COLOR_ACCENT_HOVER = "#6A48F0"   # Hover state for primary buttons
COLOR_ACCENT_LIGHT = "#A78BFA"   # Lighter shade for subtle highlights

# State Colors
COLOR_SUCCESS = "#10B981"        # Emerald green
COLOR_WARNING = "#F59E0B"        # Amber
COLOR_DANGER = "#EF4444"         # Red
COLOR_DANGER_HOVER = "#DC2626"   # Darker red for delete hover

# Category Palette Defaults
CATEGORY_COLORS = {
    "Fitness": "#10B981",          # Green
    "Academics": "#3B82F6",        # Blue
    "Productivity": "#F59E0B",     # Amber/Orange
    "Reading": "#8B5CF6",          # Violet
    "Health": "#06B6D4",           # Cyan/Teal
    "Personal": "#EC4899",         # Pink
}

TRACK_ICONS = ["🏋️", "📚", "💻", "📖", "💧", "😴", "🎯", "🧘", "🎨", "✍️", "⚡", "🌟"]

TRACK_PALETTE = [
    "#10B981", "#3B82F6", "#F59E0B", "#8B5CF6",
    "#06B6D4", "#EC4899", "#F97316", "#14B8A6"
]

# Spacing System
PAD_XS = 4
PAD_SM = 8
PAD_MD = 16
PAD_LG = 24
PAD_XL = 32

# Corner Radii
CORNER_SM = 8
CORNER_MD = 12
CORNER_LG = 16

# Typography Specifications
FONT_FAMILY = "Segoe UI"

FONT_DISPLAY_LARGE = (FONT_FAMILY, 28, "bold")
FONT_TITLE = (FONT_FAMILY, 20, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 15, "bold")
FONT_SECTION_HEADER = (FONT_FAMILY, 13, "bold")
FONT_BODY_BOLD = (FONT_FAMILY, 12, "bold")
FONT_BODY = (FONT_FAMILY, 12)
FONT_CAPTION = (FONT_FAMILY, 10)
FONT_STAT_VALUE = (FONT_FAMILY, 24, "bold")
FONT_STAT_LABEL = (FONT_FAMILY, 11)
