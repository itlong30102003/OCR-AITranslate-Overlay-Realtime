"""Main Window - Main application window with tabs"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QStackedWidget, QMessageBox)
from PyQt6.QtCore import Qt
from firebase.auth_service import FirebaseAuthService
from ui.tabs.history_tab import HistoryTab


class MainWindow(QMainWindow):
    """Main application window with sidebar navigation"""

    def __init__(self, user, app_instance):
        super().__init__()
        self.user = user
        self.app = app_instance  # Reference to OCRTranslationApp
        self.auth_service = FirebaseAuthService()
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("AI Overlay Translate")
        self.setMinimumSize(1200, 800)

        # Apply dark theme
        self.setStyleSheet(self.get_dark_theme())

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        # Main layout: Sidebar + Content
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        self.sidebar = self.create_sidebar()
        layout.addWidget(self.sidebar)

        # Content stack (different tabs)
        self.content_stack = QStackedWidget()
        layout.addWidget(self.content_stack)

        # Add tabs
        self.tab_main = self.create_main_tab()
        self.tab_history = HistoryTab(user_id=self.user['localId'])

        self.content_stack.addWidget(self.tab_main)
        self.content_stack.addWidget(self.tab_history)

        # Select first tab
        self.switch_tab(0)

    def create_sidebar(self):
        """Create left sidebar navigation"""
        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sidebar.setObjectName("sidebar")
        sidebar.setStyleSheet("""
            #sidebar {
                background-color: #1a1f2e;
                border-right: 1px solid #2a2f3e;
            }
        """)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(0)

        # App logo/title
        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(20, 0, 20, 20)

        title = QLabel("AI Overlay\nTranslate")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffffff;")
        title_layout.addWidget(title)

        # Status indicator
        status = QLabel("● Online")
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status.setStyleSheet("color: #10b981; font-size: 12px; margin-top: 5px;")
        title_layout.addWidget(status)

        layout.addWidget(title_widget)

        layout.addSpacing(20)

        # Navigation buttons
        self.nav_buttons = []

        btn_main = self.create_nav_button("🏠  Chính", 0)
        btn_history = self.create_nav_button("📜  Lịch sử", 1)

        for btn in [btn_main, btn_history]:
            self.nav_buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # User profile at bottom
        user_widget = QWidget()
        user_widget.setStyleSheet("""
            QWidget {
                background-color: #252a3a;
                border-top: 1px solid #2a2f3e;
            }
        """)
        user_layout = QVBoxLayout(user_widget)
        user_layout.setContentsMargins(15, 15, 15, 15)

        user_email = QLabel(self.user.get('email', 'User'))
        user_email.setStyleSheet("color: #e5e7eb; font-size: 12px; font-weight: bold;")
        user_email.setWordWrap(True)
        user_layout.addWidget(user_email)

        logout_btn = QPushButton("Đăng xuất")
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #374151;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-size: 11px;
                margin-top: 5px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        logout_btn.clicked.connect(self.handle_logout)
        user_layout.addWidget(logout_btn)

        layout.addWidget(user_widget)

        return sidebar

    def create_nav_button(self, text, index):
        """Create navigation button"""
        btn = QPushButton(text)
        btn.setObjectName(f"nav-button-{index}")
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #9ca3af;
                border: none;
                padding: 15px 20px;
                text-align: left;
                font-size: 14px;
                border-left: 3px solid transparent;
            }
            QPushButton:hover {
                background-color: #252a3a;
                color: #ffffff;
            }
        """)
        btn.clicked.connect(lambda: self.switch_tab(index))
        return btn

    def switch_tab(self, index):
        """Switch to tab and highlight nav button"""
        self.content_stack.setCurrentIndex(index)

        # Update button styles
        for i, btn in enumerate(self.nav_buttons):
            if i == index:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #252a3a;
                        color: #ffffff;
                        border: none;
                        padding: 15px 20px;
                        text-align: left;
                        font-size: 14px;
                        border-left: 3px solid #2563eb;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #9ca3af;
                        border: none;
                        padding: 15px 20px;
                        text-align: left;
                        font-size: 14px;
                        border-left: 3px solid transparent;
                    }
                    QPushButton:hover {
                        background-color: #252a3a;
                        color: #ffffff;
                    }
                """)

    def create_main_tab(self):
        """Create main dashboard tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Header
        header = QLabel("Dashboard")
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #ffffff;")
        layout.addWidget(header)

        # Welcome message
        welcome = QLabel(f"Welcome, {self.user.get('email', 'User')}!")
        welcome.setStyleSheet("font-size: 16px; color: #9ca3af;")
        layout.addWidget(welcome)

        layout.addSpacing(30)

        # Start OCR button
        start_btn = QPushButton("🚀 Bắt đầu OCR & Translation")
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 20px;
                border-radius: 10px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        start_btn.clicked.connect(self.start_ocr)
        layout.addWidget(start_btn)

        # Instructions
        instructions = QLabel(
            "Hướng dẫn:\n"
            "1. Click nút trên để bắt đầu\n"
            "2. Chọn vùng màn hình cần dịch\n"
            "3. Xem kết quả dịch trong overlay\n"
            "4. Lịch sử dịch sẽ tự động lưu vào Firebase"
        )
        instructions.setStyleSheet("""
            QLabel {
                background-color: #1f2937;
                color: #e5e7eb;
                padding: 20px;
                border-radius: 10px;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        layout.addWidget(instructions)

        # Overlay mode info
        overlay_mode = self.app.overlay_service.get_overlay_mode()
        mode_info = QLabel(f"Chế độ hiện tại: {overlay_mode.upper()}")
        mode_info.setStyleSheet("color: #60a5fa; font-size: 14px; margin-top: 20px;")
        layout.addWidget(mode_info)

        layout.addStretch()

        return widget

    def start_ocr(self):
        """Start OCR workflow"""
        try:
            # Minimize main window
            self.showMinimized()

            # Start capture
            self.app.start_capture()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start OCR: {e}")

    def handle_logout(self):
        """Handle logout"""
        reply = QMessageBox.question(
            self,
            "Logout",
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Sync any pending changes to Firestore before logout
            if hasattr(self.app, 'sync_service') and self.app.sync_service:
                print("[Logout] Syncing pending changes to Firestore...")
                self.app.sync_service.force_sync_now()
                # Give some time for sync to complete
                import time
                time.sleep(2)
                self.app.sync_service.stop()

            # Clear local history for current user
            if hasattr(self.app, 'local_history') and self.app.local_history and self.user:
                self.app.local_history.clear_user_history(self.user['localId'])
                print(f"[Logout] Cleared local history for user {self.user.get('email')}")

            self.auth_service.logout()
            QMessageBox.information(self, "Logged Out", "You have been logged out successfully")
            self.close()

            # Show login window again
            from ui.login_window import LoginWindow
            self.login_window = LoginWindow()
            self.login_window.show()

    def get_dark_theme(self):
        """Dark theme stylesheet"""
        return """
        QMainWindow {
            background-color: #0f1419;
        }
        QWidget {
            color: #e5e7eb;
        }
        QLabel {
            color: #e5e7eb;
        }
        """
