"""Overlay Service - Handles overlay display management"""

from typing import Dict
from overlay.tkinter_overlay import get_overlay


class OverlayService:
    """Service for managing overlay display"""

    def __init__(self, enabled: bool = True):
        """
        Initialize Overlay Service

        Args:
            enabled: Whether overlay is enabled by default
        """
        self.enabled = enabled
        self.overlay = get_overlay()
        self.translation_results: Dict[int, Dict] = {}
        print(f"[Overlay Service] Initialized (enabled: {enabled})")

    def update_translation(self, region_idx: int, result: Dict):
        """
        Update translation result for a region

        Args:
            region_idx: Region index
            result: Translation result dictionary
        """
        if not self.enabled:
            return

        try:
            # Store result
            self.translation_results[region_idx] = result

            # Update overlay
            self.overlay.update_translations(self.translation_results)
            print(f"[Overlay Service] Updated region {region_idx} - Total: {len(self.translation_results)}")

        except Exception as e:
            print(f"[Overlay Service] Error updating region {region_idx}: {e}")

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
