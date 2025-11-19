"""
Demo script to test BitBlt capture on different windows
This will help identify which windows work with BitBlt and which don't
"""

import win32gui
import win32ui
import win32con
from PIL import Image
import numpy as np
import os
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def list_all_windows():
    """List all visible windows with titles"""
    windows = []

    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:  # Only include windows with titles
                windows.append((hwnd, title))
        return True

    win32gui.EnumWindows(callback, None)
    return windows


def analyze_image(image: Image.Image):
    """Analyze captured image for issues"""
    results = {
        'size': image.size,
        'mode': image.mode,
        'is_black': False,
        'is_transparent': False,
        'avg_brightness': 0,
        'unique_colors': 0
    }

    # Convert to RGB for analysis
    if image.mode != 'RGB':
        image = image.convert('RGB')

    # Get pixel data
    pixels = np.array(image)

    # Calculate average brightness
    gray = image.convert('L')
    avg_brightness = np.array(gray).mean()
    results['avg_brightness'] = avg_brightness

    # Check if black (brightness < 10)
    if avg_brightness < 10:
        results['is_black'] = True

    # Check if transparent/empty (all pixels same color)
    unique_colors = len(np.unique(pixels.reshape(-1, pixels.shape[2]), axis=0))
    results['unique_colors'] = unique_colors

    if unique_colors < 10:  # Very few colors = likely transparent/solid color
        results['is_transparent'] = True

    return results


def capture_with_bitblt(hwnd: int):
    """
    Capture window using pure BitBlt (no fallback)
    Returns: PIL Image or None
    """
    try:
        # Get client rect
        client_rect = win32gui.GetClientRect(hwnd)
        width = client_rect[2]
        height = client_rect[3]

        if width <= 0 or height <= 0:
            print(f"[ERROR] Client area too small: {width}x{height}")
            return None

        print(f"[SIZE] Window size: {width}x{height}")

        # Get DC
        hwnd_dc = win32gui.GetDC(hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()

        # Create bitmap
        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
        save_dc.SelectObject(bitmap)

        # BitBlt
        save_dc.BitBlt(
            (0, 0),
            (width, height),
            mfc_dc,
            (0, 0),
            win32con.SRCCOPY
        )

        # Convert to PIL Image
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
        win32gui.ReleaseDC(hwnd, hwnd_dc)

        return image

    except Exception as e:
        print(f"[ERROR] Error capturing: {e}")
        return None


def test_window(hwnd: int, title: str, save_dir: str = "bitblt_test_results"):
    """Test capture on specific window"""
    print("\n" + "="*80)
    print(f"[TEST] Testing Window: {title}")
    print(f"       HWND: {hwnd}")
    print("="*80)

    # Check window state
    is_visible = win32gui.IsWindowVisible(hwnd)
    placement = win32gui.GetWindowPlacement(hwnd)
    is_minimized = placement[1] == win32con.SW_SHOWMINIMIZED

    print(f"[STATE] Window State:")
    print(f"        Visible: {is_visible}")
    print(f"        Minimized: {is_minimized}")

    if not is_visible:
        print("[WARN]  Window is not visible!")

    if is_minimized:
        print("[WARN]  Window is minimized!")

    # Capture with BitBlt
    print(f"\n[CAPTURE] Capturing with BitBlt...")
    image = capture_with_bitblt(hwnd)

    if not image:
        print("[ERROR] FAILED: Could not capture image")
        return

    print("[OK] Capture successful!")

    # Analyze image
    print(f"\n[ANALYSIS] Analyzing captured image...")
    analysis = analyze_image(image)

    print(f"           Size: {analysis['size'][0]}x{analysis['size'][1]}")
    print(f"           Mode: {analysis['mode']}")
    print(f"           Average Brightness: {analysis['avg_brightness']:.2f}/255")
    print(f"           Unique Colors: {analysis['unique_colors']}")

    # Diagnosis
    print(f"\n[DIAGNOSIS]")
    if analysis['is_black']:
        print("   [X] BLACK IMAGE - Likely GPU rendering issue")
        print("       -> Window uses hardware acceleration (Edge, Chrome, games, etc.)")
    elif analysis['is_transparent']:
        print("   [!] TRANSPARENT/SOLID COLOR - Possible issues:")
        print("       -> Window is hidden/minimized")
        print("       -> Window has no content")
    else:
        print("   [OK] LOOKS GOOD - BitBlt capture works for this window")

    # Save image
    os.makedirs(save_dir, exist_ok=True)
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))[:50]
    filename = f"{hwnd}_{safe_title}.png"
    filepath = os.path.join(save_dir, filename)

    image.save(filepath)
    print(f"\n[SAVED] Saved to: {filepath}")

    return analysis


def main():
    """Main demo function"""
    print("\n" + "="*80)
    print("BitBlt Capture Test Tool")
    print("="*80)

    # List all windows
    print("\n[LIST] Listing all visible windows...")
    windows = list_all_windows()

    # Filter out system windows
    ignore_keywords = [
        "Program Manager",
        "Windows Input Experience",
        "Microsoft Text Input Application",
        "Settings",
        "MSCTFIME UI",
        "Default IME",
    ]

    filtered_windows = []
    for hwnd, title in windows:
        if len(title) >= 2 and not any(kw in title for kw in ignore_keywords):
            filtered_windows.append((hwnd, title))

    print(f"\nFound {len(filtered_windows)} windows:")
    print("-" * 80)

    for i, (hwnd, title) in enumerate(filtered_windows, 1):
        display_title = title[:70] + "..." if len(title) > 70 else title
        print(f"{i:3d}. [{hwnd:8d}] {display_title}")

    print("-" * 80)

    # Interactive selection
    while True:
        try:
            choice = input("\n[INPUT] Enter window number to test (or 'q' to quit, 'all' to test all): ").strip()

            if choice.lower() == 'q':
                print("Goodbye!")
                break

            if choice.lower() == 'all':
                print("\n[TEST ALL] Testing all windows...")
                results = {}
                for hwnd, title in filtered_windows:
                    analysis = test_window(hwnd, title)
                    if analysis:
                        results[(hwnd, title)] = analysis

                # Summary
                print("\n" + "="*80)
                print("[SUMMARY]")
                print("="*80)

                black_count = sum(1 for a in results.values() if a['is_black'])
                transparent_count = sum(1 for a in results.values() if a['is_transparent'])
                good_count = len(results) - black_count - transparent_count

                print(f"\nTotal tested: {len(results)}")
                print(f"[OK] Good (BitBlt works): {good_count}")
                print(f"[X] Black (GPU rendering): {black_count}")
                print(f"[!] Transparent/Empty: {transparent_count}")

                if black_count > 0:
                    print(f"\n[X] Windows with BLACK images (need screenshot fallback):")
                    for (hwnd, title), analysis in results.items():
                        if analysis['is_black']:
                            print(f"    * {title[:60]}")

                break

            idx = int(choice) - 1
            if 0 <= idx < len(filtered_windows):
                hwnd, title = filtered_windows[idx]
                test_window(hwnd, title)
            else:
                print("[ERROR] Invalid choice!")

        except ValueError:
            print("[ERROR] Invalid input!")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()
