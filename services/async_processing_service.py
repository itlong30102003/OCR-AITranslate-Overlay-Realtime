"""Async Processing Service - Handles parallel OCR and Translation"""

import asyncio
import threading
from typing import Dict, Optional
from PIL import Image


class AsyncProcessingService:
    """Service for managing async OCR and Translation pipeline"""

    def __init__(self, ocr_service, translation_service, overlay_service, overlay_mode: str = "list", user_id: str = None):
        """
        Initialize Async Processing Service

        Args:
            ocr_service: OCRService instance
            translation_service: TranslationService instance
            overlay_service: OverlayService instance
            overlay_mode: Overlay mode - "list" (default) or "positioned"
            user_id: User ID for local history (optional)
        """
        self.ocr_service = ocr_service
        self.translation_service = translation_service
        self.overlay_service = overlay_service
        self.overlay_mode = overlay_mode  # "list" or "positioned"
        self.user_id = user_id
        
        # Translation mode: "realtime" (no history) or "region" (save to history)
        self.translation_mode = "realtime"

        # Local history service (lazy load)
        self._history_service = None

        # Event loop for async processing
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._running = False

        print(f"[Async Processing Service] Initialized (mode: {overlay_mode}, user_id: {user_id})")

    def start(self):
        """Start the async processing event loop in a separate thread"""
        if self._running and self._loop and not self._loop.is_closed():
            return

        # If loop exists but closed, clean up
        if self._loop and self._loop.is_closed():
            self._loop = None
            self._running = False

        self._running = True
        self._loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._loop_thread.start()
        print("[Async Processing Service] Started event loop")

    def _run_event_loop(self):
        """Run the asyncio event loop in a separate thread"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def stop(self):
        """Stop the async processing event loop"""
        if not self._running:
            return

        self._running = False

        # Properly stop the event loop to prevent "cannot schedule new futures after shutdown" errors
        if self._loop and not self._loop.is_closed():
            try:
                # Schedule the loop to stop
                self._loop.call_soon_threadsafe(self._loop.stop)
                # Wait for the thread to finish
                if self._loop_thread and self._loop_thread.is_alive():
                    self._loop_thread.join(timeout=2.0)
                print("[Async Processing Service] Event loop properly stopped")
            except Exception as e:
                print(f"[Async Processing Service] Error stopping event loop: {e}")
        else:
            print("[Async Processing Service] Stopped (loop already closed)")

    def process_region_async(self, region_idx: int, img: Image.Image, scan_counter: int, region_coords: tuple = None):
        """
        Process a region asynchronously (OCR + Translation + Overlay update)

        Args:
            region_idx: Region index
            img: PIL Image to process
            scan_counter: Scan counter
            region_coords: Region's absolute screen coordinates (x1, y1, x2, y2) - required for positioned mode
        """
        if not self._running or not self._loop:
            print("[Async Processing Service] Not running, starting...")
            self.start()
            # Wait a bit for loop to start
            import time
            time.sleep(0.3)

        # Check if loop is still running before scheduling
        if self._running and self._loop and not self._loop.is_closed():
            try:
                # Schedule the async task
                asyncio.run_coroutine_threadsafe(
                    self._process_region(region_idx, img, scan_counter, region_coords),
                    self._loop
                )
            except RuntimeError as e:
                if "cannot schedule new futures after shutdown" not in str(e):
                    print(f"[Async Processing Service] Error scheduling task: {e}")
        else:
            print("[Async Processing Service] Event loop not available")

    def set_overlay_mode(self, mode: str):
        """
        Set overlay mode

        Args:
            mode: "list" or "positioned"
        """
        if mode in ["list", "positioned"]:
            self.overlay_mode = mode
            print(f"[Async Processing Service] Overlay mode set to: {mode}")
        else:
            print(f"[Async Processing Service] Invalid overlay mode: {mode}")

    def set_user_id(self, user_id: str):
        """Set user ID for history tracking"""
        self.user_id = user_id
        print(f"[Async Processing Service] User ID set: {user_id}")
    
    def set_translation_mode(self, mode: str):
        """
        Set translation mode
        
        Args:
            mode: "realtime" (no history saving) or "region" (save to history)
        """
        if mode in ["realtime", "region"]:
            self.translation_mode = mode
            print(f"[Async Processing Service] Translation mode set to: {mode}")
        else:
            print(f"[Async Processing Service] Invalid translation mode: {mode}")

    def _get_history_service(self):
        """Lazy load local history service (SQLite - offline backup)"""
        if self._history_service is None and self.user_id:
            try:
                from firebase.local_history_service import LocalHistoryService
                # Initialize with correct user_id and batch_size
                self._history_service = LocalHistoryService(batch_size=20, current_user_id=self.user_id)
                print("[Async Processing Service] Local history service loaded (offline backup)")
            except Exception as e:
                print(f"[Async Processing Service] Failed to load local history: {e}")
        return self._history_service
    
    def _get_firebase_history_service(self):
        """Lazy load Firebase history service"""
        if not hasattr(self, '_firebase_history_service'):
            self._firebase_history_service = None
        if self._firebase_history_service is None and self.user_id:
            try:
                from firebase.history_service import FirebaseHistoryService
                self._firebase_history_service = FirebaseHistoryService(self.user_id)
                print("[Async Processing Service] Firebase history service loaded")
            except Exception as e:
                print(f"[Async Processing Service] Failed to load Firebase history: {e}")
        return self._firebase_history_service
    
    def _check_internet(self) -> bool:
        """Quick check if internet is available"""
        import socket
        try:
            # Try to connect to Google DNS (fast check)
            socket.create_connection(("8.8.8.8", 53), timeout=1)
            return True
        except (socket.timeout, socket.error):
            return False

    async def _save_to_history(self, source_text: str, translated_text: str, source_lang: str, target_lang: str, model: str, confidence: float):
        """
        Save translation to history - Online First strategy:
        - Online: Save directly to Firebase Firestore
        - Offline: Save to SQLite (will sync when back online)
        """
        if not self.user_id:
            return
        
        try:
            # Check if online
            is_online = self._check_internet()
            
            if is_online:
                # Online: Save directly to Firebase
                firebase_service = self._get_firebase_history_service()
                if firebase_service:
                    firebase_service.save_translation(
                        user_id=self.user_id,
                        source_text=source_text,
                        translated_text=translated_text,
                        source_lang=source_lang,
                        target_lang=target_lang,
                        model_used=model,
                        confidence=confidence
                    )
                    print(f"[History] Saved to Firebase: {source_text[:30]}...")
                    return
            
            # Offline or Firebase failed: Save to SQLite
            local_service = self._get_history_service()
            if local_service:
                local_service.save_translation(
                    user_id=self.user_id,
                    source_text=source_text,
                    translated_text=translated_text,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    model_used=model,
                    confidence=confidence
                )
                print(f"[History] Saved to SQLite (offline): {source_text[:30]}...")
                
        except Exception as e:
            print(f"[Async Processing Service] Failed to save history: {e}")
            import traceback
            traceback.print_exc()

    async def _process_region(self, region_idx: int, img: Image.Image, scan_counter: int, region_coords: tuple = None):
        """
        Internal async method to process region

        Args:
            region_idx: Region index
            img: PIL Image to process
            scan_counter: Scan counter
            region_coords: Region's absolute screen coordinates (x1, y1, x2, y2)
        """
        # Handle clear signal
        if region_idx == -1:
            self.overlay_service.clear_positioned_overlay()
            return

        try:
            # DO NOT clear overlay here - overlay_service handles per-region updates!
            # Clearing would remove all other regions' overlays → flickering/not smooth

            # Only positioned mode supported now
            await self._process_region_positioned(region_idx, img, scan_counter, region_coords)

        except Exception as e:
            print(f"[Async Processing Service] Error processing region {region_idx}: {e}")
            import traceback
            traceback.print_exc()

    async def _process_region_list(self, region_idx: int, img: Image.Image, scan_counter: int):
        """
        Process region for LIST overlay mode (original behavior)

        Args:
            region_idx: Region index
            img: PIL Image to process
            scan_counter: Scan counter
        """
        try:
            # Step 1: OCR (async)
            text = await self.ocr_service.process_image_async(img, region_idx, scan_counter)

            if not text:
                return

            # Step 2: Translation (async, if available)
            if self.translation_service.is_available():
                result = await self.translation_service.translate_async(text, region_idx, scan_counter)

                if result:
                    # Step 3: Update overlay (thread-safe)
                    self.overlay_service.update_translation(region_idx, result)

                    # Step 4: Save to Firebase history
                    await self._save_to_history(
                        source_text=text,
                        translated_text=result.translation,
                        source_lang=result.source_lang,
                        target_lang=result.target_lang,
                        model=result.model,
                        confidence=result.confidence
                    )

        except Exception as e:
            print(f"[Async Processing Service] Error processing region {region_idx} (list mode): {e}")

    async def _process_region_positioned(self, region_idx: int, img: Image.Image, scan_counter: int, region_coords: tuple):
        """
        Process region for POSITIONED overlay mode (new behavior)

        Args:
            region_idx: Region index
            img: PIL Image to process
            scan_counter: Scan counter
            region_coords: Region's absolute screen coordinates (x1, y1, x2, y2)
        """
        try:
            if region_coords is None:
                print(f"[Async Processing Service] Warning: region_coords is None")
                return

            # Step 1: OCR with bounding boxes (async)
            text_boxes = await self.ocr_service.process_image_with_boxes_async(
                img, region_idx, region_coords, scan_counter
            )

            if not text_boxes:
                return

            # Step 2: Translation of text boxes (async, if available)
            if self.translation_service.is_available():
                translated_boxes = await self.translation_service.translate_text_boxes_async(
                    text_boxes, scan_counter
                )

                if translated_boxes:
                    # Step 3: Update positioned overlay (thread-safe)
                    self.overlay_service.update_positioned_overlay(region_idx, translated_boxes)

                    # Step 4: Save to history ONLY in "region" mode (not realtime)
                    if self.translation_mode == "region":
                        for box in translated_boxes:
                            await self._save_to_history(
                                source_text=box.original_text,
                                translated_text=box.translated_text,
                                source_lang=self.translation_service.source_lang,
                                target_lang=self.translation_service.target_lang,
                                model=box.model,
                                confidence=box.confidence
                            )

        except Exception as e:
            print(f"[Async Processing Service] Error processing region {region_idx} (positioned mode): {e}")
            import traceback
            traceback.print_exc()

    async def process_multiple_regions(self, regions: Dict[int, tuple]):
        """
        Process multiple regions in parallel

        Args:
            regions: Dict[region_idx, (img, scan_counter)]
        """
        tasks = [
            self._process_region(region_idx, img, scan_counter)
            for region_idx, (img, scan_counter) in regions.items()
        ]

        # Run all tasks concurrently
        await asyncio.gather(*tasks, return_exceptions=True)

    def process_region_change(self, idx: int, img: Image.Image, scan_counter: int, region_coords: tuple = None):
        """
        Process a region change (called from monitor tab)

        Args:
            idx: Region index
            img: PIL Image to process
            scan_counter: Scan counter
            region_coords: Region's absolute screen coordinates (x1, y1, x2, y2)
        """
        self.process_region_async(idx, img, scan_counter, region_coords)

    def is_running(self) -> bool:
        """Check if async processing is running"""
        return self._running
