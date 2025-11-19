"""App Service - Manages application lifecycle and services initialization"""

from typing import Optional
from translation.config import TranslationConfig
from services.ocr_service import OCRService
from services.translation_service import TranslationService
from services.overlay_service import OverlayService
from services.ui_service import UIService
from services.async_processing_service import AsyncProcessingService
from firebase.local_history_service import LocalHistoryService
from firebase.sync_service import SyncService


class AppService:
    """Central service for managing app lifecycle and core services"""

    def __init__(self, user_id: Optional[str] = None):
        """
        Initialize app services

        Args:
            user_id: Firebase user ID (optional, for history tracking)
        """
        # Load configuration
        self.config = TranslationConfig('config.env')
        self.user_id = user_id

        # Get overlay mode from config
        overlay_mode = self.config.get('overlay_display', 'positioned')
        if overlay_mode not in ['list', 'positioned']:
            overlay_mode = 'positioned'

        # Initialize PyQt6 overlay early on main thread
        if overlay_mode == 'positioned':
            from overlay.positioned_overlay_qt import get_positioned_overlay_qt
            self.qt_overlay = get_positioned_overlay_qt()

            # Configure subtitle position
            subtitle_position = self.config.get('subtitle_position', 'bottom')
            if subtitle_position in ['top', 'center', 'bottom']:
                self.qt_overlay.set_subtitle_position(subtitle_position)

        # Initialize core services
        self.ocr_service = OCRService()
        self.translation_service = TranslationService(self.config)
        self.overlay_service = OverlayService(enabled=True, overlay_mode=overlay_mode)
        self.ui_service = UIService()

        # Initialize async processing service
        self.async_service = AsyncProcessingService(
            self.ocr_service,
            self.translation_service,
            self.overlay_service,
            overlay_mode=overlay_mode,
            user_id=user_id
        )

        # Start async service
        print("[AppService] Starting async processing service...")
        self.async_service.start()

        # Initialize Firebase services if user logged in
        self.local_history = None
        self.sync_service = None
        if user_id:
            self._init_firebase_services(user_id)

        print("[AppService] Initialized")
        print(f"[AppService] Translation available: {self.translation_service.is_available()}")
        print(f"[AppService] Overlay mode: {overlay_mode}")
        print(f"[AppService] User ID: {user_id}")

    def _init_firebase_services(self, user_id: str):
        """Initialize Firebase-related services"""
        self.local_history = LocalHistoryService(batch_size=20, current_user_id=user_id)
        self.sync_service = SyncService(user_id, batch_size=20)
        self.sync_service.start()
        print("[AppService] Firebase services initialized")

    def sync_user_history(self) -> int:
        """
        Sync history from Firestore to local SQLite

        Returns:
            Number of records synced
        """
        if not self.user_id:
            return 0

        try:
            synced_count = self.sync_service.sync_from_firestore()
            print(f"[AppService] Synced {synced_count} records from Firestore")
            return synced_count
        except Exception as e:
            print(f"[AppService] Failed to sync from Firestore: {e}")
            return 0

    def stop_all_services(self):
        """Stop all background services"""
        print("[AppService] Stopping all services...")

        # Stop async processing
        if self.async_service:
            self.async_service.stop()
            print("[AppService] Async processing stopped")

        # Stop sync service
        if self.sync_service:
            self.sync_service.stop()
            print("[AppService] Sync service stopped")

        # Clear overlay
        if self.overlay_service:
            self.overlay_service.clear_positioned_overlay()
            print("[AppService] Overlay cleared")

        print("[AppService] All services stopped")

    def change_overlay_mode(self, mode: str):
        """Change overlay display mode"""
        print(f"[AppService] Changing overlay mode to: {mode}")
        self.overlay_service.set_overlay_mode(mode)
        self.async_service.set_overlay_mode(mode)
        print(f"[AppService] Overlay mode changed to: {mode}")

    def get_overlay_mode(self) -> str:
        """Get current overlay mode"""
        return self.overlay_service.get_overlay_mode()

    def is_translation_available(self) -> bool:
        """Check if translation service is available"""
        return self.translation_service.is_available()
