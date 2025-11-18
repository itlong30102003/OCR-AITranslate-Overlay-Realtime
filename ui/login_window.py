"""Login Window - User authentication"""

import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox, QCheckBox,
                             QDialog, QApplication, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from firebase.auth_service import FirebaseAuthService


class LoginWindow(QWidget):
    """Login window for user authentication"""

    login_successful = pyqtSignal(dict)  # Signal emitted when login succeeds

    def __init__(self):
        super().__init__()
        self.auth_service = FirebaseAuthService()
        self.current_view = "welcome"  # welcome, login, register

        # For dragging window
        self.drag_position = None

        self.init_ui()

        # Check if already logged in
        #self.check_existing_session()

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("OCR Translator Pro - Welcome")
        self.setFixedSize(450, 680)

        # Remove window frame and title bar
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        # Color scheme
        self.bg_color = "#1a1d2e"
        self.container_color = "#1e2132"
        self.primary_blue = "#3b82f6"
        self.cyan = "#00d4ff"
        self.text_color = "#ffffff"
        self.text_secondary = "#9ca3af"
        self.input_bg = "#2a2d3e"

        # Apply dark theme
        self.setStyleSheet(self.get_dark_theme())

        # Main layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setLayout(self.main_layout)

        # Show welcome view initially
        self.show_welcome_view()

    def show_welcome_view(self):
        """Show welcome screen with login/register buttons"""
        self.current_view = "welcome"
        self.setWindowTitle("OCR Translator Pro - Welcome")

        # Clear existing widgets
        self.clear_layout()

        # Container frame
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {self.container_color};
                border: none;
                border-radius: 15px;
            }}
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(30, 30, 30, 30)
        container_layout.setSpacing(15)

        # App Icon Logo
        logo_container = QFrame()
        logo_container.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {self.primary_blue}, stop:1 #2563eb);
                border-radius: 22px;
            }}
        """)
        logo_container.setFixedSize(90, 90)

        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon from file
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("background: transparent;")

        # Load icon from file
        icon_path = "Icons/App.png"
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(70, 70, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(scaled_pixmap)
        else:
            # Fallback to emoji if image not found
            icon_label.setText("📱")
            icon_label.setStyleSheet("font-size: 45px; background: transparent;")

        logo_layout.addWidget(icon_label)

        # Center logo container
        logo_center_layout = QHBoxLayout()
        logo_center_layout.addStretch()
        logo_center_layout.addWidget(logo_container)
        logo_center_layout.addStretch()

        container_layout.addLayout(logo_center_layout)

        # App name below logo
        app_name = QLabel("OCR Translator Pro")
        app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_name.setStyleSheet(f"""
            font-size: 20px;    
            font-weight: bold;
            color: {self.text_color};
            margin-top: 12px;
        """)
        container_layout.addWidget(app_name)

        # Subtitle
        subtitle = QLabel("Chào mừng bạn đến với OCR Translator Pro.\nVui lòng chọn một tùy chọn để tiếp tục.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"font-size: 13px; color: {self.text_secondary}; margin-top: 8px; margin-bottom: 12px;")
        subtitle.setWordWrap(True)
        container_layout.addWidget(subtitle)

        container_layout.addSpacing(12)

        # Login button
        login_btn = QPushButton("🔐 ĐĂNG NHẬP")
        login_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.primary_blue};
                color: white;
                border: none;
                padding: 18px;
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
        """)
        login_btn.clicked.connect(self.show_login_view)
        container_layout.addWidget(login_btn)

        # Register button
        register_btn = QPushButton("📝 ĐĂNG KÝ")
        register_btn.setStyleSheet(f"""
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
        """)
        register_btn.clicked.connect(self.show_register_view)
        container_layout.addWidget(register_btn)

        container_layout.addSpacing(8)

        # Footer section
        footer_frame = QFrame()
        footer_frame.setStyleSheet("background-color: transparent;")
        footer_layout = QVBoxLayout(footer_frame)
        footer_layout.setContentsMargins(0, 10, 0, 0)
        footer_layout.setSpacing(8)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: {self.primary_blue}; max-height: 1px;")
        footer_layout.addWidget(separator)

        footer_layout.addSpacing(5)

        # Donate title
        donate_title = QLabel("💝 Donate & Liên hệ")
        donate_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        donate_title.setStyleSheet(f"""
            font-size: 15px;
            font-weight: bold;
            color: {self.primary_blue};
            padding: 5px 0px;
        """)
        footer_layout.addWidget(donate_title)

        # Contact info - each line separate for better formatting
        phone_label = QLabel("📞 SĐT: 0123 456 789")
        phone_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        phone_label.setStyleSheet(f"font-size: 13px; color: {self.text_secondary}; padding: 2px 0px;")
        footer_layout.addWidget(phone_label)

        bank_label = QLabel("🏦 Ngân hàng: Vietcombank")
        bank_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bank_label.setStyleSheet(f"font-size: 13px; color: {self.text_secondary}; padding: 2px 0px;")
        footer_layout.addWidget(bank_label)

        account_label = QLabel("STK: 1234567890 - NGUYEN VAN A")
        account_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        account_label.setStyleSheet(f"font-size: 13px; color: {self.text_secondary}; padding: 2px 0px;")
        footer_layout.addWidget(account_label)

        container_layout.addWidget(footer_frame)
        container_layout.addStretch()


        # Horizontal centering
        h_layout = QHBoxLayout()
        h_layout.addSpacing(0)
        h_layout.addWidget(container)
        h_layout.addSpacing(0)

        # Add spacing at top for even padding
        self.main_layout.addSpacing(0)
        self.main_layout.addLayout(h_layout)
        self.main_layout.addSpacing(0)

    def show_login_view(self):
        """Show login form"""
        self.current_view = "login"
        self.setWindowTitle("OCR Translator Pro - Login")

        # Clear existing widgets
        self.clear_layout()

        # Container frame
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {self.container_color};
                border: none;
                border-radius: 15px;
            }}
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(40, 30, 40, 30)
        container_layout.setSpacing(15)

        # Back button
        back_btn = QPushButton("← Quay lại")
        back_btn.setStyleSheet(f"""
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
        """)
        back_btn.clicked.connect(self.show_welcome_view)
        container_layout.addWidget(back_btn)

        container_layout.addSpacing(10)

        # Title
        title = QLabel("🔐 Đăng Nhập")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {self.text_color}; margin-bottom: 10px;")
        container_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Đăng nhập vào tài khoản của bạn")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"font-size: 14px; color: {self.text_secondary}; margin-bottom: 20px;")
        container_layout.addWidget(subtitle)

        container_layout.addSpacing(20)

        # Form frame
        form_frame = QFrame()
        form_frame.setStyleSheet("background-color: transparent;")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(15)

        # Username/Email label
        username_label = QLabel("Tên đăng nhập hoặc Email")
        username_label.setStyleSheet(f"color: {self.text_secondary}; font-size: 12px;")
        form_layout.addWidget(username_label)

        # Username/Email input
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Nhập tên đăng nhập hoặc email")
        self.email_input.setStyleSheet(f"""
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
        """)
        form_layout.addWidget(self.email_input)

        form_layout.addSpacing(5)

        # Password label
        password_label = QLabel("Mật khẩu")
        password_label.setStyleSheet(f"color: {self.text_secondary}; font-size: 12px;")
        form_layout.addWidget(password_label)

        # Password input
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Nhập mật khẩu")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(f"""
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
        """)
        form_layout.addWidget(self.password_input)

        # Forgot password link
        forgot_btn = QPushButton("Quên mật khẩu?")
        forgot_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.cyan};
                border: none;
                padding: 5px;
                font-size: 11px;
                text-align: right;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """)
        forgot_btn.clicked.connect(self.forgot_password)
        form_layout.addWidget(forgot_btn, alignment=Qt.AlignmentFlag.AlignRight)

        form_layout.addSpacing(10)

        # Login button
        self.login_btn = QPushButton("ĐĂNG NHẬP")
        self.login_btn.setStyleSheet(f"""
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
        """)
        self.login_btn.clicked.connect(self.handle_login)
        form_layout.addWidget(self.login_btn)

        form_layout.addSpacing(10)

        # Divider with "HOẶC"
        divider_layout = QHBoxLayout()
        divider_layout.setSpacing(10)

        divider_left = QFrame()
        divider_left.setFrameShape(QFrame.Shape.HLine)
        divider_left.setStyleSheet(f"background-color: {self.text_secondary}; max-height: 1px;")
        divider_layout.addWidget(divider_left)

        divider_text = QLabel("HOẶC")
        divider_text.setStyleSheet(f"color: {self.text_secondary}; font-size: 10px;")
        divider_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        divider_layout.addWidget(divider_text)

        divider_right = QFrame()
        divider_right.setFrameShape(QFrame.Shape.HLine)
        divider_right.setStyleSheet(f"background-color: {self.text_secondary}; max-height: 1px;")
        divider_layout.addWidget(divider_right)

        form_layout.addLayout(divider_layout)

        # Register link
        register_layout = QHBoxLayout()
        register_layout.setSpacing(5)

        register_text = QLabel("Chưa có tài khoản?")
        register_text.setStyleSheet(f"color: {self.text_secondary}; font-size: 12px;")
        register_layout.addWidget(register_text)

        register_link = QPushButton("Đăng ký ngay")
        register_link.setStyleSheet(f"""
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
        """)
        register_link.clicked.connect(self.show_register_view)
        register_layout.addWidget(register_link)

        register_layout.addStretch()

        form_layout.addLayout(register_layout)

        container_layout.addWidget(form_frame)
        container_layout.addStretch()

        # Add container to main layout with margins
        self.main_layout.addSpacing(30)

        h_layout = QHBoxLayout()
        h_layout.addSpacing(25)
        h_layout.addWidget(container)
        h_layout.addSpacing(25)

        self.main_layout.addLayout(h_layout)
        self.main_layout.addSpacing(30)

        # Set focus to email field
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.email_input.setFocus())

    def show_register_view(self):
        """Show register form"""
        self.current_view = "register"
        self.setWindowTitle("OCR Translator Pro - Create Account")

        # Clear existing widgets
        self.clear_layout()

        # Container frame
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {self.container_color};
                border: none;
                border-radius: 15px;
            }}
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(40, 30, 40, 30)
        container_layout.setSpacing(15)

        # Back button
        back_btn = QPushButton("← Quay lại")
        back_btn.setStyleSheet(f"""
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
        """)
        back_btn.clicked.connect(self.show_welcome_view)
        container_layout.addWidget(back_btn)

        container_layout.addSpacing(5)

        # Title
        title = QLabel("📝 Đăng Ký")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {self.text_color}; margin-bottom: 10px;")
        container_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Tạo tài khoản mới")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"font-size: 14px; color: {self.text_secondary}; margin-bottom: 15px;")
        container_layout.addWidget(subtitle)

        # Scrollable frame for form
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {self.container_color};
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self.primary_blue};
                border-radius: 5px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #2563eb;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        # Scrollable widget
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background-color: transparent;")
        form_layout = QVBoxLayout(scroll_widget)
        form_layout.setContentsMargins(0, 0, 10, 0)
        form_layout.setSpacing(15)

        # Full name
        fullname_label = QLabel("Họ và tên")
        fullname_label.setStyleSheet(f"color: {self.text_secondary}; font-size: 12px;")
        form_layout.addWidget(fullname_label)

        self.fullname_input = QLineEdit()
        self.fullname_input.setPlaceholderText("Nhập họ và tên")
        self.fullname_input.setStyleSheet(f"""
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
        """)
        form_layout.addWidget(self.fullname_input)

        # Email
        email_label = QLabel("Email")
        email_label.setStyleSheet(f"color: {self.text_secondary}; font-size: 12px;")
        form_layout.addWidget(email_label)

        self.reg_email_input = QLineEdit()
        self.reg_email_input.setPlaceholderText("Nhập email")
        self.reg_email_input.setStyleSheet(f"""
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
        """)
        form_layout.addWidget(self.reg_email_input)

        # Username
        username_label = QLabel("Tên đăng nhập")
        username_label.setStyleSheet(f"color: {self.text_secondary}; font-size: 12px;")
        form_layout.addWidget(username_label)

        self.reg_username_input = QLineEdit()
        self.reg_username_input.setPlaceholderText("Nhập tên đăng nhập")
        self.reg_username_input.setStyleSheet(f"""
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
        """)
        form_layout.addWidget(self.reg_username_input)

        # Password
        password_label = QLabel("Mật khẩu")
        password_label.setStyleSheet(f"color: {self.text_secondary}; font-size: 12px;")
        form_layout.addWidget(password_label)

        self.reg_password_input = QLineEdit()
        self.reg_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_password_input.setPlaceholderText("Nhập mật khẩu")
        self.reg_password_input.setStyleSheet(f"""
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
        """)
        form_layout.addWidget(self.reg_password_input)

        # Confirm password
        confirm_label = QLabel("Xác nhận mật khẩu")
        confirm_label.setStyleSheet(f"color: {self.text_secondary}; font-size: 12px;")
        form_layout.addWidget(confirm_label)

        self.reg_confirm_input = QLineEdit()
        self.reg_confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_confirm_input.setPlaceholderText("Nhập lại mật khẩu")
        self.reg_confirm_input.setStyleSheet(f"""
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
        """)
        form_layout.addWidget(self.reg_confirm_input)

        form_layout.addSpacing(5)

        # Terms checkbox
        self.terms_check = QCheckBox("Tôi đồng ý với Điều khoản và Điều kiện")
        self.terms_check.setStyleSheet(f"""
            QCheckBox {{
                color: {self.text_secondary};
                font-size: 11px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 5px;
                border: none;
                background-color: {self.input_bg};
            }}
            QCheckBox::indicator:checked {{
                background-color: {self.primary_blue};
                border: none;
            }}
            QCheckBox::indicator:hover {{
                background-color: #353a4d;
            }}
        """)
        form_layout.addWidget(self.terms_check)

        form_layout.addSpacing(10)

        # Register button
        self.register_btn = QPushButton("ĐĂNG KÝ")
        self.register_btn.setStyleSheet(f"""
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
        """)
        self.register_btn.clicked.connect(self.handle_register)
        form_layout.addWidget(self.register_btn)

        form_layout.addSpacing(5)

        # Login link
        login_layout = QHBoxLayout()
        login_layout.setSpacing(5)

        login_text = QLabel("Đã có tài khoản?")
        login_text.setStyleSheet(f"color: {self.text_secondary}; font-size: 12px;")
        login_layout.addWidget(login_text)

        login_link = QPushButton("Đăng nhập ngay")
        login_link.setStyleSheet(f"""
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
        """)
        login_link.clicked.connect(self.show_login_view)
        login_layout.addWidget(login_link)

        login_layout.addStretch()

        form_layout.addLayout(login_layout)

        # Set scroll widget
        scroll_area.setWidget(scroll_widget)
        container_layout.addWidget(scroll_area)

        # Add container to main layout with margins
        self.main_layout.addSpacing(30)

        h_layout = QHBoxLayout()
        h_layout.addSpacing(25)
        h_layout.addWidget(container)
        h_layout.addSpacing(25)

        self.main_layout.addLayout(h_layout)
        self.main_layout.addSpacing(30)

        # Set focus to fullname field
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.fullname_input.setFocus())

    def clear_layout(self):
        """Clear all widgets from main layout"""
        while self.main_layout.count():
            child = self.main_layout.takeAt(0)
            if child.widget():
                widget = child.widget()
                widget.setParent(None)
                widget.deleteLater()
            elif child.layout():
                self.clear_sub_layout(child.layout())

        # Force process events to ensure widgets are deleted
        QApplication.processEvents()

    def clear_sub_layout(self, layout):
        """Clear a sub-layout recursively"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                widget = child.widget()
                widget.setParent(None)
                widget.deleteLater()
            elif child.layout():
                self.clear_sub_layout(child.layout())

    def get_dark_theme(self):
        """Dark theme stylesheet"""
        return f"""
        QWidget {{
            background-color: {self.bg_color};
            color: {self.text_color};
        }}
        QLabel {{
            color: {self.text_color};
        }}
        QCheckBox {{
            color: {self.text_secondary};
        }}
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
            self.show_message("Lỗi", "Vui lòng nhập đầy đủ thông tin!", "error")
            return

        try:
            # Disable button during login
            self.login_btn.setEnabled(False)
            self.login_btn.setText("Đang đăng nhập...")

            user = self.auth_service.login(email, password)

            # Success
            self.show_message("Thành công", f"Đăng nhập thành công!\nXin chào, {email}!", "success")
            self.login_successful.emit(user)

        except Exception as e:
            self.show_message("Lỗi đăng nhập", str(e), "error")
            self.login_btn.setEnabled(True)
            self.login_btn.setText("ĐĂNG NHẬP")

    def handle_register(self):
        """Handle register button click"""
        fullname = self.fullname_input.text().strip()
        email = self.reg_email_input.text().strip()
        username = self.reg_username_input.text().strip()
        password = self.reg_password_input.text()
        confirm_password = self.reg_confirm_input.text()

        # Validation
        if not all([fullname, email, username, password, confirm_password]):
            self.show_message("Lỗi", "Vui lòng nhập đầy đủ thông tin!", "error")
            return

        if password != confirm_password:
            self.show_message("Lỗi", "Mật khẩu xác nhận không khớp!", "error")
            return

        if len(password) < 6:
            self.show_message("Lỗi", "Mật khẩu phải có ít nhất 6 ký tự!", "error")
            return

        if not self.terms_check.isChecked():
            self.show_message("Lỗi", "Vui lòng đồng ý với Điều khoản và Điều kiện!", "error")
            return

        try:
            # Disable button during registration
            self.register_btn.setEnabled(False)
            self.register_btn.setText("Đang đăng ký...")

            self.auth_service.register(email, password)

            # Success
            self.show_message(
                "Thành công",
                f"Đăng ký thành công!\nChào mừng, {fullname}!",
                "success"
            )
            # Go back to login view
            self.show_login_view()

        except Exception as e:
            self.show_message("Lỗi đăng ký", str(e), "error")
            self.register_btn.setEnabled(True)
            self.register_btn.setText("ĐĂNG KÝ")

    def forgot_password(self):
        """Handle forgot password"""
        self.show_message(
            "Quên mật khẩu",
            "Chức năng đang được phát triển!\nVui lòng liên hệ hỗ trợ qua SĐT: 0123 456 789",
            "info"
        )

    def show_message(self, title, message, msg_type="info"):
        """Show custom message dialog with icons"""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setFixedSize(400, 250)
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {self.bg_color};
                border-radius: 15px;
            }}
        """)

        # Make dialog modal
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        # Icon based on type
        icons = {
            "success": "✅",
            "error": "❌",
            "info": "ℹ️"
        }

        icon_label = QLabel(icons.get(msg_type, "ℹ️"))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(icon_label)

        # Message
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"font-size: 14px; color: {self.text_secondary};")
        layout.addWidget(message_label)

        layout.addSpacing(10)

        # OK button
        ok_btn = QPushButton("OK")
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.primary_blue};
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
                min-height: 40px;
            }}
            QPushButton:hover {{
                background-color: #2563eb;
            }}
        """)
        ok_btn.clicked.connect(dialog.accept)

        # Center button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        dialog.exec()

    def mousePressEvent(self, event):
        """Handle mouse press for window dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Handle mouse move for window dragging"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        self.drag_position = None

    # Removed show_register_dialog - now using show_register_view


# RegisterDialog class removed - now using show_register_view
