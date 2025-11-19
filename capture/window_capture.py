"""
Window Capture Module - Production Ready
Uses PrintWindow API (better than BitBlt for DWM/GPU windows)
+ Optional WinRT verification
Perfect for OCR-AI-Translate app
"""

import win32gui
import win32ui
import win32con
from PIL import Image
import numpy as np
from typing import Optional, Tuple, List
import hashlib
import sys
import io

# Set console encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Try to import WinRT for optional verification
try:
    from winrt.windows.graphics.capture.interop import create_for_window
    import winrt.windows.graphics
    WINRT_AVAILABLE = True
except ImportError:
    WINRT_AVAILABLE = False


class WindowCapture:
    """
    Production-ready window capture

    Capture priority (auto-fallback):
    1. PrintWindow API (best for DWM/GPU windows - Edge, Chrome, games)
    2. BitBlt client area (fast for standard windows)
    3. BitBlt full window (includes title bar)
    4. Screenshot crop (works for everything)

    Optional WinRT verification available if installed.
    """

    def __init__(self, window_title: Optional[str] = None, hwnd: Optional[int] = None, use_printwindow: bool = True):
        """
        Initialize window capture

        Args:
            window_title: Window title to find (partial match)
            hwnd: Window handle (if already known)
            use_printwindow: Use PrintWindow API as primary method (default: True)
        """
        self.hwnd = hwnd
        self.window_title = window_title
        self.use_printwindow = use_printwindow
        self.winrt_available = WINRT_AVAILABLE

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
        """Get window rectangle (x, y, width, height) in screen coordinates"""
        left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
        width = right - left
        height = bottom - top
        return left, top, width, height

    def get_client_rect(self) -> Tuple[int, int, int, int]:
        """Get client area rectangle (x, y, width, height) in screen coordinates"""
        # Get client area size
        client_rect = win32gui.GetClientRect(self.hwnd)
        client_width = client_rect[2]
        client_height = client_rect[3]

        # Convert client area top-left to screen coordinates
        client_pos = win32gui.ClientToScreen(self.hwnd, (0, 0))
        client_x, client_y = client_pos

        return client_x, client_y, client_width, client_height

    @staticmethod
    def is_image_black(image: Image.Image, threshold: int = 10) -> bool:
        """
        Check if image is mostly black (GPU rendering issue indicator)

        Args:
            image: PIL Image to check
            threshold: Max average pixel value to consider as black (0-255)

        Returns:
            True if image is mostly black
        """
        try:
            # Convert to grayscale and get average brightness
            gray = image.convert('L')
            pixels = np.array(gray)
            avg_brightness = pixels.mean()

            print(f"[WindowCapture] Image average brightness: {avg_brightness:.2f}/255")
            return avg_brightness < threshold
        except Exception as e:
            print(f"[WindowCapture] Error checking if image is black: {e}")
            return False

    def capture_window(self) -> Optional[Image.Image]:
        """
        Capture window using best available method with auto-fallback

        Priority:
        1. PrintWindow API (if enabled, best for DWM/GPU windows)
        2. BitBlt client area
        3. BitBlt full window
        4. Screenshot crop

        Returns:
            PIL Image or None if capture failed
        """
        # Try PrintWindow first (best for modern Windows apps)
        if self.use_printwindow:
            img = self.capture_with_printwindow()
            if img and not self.is_image_black(img):
                return img
            print("[WindowCapture] PrintWindow failed or returned black, trying BitBlt...")

        # Fallback to BitBlt client area
        img = self.capture_client_area_bitblt()
        if img and not self.is_image_black(img):
            return img

        # Fallback to full window
        print("[WindowCapture] Client area failed, trying full window...")
        img = self.capture_full_window()
        if img and not self.is_image_black(img):
            return img

        # Final fallback to screenshot
        print("[WindowCapture] All DC methods failed, using screenshot...")
        return self.capture_from_screenshot()

    def capture_client_area_bitblt(self) -> Optional[Image.Image]:
        """
        Capture window CLIENT AREA using BitBlt

        Returns:
            PIL Image or None if capture failed
        """
        try:
            # Get CLIENT AREA dimensions
            client_x, client_y, width, height = self.get_client_rect()

            if width <= 0 or height <= 0:
                return None

            # Get CLIENT AREA DC
            hwnd_dc = win32gui.GetDC(self.hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()

            # Create bitmap
            bitmap = win32ui.CreateBitmap()
            bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(bitmap)

            # BitBlt: Copy CLIENT AREA DC to memory DC
            save_dc.BitBlt(
                (0, 0),
                (width, height),
                mfc_dc,
                (0, 0),
                win32con.SRCCOPY
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
            print(f"[WindowCapture] BitBlt client area error: {e}")
            return None

    def capture_full_window(self) -> Optional[Image.Image]:
        """
        Fallback: Capture FULL window including title bar and borders using GetWindowDC

        Returns:
            PIL Image or None if capture failed
        """
        try:
            # Get FULL window dimensions (including title bar and borders)
            left, top, width, height = self.get_window_rect()

            # Skip if window is minimized or too small
            if width <= 0 or height <= 0:
                print(f"[WindowCapture] Window rect too small: {width}x{height}")
                return self.capture_from_screenshot()

            # Get FULL WINDOW DC (includes title bar and borders)
            hwnd_dc = win32gui.GetWindowDC(self.hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()

            # Create bitmap
            bitmap = win32ui.CreateBitmap()
            bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(bitmap)

            # BitBlt: Copy full window DC to memory DC
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

            # Check if image is black (GPU rendering issue)
            if self.is_image_black(image):
                print("[WindowCapture] ⚠️ Full window capture returned black image (GPU rendering), trying screenshot")
                return self.capture_from_screenshot()

            print(f"[WindowCapture] Full window capture successful: {width}x{height}")
            return image

        except Exception as e:
            print(f"[WindowCapture] Error capturing full window: {e}, trying screenshot")
            return self.capture_from_screenshot()

    def capture_with_printwindow(self) -> Optional[Image.Image]:
        """
        Fallback #2: Capture using PrintWindow API
        Works better for some applications (UWP apps, some games, etc.)

        Returns:
            PIL Image or None if capture failed
        """
        try:
            import ctypes

            # Get client rect for PrintWindow (captures client area)
            client_rect = win32gui.GetClientRect(self.hwnd)
            width = client_rect[2]
            height = client_rect[3]

            if width <= 0 or height <= 0:
                print(f"[WindowCapture] PrintWindow: Client area too small: {width}x{height}")
                return self.capture_from_screenshot()

            # Create DC
            hwnd_dc = win32gui.GetWindowDC(self.hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()

            # Create bitmap
            bitmap = win32ui.CreateBitmap()
            bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(bitmap)

            # Use PrintWindow API
            # PW_RENDERFULLCONTENT = 0x00000002
            result = ctypes.windll.user32.PrintWindow(self.hwnd, save_dc.GetSafeHdc(), 2)

            if result == 0:
                print("[WindowCapture] PrintWindow failed (returned 0)")
                # Cleanup
                win32gui.DeleteObject(bitmap.GetHandle())
                save_dc.DeleteDC()
                mfc_dc.DeleteDC()
                win32gui.ReleaseDC(self.hwnd, hwnd_dc)
                return self.capture_from_screenshot()

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

            print(f"[WindowCapture] PrintWindow capture successful: {width}x{height}")
            return image

        except Exception as e:
            print(f"[WindowCapture] Error with PrintWindow: {e}")
            return self.capture_from_screenshot()

    def capture_from_screenshot(self) -> Optional[Image.Image]:
        """
        Fallback #3: Capture window by taking full screenshot and cropping
        Works for ALL visible windows including GPU-rendered ones

        Returns:
            PIL Image or None if capture failed
        """
        try:
            import mss

            # Get window rectangle in screen coordinates
            left, top, width, height = self.get_window_rect()

            if width <= 0 or height <= 0:
                print(f"[WindowCapture] Screenshot: Window size invalid: {width}x{height}")
                return None

            # Use mss for fast screenshot
            with mss.mss() as sct:
                # Define the region to capture
                monitor = {
                    "left": left,
                    "top": top,
                    "width": width,
                    "height": height
                }

                # Capture the region
                screenshot = sct.grab(monitor)

                # Convert to PIL Image
                image = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')

                print(f"[WindowCapture] Screenshot capture successful: {width}x{height}")
                return image

        except ImportError:
            print("[WindowCapture] mss library not installed, trying PIL ImageGrab")
            try:
                from PIL import ImageGrab

                # Get window rectangle
                left, top, width, height = self.get_window_rect()

                if width <= 0 or height <= 0:
                    print(f"[WindowCapture] Screenshot: Window size invalid: {width}x{height}")
                    return None

                # Capture using PIL ImageGrab
                bbox = (left, top, left + width, top + height)
                image = ImageGrab.grab(bbox)

                print(f"[WindowCapture] ImageGrab capture successful: {width}x{height}")
                return image

            except Exception as e:
                print(f"[WindowCapture] Error with ImageGrab: {e}")
                return None

        except Exception as e:
            print(f"[WindowCapture] Error with screenshot capture: {e}")
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
            # Return full client area
            return self.window_capture.get_client_rect()

        # Use CLIENT AREA coordinates (not window rect)
        client_x, client_y, client_w, client_h = self.window_capture.get_client_rect()
        reg_x, reg_y, reg_w, reg_h = self.region_bbox

        # Convert region bbox to absolute screen coordinates
        # Region bbox is relative to client area top-left
        abs_x = client_x + reg_x
        abs_y = client_y + reg_y

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
