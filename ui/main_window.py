"""Main Window - Main application window with header and tabs"""

import socket
import time
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTabWidget, QMessageBox, QApplication, QFrame)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import QSize
from firebase.auth_service import FirebaseAuthService
from ui.tabs.history_tab import HistoryTab
from ui.tabs.main_tab import MainTab
from ui.tabs.settings_tab import SettingsTab
from config import new_theme as theme


class MainWindow(QMainWindow):
    """Main application window with header and tab navigation"""

    def __init__(self, user, app_instance):
        super().__init__()
        self.user = user
        self.app = app_instance
        self.auth_service = FirebaseAuthService()
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("AI Overlay Translate")
        self.setGeometry(100, 100, 1200, 800)

        # Remove window frame for frameless window
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        # Apply dark theme
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {theme.BG_PRIMARY};
            }}
            QWidget {{
                color: {theme.TEXT_PRIMARY};
            }}
        """)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = self._create_header()
        main_layout.addWidget(header)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(theme.get_tab_style())

        # Create tabs
        self.tab_main = MainTab(app_instance=self.app)
        self.tab_settings = SettingsTab(app_instance=self.app)
        self.tab_history = HistoryTab(user_id=self.user['localId'])

        self.tabs.addTab(self.tab_main, "Chính")
        self.tabs.addTab(self.tab_settings, "Cài đặt")
        self.tabs.addTab(self.tab_history, "Lịch sử")

        main_layout.addWidget(self.tabs)

        # Floating toggle button
        self._create_floating_toggle()

        # Make main window draggable
        self.dragging = False
        self.offset = None

        # UI visibility state
        self.ui_visible = True
        self.original_position = None

    def _create_header(self):
        """Create header with logo, status, and window controls"""
        header = QWidget()
        header.setFixedHeight(50)
        header.setStyleSheet(f"""
            background-color: {theme.BG_SECONDARY};
            border-bottom: 1px solid {theme.BORDER_DEFAULT};
        """)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(15, 0, 15, 0)

        # Logo badge
        logo_label = QLabel()
        logo_pixmap = QPixmap("Icons/App.png")
        if not logo_pixmap.isNull():
            # Scale the icon to fit nicely in the header
            logo_pixmap = logo_pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
        else:
            # Fallback to text if image not found
            logo_label.setText("AI")
        logo_label.setStyleSheet(f"""
            padding: 5px;
            border-radius: 5px;
        """)

        # Title
        title = QLabel("AI Overlay Translate")
        title.setStyleSheet(f"font-weight: bold; font-size: 20px; margin-left: 10px; color: {theme.TEXT_PRIMARY};")

        # Status badge (network latency indicator)
        # Status badge (network latency indicator)
        self.status_badge = QFrame()
        self.status_badge.setObjectName("status_badge")
        self.status_badge.setFixedHeight(24)
        self.status_badge.setStyleSheet("""
            #status_badge {
                background-color: #7A6969;
                border-radius: 12px;
            }
        """)
        
        badge_layout = QHBoxLayout(self.status_badge)
        badge_layout.setContentsMargins(12, 0, 12, 0)
        badge_layout.setSpacing(8)
        
        # Status dot (pure geometric shape)
        self.status_dot = QFrame()
        self.status_dot.setFixedSize(10, 10)
        # Default gray
        self.status_dot.setStyleSheet(f"background-color: #9CA3AF; border-radius: 5px; border: none;")
        
        # Status text
        self.status_text = QLabel("--ms")
        self.status_text.setStyleSheet("color: white; font-weight: bold; font-size: 12px; border: none; background: transparent;")
        
        badge_layout.addWidget(self.status_dot)
        badge_layout.addWidget(self.status_text)
        
        # Network ping timer
        self.ping_timer = QTimer()
        self.ping_timer.timeout.connect(self._check_network_latency)
        self.ping_timer.start(5000)  # Check every 5 seconds
        self._check_network_latency()  # Initial check

        layout.addWidget(logo_label)
        layout.addWidget(title)
        layout.addWidget(self.status_badge)
        layout.addStretch()

        # User email
        user_email = QLabel(self.user.get('email', 'User'))
        user_email.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; font-size: 12px; margin-right: 15px;")
        layout.addWidget(user_email)

        # Logout button
        logout_btn = QPushButton("Đăng xuất")
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.BG_TERTIARY};
                color: {theme.TEXT_PRIMARY};
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {theme.ERROR};
            }}
        """)
        logout_btn.clicked.connect(self.handle_logout)
        layout.addWidget(logout_btn)

        # Window controls
        min_btn = QPushButton("−")
        max_btn = QPushButton("□")
        close_btn = QPushButton("×")

        for btn in [min_btn, max_btn, close_btn]:
            btn.setFixedSize(35, 35)
            btn.setStyleSheet(theme.get_window_button_style())

        close_btn.setStyleSheet(theme.get_close_button_style())

        min_btn.clicked.connect(self.showMinimized)
        max_btn.clicked.connect(self._toggle_maximize)
        close_btn.clicked.connect(self.close)

        layout.addWidget(min_btn)
        layout.addWidget(max_btn)
        layout.addWidget(close_btn)

        return header

    def _create_floating_toggle(self):
        """Create floating toggle button"""
        self.toggle_ui_btn = QPushButton()
        self.toggle_ui_btn.setFixedSize(50, 50)

        # Set icon
        icon_pixmap = QPixmap("Icons/App.png")
        if not icon_pixmap.isNull():
            self.toggle_ui_btn.setIcon(QIcon(icon_pixmap))
            self.toggle_ui_btn.setIconSize(QSize(50, 50))

        self.toggle_ui_btn.clicked.connect(self._toggle_ui_visibility)
        self.toggle_ui_btn.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.toggle_ui_btn.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Position in bottom-right corner
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        self.toggle_ui_btn.move(screen_geometry.width() - 50, screen_geometry.height() - 120)
        self.toggle_ui_btn.show()
        self.toggle_ui_btn.raise_()

        # Make toggle button draggable
        self.toggle_dragging = False
        self.toggle_offset = None
        self.toggle_ui_btn.mousePressEvent = self._toggle_mouse_press
        self.toggle_ui_btn.mouseMoveEvent = self._toggle_mouse_move
        self.toggle_ui_btn.mouseReleaseEvent = self._toggle_mouse_release

    def _toggle_maximize(self):
        """Toggle maximize window"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def handle_logout(self):
        """Handle logout"""
        reply = QMessageBox.question(
            self,
            "Đăng xuất",
            "Bạn có chắc muốn đăng xuất không?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Sync before logout
            if hasattr(self.app, 'sync_service') and self.app.sync_service:
                self.app.sync_service.force_sync_now()
                import time
                time.sleep(2)

            # Clear local history
            if hasattr(self.app, 'local_history') and self.app.local_history and self.user:
                self.app.local_history.clear_user_history(self.user['localId'])

            self.auth_service.logout()
            QMessageBox.information(self, "Đăng xuất", "Đăng xuất thành công!")
            self.close()

            # Show login window
            from ui.login_window import LoginWindow
            self.login_window = LoginWindow()
            self.login_window.show()

    def toggle_visibility(self):
        """Toggle main window visibility"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

    def _toggle_ui_visibility(self):
        """Toggle UI widget visibility"""
        if self.ui_visible:
            self.original_position = self.pos()
            self.hide()
            self.ui_visible = False
        else:
            self.show()
            self.raise_()
            self.activateWindow()
            if self.original_position:
                self.move(self.original_position)
            self.ui_visible = True

    def mousePressEvent(self, event):
        """Handle mouse press for dragging main window"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging main window"""
        if self.dragging and self.offset:
            self.move(self.pos() + event.pos() - self.offset)

    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.offset = None

    def _toggle_mouse_press(self, event):
        """Handle mouse press for toggle button"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_drag_start_pos = event.pos()
            self.toggle_dragging = False
            self.toggle_offset = event.pos()

    def _toggle_mouse_move(self, event):
        """Handle mouse move for toggle button"""
        if not self.toggle_dragging:
            if hasattr(self, 'toggle_drag_start_pos'):
                dx = abs(event.pos().x() - self.toggle_drag_start_pos.x())
                dy = abs(event.pos().y() - self.toggle_drag_start_pos.y())
                if dx > 5 or dy > 5:
                    self.toggle_dragging = True

        if self.toggle_dragging and self.toggle_offset:
            self.toggle_ui_btn.move(self.toggle_ui_btn.pos() + event.pos() - self.toggle_offset)

    def _toggle_mouse_release(self, event):
        """Handle mouse release for toggle button"""
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.toggle_dragging:
                self._toggle_ui_visibility()
            self.toggle_dragging = False
            self.toggle_offset = None
            if hasattr(self, 'toggle_drag_start_pos'):
                delattr(self, 'toggle_drag_start_pos')

    def _check_network_latency(self):
        """Check network latency by pinging Google DNS"""
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect(("8.8.8.8", 53))
            sock.close()
            latency_ms = int((time.time() - start_time) * 1000)
            self._update_status_badge_style(True, latency_ms)
        except (socket.timeout, socket.error, OSError):
            self._update_status_badge_style(False, 0)

    def _update_status_badge_style(self, is_online: bool, latency_ms: int):
        """Update status badge appearance based on network status"""
        if is_online:
            dot_color = "#22C55E"  # Green
            display_text = f"{latency_ms}ms"
        else:
            dot_color = "#EF4444"  # Red
            display_text = "Offline"
            
        # Update dot color
        self.status_dot.setStyleSheet(f"background-color: {dot_color}; border-radius: 5px; border: none;")
        
        # Update text
        self.status_text.setText(display_text)