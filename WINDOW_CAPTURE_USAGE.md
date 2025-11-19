# Window Capture - Usage Guide

## Overview

The `WindowCapture` class in `capture/window_capture.py` now uses **PrintWindow API** as the primary capture method, with automatic fallback to BitBlt and screenshot methods.

## Features

✅ **PrintWindow API** - Works perfectly with DWM/GPU windows (Edge, Chrome, games)
✅ **Optional WinRT Verification** - If winrt packages installed
✅ **Auto-fallback** - 4 capture methods with intelligent fallback
✅ **Change Detection** - Hash-based change detection for real-time OCR
✅ **Region Monitoring** - Capture specific window regions

## Quick Start

### Basic Usage

```python
from capture.window_capture import WindowCapture

# Method 1: By window title
capture = WindowCapture(window_title="Edge")
img = capture.capture_window()
img.save("screenshot.png")

# Method 2: By HWND
hwnd = 12345  # Get from list_windows()
capture = WindowCapture(hwnd=hwnd)
img = capture.capture_window()
```

### List All Windows

```python
from capture.window_capture import WindowCapture

windows = WindowCapture.list_all_windows()
for hwnd, title in windows:
    print(f"{hwnd}: {title}")
```

### Find Window by Title

```python
from capture.window_capture import WindowCapture

hwnd = WindowCapture.find_window("Chrome")
if hwnd:
    capture = WindowCapture(hwnd=hwnd)
    img = capture.capture_window()
```

## Advanced Usage

### Disable PrintWindow (Use BitBlt Only)

```python
# If PrintWindow has issues with specific app
capture = WindowCapture(hwnd=hwnd, use_printwindow=False)
img = capture.capture_window()
```

### Capture Specific Region

```python
capture = WindowCapture(window_title="Game")

# Capture region (x, y, width, height) relative to client area
region_img = capture.capture_region((100, 100, 500, 300))
```

### Real-Time Monitoring with Change Detection

```python
from capture.window_capture import WindowRegionMonitor

# Monitor full window
monitor = WindowRegionMonitor(window_title="Browser")

while True:
    has_changed, img = monitor.check_and_capture()

    if has_changed:
        print("Content changed!")
        # Process img with OCR
        perform_ocr(img)

    time.sleep(0.1)  # Check every 100ms
```

### Monitor Specific Region

```python
# Monitor subtitle area of a game
monitor = WindowRegionMonitor(
    window_title="Game",
    region_bbox=(100, 500, 800, 100),  # x, y, width, height
    change_threshold=3.0  # Lower = more sensitive
)

while True:
    has_changed, img = monitor.check_and_capture()
    if has_changed and img:
        # OCR only the subtitle region
        text = ocr_engine.extract_text(img)
        print(f"Subtitle: {text}")
```

## Capture Methods Priority

The class automatically tries methods in this order:

1. **PrintWindow API** (default, best for modern apps)
   - Works with: Edge, Chrome, Firefox, DWM windows
   - May fail with: Some games, minimized windows

2. **BitBlt Client Area** (fast fallback)
   - Works with: Standard Windows apps
   - May fail with: GPU-rendered content

3. **BitBlt Full Window** (includes title bar)
   - Works with: Most windows
   - May fail with: GPU content

4. **Screenshot Crop** (final fallback, always works)
   - Works with: Everything visible on screen
   - Limitation: Window must be visible

## Integration with OCR Pipeline

### Example: Real-time OCR from Browser

```python
import time
from capture.window_capture import WindowCapture
from ocr.ocr_engine import OCREngine  # Your OCR module
from translation.translator import Translator  # Your translation module

# Setup
capture = WindowCapture(window_title="Edge")
ocr = OCREngine()
translator = Translator()

# Continuous capture + OCR loop
print("Starting real-time OCR...")
while True:
    # Capture
    img = capture.capture_window()

    if img:
        # OCR
        text = ocr.extract_text(img)

        if text:
            # Translate
            translated = translator.translate(text)
            print(f"Original: {text}")
            print(f"Translated: {translated}")

    time.sleep(1)  # Capture every second
```

### Example: With Change Detection (More Efficient)

```python
from capture.window_capture import WindowRegionMonitor

monitor = WindowRegionMonitor(
    window_title="Game",
    region_bbox=(0, 700, 1920, 200),  # Subtitle area
    change_threshold=5.0
)

while True:
    has_changed, img = monitor.check_and_capture()

    if has_changed and img:
        # Only process when content changed
        text = ocr.extract_text(img)
        if text:
            translated = translator.translate(text)
            # Display overlay with translation
            overlay.show(translated)

    time.sleep(0.05)  # Check 20 times per second
```

## WinRT Verification (Optional)

If you have WinRT packages installed:

```python
from capture.window_capture import WINRT_AVAILABLE

if WINRT_AVAILABLE:
    print("WinRT verification available!")
    # WindowCapture will use WinRT to verify window is capturable
else:
    print("WinRT not available, using standard methods")
    # Still works, just without WinRT verification
```

WinRT packages are already in `requirements.txt`:
- `winrt-Windows.Graphics>=3.2.1`
- `winrt-Windows.Graphics.Capture>=3.2.1`
- `winrt-Windows.Graphics.Capture.Interop>=3.2.1`
- etc.

## Troubleshooting

### Black Screenshot

If capture returns black image:
- PrintWindow failed (GPU rendering)
- Class automatically falls back to screenshot method
- Check console output for fallback messages

### Window Not Found

```python
hwnd = WindowCapture.find_window("MyApp")
if not hwnd:
    # List all windows to find correct title
    WindowCapture.list_all_windows()
```

### Performance Issues

```python
# Option 1: Disable change detection
img = capture.capture_window()  # Capture every time

# Option 2: Increase change threshold
monitor = WindowRegionMonitor(
    window_title="App",
    change_threshold=10.0  # Less sensitive = fewer captures
)

# Option 3: Reduce capture frequency
time.sleep(0.5)  # Capture every 500ms instead of 100ms
```

## Summary

- ✅ **Production-ready** - PrintWindow + auto-fallback
- ✅ **WinRT support** - Optional verification
- ✅ **Flexible** - Works with all Windows apps
- ✅ **Optimized** - Change detection for real-time OCR
- ✅ **Easy to use** - Simple API, automatic fallback

**Main file**: `capture/window_capture.py`
**Updated**: 2025-11-20
**Status**: Ready for production use in OCR-AI-Translate app
