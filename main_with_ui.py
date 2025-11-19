"""Main Entry Point with Firebase UI Integration - Refactored"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
import ctypes

# IMPORTANT: Enable High DPI scaling BEFORE creating QApplication
# This fixes DPI scaling issues on Windows

# Method 1: Windows native DPI awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()  # Fallback for older Windows
    except:
        pass

# Method 2: Qt High DPI support
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

# Create QApplication
app = QApplication(sys.argv)

from services import WindowService
from ui.login_window import LoginWindow
from ui.main_window import MainWindow


def main():
    """Main entry point"""
    print("=== OCR Translation Overlay with Firebase ===")

    # Check if Firebase is available
    try:
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

        # Create app service and sync history
        app_service = window_service.handle_login_success(current_user)

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

            # Create app service and sync history
            app_service = window_service.handle_login_success(user)

            # Show main window
            main_window = MainWindow(user=user, app_instance=app_service)
            main_window.show()

        login_window.login_successful.connect(on_login_success)
        login_window.show()

    # Run Qt event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
