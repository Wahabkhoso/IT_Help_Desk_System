"""
theme.py
Central place for colors, fonts, and spacing so the whole app looks consistent
and professional rather than default-Tkinter grey.
"""

# Color palette (a clean, modern "IT ticketing" blue/slate palette)
PRIMARY = "#1E3A5F"        # deep navy blue - sidebar / headers
PRIMARY_DARK = "#142B47"
ACCENT = "#2E86AB"         # bright blue - buttons/links
ACCENT_HOVER = "#256E8A"
SUCCESS = "#2E8B57"
WARNING = "#E1A100"
DANGER = "#C0392B"
CRITICAL_BG = "#FDEDEC"
HIGH_BG = "#FEF5E7"

BG_LIGHT = "#F4F6F8"
CARD_BG = "#FFFFFF"
BORDER = "#D9DEE4"
TEXT_DARK = "#1F2A37"
TEXT_MUTED = "#6B7280"
SIDEBAR_TEXT = "#E8EEF5"
SIDEBAR_HOVER = "#2A4C73"

FONT_FAMILY = "Segoe UI"
FONT_TITLE = (FONT_FAMILY, 20, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 12, "bold")
FONT_BODY = (FONT_FAMILY, 10)
FONT_BODY_BOLD = (FONT_FAMILY, 10, "bold")
FONT_SMALL = (FONT_FAMILY, 9)
FONT_CARD_NUMBER = (FONT_FAMILY, 26, "bold")
FONT_SIDEBAR = (FONT_FAMILY, 11)

PRIORITY_COLORS = {
    "Low": "#2E8B57",
    "Medium": "#2E86AB",
    "High": "#E1A100",
    "Critical": "#C0392B",
}

STATUS_COLORS = {
    "New": "#6B7280",
    "Assigned": "#2E86AB",
    "In Progress": "#E1A100",
    "Resolved": "#2E8B57",
    "Closed": "#4B5563",
    "Reopened": "#C0392B",
}
