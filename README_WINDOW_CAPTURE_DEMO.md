# Window DC Capture + OCR Demo

## Tổng quan

Demo này thể hiện phương pháp **Window DC Capture (BitBlt)** để giải quyết vấn đề race condition và tối ưu performance trong OCR realtime.

### Phương pháp truyền thống (vấn đề)

```
Full Screen Capture → Crop Region → OCR → Overlay
          ↑                                    ↓
          └────────── Race Condition! ─────────┘
```

**Vấn đề:**
- Overlay che cản khi capture → phải hide/show → nhấp nháy
- Capture toàn màn hình → tốn tài nguyên
- OCR liên tục mỗi frame → CPU cao
- Race condition giữa overlay và capture

### Phương pháp mới (Window DC Capture)

```
Target Window → Bbox → BitBlt Capture → Hash Check → OCR (if changed) → Overlay
                              ↑                                              ↓
                              └──────── No Race Condition! ─────────────────┘
```

**Ưu điểm:**
- ✅ BitBlt chỉ capture window target, bỏ qua overlay
- ✅ Không cần hide/show overlay → không nhấp nháy
- ✅ Hash detection → chỉ OCR khi có thay đổi
- ✅ Performance cao, CPU thấp
- ✅ Không có race condition

---

## Kiến trúc

### 1. Window DC Capture (`capture/window_capture.py`)

#### Class `WindowCapture`
Capture window sử dụng Windows API (BitBlt).

```python
from capture.window_capture import WindowCapture

# Tìm window theo title
hwnd = WindowCapture.find_window("Notepad")

# Khởi tạo
capture = WindowCapture(hwnd=hwnd)

# Capture toàn bộ window
image = capture.capture_window()

# Hoặc capture vùng cụ thể (x, y, width, height)
region_image = capture.capture_region((100, 50, 400, 200))
```

**Key features:**
- `BitBlt`: Windows API để copy window DC → không bị overlay che
- Hỗ trợ capture full window hoặc region
- Trả về PIL Image

#### Class `HashChangeDetector`
Phát hiện thay đổi sử dụng perceptual hash (dHash).

```python
from capture.window_capture import HashChangeDetector

detector = HashChangeDetector(threshold=5.0)

# Check từng frame
if detector.has_changed(image):
    # Content đã thay đổi → chạy OCR
    run_ocr(image)
else:
    # Không đổi → skip OCR
    pass
```

**Key features:**
- dHash (difference hash): nhanh và hiệu quả
- Threshold điều chỉnh độ nhạy:
  - Thấp (1-3): Nhạy cao, detect thay đổi nhỏ
  - Trung bình (5-10): Cân bằng
  - Cao (15+): Chỉ detect thay đổi lớn

#### Class `WindowRegionMonitor`
Kết hợp capture + hash detection.

```python
from capture.window_capture import WindowRegionMonitor

# Monitor vùng cụ thể của window
monitor = WindowRegionMonitor(
    hwnd=hwnd,
    region_bbox=(100, 50, 400, 200),  # None = full window
    change_threshold=5.0
)

# Check và capture (chỉ khi có thay đổi)
has_changed, image = monitor.check_and_capture()

if has_changed:
    # Chạy OCR
    ocr_result = run_ocr(image)

    # Lấy absolute coordinates cho overlay
    abs_x, abs_y, abs_w, abs_h = monitor.get_absolute_bbox()
```

---

### 2. Demo Application (`demo_window_capture_ocr.py`)

#### Class `WindowOCRDemo`
Demo ứng dụng hoàn chỉnh: Capture → OCR → Overlay.

**Flow:**

```
1. User chọn target window
2. User chọn region (hoặc full window)
3. Start monitoring loop (15 FPS):
   ├─ Capture window với BitBlt
   ├─ Check hash → changed?
   │  ├─ No → Skip OCR, next frame
   │  └─ Yes → Continue
   ├─ Run OCR (Tesseract)
   ├─ Convert to overlay format
   └─ Update overlay (positioned)
```

---

## Cài đặt

