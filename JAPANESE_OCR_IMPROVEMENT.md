# Japanese OCR Quality Improvement Plan

## Vấn đề hiện tại
- Tesseract đọc tiếng Nhật kém chính xác
- Config hiện tại: `--oem 1 --psm 6 -l eng+vie+jpn+chi_sim+fra`

## Nguyên nhân có thể

### 1. OEM (OCR Engine Mode) không tối ưu
- `--oem 1`: Chỉ dùng LSTM (neural net) - tốt cho chữ in rõ
- `--oem 3`: Kết hợp Legacy + LSTM - tốt hơn cho font phức tạp

### 2. PSM (Page Segmentation Mode) không phù hợp
- `--psm 6`: Assume uniform text block - OK cho đoạn văn
- `--psm 11`: Sparse text. Find as much text as possible - **TỐT HƠN cho game/UI**
- `--psm 3`: Fully automatic - best cho ảnh hỗn hợp

### 3. Language priority
- Đang dùng: `eng+vie+jpn+chi_sim+fra` (Tiếng Anh ưu tiên đầu)
- Nên dùng: `jpn+eng` (Nhật ưu tiên khi detect nhiều chữ Nhật)

### 4. Thiếu vertical text support
- Tiếng Nhật thường viết dọc (manga, game)
- Cần: `jpn_vert` language data

## Giải pháp đề xuất

### Option 1: Cải thiện config cho tất cả ngôn ngữ
```python
# Tốt hơn cho game/manga
custom_config = r'--oem 3 --psm 11 -l jpn+eng+chi_sim+vie+fra'
```

### Option 2: Dynamic config theo nội dung
```python
# Nếu detect nhiều chữ Nhật → dùng config tối ưu cho Nhật
if has_japanese_characters(image):
    config = r'--oem 3 --psm 11 -l jpn+eng'
else:
    config = r'--oem 3 --psm 6 -l eng+vie+chi_sim+fra'
```

### Option 3: Image preprocessing
```python
# Tăng contrast, denoise, resize
from PIL import ImageEnhance, ImageFilter

def preprocess_for_japanese(img):
    # Resize nếu quá nhỏ
    if img.width < 300:
        img = img.resize((img.width * 2, img.height * 2))
    
    # Tăng contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)
    
    # Sharpen
    img = img.filter(ImageFilter.SHARPEN)
    
    return img
```

### Option 4: Install jpn_vert (cho chữ dọc)
```bash
# Download từ GitHub
# https://github.com/tesseract-ocr/tessdata/blob/main/jpn_vert.traineddata
# Copy vào: C:\Program Files\Tesseract-OCR\tessdata\

# Sau đó config:
custom_config = r'--oem 3 --psm 11 -l jpn_vert+jpn+eng'
```

## Khuyến nghị thực hiện

### Cách 1: Nhanh nhất - Thay đổi config
Chỉ cần sửa 1 dòng trong `ocr/ocr.py`:
```python
# Thay dòng 20:
custom_config = r'--oem 3 --psm 11 -l jpn+eng+chi_sim+vie+fra'
# OEM 3 = Legacy+LSTM
# PSM 11 = Tìm mọi text có thể (tốt cho game/manga)
# jpn ưu tiên đầu
```

### Cách 2: Tốt nhất - Dynamic + Preprocessing
1. Detect language từ ảnh (trước OCR)
2. Áp dụng preprocessing phù hợp
3. Chọn config tối ưu

Bạn muốn thử cách nào?
