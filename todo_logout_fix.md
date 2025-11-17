# TODO: Fix Logout Services Issue

## Current Status
- Logout không dừng background services (async_processing_service, screen_capture, sync_service)
- Region monitor và overlay tiếp tục chạy sau logout
- Ngăn login tài khoản khác

## Tasks
- [x] Thêm method `stop_all_services()` trong OCRTranslationApp (main_with_ui.py)
- [x] Gọi `stop_all_services()` trong handle_logout của MainWindow (ui/main_window.py)
- [ ] Test logout để đảm bảo services dừng hoàn toàn
- [ ] Test login lại với tài khoản khác
