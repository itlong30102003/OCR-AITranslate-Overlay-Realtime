"""Forgot Password View - Password reset dialog"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer


class ForgotPasswordView(QDialog):
    """Forgot password dialog for password reset"""

    # Signals
    reset_requested = pyqtSignal(str)  # email

    def __init__(self, parent=None):
        super().__init__(parent)

        # Color scheme - shared with BaseView
        self.container_color = "#1e2132"
        self.primary_blue = "#3b82f6"
        self.text_color = "#ffffff"
        self.text_secondary = "#9ca3af"
        self.input_bg = "#2a2d3e"

        # For dragging dialog
        self.drag_position = None

        self.init_ui()

    def init_ui(self):
        """Initialize the forgot password dialog UI"""
        self.setWindowTitle("Quên mật khẩu")
        self.setFixedSize(450, 320)

        # Set window flags - MUST include Dialog flag for proper display
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        # Ensure dialog is visible
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.container_color};
                border-radius: 15px;
                border: 2px solid {self.primary_blue};
            }}
        """)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        # Title
        title_label = QLabel("🔐 Quên mật khẩu")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"""
            font-size: 22px;
            font-weight: bold;
            color: {self.text_color};
        """)
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel("Nhập email của bạn để nhận liên kết đặt lại mật khẩu")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"""
            font-size: 13px;
            color: {self.text_secondary};
            padding: 5px 10px;
        """)
        layout.addWidget(desc_label)

        layout.addSpacing(10)

        # Email label
        email_label = QLabel("Email")
        email_label.setStyleSheet(f"color: {self.text_secondary}; font-size: 12px;")
        layout.addWidget(email_label)

        # Email input
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Nhập email của bạn")
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
        layout.addWidget(self.email_input)

        # Status label
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
        layout.addWidget(self.status_label)

        layout.addSpacing(10)

        # Buttons layout
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        # Cancel button
        cancel_btn = QPushButton("Hủy")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.text_secondary};
                border: 2px solid {self.text_secondary};
                padding: 12px;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
                min-height: 45px;
            }}
            QPushButton:hover {{
                background-color: rgba(156, 163, 175, 0.1);
                border-color: {self.text_color};
                color: {self.text_color};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        # Send button
        self.send_btn = QPushButton("Gửi email")
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.primary_blue};
                color: white;
                border: none;
                padding: 12px;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
                min-height: 45px;
            }}
            QPushButton:hover {{
                background-color: #2563eb;
            }}
            QPushButton:pressed {{
                background-color: #1d4ed8;
            }}
        """)
        self.send_btn.clicked.connect(self._handle_send_click)
        btn_layout.addWidget(self.send_btn)

        layout.addLayout(btn_layout)

        # Set focus to email input
        QTimer.singleShot(100, lambda: self.email_input.setFocus())

    def _handle_send_click(self):
        """Handle send button click - validate and emit signal"""
        email = self.email_input.text().strip()

        if not email:
            self.show_status("⚠️ Vui lòng nhập email!", "error")
            return

        # Emit signal for parent to handle actual reset
        self.reset_requested.emit(email)

    def set_loading(self, loading=True):
        """Set send button to loading state"""
        if loading:
            self.send_btn.setEnabled(False)
            self.send_btn.setText("Đang gửi...")
            self.status_label.setText("Đang gửi email...")
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.text_secondary};
                    font-size: 12px;
                    padding: 4px;
                }}
            """)
            self.status_label.show()
        else:
            self.send_btn.setEnabled(True)
            self.send_btn.setText("Gửi email")

    def show_status(self, message, status_type="error"):
        """Show status message"""
        self.status_label.setText(message)

        if status_type == "success":
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    color: #10b981;
                    font-size: 12px;
                    padding: 4px;
                }}
            """)
        else:  # error
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    color: #ef4444;
                    font-size: 12px;
                    padding: 4px;
                }}
            """)

        self.status_label.show()

    def show_success(self, message):
        """Show success message and close after delay"""
        self.show_status(f"✅ {message}", "success")
        QTimer.singleShot(2000, self.accept)

    def show_error(self, message):
        """Show error message"""
        self.show_status(f"❌ {message}", "error")
        self.set_loading(False)

    def mousePressEvent(self, event):
        """Handle mouse press for dialog dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Handle mouse move for dialog dragging"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        self.drag_position = None
