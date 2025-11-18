"""
Window DC Capture Module - BitBlt method
Capture specific window without overlay interference
High performance, no flicker
"""

import win32gui
import win32ui
import win32con
from PIL import Image
import numpy as np
from typing import Optional, Tuple, List
import hashlib


class WindowCapture:
    """Capture specific window using Windows DC BitBlt"""

    def __init__(self, window_title: Optional[str] = None, hwnd: Optional[int] = None):
        """
        Initialize window capture

        Args:
            window_title: Window title to find (partial match)
            hwnd: Window handle (if already known)
        """
        self.hwnd = hwnd
        self.window_title = window_title

        if not self.hwnd and self.window_title:
            self.hwnd = self.find_window(self.window_title)

        if not self.hwnd:
            raise ValueError("No window handle provided or found")

    @staticmethod
    def list_all_windows() -> List[Tuple[int, str]]:
        """List all visible windows with titles"""
        windows = []

        def enum_callback(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    results.append((hwnd, title))

        win32gui.EnumWindows(enum_callback, windows)
        return windows

    @staticmethod
    def find_window(title_substring: str) -> Optional[int]:
        """Find window by title substring (case-insensitive)"""
        windows = WindowCapture.list_all_windows()
        title_lower = title_substring.lower()

        for hwnd, title in windows:
            if title_lower in title.lower():
                return hwnd

        return None

    def get_window_rect(self) -> Tuple[int, int, int, int]:
        """Get window rectangle (x, y, width, height)"""
        left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
        width = right - left
        height = bottom - top
        return left, top, width, height

    def capture_window(self) -> Optional[Image.Image]:
        """
        Capture window using BitBlt (Windows DC)
        This captures ONLY the window content, ignoring overlays

        Returns:
            PIL Image or None if capture failed
        """
        try:
            # Get window dimensions
            left, top, width, height = self.get_window_rect()

            # Skip if window is minimized or too small
            if width <= 0 or height <= 0:
                return None

            # Get window DC
            hwnd_dc = win32gui.GetWindowDC(self.hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()

            # Create bitmap
            bitmap = win32ui.CreateBitmap()
            bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(bitmap)

            # BitBlt: Copy window DC to memory DC
            # This is the KEY: BitBlt captures window content directly
            # without overlay interference!
            save_dc.BitBlt(
                (0, 0),           # Destination top-left
                (width, height),  # Dimensions
                mfc_dc,           # Source DC
                (0, 0),           # Source top-left
                win32con.SRCCOPY  # Copy mode
            )

            # Convert bitmap to PIL Image
            bmp_info = bitmap.GetInfo()
            bmp_str = bitmap.GetBitmapBits(True)

            image = Image.frombuffer(
                'RGB',
                (bmp_info['bmWidth'], bmp_info['bmHeight']),
                bmp_str,
                'raw',
                'BGRX',
                0,
                1
            )

            # Cleanup
            win32gui.DeleteObject(bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(self.hwnd, hwnd_dc)

            return image

        except Exception as e:
            print(f"[WindowCapture] Error capturing window: {e}")
            return None

    def capture_region(self, bbox: Tuple[int, int, int, int]) -> Optional[Image.Image]:
        """
        Capture specific region of window

        Args:
            bbox: (x, y, width, height) relative to window client area

        Returns:
            PIL Image or None
        """
        full_image = self.capture_window()
        if not full_image:
            return None

        x, y, w, h = bbox

        # Ensure bbox is within bounds
        img_w, img_h = full_image.size
        x = max(0, min(x, img_w))
        y = max(0, min(y, img_h))
        w = min(w, img_w - x)
        h = min(h, img_h - y)

        if w <= 0 or h <= 0:
            return None

        return full_image.crop((x, y, x + w, y + h))


class HashChangeDetector:
    """Detect image changes using perceptual hash"""

    def __init__(self, threshold: float = 5.0):
        """
        Initialize change detector

        Args:
            threshold: Hamming distance threshold for change detection
                      Lower = more sensitive (detect small changes)
                      Higher = less sensitive (only detect big changes)
        """
        self.threshold = threshold
        self.previous_hash = None

    @staticmethod
    def compute_dhash(image: Image.Image, hash_size: int = 8) -> str:
        """
        Compute difference hash (dHash) for image
        Fast and effective for change detection

        Args:
            image: PIL Image
            hash_size: Hash size (default 8 = 64 bits)

        Returns:
            Hash string (hex)
        """
        # Convert to grayscale and resize
        gray = image.convert('L').resize((hash_size + 1, hash_size), Image.LANCZOS)
        pixels = np.array(gray)

        # Compute horizontal gradient
        diff = pixels[:, 1:] > pixels[:, :-1]

        # Convert to hash
        hash_bytes = np.packbits(diff.flatten())
        return hash_bytes.tobytes().hex()

    @staticmethod
    def hamming_distance(hash1: str, hash2: str) -> int:
        """Compute Hamming distance between two hashes"""
        if len(hash1) != len(hash2):
            return float('inf')

        # Convert hex to binary and count different bits
        bytes1 = bytes.fromhex(hash1)
        bytes2 = bytes.fromhex(hash2)

        distance = 0
        for b1, b2 in zip(bytes1, bytes2):
            xor = b1 ^ b2
            distance += bin(xor).count('1')

        return distance

    def has_changed(self, image: Image.Image) -> bool:
        """
        Check if image has changed compared to previous frame

        Args:
            image: Current frame

        Returns:
            True if changed, False otherwise
        """
        current_hash = self.compute_dhash(image)

        if self.previous_hash is None:
            # First frame, always changed
            self.previous_hash = current_hash
            return True

        # Compare with previous hash
        distance = self.hamming_distance(current_hash, self.previous_hash)
        changed = distance > self.threshold

        if changed:
            self.previous_hash = current_hash

        return changed

    def reset(self):
        """Reset detector state"""
        self.previous_hash = None


class WindowRegionMonitor:
    """Monitor specific region of a window with change detection"""

    def __init__(
        self,
        window_title: Optional[str] = None,
        hwnd: Optional[int] = None,
        region_bbox: Optional[Tuple[int, int, int, int]] = None,
        change_threshold: float = 5.0
    ):
        """
        Initialize window region monitor

        Args:
            window_title: Window title to capture
            hwnd: Window handle
            region_bbox: (x, y, width, height) or None for full window
            change_threshold: Hash threshold for change detection
        """
        self.window_capture = WindowCapture(window_title=window_title, hwnd=hwnd)
        self.region_bbox = region_bbox
        self.change_detector = HashChangeDetector(threshold=change_threshold)

    def capture_current(self) -> Optional[Image.Image]:
        """Capture current frame"""
        if self.region_bbox:
            return self.window_capture.capture_region(self.region_bbox)
        else:
            return self.window_capture.capture_window()

    def check_and_capture(self) -> Tuple[bool, Optional[Image.Image]]:
        """
        Check if region has changed and capture if so

        Returns:
            (has_changed, image)
            - has_changed: True if content changed
            - image: Captured image (only if changed)
        """
        image = self.capture_current()

        if image is None:
            return False, None

        has_changed = self.change_detector.has_changed(image)

        return has_changed, image if has_changed else None

    def get_absolute_bbox(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Get absolute screen coordinates of monitored region
        Useful for overlay positioning

        Returns:
            (x, y, width, height) in screen coordinates
        """
        if not self.region_bbox:
            return self.window_capture.get_window_rect()

        win_x, win_y, win_w, win_h = self.window_capture.get_window_rect()
        reg_x, reg_y, reg_w, reg_h = self.region_bbox

        # Convert to absolute screen coordinates
        abs_x = win_x + reg_x
        abs_y = win_y + reg_y

        return abs_x, abs_y, reg_w, reg_h


# Utility functions for easy usage

def list_windows():
    """List all available windows"""
    windows = WindowCapture.list_all_windows()
    print(f"\n{'='*80}")
    print(f"{'HWND':<12} | Window Title")
    print(f"{'='*80}")
    for hwnd, title in windows:
        print(f"{hwnd:<12} | {title}")
    print(f"{'='*80}\n")
    return windows


def select_window_interactive() -> Optional[int]:
    """Interactive window selection"""
    windows = list_windows()

    print("Enter window title (or part of it): ", end="")
    title_input = input().strip()

    hwnd = WindowCapture.find_window(title_input)

    if hwnd:
        title = win32gui.GetWindowText(hwnd)
        print(f"✓ Found window: {title} (HWND: {hwnd})")
        return hwnd
    else:
        print(f"✗ No window found matching '{title_input}'")
        return None
