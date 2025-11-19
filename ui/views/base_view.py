"""Base View - Common styling and utilities for all views"""

from PyQt6.QtWidgets import QWidget, QFrame
from PyQt6.QtCore import pyqtSignal


class BaseView(QWidget):
    """Base class for all view components with common styling"""

    # Signals
    view_changed = pyqtSignal(str)  # Emit view name to switch to

    def __init__(self, parent=None):
        super().__init__(parent)

        # Color scheme - shared across all views
        self.bg_color = "#1a1d2e"
        self.container_color = "#1e2132"
        self.primary_blue = "#3b82f6"
        self.cyan = "#00d4ff"
        self.text_color = "#ffffff"
        self.text_secondary = "#9ca3af"
        self.input_bg = "#2a2d3e"

    def get_input_style(self):
        """Get standard input field stylesheet"""
        return f"""
            QLineEdit {{
                background-color: {self.input_bg};
                border: none;
                border-radius: 10px;
                padding: 12px;
                color: {self.text_color};
                font-size: 14px;
                min-height: 45px;
            }}
            QLineEdit:focus {{
                background-color: #353a4d;
            }}
        """

    def get_label_style(self):
        """Get standard label stylesheet"""
        return f"color: {self.text_secondary}; font-size: 12px;"

    def get_primary_button_style(self):
        """Get primary button stylesheet"""
        return f"""
            QPushButton {{
                background-color: {self.primary_blue};
                color: white;
                border: none;
                padding: 14px;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                min-height: 50px;
            }}
            QPushButton:hover {{
                background-color: #2563eb;
            }}
            QPushButton:pressed {{
                background-color: #1d4ed8;
            }}
        """

    def get_secondary_button_style(self):
        """Get secondary (outlined) button stylesheet"""
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {self.cyan};
                border: 2px solid {self.cyan};
                padding: 18px;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                min-height: 50px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 212, 255, 0.1);
                border-color: {self.cyan};
            }}
        """

    def get_link_button_style(self):
        """Get link button stylesheet"""
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {self.cyan};
                border: none;
                padding: 0px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """

    def get_back_button_style(self):
        """Get back button stylesheet"""
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {self.cyan};
                border: none;
                padding: 5px;
                font-size: 12px;
                text-align: left;
            }}
            QPushButton:hover {{
                color: {self.text_color};
            }}
        """

    def get_container_style(self):
        """Get container frame stylesheet"""
        return f"""
            QFrame {{
                background-color: {self.container_color};
                border: none;
                border-radius: 15px;
            }}
        """

    def create_container(self, margins=(40, 30, 40, 30), spacing=15):
        """Create a standard container frame"""
        container = QFrame()
        container.setStyleSheet(self.get_container_style())
        return container

    def show_status(self, label, message, status_type="error", auto_hide_ms=4000):
        """
        Show status message

        Args:
            label: QLabel to display message in
            message: Message text
            status_type: "error" or "success"
            auto_hide_ms: Milliseconds before auto-hiding (0 = no auto-hide)
        """
        label.setText(message)

        if status_type == "success":
            label.setStyleSheet(f"""
                QLabel {{
                    color: #10b981;
                    font-size: 12px;
                    padding: 4px;
                }}
            """)
        else:  # error
            label.setStyleSheet(f"""
                QLabel {{
                    color: #ef4444;
                    font-size: 12px;
                    padding: 4px;
                }}
            """)

        label.show()

        # Auto-hide after delay
        if auto_hide_ms > 0:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(auto_hide_ms, label.hide)
