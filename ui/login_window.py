"""Login Window - User authentication (Refactored)"""

from PyQt6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from firebase.auth_service import FirebaseAuthService

# Import view components
from .views import (
    WelcomeView,
    LoginView,
    RegisterView,
    ForgotPasswordView
)


class LoginWindow(QWidget):
    """Login window for user authentication - manages view switching"""

    login_successful = pyqtSignal(dict)  # Signal emitted when login succeeds

    def __init__(self):
        super().__init__()
        self.auth_service = FirebaseAuthService()
        self.current_view = "welcome"  # welcome, login, register

        # For dragging window
        self.drag_position = None

        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("OCR Translator Pro - Welcome")
        self.setFixedSize(450, 680)

        # Remove window frame and title bar
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        # Color scheme
        bg_color = "#1a1d2e"
        text_color = "#ffffff"

        # Apply dark theme
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                color: {text_color};
            }}
        """)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        # Create stacked widget to hold all views
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Create and add all view components
        self.welcome_view = WelcomeView()
        self.login_view = LoginView()
        self.register_view = RegisterView()

        self.stacked_widget.addWidget(self.welcome_view)
        self.stacked_widget.addWidget(self.login_view)
        self.stacked_widget.addWidget(self.register_view)

        # Connect signals from views
        self._connect_view_signals()

        # Show welcome view initially
        self.show_view("welcome")

    def _connect_view_signals(self):
        """Connect all signals from view components"""
        # View change signals
        self.welcome_view.view_changed.connect(self.show_view)
        self.login_view.view_changed.connect(self.show_view)
        self.register_view.view_changed.connect(self.show_view)

        # Action signals
        self.login_view.login_requested.connect(self.handle_login)
        self.login_view.forgot_password_clicked.connect(self.show_forgot_password)
        self.register_view.register_requested.connect(self.handle_register)

    def show_view(self, view_name):
        """Switch to a specific view"""
        self.current_view = view_name

        # Map view names to widgets
        view_map = {
            "welcome": (self.welcome_view, "OCR Translator Pro - Welcome"),
            "login": (self.login_view, "OCR Translator Pro - Login"),
            "register": (self.register_view, "OCR Translator Pro - Register")
        }

        if view_name in view_map:
            widget, title = view_map[view_name]
            self.stacked_widget.setCurrentWidget(widget)
            self.setWindowTitle(title)

    def handle_login(self, email, password):
        """Handle login request from LoginView"""
        # Set loading state
        self.login_view.set_loading(True)

        try:
            # Perform login
            user = self.auth_service.login(email, password)

            # Success
            success_msg = f"Đăng nhập thành công! Xin chào, {email.split('@')[0]}!"
            self.login_view.show_success(success_msg)

            # Emit signal after a short delay to show success message
            QTimer.singleShot(800, lambda: self.login_successful.emit(user))

        except Exception as e:
            # Handle errors
            error_message = str(e)
            if "Invalid email or password" in error_message:
                self.login_view.show_error("Email hoặc mật khẩu không đúng!")
            elif "network" in error_message.lower():
                self.login_view.show_error("Lỗi kết nối mạng. Vui lòng kiểm tra internet!")
            else:
                self.login_view.show_error(error_message)

    def handle_register(self, _fullname, email, _username, password):
        """Handle registration request from RegisterView

        Note: fullname and username are not currently used by Firebase auth
        but are kept for future user profile implementation
        """
        # Set loading state
        self.register_view.set_loading(True)

        try:
            # Perform registration
            self.auth_service.register(email, password)

            # Success
            self.register_view.show_success(email)

            # Go back to login view after a delay
            QTimer.singleShot(2000, lambda: self.show_view("login"))

        except Exception as e:
            # Handle errors
            error_message = str(e)
            if "email already exists" in error_message.lower():
                self.register_view.show_error("Email đã được sử dụng!")
            elif "network" in error_message.lower():
                self.register_view.show_error("Lỗi kết nối mạng!")
            else:
                self.register_view.show_error(error_message)

    def show_forgot_password(self):
        """Show forgot password dialog"""
        try:
            dialog = ForgotPasswordView(self)

            # Connect signal
            dialog.reset_requested.connect(lambda email: self.handle_password_reset(email, dialog))

            # Center dialog on parent window after initialization
            QTimer.singleShot(50, lambda: self._center_and_show_dialog(dialog))

        except Exception as e:
            print(f"[LoginWindow] ERROR showing forgot password dialog: {e}")
            import traceback
            traceback.print_exc()

    def _center_and_show_dialog(self, dialog):
        """Center and show dialog - called after a short delay to ensure proper geometry"""
        try:
            # Center on parent window
            parent_center = self.frameGeometry().center()
            dialog_rect = dialog.frameGeometry()
            dialog_rect.moveCenter(parent_center)
            dialog.move(dialog_rect.topLeft())

            # Show dialog
            dialog.exec()

        except Exception as e:
            print(f"[LoginWindow] ERROR in _center_and_show_dialog: {e}")
            import traceback
            traceback.print_exc()

    def handle_password_reset(self, email, dialog):
        """Handle password reset request"""
        # Set loading state
        dialog.set_loading(True)

        try:
            # Send reset email
            self.auth_service.send_password_reset_email(email)

            # Success
            dialog.show_success("Email đã được gửi! Vui lòng kiểm tra hộp thư.")

        except Exception as e:
            # Handle errors
            error_message = str(e)
            dialog.show_error(error_message)

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
