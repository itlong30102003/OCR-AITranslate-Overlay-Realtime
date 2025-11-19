"""Main Entry Point with Firebase UI Integration"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from typing import Optional
from PIL import Image
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

from capture.screen_capture_integrated import IntegratedScreenCapture
from translation.config import TranslationConfig
from services import OCRService, TranslationService, OverlayService, UIService, AsyncProcessingService
from firebase.auth_service import FirebaseAuthService
from firebase.local_history_service import LocalHistoryService
from firebase.sync_service import SyncService
from ui.login_window import LoginWindow
from ui.main_window import MainWindow


class OCRTranslationApp:
    """Main OCR Translation Application with Firebase Integration"""

    def __init__(self, user_id: str = None):
        """
        Initialize app

        Args:
            user_id: Firebase user ID (optional, for history tracking)
        """
        # Load configuration
        self.config = TranslationConfig('config.env')

        # User ID for Firebase history
        self.user_id = user_id

        # Get overlay mode from config (default: "positioned")
        overlay_mode = self.config.get('overlay_display', 'positioned')
        if overlay_mode not in ['list', 'positioned']:
            overlay_mode = 'positioned'

        # IMPORTANT: Initialize PyQt6 overlay EARLY on main thread (before Tkinter starts)
        if overlay_mode == 'positioned':
            from overlay.positioned_overlay_qt import get_positioned_overlay_qt
            self.qt_overlay = get_positioned_overlay_qt()

            # Configure subtitle position from config
            subtitle_position = self.config.get('subtitle_position', 'bottom')
            if subtitle_position in ['top', 'center', 'bottom']:
                self.qt_overlay.set_subtitle_position(subtitle_position)

        # Initialize services
        self.ocr_service = OCRService()
        self.translation_service = TranslationService(self.config)
        self.overlay_service = OverlayService(enabled=True, overlay_mode=overlay_mode)
        self.ui_service = UIService()

        # Initialize async processing service WITH user_id
        self.async_service = AsyncProcessingService(
            self.ocr_service,
            self.translation_service,
            self.overlay_service,
            overlay_mode=overlay_mode,
            user_id=user_id
        )

        # Start async service immediately so event loop is ready
        print("[INFO] Starting async processing service...")
        self.async_service.start()

        # Initialize local history and sync services if user_id provided
        self.local_history = None
        self.sync_service = None
        if user_id:
            self.local_history = LocalHistoryService(batch_size=20, current_user_id=user_id)  # Batch 20 records, per user
            self.sync_service = SyncService(user_id, batch_size=20)  # Batch 20 records
            self.sync_service.start()  # Start background batch sync
            print("[INFO] Local history and batch sync services initialized")

        # Window capture monitor (will be initialized when monitoring starts)
        self.window_monitor = None
        self.selected_hwnd = None
        self.selected_window_title = None

        print("[INFO] OCR Translation App initialized")
        print(f"[INFO] Translation available: {self.translation_service.is_available()}")
        print(f"[INFO] Overlay mode: {overlay_mode}")
        print(f"[INFO] User ID: {user_id}")

    def stop_all_services(self):
        """Stop all background services"""
        print("[App] Stopping all background services...")

        # Stop async processing service
        if hasattr(self, 'async_service') and self.async_service:
            self.async_service.stop()
            print("[App] Async processing service stopped")

        # Stop integrated capture
        if hasattr(self, 'integrated_capture') and self.integrated_capture:
            self.integrated_capture.stop_monitoring()
            print("[App] Integrated capture stopped")

        # Stop sync service
        if hasattr(self, 'sync_service') and self.sync_service:
            self.sync_service.stop()
            print("[App] Sync service stopped")

        # Clear overlay
        if hasattr(self, 'overlay_service') and self.overlay_service:
            self.overlay_service.clear_positioned_overlay()
            print("[App] Overlay cleared")

        print("[App] All services stopped successfully")

    def on_region_change(self, idx: int, img: Image.Image, scan_counter: int, region_coords: tuple = None):
        """
        Callback when region changes - OCR + Translation (Async)

        Args:
            idx: Region index
            img: PIL Image of the region
            scan_counter: Current scan counter
            region_coords: Region's absolute screen coordinates (x1, y1, x2, y2)
        """
        # Process asynchronously with history saving
        self.async_service.process_region_async(idx, img, scan_counter, region_coords)

    def change_overlay_mode(self, mode: str):
        """Change overlay mode"""
        print(f"[App] Changing overlay mode to: {mode}")
        self.overlay_service.set_overlay_mode(mode)
        self.async_service.set_overlay_mode(mode)
        print(f"[App] Overlay mode changed successfully to: {mode}")

    def start_capture(self):
        """Start window capture and monitoring"""
        if not self.translation_service.is_available():
            print("[WARNING] Translation system not available, running OCR only")

        # Start async processing service
        self.async_service.start()

        # Set scan mode based on overlay mode
        overlay_mode = self.overlay_service.get_overlay_mode()
        if overlay_mode == "list":
            scan_mode = "realtime"  # List overlay: continuous monitoring
        else:
            scan_mode = "snapshot"  # Positioned overlay: scan once

        print(f"[INFO] Overlay mode: {overlay_mode} -> Scan mode: {scan_mode}")

        # Note: Window capture is now handled by the MonitorTab in the UI
        # The tab will create its own WindowRegionMonitor instance
        print(f"[INFO] Capture mode delegated to MonitorTab ({scan_mode} mode)")


def main():
    """Main entry point"""
    print("=== OCR Translation Overlay with Firebase ===")

    # QApplication already created above
    # app = QApplication(sys.argv)

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

    # Create auth service
    auth_service = FirebaseAuthService()

    # Check if user is already logged in
    current_user = auth_service.get_current_user()

    if current_user:
        # User already logged in, show main window
        print(f"[INFO] User already logged in: {current_user.get('email')}")

        # Create main app with user_id
        ocr_app = OCRTranslationApp(user_id=current_user['localId'])

        # Sync history from Firestore to local SQLite before showing UI
        try:
            from firebase.sync_service import SyncService
            sync_service = SyncService(user_id=current_user['localId'])
            synced_count = sync_service.sync_from_firestore()
            print(f"[Login] Synced {synced_count} records from Firestore to local SQLite")
        except Exception as e:
            print(f"[Login] Failed to sync from Firestore: {e}")

        main_window = MainWindow(user=current_user, app_instance=ocr_app)
        main_window.show()
    else:
        # Show login window
        login_window = LoginWindow()

        # Connect login successful signal
        def on_login_success(user):
            print(f"[INFO] Login successful: {user.get('email')}")
            login_window.hide()

            # Create main app with user_id
            ocr_app = OCRTranslationApp(user_id=user['localId'])

            # Sync history from Firestore to local SQLite before showing UI
            try:
                from firebase.sync_service import SyncService
                sync_service = SyncService(user_id=user['localId'])
                synced_count = sync_service.sync_from_firestore()
                print(f"[Login] Synced {synced_count} records from Firestore to local SQLite")
            except Exception as e:
                print(f"[Login] Failed to sync from Firestore: {e}")

            main_window = MainWindow(user=user, app_instance=ocr_app)
            main_window.show()

        login_window.login_successful.connect(on_login_success)
        login_window.show()

    # Run Qt event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()