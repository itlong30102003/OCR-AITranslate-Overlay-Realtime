"""Overlay Service - Handles overlay display management"""

import threading
from typing import Dict, List, Set
from overlay.tkinter_overlay import get_overlay
from overlay.positioned_overlay_qt import get_positioned_overlay_qt


class OverlayService:
    """Service for managing overlay display"""

    def __init__(self, enabled: bool = True, overlay_mode: str = "list"):
        """
        Initialize Overlay Service

        Args:
            enabled: Whether overlay is enabled by default
            overlay_mode: Overlay mode - "list" (default) or "positioned"
        """
        self.enabled = enabled
        self.overlay_mode = overlay_mode

        # List overlay (original)
        self.overlay = get_overlay()
        self.translation_results: Dict[int, Dict] = {}

        # Positioned overlay (new)
        self.positioned_overlay = None  # Lazy initialization
        self.positioned_text_boxes: Dict[int, List] = {}  # Store text boxes by region
        
        # Track deleted regions to prevent race conditions
        self.deleted_regions: Set[int] = set()

        self._lock = threading.Lock()  # Thread-safe lock for async updates
        print(f"[Overlay Service] Initialized (enabled: {enabled}, mode: {overlay_mode})")

    def update_translation(self, region_idx: int, result: Dict):
        """
        Update translation result for a region (Thread-safe)

        Args:
            region_idx: Region index
            result: Translation result dictionary
        """
        if not self.enabled:
            return

        try:
            # Thread-safe update
            with self._lock:
                # Store result
                self.translation_results[region_idx] = result

            # Get or create a Tk root to schedule updates
            import tkinter as tk
            try:
                # Try to get existing root
                root = tk._default_root
                if root is None:
                    # No root exists, try to create a hidden one
                    root = tk.Tk()
                    root.withdraw()

                # Schedule update on main thread
                root.after(0, self._update_overlay_ui)
                print(f"[Overlay Service] Scheduled update for region {region_idx} - Total: {len(self.translation_results)}")
            except Exception as e:
                print(f"[Overlay Service] Error scheduling update: {e}")

        except Exception as e:
            print(f"[Overlay Service] Error updating region {region_idx}: {e}")

    def _update_overlay_ui(self):
        """Update overlay UI (must be called from main thread)"""
        try:
            with self._lock:
                results_copy = self.translation_results.copy()
            self.overlay.update_translations(results_copy)
        except Exception as e:
            print(f"[Overlay Service] Error in UI update: {e}")

    def show_results(self):
        """Show the overlay window with current results"""
        if not self.translation_results:
            print("[Overlay Service] No results to show")
            return

        try:
            self.overlay.show()
            self.overlay.update_translations(self.translation_results)
            print(f"[Overlay Service] Showing {len(self.translation_results)} results")
        except Exception as e:
            print(f"[Overlay Service] Error showing results: {e}")

    def hide_overlay(self):
        """Hide the overlay window"""
        try:
            self.overlay.hide()
            print("[Overlay Service] Overlay hidden")
        except Exception as e:
            print(f"[Overlay Service] Error hiding overlay: {e}")

    def clear_results(self):
        """Clear all translation results"""
        self.translation_results.clear()
        if self.enabled:
            try:
                self.overlay.update_translations(self.translation_results)
                print("[Overlay Service] Results cleared")
            except Exception as e:
                print(f"[Overlay Service] Error clearing results: {e}")

    def set_enabled(self, enabled: bool):
        """
        Enable or disable overlay

        Args:
            enabled: True to enable, False to disable
        """
        self.enabled = enabled
        if not enabled:
            self.hide_overlay()
        print(f"[Overlay Service] {'Enabled' if enabled else 'Disabled'}")

    def is_enabled(self) -> bool:
        """Check if overlay is enabled"""
        return self.enabled

    def get_results(self) -> Dict[int, Dict]:
        """Get all translation results"""
        return self.translation_results.copy()

    def get_result_count(self) -> int:
        """Get number of stored results"""
        return len(self.translation_results)

    def _get_positioned_overlay(self):
        """Get or create positioned overlay instance (lazy initialization)"""
        if self.positioned_overlay is None:
            # Use PyQt6 overlay (singleton)
            self.positioned_overlay = get_positioned_overlay_qt()
        return self.positioned_overlay

    def update_positioned_overlay(self, region_idx: int, translated_boxes: List):
        """
        Update positioned overlay with translated text boxes (Thread-safe)

        Args:
            region_idx: Region index
            translated_boxes: List of TranslatedTextBox objects
        """
        if not self.enabled:
            return

        try:
            # Thread-safe update
            with self._lock:
                # Check if this region was deleted (race condition prevention)
                if region_idx in self.deleted_regions:
                    print(f"[Overlay Service] Skipping update for deleted region {region_idx}")
                    return
                    
                # Store text boxes for this region
                self.positioned_text_boxes[region_idx] = translated_boxes

                # Flatten all text boxes from all regions
                all_boxes = []
                for boxes in self.positioned_text_boxes.values():
                    all_boxes.extend(boxes)

            # Get overlay instance
            overlay = self._get_positioned_overlay()

            # Update overlay (PyQt signals handle thread-safety)
            overlay.update_text_boxes(all_boxes)
            print(f"[Overlay Service] Updated positioned overlay - Region {region_idx}: {len(translated_boxes)} boxes, Total: {len(all_boxes)} boxes")

        except Exception as e:
            print(f"[Overlay Service] Error updating positioned overlay: {e}")

    def show_positioned_overlay(self):
        """Show the positioned overlay window"""
        try:
            overlay = self._get_positioned_overlay()
            overlay.show()
            print("[Overlay Service] Positioned overlay shown")
        except Exception as e:
            print(f"[Overlay Service] Error showing positioned overlay: {e}")

    def hide_positioned_overlay(self):
        """Hide the positioned overlay window"""
        if self.positioned_overlay:
            try:
                self.positioned_overlay.hide()
                print("[Overlay Service] Positioned overlay hidden")
            except Exception as e:
                print(f"[Overlay Service] Error hiding positioned overlay: {e}")

    def clear_positioned_overlay(self):
        """Clear positioned overlay"""
        self.positioned_text_boxes.clear()
        if self.positioned_overlay:
            try:
                self.positioned_overlay.clear()
                print("[Overlay Service] Positioned overlay cleared")
            except Exception as e:
                print(f"[Overlay Service] Error clearing positioned overlay: {e}")

    def clear_region_overlay(self, region_id: int):
        """
        Clear overlay for a specific region only (Thread-safe)

        Args:
            region_id: Region ID to remove
        """
        try:
            # Thread-safe removal
            with self._lock:
                # Mark as deleted FIRST to prevent async updates from recreating it
                self.deleted_regions.add(region_id)
                
                # Remove this region's text boxes
                if region_id in self.positioned_text_boxes:
                    removed_count = len(self.positioned_text_boxes[region_id])
                    del self.positioned_text_boxes[region_id]
                    print(f"[Overlay Service] Removed region {region_id} ({removed_count} boxes)")
                else:
                    print(f"[Overlay Service] Region {region_id} marked as deleted (not yet in overlay)")

                # Flatten remaining text boxes from all other regions
                all_boxes = []
                for boxes in self.positioned_text_boxes.values():
                    all_boxes.extend(boxes)

            # Get overlay instance
            if self.positioned_overlay:
                # Update overlay with remaining boxes
                self.positioned_overlay.update_text_boxes(all_boxes)
                print(f"[Overlay Service] Updated overlay after removing region {region_id}")
                print(f"  - Remaining: {len(all_boxes)} boxes from {len(self.positioned_text_boxes)} regions")
            else:
                print(f"[Overlay Service] No positioned overlay instance to update")

        except Exception as e:
            import traceback
            print(f"[Overlay Service] Error clearing region {region_id} overlay:")
            traceback.print_exc()

    def set_overlay_mode(self, mode: str):
        """
        Set overlay mode and switch between overlays

        Args:
            mode: "list" or "positioned"
        """
        if mode not in ["list", "positioned"]:
            print(f"[Overlay Service] Invalid mode: {mode}")
            return

        self.overlay_mode = mode
        print(f"[Overlay Service] Overlay mode set to: {mode}")

        # Hide the overlay we're switching away from
        if mode == "positioned":
            self.hide_overlay()
        else:
            self.hide_positioned_overlay()

    def get_overlay_mode(self) -> str:
        """Get current overlay mode"""
        return self.overlay_mode
