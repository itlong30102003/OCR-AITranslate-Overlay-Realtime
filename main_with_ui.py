"""Main Entry Point with Firebase UI Integration - Refactored"""

import sys
import os
import warnings

# Suppress all warnings for cleaner output
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Suppress Qt DPI warnings
os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"

# Suppress gRPC/Google Cloud warnings (C++ level)
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "3"  # 3 = FATAL only
os.environ["GRPC_TRACE"] = ""
os.environ["GRPC_VERBOSITY"] = "NONE"

# Suppress ABSL logging (Google's C++ logging library)
os.environ["ABSL_MINLOGLEVEL"] = "3"  # Only show FATAL
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# IMPORTANT: Set environment variables BEFORE importing PyQt6
# This tells Qt to not manage DPI awareness - we'll let Windows handle it
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
os.environ["QT_SCALE_FACTOR"] = "1"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# IMPORTANT: Disable Qt's DPI awareness management completely
# This prevents the "SetProcessDpiAwarenessContext failed" error
QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

# Create QApplication (Qt will NOT try to set DPI awareness)
app = QApplication(sys.argv)

from services import WindowService
from ui.login_window import LoginWindow
from ui.main_window import MainWindow


def suppress_stderr():
    """Context manager to suppress stderr output (for gRPC warnings)"""
    import io
    import sys

    class SuppressStderr:
        def __enter__(self):
            self.old_stderr = sys.stderr
            sys.stderr = io.StringIO()
            return self

        def __exit__(self, *_):
            sys.stderr = self.old_stderr
            return False

    return SuppressStderr()


def main():
    """Main entry point"""
    print("=== OCR Translation Overlay with Firebase ===")

    # Check if Firebase is available
    try:
        # Temporarily suppress stderr to hide gRPC/ALTS warnings during import
        import contextlib
        import io

        with contextlib.redirect_stderr(io.StringIO()):
            from firebase.firebase_manager import FirebaseManager
            firebase_available = FirebaseManager.is_available()
    except Exception as e:
        print(f"[WARNING] Firebase not available: {e}")
        firebase_available = False

    if not firebase_available:
        print("[ERROR] Firebase is not configured. Please setup Firebase first!")
        print("See README_FIREBASE.md for setup instructions")
        sys.exit(1)

    # Create window service
    window_service = WindowService()

    # Check if user is already logged in
    current_user = window_service.get_current_user()

    if current_user:
        # User already logged in, show main window
        print(f"[INFO] User already logged in: {current_user.get('email')}")

        # Create app service with history saving enabled
        from services.app_service import AppService
        app_service = AppService(user_id=current_user['localId'])

        # Show main window
        main_window = MainWindow(user=current_user, app_instance=app_service)
        main_window.show()
    else:
        # Show login window
        login_window = LoginWindow()

        # Connect login successful signal
        def on_login_success(user):
            print(f"[INFO] Login successful: {user.get('email')}")
            login_window.hide()

            # Create app service with history saving enabled
            from services.app_service import AppService
            app_service = AppService(user_id=user['localId'])

            # Show main window
            main_window = MainWindow(user=user, app_instance=app_service)
            main_window.show()

        login_window.login_successful.connect(on_login_success)
        login_window.show()

    # Run Qt event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()