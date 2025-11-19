"""Login View - User login form"""

from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from .base_view import BaseView


class LoginView(BaseView):
    """Login form view"""

    # Signals
    login_requested = pyqtSignal(str, str)  # email, password
    forgot_password_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize the login UI"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Container frame
        container = self.create_container()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(40, 30, 40, 30)
        container_layout.setSpacing(15)

        # Back button
        back_btn = QPushButton("← Quay lại")
        back_btn.setStyleSheet(self.get_back_button_style())
        back_btn.clicked.connect(lambda: self.view_changed.emit("welcome"))
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
        username_label.setStyleSheet(self.get_label_style())
        form_layout.addWidget(username_label)

        # Username/Email input
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Nhập tên đăng nhập hoặc email")
        self.email_input.setStyleSheet(self.get_input_style())
        form_layout.addWidget(self.email_input)

        form_layout.addSpacing(5)

        # Password label
        password_label = QLabel("Mật khẩu")
        password_label.setStyleSheet(self.get_label_style())
        form_layout.addWidget(password_label)

        # Password input
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Nhập mật khẩu")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(self.get_input_style())
        form_layout.addWidget(self.password_input)

        # Forgot password link
        forgot_btn = QPushButton("Quên mật khẩu?")
        forgot_btn.setCursor(Qt.CursorShape.PointingHandCursor)  # Show hand cursor
        forgot_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.cyan};
                border: none;
                padding: 8px 5px;
                font-size: 12px;
                text-align: right;
                min-height: 25px;
            }}
            QPushButton:hover {{
                color: {self.text_color};
                text-decoration: underline;
            }}
            QPushButton:pressed {{
                color: {self.primary_blue};
            }}
        """)
        forgot_btn.clicked.connect(self._on_forgot_password_clicked)
        form_layout.addWidget(forgot_btn, alignment=Qt.AlignmentFlag.AlignRight)

        form_layout.addSpacing(5)

        # Status message label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {self.text_secondary};
                font-size: 12px;
            }}
        """)
        self.status_label.hide()
        form_layout.addWidget(self.status_label)

        form_layout.addSpacing(5)

        # Login button
        self.login_btn = QPushButton("ĐĂNG NHẬP")
        self.login_btn.setStyleSheet(self.get_primary_button_style())
        self.login_btn.clicked.connect(self._handle_login_click)
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
        register_link.setStyleSheet(self.get_link_button_style())
        register_link.clicked.connect(lambda: self.view_changed.emit("register"))
        register_layout.addWidget(register_link)

        register_layout.addStretch()

        form_layout.addLayout(register_layout)

        container_layout.addWidget(form_frame)
        container_layout.addStretch()

        # Add container to main layout with margins
        main_layout.addSpacing(30)

        h_layout = QHBoxLayout()
        h_layout.addSpacing(25)
        h_layout.addWidget(container)
        h_layout.addSpacing(25)

        main_layout.addLayout(h_layout)
        main_layout.addSpacing(30)

        # Set focus to email field
        QTimer.singleShot(100, lambda: self.email_input.setFocus())

    def _handle_login_click(self):
        """Handle login button click - validate and emit signal"""
        email = self.email_input.text().strip()
        password = self.password_input.text()

        # Hide previous status message
        self.status_label.hide()

        if not email or not password:
            self.show_status(self.status_label, "Vui lòng nhập đầy đủ thông tin!", "error")
            return

        # Emit signal for parent to handle actual login
        self.login_requested.emit(email, password)

    def _on_forgot_password_clicked(self):
        """Handle forgot password button click"""
        self.forgot_password_clicked.emit()

    def set_loading(self, loading=True):
        """Set login button to loading state"""
        if loading:
            self.login_btn.setEnabled(False)
            self.login_btn.setText("Đang đăng nhập...")
            self.status_label.setText("Đang đăng nhập...")
            self.status_label.show()
        else:
            self.login_btn.setEnabled(True)
            self.login_btn.setText("ĐĂNG NHẬP")

    def show_error(self, message):
        """Show error message"""
        self.show_status(self.status_label, f"✗ {message}", "error")
        self.set_loading(False)

    def show_success(self, message):
        """Show success message"""
        self.show_status(self.status_label, f"✓ {message}", "success", auto_hide_ms=3000)

    def clear_inputs(self):
        """Clear all input fields"""
        self.email_input.clear()
        self.password_input.clear()
        self.status_label.hide()
