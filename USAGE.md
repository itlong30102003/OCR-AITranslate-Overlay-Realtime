# OCR AI Translate Overlay - Usage
## Gemma 3 2B local translator (demo)

This project includes a standalone demo to try Google Gemma local models for translation without external APIs.

### 1) Install (Windows PowerShell)

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

Optional GPU (CUDA) users should install the matching `torch` build from the official instructions.

### 2) Run the demo

```bash
python gemma3_demo.py
```
Optional: 8-bit loading (faster, less VRAM)

```bash
pip install bitsandbytes>=0.44.1
$env:GEMMA_LOAD_8BIT = "1"  # Windows PowerShell
python gemma3_demo.py
```

Offline local directory

```bash
# After snapshot_download to C:/Models/gemma-3-2b-it
$env:GEMMA_LOCAL_DIR = "C:/Models/gemma-3-2b-it"
$env:HF_HUB_OFFLINE = "1"
python gemma3_demo.py
```

The first run will download the model weights. By default, it attempts `google/gemma-3-4b-it`, falls back to `google/gemma-3-2b-it`, then `google/gemma-2-2b-it` if needed.

Environment overrides:

- `GEMMA3_MODEL_ID` – set to a specific HF model id
- `GEMMA_FALLBACK_MODEL_ID` – change the fallback model id (secondary)

### 3) What the demo does

- Tests multiple language pairs: `en<->vi`, `en<->fr`, `ja<->vi`, `zh<->vi`
- Benchmarks short to long inputs and reports latency

Notes:

- Local LMs use prompting for translation; quality varies by pair.
- Latency scales with input length and hardware; GPU is recommended.
# OCR Translation Overlay - Hướng dẫn sử dụng

## Tổng quan
Ứng dụng OCR Translation Overlay cho phép bạn:
- Chọn các vùng trên màn hình để theo dõi
- Tự động nhận diện text (OCR) khi có thay đổi
- Dịch thuật text tự động với nhiều mô hình AI
- Hiển thị kết quả dịch thuật dưới dạng overlay

## Cách chạy
```bash
python main.py
```

## Tính năng chính

### 1. Menu chính
- **Start Monitoring**: Bắt đầu chọn vùng để theo dõi
- **Language Settings**: Cài đặt ngôn ngữ nguồn và đích
- **View Translation Results**: Xem tất cả kết quả dịch thuật
- **Enable/Disable Overlay**: Bật/tắt hiển thị overlay

### 2. Chọn vùng theo dõi
1. Click "Start Monitoring"
2. Kéo chuột để chọn vùng muốn theo dõi
3. Chọn "Yes" để thêm vùng khác, "No" để bắt đầu theo dõi

### 3. Theo dõi và dịch thuật
- OCR sẽ tự động nhận diện text khi có thay đổi
- Translation sẽ được thực hiện tự động
- Kết quả hiển thị trong console và overlay

### 4. Cài đặt ngôn ngữ
- **Source Language**: Ngôn ngữ nguồn (auto để tự động phát hiện)
- **Target Language**: Ngôn ngữ đích (mặc định: Vietnamese)

## Mô hình dịch thuật

### Gemini (Online)
- Chất lượng cao nhất
- Cần API key
- Hỗ trợ nhiều ngôn ngữ

### NLLB-200 (Offline)
- Mô hình offline mạnh mẽ
- Hỗ trợ 200+ ngôn ngữ
- Chất lượng tốt cho tiếng Việt

### OPUS-MT (Offline)
- Nhẹ và nhanh
- Hỗ trợ các cặp ngôn ngữ phổ biến

### M2M-100 (Offline)
- Hỗ trợ dịch trực tiếp giữa các ngôn ngữ
- Chất lượng tốt cho ngôn ngữ châu Á

## Cấu hình

### File config.env
```env
# API Keys
GEMINI_API_KEY=your_api_key_here

# Translation Settings
DEFAULT_TARGET_LANG=vi
MIN_CONFIDENCE=0.7
MAX_TEXT_LENGTH=1000

# Performance Settings
USE_GPU=true
CACHE_TRANSLATIONS=true
```

## Troubleshooting

### Lỗi thường gặp
1. **Translation not available**: Kiểm tra API key trong config.env
2. **OCR not working**: Kiểm tra dependencies (PIL, pytesseract)
3. **Overlay not showing**: Kiểm tra quyền hiển thị cửa sổ

### Dependencies
```bash
pip install -r requirements.txt
```

## Lưu ý
- Ứng dụng sẽ tự động chọn mô hình dịch thuật tốt nhất cho từng cặp ngôn ngữ
- Overlay sẽ tự động biến mất sau 5 giây
- Có thể xem tất cả kết quả trong "Translation Results"
