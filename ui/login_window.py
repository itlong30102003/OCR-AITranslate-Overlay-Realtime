"""Login Window - User authentication"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox, QCheckBox,
                             QDialog, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from firebase.auth_service import FirebaseAuthService


class LoginWindow(QWidget):
    """Login window for user authentication"""

    login_successful = pyqtSignal(dict)  # Signal emitted when login succeeds

    def __init__(self):
        super().__init__()
        self.auth_service = FirebaseAuthService()
        self.current_view = "welcome"  # welcome, login, register
        self.init_ui()

        # Check if already logged in
        #self.check_existing_session()

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("OCR Translator Pro - Welcome")
        self.setFixedSize(450, 500)

        # Apply dark theme
        self.setStyleSheet(self.get_dark_theme())

        # Main layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(20)
        self.setLayout(self.main_layout)

        # Show welcome view initially
        self.show_welcome_view()

    def show_welcome_view(self):
        """Show welcome screen with login/register buttons"""
        self.current_view = "welcome"
        self.setWindowTitle("OCR Translator Pro - Welcome")

        # Clear existing widgets
        self.clear_layout()

        # Logo/Title
        title = QLabel("AI Overlay Translate")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #ffffff; margin-bottom: 10px;")
        self.main_layout.addWidget(title)

        subtitle = QLabel("Real-time OCR & Translation")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 16px; color: #9ca3af; margin-bottom: 50px;")
        self.main_layout.addWidget(subtitle)

        # Buttons
        login_btn = QPushButton("Login")
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 18px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                min-height: 50px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
        """)
        login_btn.clicked.connect(self.show_login_view)
        self.main_layout.addWidget(login_btn)

        self.main_layout.addSpacing(20)

        register_btn = QPushButton("Create Account")
        register_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #60a5fa;
                border: 2px solid #60a5fa;
                padding: 18px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                min-height: 50px;
            }
            QPushButton:hover {
                background-color: #1f2937;
                border-color: #93c5fd;
                color: #93c5fd;
            }
        """)
        register_btn.clicked.connect(self.show_register_view)
        self.main_layout.addWidget(register_btn)

        self.main_layout.addStretch()

        # Footer
        footer = QLabel("© 2025 OCR Translator Pro")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: #6b7280; font-size: 11px;")
        self.main_layout.addWidget(footer)

    def show_login_view(self):
        """Show login form"""
        self.current_view = "login"
        self.setWindowTitle("OCR Translator Pro - Login")

        # Clear existing widgets
        self.clear_layout()

        # Back button
        back_btn = QPushButton("← Back")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #9ca3af;
                border: none;
                padding: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #ffffff;
            }
        """)
        back_btn.clicked.connect(self.show_welcome_view)
        self.main_layout.addWidget(back_btn)

        # Title
        title = QLabel("Login to your account")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff; margin-bottom: 30px;")
        self.main_layout.addWidget(title)

        # Email input
        email_label = QLabel("Email:")
        email_label.setStyleSheet("color: #e5e7eb; font-size: 13px;")
        self.main_layout.addWidget(email_label)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("your@email.com")
        self.email_input.setStyleSheet("""
            QLineEdit {
                background-color: #1f2937;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 12px;
                color: #ffffff;
                font-size: 14px;
                selection-background-color: #2563eb;
            }
            QLineEdit:focus {
                border: 1px solid #2563eb;
            }
        """)
        self.main_layout.addWidget(self.email_input)

        # Password input
        password_label = QLabel("Password:")
        password_label.setStyleSheet("color: #e5e7eb; font-size: 13px;")
        self.main_layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("••••••••")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: #1f2937;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 12px;
                color: #ffffff;
                font-size: 14px;
                selection-background-color: #2563eb;
            }
            QLineEdit:focus {
                border: 1px solid #2563eb;
            }
        """)
        self.main_layout.addWidget(self.password_input)

        # Remember me checkbox
        self.remember_check = QCheckBox("Remember me")
        self.remember_check.setChecked(True)
        self.remember_check.setStyleSheet("color: #9ca3af; font-size: 13px;")
        self.main_layout.addWidget(self.remember_check)

        self.main_layout.addSpacing(20)

        # Login button
        self.login_btn = QPushButton("Login")
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 14px;
                border-radius: 6px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
        """)
        self.login_btn.clicked.connect(self.handle_login)
        self.main_layout.addWidget(self.login_btn)

        self.main_layout.addStretch()

        # Set focus to email field
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.email_input.setFocus())

    def show_register_view(self):
        """Show register form"""
        self.current_view = "register"
        self.setWindowTitle("OCR Translator Pro - Create Account")

        # Clear existing widgets
        self.clear_layout()

        # Back button
        back_btn = QPushButton("← Back")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #9ca3af;
                border: none;
                padding: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #ffffff;
            }
        """)
        back_btn.clicked.connect(self.show_welcome_view)
        self.main_layout.addWidget(back_btn)

        # Title
        title = QLabel("Create new account")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff; margin-bottom: 30px;")
        self.main_layout.addWidget(title)

        # Email
        email_label = QLabel("Email:")
        email_label.setStyleSheet("color: #e5e7eb; font-size: 13px;")
        self.main_layout.addWidget(email_label)

        self.reg_email_input = QLineEdit()
        self.reg_email_input.setPlaceholderText("your@email.com")
        self.reg_email_input.setStyleSheet("""
            QLineEdit {
                background-color: #1f2937;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 12px;
                color: #ffffff;
                font-size: 14px;
                selection-background-color: #2563eb;
            }
            QLineEdit:focus {
                border: 1px solid #2563eb;
            }
        """)
        self.main_layout.addWidget(self.reg_email_input)

        # Password
        password_label = QLabel("Password (min 6 characters):")
        password_label.setStyleSheet("color: #e5e7eb; font-size: 13px;")
        self.main_layout.addWidget(password_label)

        self.reg_password_input = QLineEdit()
        self.reg_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_password_input.setPlaceholderText("••••••••")
        self.reg_password_input.setStyleSheet("""
            QLineEdit {
                background-color: #1f2937;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 12px;
                color: #ffffff;
                font-size: 14px;
                selection-background-color: #2563eb;
            }
            QLineEdit:focus {
                border: 1px solid #2563eb;
            }
        """)
        self.main_layout.addWidget(self.reg_password_input)

        # Confirm password
        confirm_label = QLabel("Confirm Password:")
        confirm_label.setStyleSheet("color: #e5e7eb; font-size: 13px;")
        self.main_layout.addWidget(confirm_label)

        self.reg_confirm_input = QLineEdit()
        self.reg_confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_confirm_input.setPlaceholderText("••••••••")
        self.reg_confirm_input.setStyleSheet("""
            QLineEdit {
                background-color: #1f2937;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 12px;
                color: #ffffff;
                font-size: 14px;
                selection-background-color: #2563eb;
            }
            QLineEdit:focus {
                border: 1px solid #2563eb;
            }
        """)
        self.main_layout.addWidget(self.reg_confirm_input)

        self.main_layout.addSpacing(20)

        # Register button
        self.register_btn = QPushButton("Create Account")
        self.register_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 14px;
                border-radius: 6px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
        """)
        self.register_btn.clicked.connect(self.handle_register)
        self.main_layout.addWidget(self.register_btn)

        self.main_layout.addStretch()

        # Set focus to email field
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.reg_email_input.setFocus())

    def clear_layout(self):
        """Clear all widgets from main layout"""
        while self.main_layout.count():
            child = self.main_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def get_dark_theme(self):
        """Dark theme stylesheet"""
        return """
        QWidget {
            background-color: #0f1419;
            color: #e5e7eb;
        }
        QLineEdit {
            background-color: #1f2937;
            border: 1px solid #374151;
            border-radius: 6px;
            padding: 12px;
            color: #ffffff;
            font-size: 14px;
            selection-background-color: #2563eb;
        }
        QLineEdit:focus {
            border: 1px solid #2563eb;
        }
        QLabel {
            color: #e5e7eb;
        }
        QCheckBox {
            color: #9ca3af;
        }
        QPushButton {
            color: white;
        }
        """

    def check_existing_session(self):
        """Check if user is already logged in"""
        # Delay session check to allow UI to fully render
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(200, self._do_session_check)

    def _do_session_check(self):
        """Perform actual session check"""
        user = self.auth_service.get_current_user()
        if user:
            print("[Login] Found existing session")
            self.login_successful.emit(user)

    def handle_login(self):
        """Handle login button click"""
        email = self.email_input.text().strip()
        password = self.password_input.text()

        if not email or not password:
            QMessageBox.warning(self, "Login Error", "Please enter email and password")
            return

        try:
            # Disable button during login
            self.login_btn.setEnabled(False)
            self.login_btn.setText("Logging in...")

            user = self.auth_service.login(email, password)

            # Success
            QMessageBox.information(self, "Success", f"Welcome back, {email}!")
            self.login_successful.emit(user)

        except Exception as e:
            QMessageBox.critical(self, "Login Failed", str(e))
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Login")

    def handle_register(self):
        """Handle register button click"""
        email = self.reg_email_input.text().strip()
        password = self.reg_password_input.text()
        confirm_password = self.reg_confirm_input.text()

        # Validation
        if not email or not password:
            QMessageBox.warning(self, "Error", "Please fill all fields")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return

        if len(password) < 6:
            QMessageBox.warning(self, "Error", "Password must be at least 6 characters")
            return

        try:
            # Disable button during registration
            self.register_btn.setEnabled(False)
            self.register_btn.setText("Creating account...")

            self.auth_service.register(email, password)

            # Success
            QMessageBox.information(
                self,
                "Registration Successful",
                "Account created! You can now login."
            )
            # Go back to login view
            self.show_login_view()

        except Exception as e:
            QMessageBox.critical(self, "Registration Failed", str(e))
            self.register_btn.setEnabled(True)
            self.register_btn.setText("Create Account")

    # Removed show_register_dialog - now using show_register_view


# RegisterDialog class removed - now using show_register_view
