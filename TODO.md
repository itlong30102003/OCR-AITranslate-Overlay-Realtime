# TODO: Refactor to Window Capture as Single Workflow

## 1. Refactor Main Workflow - Sử dụng Window Capture
- [ ] Thay thế IntegratedScreenCapture bằng WindowRegionMonitor trong main_with_ui.py
- [ ] Update OCRTranslationApp.__init__() để khởi tạo window capture thay vì screen capture

## 2. Update UI - Thêm Window Selection
- [ ] Thêm "Select Window" button vào ui/tabs/monitor_tab.py
- [ ] Thêm flow: Select Window → Select Region (trong window) → Start Monitoring
- [ ] Hiển thị window name/title đã chọn
- [ ] Tích hợp select_window_interactive() vào UI

## 3. Implement Window Position Tracking
- [ ] Thêm QTimer vào RegionOverlay để update vị trí liên tục (60 FPS)
- [ ] Sử dụng WindowRegionMonitor.get_absolute_bbox() để track window movement
- [ ] Update cả PositionedOverlayQt và TranslationOverlay (list mode)
- [ ] Đảm bảo overlay luôn đè đúng vị trí khi window di chuyển

## 4. Tích hợp Translation Service
- [ ] Kết nối OCR result với TranslationService.translate_text_boxes_async()
- [ ] Update AsyncProcessingService để xử lý window capture workflow
- [ ] Flow: Window DC Capture → OCR → Translation → Overlay (positioned/list)

## 5. Refactor Async Processing Service
- [ ] Loại bỏ _process_region_list() method cũ
- [ ] Chỉ giữ _process_region_positioned() với 2 display options
- [ ] Đơn giản hóa logic, tập trung vào window capture

## 6. Cleanup Code Cũ
- [ ] Deprecate/xóa capture/screen_capture.py (MultiRegionMonitor)
- [ ] Xóa logic screen capture trong capture/screen_capture_integrated.py
- [ ] Update config.env: Đặt capture_mode=window làm mặc định
- [ ] Giữ overlay modes: overlay_display=positioned hoặc overlay_display=list

## 7. Testing & Verification
- [ ] Test với nhiều loại window (Chrome, Notepad, game)
- [ ] Verify overlay tracking khi di chuyển window
- [ ] Test cả 2 display modes (positioned và list)
- [ ] Đảm bảo không có overlay interference với OCR
