"""Async Processing Service - Handles parallel OCR and Translation"""

import asyncio
import threading
from typing import Dict, Optional
from PIL import Image


class AsyncProcessingService:
    """Service for managing async OCR and Translation pipeline"""

    def __init__(self, ocr_service, translation_service, overlay_service, overlay_mode: str = "list"):
        """
        Initialize Async Processing Service

        Args:
            ocr_service: OCRService instance
            translation_service: TranslationService instance
            overlay_service: OverlayService instance
            overlay_mode: Overlay mode - "list" (default) or "positioned"
        """
        self.ocr_service = ocr_service
        self.translation_service = translation_service
        self.overlay_service = overlay_service
        self.overlay_mode = overlay_mode  # "list" or "positioned"

        # Event loop for async processing
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._running = False

        print(f"[Async Processing Service] Initialized (mode: {overlay_mode})")

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
            time.sleep(0.1)

        # Schedule the async task
        asyncio.run_coroutine_threadsafe(
            self._process_region(region_idx, img, scan_counter, region_coords),
            self._loop
        )

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

    async def _process_region(self, region_idx: int, img: Image.Image, scan_counter: int, region_coords: tuple = None):
        """
        Internal async method to process region

        Args:
            region_idx: Region index
            img: PIL Image to process
            scan_counter: Scan counter
            region_coords: Region's absolute screen coordinates (x1, y1, x2, y2)
        """
        try:
            # Branch based on overlay mode
            if self.overlay_mode == "positioned":
                await self._process_region_positioned(region_idx, img, scan_counter, region_coords)
            else:
                await self._process_region_list(region_idx, img, scan_counter)

        except Exception as e:
            print(f"[Async Processing Service] Error processing region {region_idx}: {e}")

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
                print(f"[Async Processing Service] Warning: region_coords is None for positioned mode")
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

        except Exception as e:
            print(f"[Async Processing Service] Error processing region {region_idx} (positioned mode): {e}")

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
