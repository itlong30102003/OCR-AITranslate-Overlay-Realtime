"""Register View - User registration form"""

from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QFrame, QScrollArea,
                             QWidget, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from .base_view import BaseView


class RegisterView(BaseView):
    """Registration form view"""

    # Signals
    register_requested = pyqtSignal(str, str, str, str)  # fullname, email, username, password

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize the register UI"""
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
        fullname_label.setStyleSheet(self.get_label_style())
        form_layout.addWidget(fullname_label)

        self.fullname_input = QLineEdit()
        self.fullname_input.setPlaceholderText("Nhập họ và tên")
        self.fullname_input.setStyleSheet(self.get_input_style())
        form_layout.addWidget(self.fullname_input)

        # Email
        email_label = QLabel("Email")
        email_label.setStyleSheet(self.get_label_style())
        form_layout.addWidget(email_label)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Nhập email")
        self.email_input.setStyleSheet(self.get_input_style())
        form_layout.addWidget(self.email_input)

        # Username
        username_label = QLabel("Tên đăng nhập")
        username_label.setStyleSheet(self.get_label_style())
        form_layout.addWidget(username_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nhập tên đăng nhập")
        self.username_input.setStyleSheet(self.get_input_style())
        form_layout.addWidget(self.username_input)

        # Password
        password_label = QLabel("Mật khẩu")
        password_label.setStyleSheet(self.get_label_style())
        form_layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Nhập mật khẩu")
        self.password_input.setStyleSheet(self.get_input_style())
        form_layout.addWidget(self.password_input)

        # Confirm password
        confirm_label = QLabel("Xác nhận mật khẩu")
        confirm_label.setStyleSheet(self.get_label_style())
        form_layout.addWidget(confirm_label)

        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setPlaceholderText("Nhập lại mật khẩu")
        self.confirm_input.setStyleSheet(self.get_input_style())
        form_layout.addWidget(self.confirm_input)

        form_layout.addSpacing(5)

        # Status message label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {self.text_secondary};
                font-size: 12px;
                padding: 4px;
            }}
        """)
        self.status_label.hide()
        form_layout.addWidget(self.status_label)

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
        self.register_btn.setStyleSheet(self.get_primary_button_style())
        self.register_btn.clicked.connect(self._handle_register_click)
        form_layout.addWidget(self.register_btn)

        form_layout.addSpacing(5)

        # Login link
        login_layout = QHBoxLayout()
        login_layout.setSpacing(5)

        login_text = QLabel("Đã có tài khoản?")
        login_text.setStyleSheet(f"color: {self.text_secondary}; font-size: 12px;")
        login_layout.addWidget(login_text)

        login_link = QPushButton("Đăng nhập ngay")
        login_link.setStyleSheet(self.get_link_button_style())
        login_link.clicked.connect(lambda: self.view_changed.emit("login"))
        login_layout.addWidget(login_link)

        login_layout.addStretch()

        form_layout.addLayout(login_layout)

        # Set scroll widget
        scroll_area.setWidget(scroll_widget)
        container_layout.addWidget(scroll_area)

        # Add container to main layout with margins
        main_layout.addSpacing(30)

        h_layout = QHBoxLayout()
        h_layout.addSpacing(25)
        h_layout.addWidget(container)
        h_layout.addSpacing(25)

        main_layout.addLayout(h_layout)
        main_layout.addSpacing(30)

        # Set focus to fullname field
        QTimer.singleShot(100, lambda: self.fullname_input.setFocus())

    def _handle_register_click(self):
        """Handle register button click - validate and emit signal"""
        fullname = self.fullname_input.text().strip()
        email = self.email_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_input.text()

        # Validation
        if not all([fullname, email, username, password, confirm_password]):
            self.show_status(self.status_label, "Thất bại: Vui lòng nhập đầy đủ thông tin!", "error")
            return

        if password != confirm_password:
            self.show_status(self.status_label, "Thất bại: Mật khẩu xác nhận không khớp!", "error")
            return

        if len(password) < 6:
            self.show_status(self.status_label, "Thất bại: Mật khẩu phải có ít nhất 6 ký tự!", "error")
            return

        if not self.terms_check.isChecked():
            self.show_status(self.status_label, "Thất bại: Vui lòng đồng ý với Điều khoản và Điều kiện!", "error")
            return

        # Emit signal for parent to handle actual registration
        self.register_requested.emit(fullname, email, username, password)

    def set_loading(self, loading=True):
        """Set register button to loading state"""
        if loading:
            self.register_btn.setEnabled(False)
            self.register_btn.setText("Đang đăng ký...")
        else:
            self.register_btn.setEnabled(True)
            self.register_btn.setText("ĐĂNG KÝ")

    def show_error(self, message):
        """Show error message"""
        self.show_status(self.status_label, f"Thất bại: {message}", "error")
        self.set_loading(False)

    def show_success(self, message):
        """Show success message"""
        self.show_status(self.status_label, f"Đăng ký thành công với {message}!", "success", auto_hide_ms=3000)

    def clear_inputs(self):
        """Clear all input fields"""
        self.fullname_input.clear()
        self.email_input.clear()
        self.username_input.clear()
        self.password_input.clear()
        self.confirm_input.clear()
        self.terms_check.setChecked(False)
        self.status_label.hide()
