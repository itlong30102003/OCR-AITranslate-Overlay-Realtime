# TODO: Tích hợp Region Monitor vào Main UI

## Đã hoàn thành:
- [x] Thêm tab "Giám sát" vào main window
- [x] Di chuyển UI region monitor từ Tkinter vào PyQt6 tab
- [x] Cập nhật logic start/stop monitor từ main window
- [x] Loại bỏ cửa sổ Tkinter riêng biệt
- [x] Test tích hợp UI mới

## Chi tiết thay đổi:

### 1. capture/screen_capture_integrated.py
- Thêm signal `snapshot_completed` để thông báo khi snapshot hoàn thành
- Thêm method `_on_snapshot_complete()` để emit signal

### 2. capture/screen_capture.py
- Thêm `set_completion_callback()` method cho MultiRegionMonitor
- Thêm callback khi snapshot hoàn thành trong `_run_loop()`

### 3. ui/tabs/monitor_tab.py
- Tạo tab mới với UI PyQt6 cho region monitoring
- Tích hợp IntegratedScreenCapture thay vì Tkinter
- Thêm RegionThumbnail widgets để hiển thị thumbnails
- Connect signal snapshot_completed để restore window

### 4. ui/main_window.py
- Import MonitorTab
- Thêm tab_monitor vào content_stack

### 5. main_with_ui.py
- Thêm method `on_region_change()` để forward từ monitor tab

### 6. services/async_processing_service.py
- Thêm method `process_region_change()` để xử lý region changes từ monitor tab

## Test:
- Chạy ứng dụng và kiểm tra tab "Giám sát"
- Chọn vùng và bắt đầu giám sát
- Kiểm tra overlay hiển thị đúng
- Dừng giám sát và kiểm tra UI restore
hide