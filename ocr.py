import pytesseract
from PIL import ImageGrab
import re
# Đường dẫn Tesseract.exe
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# 1. Chụp màn hình
screenshot = ImageGrab.grab()
# 2. Config cho Tesseract
custom_oem_psm_config = r'--oem 3 --psm 6'
# 3. OCR lấy dữ liệu chi tiết
data = pytesseract.image_to_data(screenshot, lang="eng+vie+jpn", config=custom_oem_psm_config, output_type=pytesseract.Output.DICT)

# 4. Gom text theo dòng
lines = {}
for i in range(len(data['text'])):
    text = data['text'][i].strip()
    
    if not text:
        continue

    conf = data['conf'][i]  
    if conf <= 50:
        continue  # bỏ text kém chất lượng

    line_id = (data['page_num'][i], data['block_num'][i], data['par_num'][i], data['line_num'][i])
    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]

    # Bộ lọc chống tạp nham
    if w < 5:  # bỏ bbox quá nhỏ (rác)
        continue

    # Regex giữ lại Latin, Tiếng Việt, Nhật (Kanji, Hiragana, Katakana), số, và dấu câu
    pattern = r'[A-Za-zÀ-ỹ一-龯ぁ-んァ-ヶー々〆〤0-9。、！？「」『』.,!?;:()\-–—"\'“”‘’]'
    if not re.search(pattern, text):
        continue
    # Nếu text quá ngắn (<2 ký tự) nhưng KHÔNG phải tiếng Nhật thì bỏ
    if len(text.strip()) < 2 and not re.search(r'[一-龯ぁ-んァ-ヶ]', text):
        continue
        
    
    if line_id not in lines:
        lines[line_id] = {"text": [], "x1": x, "y1": y, "x2": x+w, "y2": y+h}
    lines[line_id]["text"].append(text)
    lines[line_id]["x1"] = min(lines[line_id]["x1"], x)
    lines[line_id]["y1"] = min(lines[line_id]["y1"], y)
    lines[line_id]["x2"] = max(lines[line_id]["x2"], x+w)
    lines[line_id]["y2"] = max(lines[line_id]["y2"], y+h)

# 5. Print kết quả
print("Kết quả OCR (lọc conf > 70):")
for line in lines.values():
    txt = " ".join(line["text"])
    bbox = (line["x1"], line["y1"], line["x2"], line["y2"])
    print(f"{txt} -> bbox={bbox}")
