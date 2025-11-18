"""
Demo: Window DC Capture + Hash Detection + OCR + Overlay
Method: target window -> bbox -> capture -> OCR -> overlay

Advantages:
- BitBlt captures window directly (no overlay interference)
- Hash detection prevents unnecessary OCR
- No flicker, high performance
- No need to hide overlay during capture
"""

import sys
import time
from pathlib import Path
from typing import Optional, Dict, List
import threading
from dataclasses import dataclass

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from capture.window_capture import (
    WindowCapture,
    WindowRegionMonitor,
    HashChangeDetector,
    list_windows,
    select_window_interactive
)
from capture.window_region_selector import select_window_region_interactive
from ocr.ocr import run_ocr_on_image
from overlay.positioned_overlay_qt import PositionedOverlayQt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, Qt
from PIL import Image


# Simple dataclass for demo (avoid heavy imports from services)
@dataclass
class TranslatedTextBox:
    """Lightweight data structure for translated text with position"""
    original_text: str
    translated_text: str
    bbox: tuple  # Relative bbox (x1, y1, x2, y2)
    abs_bbox: tuple  # Absolute screen bbox (x1, y1, x2, y2)
    region_idx: int
    region_coords: tuple
    model: str
    confidence: float


class WindowOCRDemo:
    """Demo application for Window DC Capture + OCR + Overlay"""

    def __init__(self, hwnd: int, region_bbox: Optional[tuple] = None):
        """
        Initialize demo

        Args:
            hwnd: Target window handle
            region_bbox: (x, y, width, height) relative to window, or None for full window
        """
        self.hwnd = hwnd
        self.region_bbox = region_bbox

        # Initialize monitor
        self.monitor = WindowRegionMonitor(
            hwnd=hwnd,
            region_bbox=region_bbox,
            change_threshold=5.0  # Adjust sensitivity (lower = more sensitive)
        )

        # Initialize overlay
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.overlay = PositionedOverlayQt()

        # Stats
        self.frame_count = 0
        self.ocr_count = 0
        self.last_ocr_time = 0
        self.running = False

        # Timer for monitoring
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer)

    def start(self, fps: int = 15):
        """Start monitoring"""
        self.running = True
        interval_ms = int(1000 / fps)
        self.timer.start(interval_ms)

        print(f"\n{'='*80}")
        print(f"Window DC Capture + OCR Demo Started")
        print(f"{'='*80}")
        print(f"Target Window: {win32gui.GetWindowText(self.hwnd)}")
        print(f"Region: {self.region_bbox or 'Full Window'}")
        print(f"FPS: {fps}")
        print(f"Hash Threshold: {self.monitor.change_detector.threshold}")
        print(f"{'='*80}\n")
        print("[Press Ctrl+C to stop]")
        print()

        self.app.exec()

    def stop(self):
        """Stop monitoring"""
        self.running = False
        self.timer.stop()
        self.overlay.hide()
        print(f"\n{'='*80}")
        print(f"Demo Stopped")
        print(f"{'='*80}")
        print(f"Total Frames: {self.frame_count}")
        print(f"OCR Runs: {self.ocr_count}")
        print(f"OCR Rate: {self.ocr_count / max(1, self.frame_count) * 100:.1f}%")
        print(f"{'='*80}\n")

    def on_timer(self):
        """Timer callback - check for changes and run OCR"""
        if not self.running:
            return

        self.frame_count += 1

        try:
            # Check for changes and capture
            has_changed, image = self.monitor.check_and_capture()

            if not has_changed:
                # No change detected, skip OCR
                return

            # Change detected! Run OCR
            self.ocr_count += 1
            start_time = time.time()

            ocr_result = run_ocr_on_image(image)

            ocr_time = time.time() - start_time
            self.last_ocr_time = ocr_time

            # Update overlay
            if ocr_result:
                self.update_overlay(ocr_result)

                # Print stats
                print(f"[Frame {self.frame_count:4d}] "
                      f"OCR #{self.ocr_count:3d} | "
                      f"Lines: {len(ocr_result):2d} | "
                      f"Time: {ocr_time*1000:5.1f}ms")

                # Print detected text
                for line_id, line_data in ocr_result.items():
                    text = ' '.join(line_data['text'])
                    if text.strip():
                        print(f"  └─ {text[:60]}")

            else:
                print(f"[Frame {self.frame_count:4d}] "
                      f"OCR #{self.ocr_count:3d} | "
                      f"No text detected")

        except Exception as e:
            print(f"[ERROR] Frame {self.frame_count}: {e}")

    def update_overlay(self, ocr_result: Dict):
        """Update overlay with OCR result"""
        # Get absolute bbox for overlay positioning
        abs_bbox = self.monitor.get_absolute_bbox()

        if not abs_bbox:
            return

        abs_x, abs_y, abs_w, abs_h = abs_bbox

        # Convert OCR result to TranslatedTextBox format
        translated_boxes = []

        for line_id, line_data in ocr_result.items():
            text = ' '.join(line_data['text'])
            if not text.strip():
                continue

            # Convert relative coordinates to absolute screen coordinates
            rel_x1 = line_data['x1']
            rel_y1 = line_data['y1']
            rel_x2 = line_data['x2']
            rel_y2 = line_data['y2']

            # Add window/region offset
            screen_x1 = abs_x + rel_x1
            screen_y1 = abs_y + rel_y1
            screen_x2 = abs_x + rel_x2
            screen_y2 = abs_y + rel_y2

            # Create TranslatedTextBox object
            text_box = TranslatedTextBox(
                original_text=text,
                translated_text=text,  # In demo, just show original text
                bbox=(rel_x1, rel_y1, rel_x2, rel_y2),
                abs_bbox=(screen_x1, screen_y1, screen_x2, screen_y2),
                region_idx=0,  # Demo only has 1 region
                region_coords=(abs_x, abs_y, abs_x + abs_w, abs_y + abs_h),
                model='tesseract',
                confidence=1.0
            )
            translated_boxes.append(text_box)

        # Update overlay with TranslatedTextBox list
        self.overlay.update_text_boxes(translated_boxes)


