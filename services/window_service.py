"""Window Service - Manages UI windows and navigation"""

from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal
from services.app_service import AppService
from firebase.auth_service import FirebaseAuthService


class WindowService(QObject):
    """Service for managing application windows and navigation"""

    # Signals
    show_main_window = pyqtSignal(dict, AppService)  # user, app_service
    show_login_window = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.auth_service = FirebaseAuthService()
        self.current_app: Optional[AppService] = None
        self.current_user: Optional[dict] = None

    def get_current_user(self) -> Optional[dict]:
        """Get currently logged in user"""
        return self.auth_service.get_current_user()

    def handle_login_success(self, user: dict) -> AppService:
        """
        Handle successful login

        Args:
            user: Firebase user dict

        Returns:
            AppService instance for the logged in user
        """
        print(f"[WindowService] Login successful: {user.get('email')}")

        # Create app service for this user
        app_service = AppService(user_id=user['localId'])

        # Sync history from Firestore
        app_service.sync_user_history()

        # Store current user and app
        self.current_user = user
        self.current_app = app_service

        return app_service

    def logout(self):
        """Handle logout"""
        print("[WindowService] Logging out...")

        # Stop current app services
        if self.current_app:
            self.current_app.stop_all_services()
            self.current_app = None

        # Logout from Firebase
        self.auth_service.logout()

        # Clear current user
        self.current_user = None

        print("[WindowService] Logout complete")

    def cleanup(self):
        """Cleanup resources"""
        if self.current_app:
            self.current_app.stop_all_services()
            self.current_app = None
