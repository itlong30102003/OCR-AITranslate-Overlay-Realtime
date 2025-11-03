"""Async Processing Service - Handles parallel OCR and Translation"""

import asyncio
import threading
from typing import Dict, Optional
from PIL import Image


class AsyncProcessingService:
    """Service for managing async OCR and Translation pipeline"""

    def __init__(self, ocr_service, translation_service, overlay_service):
        """
        Initialize Async Processing Service

        Args:
            ocr_service: OCRService instance
            translation_service: TranslationService instance
            overlay_service: OverlayService instance
        """
        self.ocr_service = ocr_service
        self.translation_service = translation_service
        self.overlay_service = overlay_service

        # Event loop for async processing
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._running = False

        print("[Async Processing Service] Initialized")

    def start(self):
        """Start the async processing event loop in a separate thread"""
        if self._running:
            return

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
        if self._loop:
            # Cancel all pending tasks
            pending = asyncio.all_tasks(self._loop)
            for task in pending:
                self._loop.call_soon_threadsafe(task.cancel)

            # Stop the loop
            self._loop.call_soon_threadsafe(self._loop.stop)
        print("[Async Processing Service] Stopped")

    def process_region_async(self, region_idx: int, img: Image.Image, scan_counter: int):
        """
        Process a region asynchronously (OCR + Translation + Overlay update)

        Args:
            region_idx: Region index
            img: PIL Image to process
            scan_counter: Scan counter
        """
        if not self._running or not self._loop:
            print("[Async Processing Service] Not running, starting...")
            self.start()
            # Wait a bit for loop to start
            import time
            time.sleep(0.1)

        # Schedule the async task
        asyncio.run_coroutine_threadsafe(
            self._process_region(region_idx, img, scan_counter),
            self._loop
        )

    async def _process_region(self, region_idx: int, img: Image.Image, scan_counter: int):
        """
        Internal async method to process region

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

        except Exception as e:
            print(f"[Async Processing Service] Error processing region {region_idx}: {e}")

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

    def is_running(self) -> bool:
        """Check if async processing is running"""
        return self._running
