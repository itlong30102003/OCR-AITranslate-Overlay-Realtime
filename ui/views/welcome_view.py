"""Welcome View - Initial welcome screen with login/register options"""

from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from .base_view import BaseView


class WelcomeView(BaseView):
    """Welcome screen with app branding and action buttons"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize the welcome UI"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Container frame
        container = self.create_container()
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
        login_btn.setStyleSheet(self.get_primary_button_style())
        login_btn.clicked.connect(lambda: self.view_changed.emit("login"))
        container_layout.addWidget(login_btn)

        # Register button
        register_btn = QPushButton("📝 ĐĂNG KÝ")
        register_btn.setStyleSheet(self.get_secondary_button_style())
        register_btn.clicked.connect(lambda: self.view_changed.emit("register"))
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
        main_layout.addSpacing(0)
        main_layout.addLayout(h_layout)
        main_layout.addSpacing(0)
