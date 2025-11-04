# Overlay Update - Individual Text Box Mode

## Tổng quan

Đã cập nhật `positioned_overlay_qt.py` từ **subtitle mode** (nhóm tất cả text vào 1 box) sang **individual text box mode** (mỗi text có overlay riêng đè lên đúng vị trí bbox).

## Thay đổi chính

### 1. Class mới: `IndividualTextBox`

```python
class IndividualTextBox(QLabel):
    """Individual text box overlay widget"""
```

**Chức năng:**
- Tạo 1 QLabel riêng cho MỖI text box được OCR
- Đè lên đúng vị trí `abs_bbox` của text gốc
- Nền đen mờ với opacity thay đổi theo `confidence` (128-255)
- Font size tự động điều chỉnh theo chiều cao bbox
- Click-through (không chặn tương tác với nội dung bên dưới)

### 2. Class cập nhật: `PositionedOverlayQt`

**Thay đổi:**
- Từ: Fullscreen overlay với `paintEvent()` vẽ subtitle
- Sang: Manager quản lý danh sách `IndividualTextBox` widgets

**Thuộc tính mới:**
```python
self.text_box_widgets: List[IndividualTextBox] = []  # Danh sách các widget
```

**Methods chính:**
- `update_text_boxes(translated_boxes)` → Tạo overlay cho từng text box
- `_clear_widgets()` → Xóa tất cả widgets cũ
- `show()` / `hide()` → Hiển thị/ẩn tất cả widgets
- `clear()` → Xóa tất cả text boxes

### 3. Thread-safety

Sử dụng PyQt6 signals để đảm bảo thread-safe:
```python
self.signals.update_boxes.connect(self._update_boxes_slot)
self.signals.show_window.connect(self._show_slot)
self.signals.hide_window.connect(self._hide_slot)
self.signals.clear_boxes.connect(self._clear_slot)
```

## Flow hoạt động

```
1. OCR Service → Phát hiện text boxes với abs_bbox
2. Translation Service → Dịch từng text box
3. Overlay Service → Gọi update_text_boxes(translated_boxes)
4. PositionedOverlayQt:
   - Clear widgets cũ
   - Tạo IndividualTextBox cho MỖI translated_box
   - Set geometry = abs_bbox
   - Show tất cả widgets
```

## Ưu điểm

✅ **Chính xác**: Mỗi overlay đè lên đúng vị trí text gốc
✅ **Linh hoạt**: Mỗi text box có style riêng (opacity theo confidence)
✅ **Performance**: Chỉ tạo widget khi cần, xóa khi update mới
✅ **Thread-safe**: Sử dụng signals cho async updates
✅ **Click-through**: Không chặn tương tác với UI bên dưới

## So sánh với subtitle mode

| Feature | Subtitle Mode (cũ) | Individual Mode (mới) |
|---------|-------------------|----------------------|
| Hiển thị | 1 box cho cả region | 1 box cho mỗi text |
| Vị trí | Bottom/top/center của region | Đúng bbox của text |
| Style | Unified cho cả region | Riêng biệt cho mỗi text |
| Performance | Vẽ trên 1 widget | Nhiều widgets riêng |
| Độ chính xác | Thấp | Cao |

## Compatibility

- `set_subtitle_position()` → Deprecated (giữ lại cho tương thích, nhưng không hoạt động)
- Tất cả methods khác giữ nguyên interface để tương thích với code hiện tại

## Testing

Chạy app với positioned overlay mode:
```bash
python main.py
```

Config trong `config.env`:
```
overlay_mode=positioned
```

## Notes

- Parent widget bị ẩn (1x1 pixel) nhưng vẫn cần thiết để quản lý lifecycle của children widgets
- Mỗi `IndividualTextBox` là independent window với own window flags
- Opacity: `128 + (confidence * 127)` → Range từ 128 (low confidence) đến 255 (high confidence)