### 1. Dependencies

Cần thêm `pywin32` cho Windows API:

```bash
pip install pywin32
```

Các dependencies khác đã có trong `requirements.txt`:
- pytesseract
- Pillow
- PyQt6
- numpy

### 2. Tesseract OCR

Đảm bảo Tesseract đã cài đặt:
- Path: `C:\Program Files\Tesseract-OCR\tesseract.exe`
- Hoặc sửa trong `ocr/ocr.py`

---

## Cách sử dụng

### Mode 1: Interactive (Select any window)

```bash
python demo_window_capture_ocr.py
```

**Steps:**
1. Nhập 1 → Interactive mode
2. Danh sách windows hiện ra
3. Nhập tên window (hoặc một phần)
4. Chọn region:
   - Option 1: Full window
   - Option 2: Custom (x, y, width, height)
5. Demo bắt đầu

**Ví dụ:**
```
Enter window title (or part of it): Chrome
✓ Found window: Google Chrome (HWND: 12345678)

Region Selection:
  1. Full window
  2. Visual selection (click and drag)  ← NEW! Recommended
  3. Manual input (x, y, width, height)

Select option (1, 2, or 3): 2

================================================================================
Interactive Region Selection
================================================================================
Instructions:
  1. Click and drag to select a region
  2. Press ENTER to confirm selection
  3. Press ESC to use full window
================================================================================

[A Tkinter window appears showing the window screenshot]
[Click and drag to draw a red rectangle around the text area you want to monitor]
[Press ENTER]

✓ Region selected: (100, 200) - 800x400
```

**Option 3 - Manual input:**
```
Select option (1, 2, or 3): 3

Enter region coordinates relative to window:
  X (left): 100
  Y (top): 200
  Width: 800
  Height: 400
```

### Mode 2: Quick Demo (Notepad)

```bash
python demo_window_capture_ocr.py
```

Nhập 2 → Tự động target Notepad.

**Test:**
1. Mở Notepad
2. Chạy demo mode 2
3. Gõ text trong Notepad → overlay hiện ngay lập tức

---

## Demo Output

```
================================================================================
                      Window DC Capture + OCR Demo
================================================================================

[Step 1/3] Select Target Window
Enter window title (or part of it): Notepad
✓ Found window: Untitled - Notepad (HWND: 987654)

[Step 2/3] Select Region
Window dimensions: 800 x 600
Region Selection:
  1. Full window
  2. Custom region (x, y, width, height)
Select option (1 or 2): 1

[Step 3/3] Starting Demo...

================================================================================
Window DC Capture + OCR Demo Started
================================================================================
Target Window: Untitled - Notepad
Region: Full Window
FPS: 15
Hash Threshold: 5.0
================================================================================

[Press Ctrl+C to stop]

[Frame    1] OCR #  1 | Lines:  0 | Time:  45.2ms
[Frame   12] OCR #  2 | Lines:  1 | Time:  52.3ms
  └─ Hello World
[Frame   28] OCR #  3 | Lines:  2 | Time:  68.1ms
  └─ Hello World
  └─ This is a test
[Frame   45] OCR #  4 | Lines:  3 | Time:  71.5ms
  └─ Hello World
  └─ This is a test
  └─ Window DC Capture works!

^C
[Interrupted by user]

================================================================================
Demo Stopped
================================================================================
Total Frames: 180
OCR Runs: 4
OCR Rate: 2.2%
================================================================================
```

**Giải thích:**
- **Total Frames:** 180 frames trong 12 giây (15 FPS)
- **OCR Runs:** Chỉ 4 lần OCR (khi user gõ text)
- **OCR Rate:** 2.2% → tiết kiệm 97.8% CPU so với OCR mỗi frame!

---

## Performance Analysis

### So sánh phương pháp

