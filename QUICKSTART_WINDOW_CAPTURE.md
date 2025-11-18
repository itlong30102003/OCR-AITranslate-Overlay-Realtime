# Quick Start - Window DC Capture Demo

## Cài đặt nhanh (1 phút)

### 1. Cài đặt dependencies

```bash
# Chỉ cần cài pywin32 (nếu chưa có)
pip install pywin32

# Hoặc cài đặt tất cả (nếu là lần đầu)
pip install -r requirements.txt
```

### 2. Kiểm tra Tesseract OCR

Đảm bảo Tesseract đã cài đặt tại:
```
C:\Program Files\Tesseract-OCR\tesseract.exe
```

Nếu chưa có, tải tại: https://github.com/UB-Mannheim/tesseract/wiki

---

## Chạy demo (30 giây)

### Demo 1: Quick Test với Notepad

```bash
# 1. Mở Notepad
notepad

# 2. Chạy demo
python demo_window_capture_ocr.py

# 3. Chọn mode 2 (Quick demo - Notepad)
Select mode (1 or 2): 2

# 4. Gõ text trong Notepad → overlay hiện ngay!
```

### Demo 2: Bất kỳ window nào

```bash
# 1. Mở ứng dụng bạn muốn (Chrome, Word, game, v.v.)

# 2. Chạy demo
python demo_window_capture_ocr.py

# 3. Chọn mode 1 (Interactive)
Select mode (1 or 2): 1

# 4. Nhập tên window (hoặc một phần)
Enter window title (or part of it): Chrome

# 5. Chọn region
Select option (1, 2, or 3):
  - 1: Full window
  - 2: Visual selection (click & drag) ← RECOMMENDED!
  - 3: Manual input (x, y, width, height)

# 6. Nếu chọn option 2, cửa sổ preview sẽ hiện:
  - Click và kéo chuột để chọn vùng
  - Nhấn ENTER để xác nhận
  - Nhấn ESC để dùng full window

# 7. Xong! OCR và overlay sẽ chạy tự động
```

---

## Test scenarios

### Test 1: Text detection (Notepad)

1. Mở Notepad
2. Chạy demo (mode 2)
3. Gõ: "Hello World"
4. **Expected:** Overlay hiện "Hello World" đúng vị trí

### Test 2: Change detection (Hash)

1. Chạy demo
2. Để Notepad không đổi 5 giây
3. **Expected:** Console không in OCR (no change detected)
4. Gõ thêm text
5. **Expected:** Console in OCR ngay lập tức (change detected)

### Test 3: No overlay interference

1. Chạy demo
2. Overlay hiện trên Notepad
3. Gõ text mới
4. **Expected:** OCR vẫn detect đúng (không bị overlay che)

### Test 4: Performance (OCR rate)

1. Chạy demo với Notepad (1 dòng text)
2. Để 30 giây không đổi
3. Stop (Ctrl+C)
4. **Expected:**
   - Total Frames: ~450 (15 FPS × 30s)
   - OCR Runs: 1-2 (chỉ lần đầu)
   - OCR Rate: < 1% → tiết kiệm >99% CPU!

---

## Troubleshooting nhanh

### Lỗi: `ModuleNotFoundError: No module named 'win32gui'`

**Giải pháp:**
```bash
pip install pywin32
```

### Lỗi: `No window found matching 'Notepad'`

**Giải pháp:**
- Đảm bảo Notepad đang mở
- Hoặc thử tên khác: "Untitled - Notepad"
- Hoặc dùng Interactive mode (option 1) để xem danh sách windows

### Lỗi: Tesseract not found

**Giải pháp:**
- Cài Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
- Hoặc sửa path trong [ocr/ocr.py:7](ocr/ocr.py#L7)

### Overlay không hiện

**Giải pháp:**
- Kiểm tra PyQt6 đã cài đặt: `pip install PyQt6`
- Đảm bảo window có text (Notepad không trống)

---

## Demo output mẫu

```
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
  └─ This is OCR test
[Frame   45] OCR #  4 | Lines:  2 | Time:  71.5ms
  └─ Hello World
  └─ This is OCR test with Window DC Capture!

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

---

## Next steps

Sau khi test demo thành công:

1. **Đọc README chi tiết:** [README_WINDOW_CAPTURE_DEMO.md](README_WINDOW_CAPTURE_DEMO.md)
2. **Tích hợp vào main app:** Xem phần "Integration với Main App"
3. **Thêm translation:** Kết hợp với `TranslationService`
4. **Customize overlay:** Sửa `positioned_overlay_qt.py`

Enjoy! 🚀