def interactive_region_selection(window_capture: WindowCapture) -> Optional[tuple]:
    """
    Interactive region selection UI

    Returns:
        (x, y, width, height) or None for full window
    """
    print("\nRegion Selection:")
    print("  1. Full window")
    print("  2. Visual selection (click and drag)")
    print("  3. Manual input (x, y, width, height)")
    print()
    choice = input("Select option (1, 2, or 3): ").strip()

    if choice == '1':
        return None

    elif choice == '2':
        # Visual selection using Tkinter
        return select_window_region_interactive(window_capture)

    elif choice == '3':
        print("\nEnter region coordinates relative to window:")
        try:
            x = int(input("  X (left): "))
            y = int(input("  Y (top): "))
            w = int(input("  Width: "))
            h = int(input("  Height: "))
            return (x, y, w, h)
        except ValueError:
            print("Invalid input. Using full window.")
            return None

    else:
        print("Invalid choice. Using full window.")
        return None


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print(" Window DC Capture + OCR Demo ".center(80, "="))
    print("="*80 + "\n")

    # Step 1: Select target window
    print("[Step 1/3] Select Target Window")
    hwnd = select_window_interactive()

    if not hwnd:
        print("\n✗ No window selected. Exiting.")
        return

    # Step 2: Select region
    print("\n[Step 2/3] Select Region")
    window_capture = WindowCapture(hwnd=hwnd)

    # Show window dimensions
    win_x, win_y, win_w, win_h = window_capture.get_window_rect()
    print(f"\nWindow dimensions: {win_w} x {win_h}")

    region_bbox = interactive_region_selection(window_capture)

    # Step 3: Start demo
    print("\n[Step 3/3] Starting Demo...")

    try:
        demo = WindowOCRDemo(hwnd=hwnd, region_bbox=region_bbox)
        demo.start(fps=15)
    except KeyboardInterrupt:
        print("\n\n[Interrupted by user]")
        demo.stop()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


def quick_demo_notepad():
    """Quick demo targeting Notepad"""
    print("\n" + "="*80)
    print(" Quick Demo - Targeting Notepad ".center(80, "="))
    print("="*80 + "\n")

    hwnd = WindowCapture.find_window("Notepad")

    if not hwnd:
        print("✗ Notepad not found. Please open Notepad and try again.")
        return

    print(f"✓ Found Notepad (HWND: {hwnd})")

    # Monitor full Notepad window
    demo = WindowOCRDemo(hwnd=hwnd, region_bbox=None)

    try:
        demo.start(fps=10)
    except KeyboardInterrupt:
        print("\n\n[Interrupted by user]")
        demo.stop()


if __name__ == "__main__":
    import win32gui

    # Choose demo mode
    print("\nDemo Mode:")
    print("  1. Interactive (select any window)")
    print("  2. Quick demo (Notepad)")
    print()

    mode = input("Select mode (1 or 2): ").strip()

    if mode == '2':
        quick_demo_notepad()
    else:
        main()
