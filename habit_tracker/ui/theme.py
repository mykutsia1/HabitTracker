"""Modern dark theme stylesheet and design tokens for PyQt6."""

# Design Tokens
BG_BASE = "#0D0F17"          # Darkest background
BG_SURFACE = "#151824"       # Card / container background
BG_SURFACE_HOVER = "#1D2132" # Card hover background
BG_ELEVATED = "#23283B"      # Dropdowns, dialogs, inputs
BORDER_COLOR = "#2A3047"     # Subtle borders
BORDER_FOCUS = "#6366F1"     # Focus highlight

TEXT_PRIMARY = "#F8FAFC"     # Primary text
TEXT_SECONDARY = "#94A3B8"   # Secondary / subtext
TEXT_MUTED = "#64748B"       # Disabled / muted text

ACCENT_PRIMARY = "#6366F1"   # Indigo
ACCENT_HOVER = "#4F46E5"
ACCENT_LIGHT = "#818CF8"

SUCCESS_EMERALD = "#10B981"  # Emerald completed
SUCCESS_HOVER = "#059669"
SUCCESS_BG = "#064E3B"

DANGER_RED = "#EF4444"       # Delete / error
WARNING_AMBER = "#F59E0B"    # Streaks / warnings

HEATMAP_COLORS = [
    "#1A1E2E",  # 0: Empty / None
    "#064E3B",  # 1: Low (1-33%)
    "#047857",  # 2: Medium (34-66%)
    "#059669",  # 3: High (67-99%)
    "#10B981",  # 4: Max (100%)
]

PRESET_COLORS = [
    "#6366F1",  # Indigo
    "#3B82F6",  # Blue
    "#0EA5E9",  # Sky
    "#10B981",  # Emerald
    "#84CC16",  # Lime
    "#F59E0B",  # Amber
    "#F97316",  # Orange
    "#EF4444",  # Red
    "#EC4899",  # Pink
    "#8B5CF6",  # Violet
]

DARK_THEME_QSS = f"""
QMainWindow {{
    background-color: {BG_BASE};
}}

QWidget {{
    background-color: transparent;
    color: {TEXT_PRIMARY};
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Ubuntu, sans-serif;
    font-size: 13px;
}}

/* Sidebar & Navigation */
#sidebar {{
    background-color: {BG_SURFACE};
    border-right: 1px solid {BORDER_COLOR};
}}

#sidebar QPushButton {{
    text-align: left;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    color: {TEXT_SECONDARY};
    background-color: transparent;
    border: none;
}}

#sidebar QPushButton:hover {{
    background-color: {BG_SURFACE_HOVER};
    color: {TEXT_PRIMARY};
}}

#sidebar QPushButton:checked {{
    background-color: {ACCENT_PRIMARY};
    color: #FFFFFF;
    font-weight: 600;
}}

/* Cards & Surfaces */
QFrame.Card {{
    background-color: {BG_SURFACE};
    border: 1px solid {BORDER_COLOR};
    border-radius: 12px;
}}

QFrame.Card:hover {{
    border-color: #374151;
}}

/* Inputs & Forms */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDateEdit, QComboBox {{
    background-color: {BG_ELEVATED};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 8px 12px;
    color: {TEXT_PRIMARY};
    selection-background-color: {ACCENT_PRIMARY};
}}

QLineEdit:focus, QTextEdit:focus, QDateEdit:focus, QComboBox:focus {{
    border: 1px solid {BORDER_FOCUS};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox QAbstractItemView {{
    background-color: {BG_ELEVATED};
    border: 1px solid {BORDER_COLOR};
    selection-background-color: {ACCENT_PRIMARY};
    selection-color: #FFFFFF;
    padding: 4px;
    border-radius: 6px;
}}

/* Standard Buttons */
QPushButton.PrimaryBtn {{
    background-color: {ACCENT_PRIMARY};
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 9px 18px;
    font-weight: 600;
}}

QPushButton.PrimaryBtn:hover {{
    background-color: {ACCENT_HOVER};
}}

QPushButton.PrimaryBtn:pressed {{
    background-color: #3730A3;
}}

QPushButton.SecondaryBtn {{
    background-color: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 500;
}}

QPushButton.SecondaryBtn:hover {{
    background-color: {BG_SURFACE_HOVER};
    border-color: #475569;
}}

QPushButton.DangerBtn {{
    background-color: rgba(239, 68, 68, 0.15);
    color: {DANGER_RED};
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: 500;
}}

QPushButton.DangerBtn:hover {{
    background-color: {DANGER_RED};
    color: #FFFFFF;
}}

/* Progress Bar */
QProgressBar {{
    background-color: {BG_ELEVATED};
    border: none;
    border-radius: 5px;
    height: 10px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {SUCCESS_EMERALD};
    border-radius: 5px;
}}

/* Checkboxes */
QCheckBox {{
    spacing: 8px;
    color: {TEXT_PRIMARY};
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid {BORDER_COLOR};
    background-color: {BG_ELEVATED};
}}

QCheckBox::indicator:hover {{
    border-color: {ACCENT_PRIMARY};
}}

QCheckBox::indicator:checked {{
    background-color: {SUCCESS_EMERALD};
    border-color: {SUCCESS_EMERALD};
}}

/* Scrollbars */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: #334155;
    min-height: 24px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: #475569;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* Dialogs */
QDialog {{
    background-color: {BG_SURFACE};
    border: 1px solid {BORDER_COLOR};
    border-radius: 12px;
}}

/* Tooltips */
QToolTip {{
    background-color: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 12px;
}}
"""