| Metric | Old Method (Full Capture) | New Method (Window DC) |
|--------|--------------------------|------------------------|
| Capture method | PIL screenshot (full screen) | BitBlt (window only) |
| Overlay handling | Hide/show → flicker | No need to hide |
| OCR frequency | Every frame (100%) | Only on change (~5%) |
| CPU usage | High (continuous OCR) | Low (hash + selective OCR) |
| Race condition | Yes (overlay vs capture) | No (BitBlt ignores overlay) |
| Flicker | Yes (hide/show overlay) | No |

### Tại sao Window DC Capture không bị overlay che?

**Technical explanation:**

```cpp
// BitBlt API
BitBlt(
    hdcDest,      // Destination DC (memory)
    nXDest,       // X coord
    nYDest,       // Y coord
    nWidth,       // Width
    nHeight,      // Height
    hdcSrc,       // Source DC (WINDOW DC, not screen DC!)
    nXSrc,        // Source X
    nYSrc,        // Source Y
    SRCCOPY       // Copy mode
);
```

- **Window DC:** Nội dung riêng của window (client area)
- **Screen DC:** Toàn bộ màn hình (bao gồm overlay)

BitBlt lấy từ **Window DC** → chỉ có nội dung window, không có overlay!

### Hash Detection Efficiency

**dHash Algorithm:**

1. Resize image to 9x8 (72 pixels)
2. Convert to grayscale
3. Compute horizontal gradient (left vs right)
4. Generate 64-bit hash
5. Compare with previous hash (Hamming distance)

**Time complexity:** O(1) (constant 72 pixels)
**OCR time:** O(n×m) (full image processing)

**Example:**
- Hash check: ~0.5ms
- OCR: ~50-100ms
- **Speedup:** 100-200x faster!

---

## Customization

### 1. Điều chỉnh độ nhạy (Sensitivity)

Trong `demo_window_capture_ocr.py`:

```python
self.monitor = WindowRegionMonitor(
    hwnd=hwnd,
    region_bbox=region_bbox,
    change_threshold=5.0  # ← Thay đổi giá trị này
)
```

**Gợi ý:**
- `1-3`: Rất nhạy → detect cả thay đổi nhỏ (di chuột, cursor blink)
- `5-10`: Cân bằng → detect khi text thay đổi
- `15+`: Ít nhạy → chỉ detect thay đổi lớn (nhiều text mới)

### 2. Điều chỉnh FPS

```python
demo.start(fps=15)  # ← 15 FPS (mặc định)
```

**Gợi ý:**
- `5-10 FPS`: Tiết kiệm CPU, vẫn đủ nhanh
- `15 FPS`: Cân bằng
- `30 FPS`: Smooth hơn nhưng tốn CPU

### 3. Thêm Translation

Sửa trong `WindowOCRDemo.update_overlay()`:

```python
# Thay vì:
overlay_data[line_id] = {
    'original': text,
    'translation': text,  # ← Hiện tại chỉ show original
    ...
}

# Thành:
from services.translation_service import TranslationService

translation_service = TranslationService()
translation = translation_service.translate(text, target_lang='vi')

overlay_data[line_id] = {
    'original': text,
    'translation': translation,
    ...
}
```

---

## Integration với Main App

### Thay thế MultiRegionMonitor

Trong `main_with_ui.py`, thay:

```python
# Cũ:
from capture.screen_capture import MultiRegionMonitor

# Mới:
from capture.window_capture import WindowRegionMonitor
```

### Workflow mới

```python
# 1. User chọn target window
hwnd = select_window_interactive()

# 2. User chọn region
region_bbox = select_region_ui()

# 3. Initialize monitor
monitor = WindowRegionMonitor(
    hwnd=hwnd,
    region_bbox=region_bbox,
    change_threshold=5.0
)

# 4. Monitoring loop
while running:
    has_changed, image = monitor.check_and_capture()

    if has_changed:
        # OCR
        ocr_result = ocr_service.process_image(image)

        # Translate
        translated = translation_service.translate(ocr_result)

        # Overlay (với absolute coords)
        abs_bbox = monitor.get_absolute_bbox()
        overlay_service.update_positioned(translated, abs_bbox)
```

---

## Troubleshooting

### 1. "No window found"

