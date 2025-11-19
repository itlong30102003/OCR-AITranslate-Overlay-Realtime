"""Floating Control Button - Always on-top control panel"""

from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class FloatingControl(QWidget):
    """Floating control panel with always-on-top buttons"""

    # Signals
    toggle_main_window = pyqtSignal()
    stop_monitoring = pyqtSignal()
    select_new_region = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window_visible = True
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        # Window flags - always on top, frameless
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )

        # Set size and style
        self.setFixedSize(120, 180)
        self.setStyleSheet("""
            QWidget {
                background-color: #1f2937;
                border: 2px solid #3b82f6;
                border-radius: 10px;
            }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
            QLabel {
                color: #e5e7eb;
                font-size: 10px;
                font-weight: bold;
            }
        """)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Title
        title = QLabel("Control")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Show Main UI button
        self.show_ui_btn = QPushButton("🏠 Show Main UI")
        self.show_ui_btn.clicked.connect(self._on_show_main_ui)
        layout.addWidget(self.show_ui_btn)

        # Draggable
        self.dragging = False
        self.offset = None

    def _on_show_main_ui(self):
        """Toggle main window visibility"""
        self.toggle_main_window.emit()

    def _on_stop_monitoring(self):
        """Stop monitoring"""
        self.stop_monitoring.emit()

    def _on_select_new_region(self):
        """Select new region"""
        self.select_new_region.emit()

    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if self.dragging and self.offset:
            self.move(self.pos() + event.pos() - self.offset)

    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.offset = None

    def set_monitoring_state(self, is_monitoring: bool):
        """Update button states based on monitoring state"""
        # Show floating control when monitoring starts
        if is_monitoring:
            self.show()
            self.raise_()
            self.activateWindow()
        else:
            self.hide()
