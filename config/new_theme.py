"""New Theme - Modern dark theme color constants"""

# Main backgrounds
BG_PRIMARY = "#0f172a"      # Darkest background (main area)
BG_SECONDARY = "#1e293b"    # Lighter background (panels, cards)
BG_TERTIARY = "#334155"     # Even lighter (hover states)

# Accent colors
ACCENT_PRIMARY = "#6366f1"  # Indigo (primary buttons, active states)
ACCENT_SECONDARY = "#818cf8"  # Lighter indigo (hover)
ACCENT_PURPLE = "#a855f7"   # Purple (GPU metrics)

# Status colors
SUCCESS = "#16a34a"         # Green
WARNING = "#f59e0b"         # Amber
ERROR = "#dc2626"           # Red
INFO = "#3b82f6"            # Blue

# Text colors
TEXT_PRIMARY = "#e2e8f0"    # Main text
TEXT_SECONDARY = "#94a3b8"  # Muted text
TEXT_MUTED = "#64748b"      # Very muted

# Border colors
BORDER_DEFAULT = "#334155"
BORDER_HOVER = "#6366f1"

# Panel widths
LEFT_PANEL_WIDTH = 400

# Component styles
def get_header_style():
    """Header bar style"""
    return f"""
        QWidget {{
            background-color: {BG_SECONDARY};
            border-bottom: 1px solid {BORDER_DEFAULT};
        }}
    """

def get_tab_style():
    """Tab widget style"""
    return f"""
        QTabWidget::pane {{
            border: none;
            background-color: {BG_PRIMARY};
        }}
        QTabBar::tab {{
            background-color: {BG_SECONDARY};
            color: {TEXT_SECONDARY};
            padding: 12px 20px;
            border: none;
            border-bottom: 2px solid transparent;
        }}
        QTabBar::tab:selected {{
            color: {ACCENT_SECONDARY};
            border-bottom: 2px solid {ACCENT_PRIMARY};
        }}
        QTabBar::tab:hover {{
            color: {TEXT_PRIMARY};
        }}
    """

def get_group_box_style():
    """GroupBox style for sections"""
    return f"""
        QGroupBox {{
            color: {TEXT_PRIMARY};
            font-weight: bold;
            font-size: 14px;
            border: none;
            margin-top: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 0px;
            padding: 0 0 10px 0;
        }}
    """

def get_combo_box_style():
    """ComboBox style"""
    return f"""
        QComboBox {{
            background-color: {BG_SECONDARY};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER_DEFAULT};
            border-radius: 5px;
            padding: 8px 12px;
            font-size: 13px;
        }}
        QComboBox:hover {{
            border: 1px solid {ACCENT_PRIMARY};
        }}
        QComboBox::drop-down {{
            border: none;
        }}
        QComboBox QAbstractItemView {{
            background-color: {BG_SECONDARY};
            color: {TEXT_PRIMARY};
            selection-background-color: {ACCENT_PRIMARY};
            border: 1px solid {BORDER_DEFAULT};
        }}
    """

def get_progress_bar_style(color: str):
    """Progress bar style with custom color"""
    return f"""
        QProgressBar {{
            background-color: {BORDER_DEFAULT};
            border: none;
            border-radius: 4px;
        }}
        QProgressBar::chunk {{
            background-color: {color};
            border-radius: 4px;
        }}
    """

def get_frame_style():
    """Frame/card style"""
    return f"""
        QFrame {{
            background-color: {BG_SECONDARY};
            border-radius: 6px;
            padding: 12px;
        }}
        QFrame:hover {{
            background-color: {BG_TERTIARY};
        }}
    """

def get_scroll_area_style():
    """Scroll area style"""
    return f"""
        QScrollArea {{
            border: none;
            background-color: transparent;
        }}
    """

def get_window_button_style():
    """Window control button style (min/max/close)"""
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {TEXT_SECONDARY};
            border: none;
            font-size: 18px;
        }}
        QPushButton:hover {{
            background-color: {BG_TERTIARY};
            color: white;
        }}
    """

def get_close_button_style():
    """Close button style (red on hover)"""
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {TEXT_SECONDARY};
            border: none;
            font-size: 18px;
        }}
        QPushButton:hover {{
            background-color: {ERROR};
            color: white;
        }}
    """