**Nguyên nhân:** Window title không khớp.

**Giải pháp:**
```python
# List tất cả windows
from capture.window_capture import list_windows
list_windows()
```

### 2. "Capture failed"

**Nguyên nhân:** Window bị minimize hoặc không có quyền truy cập.

**Giải pháp:**
- Đảm bảo window không minimize
- Chạy script với quyền Administrator (nếu target app cần quyền cao)

### 3. "OCR không detect text"

**Nguyên nhân:** Hash threshold quá cao hoặc region không đúng.

**Giải pháp:**
- Giảm `change_threshold` (e.g., 3.0)
- Kiểm tra region bbox có đúng không
- Test với ảnh đơn giản (Notepad)

### 4. "Overlay không hiện đúng vị trí"

**Nguyên nhân:** Window position thay đổi sau khi start.

**Giải pháp:**
- `get_absolute_bbox()` được gọi mỗi frame → tự động update
- Nếu vẫn lỗi, check DPI scaling (Windows 10/11)

---

## Advanced: Multi-Window Monitoring

Muốn monitor nhiều windows cùng lúc?

```python
from capture.window_capture import WindowRegionMonitor

# Setup monitors
monitors = []
for hwnd, region in window_regions:
    monitor = WindowRegionMonitor(hwnd=hwnd, region_bbox=region)
    monitors.append(monitor)

# Monitoring loop
while running:
    for i, monitor in enumerate(monitors):
        has_changed, image = monitor.check_and_capture()

        if has_changed:
            # Process window i
            process_window(i, image, monitor.get_absolute_bbox())
```

---

## Technical Details

### BitBlt vs Screenshot Comparison

```python
# Method 1: PIL Screenshot (old)
import PIL.ImageGrab
screenshot = PIL.ImageGrab.grab()  # Full screen
region = screenshot.crop((x, y, x+w, y+h))
# ✗ Captures overlay
# ✗ Full screen → slow
# ✗ Race condition

# Method 2: BitBlt (new)
from capture.window_capture import WindowCapture
capture = WindowCapture(hwnd=hwnd)
region = capture.capture_region((x, y, w, h))
# ✓ Ignores overlay
# ✓ Window only → fast
# ✓ No race condition
```

### Hash Algorithm (dHash)

```python
def compute_dhash(image):
    # 1. Resize to 9x8 (need 1 extra column for diff)
    resized = image.resize((9, 8))

    # 2. Grayscale
    gray = resized.convert('L')

    # 3. Compute horizontal gradient
    #    Compare each pixel with its right neighbor
    pixels = np.array(gray)
    diff = pixels[:, 1:] > pixels[:, :-1]  # 8x8 boolean matrix

    # 4. Convert to 64-bit hash
    hash_bits = np.packbits(diff.flatten())

    return hash_bits.tobytes().hex()
```

**Why dHash?**
- Fast: O(1) complexity (constant 72 pixels)
- Robust: Resistant to small changes (compression, noise)
- Perceptual: Similar images → similar hashes
- Efficient: 64 bits = 8 bytes

---

## Next Steps

### 1. Thêm Translation
Tích hợp với `TranslationService` để hiển thị bản dịch thay vì text gốc.

### 2. Multi-Language Overlay
Hiển thị cả original + translation (2 dòng).

### 3. History Integration
Lưu OCR results vào Firebase history.

### 4. UI Integration
Tích hợp vào `MainWindow` với PyQt6.

### 5. Performance Tuning
- Async OCR với `asyncio`
- GPU acceleration với Tesseract
- Batch processing

---

## Conclusion

**Window DC Capture + Hash Detection** là giải pháp tối ưu cho OCR realtime:

✅ **No race condition** (BitBlt ignores overlay)
✅ **High performance** (hash detection → selective OCR)
✅ **No flicker** (no hide/show overlay)
✅ **Low CPU usage** (OCR chỉ khi cần)

**Use cases:**
- Game subtitle translation (realtime)
- Live video caption
- Application monitoring
- Automated testing with OCR

Enjoy! 🚀
