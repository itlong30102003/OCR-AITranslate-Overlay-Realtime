import pytesseract
from PIL import ImageGrab, Image
import re
# Đường dẫn Tesseract.exe
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def _image_to_lines(image: Image.Image):
    # 2. Config cho Tesseract
    custom_config = r'--oem 1 --psm 6 -l eng+vie+jpn+chi_sim+fra'
    # 3. OCR lấy dữ liệu chi tiết
    data = pytesseract.image_to_data(image, config=custom_config, output_type=pytesseract.Output.DICT)

    # 4. Gom text theo dòng
    lines = {}
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        
        if not text:
            continue

        conf = data['conf'][i]  
        if conf <= 60:
            continue  # bỏ text kém chất lượng

        line_id = (data['page_num'][i], data['block_num'][i], data['par_num'][i], data['line_num'][i])
        x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]

        # Bộ lọc chống tạp nham
        if w < 5:  # Bỏ bbox quá nhỏ (rác OCR)
            continue

        # Regex giữ lại Latin (có dấu), Nhật/Trung, số, dấu câu, symbol phổ biến
        pattern = (
            r'[A-Za-zÀ-ỹ'                      # Latin + Tiếng Việt/French accents
            r'\u4E00-\u9FFF\u3400-\u4DBF'      # Chinese Hanzi (basic + Ext A)
            r'一-龯ぁ-んァ-ヶー々〆〤'            # Japanese Kanji + Hiragana + Katakana
            r'0-9'                             # Số
            r'。、！？：；「」『』（）［］｛｝'  # Dấu câu Nhật/Trung
            r'.,!?;:()\-\–—"\'“”‘’'            # Dấu câu Latin
            r'=_+%#@*\[\]{}<>/\\]'             # Symbol phổ biến
        )

        # Nếu text không chứa ký tự hợp lệ → bỏ
        if not re.search(pattern, text):
            continue

        # Loại text quá ngắn không hợp lệ
        text_stripped = text.strip()
        if len(text_stripped) < 2:
            # Nếu không phải chữ Nhật/Trung → bỏ
            if not re.search(r'[\u4E00-\u9FFFぁ-んァ-ヶ]', text_stripped):
                continue

            
        
        if line_id not in lines:
            lines[line_id] = {"text": [], "x1": x, "y1": y, "x2": x+w, "y2": y+h}
        lines[line_id]["text"].append(text)
        lines[line_id]["x1"] = min(lines[line_id]["x1"], x)
        lines[line_id]["y1"] = min(lines[line_id]["y1"], y)
        lines[line_id]["x2"] = max(lines[line_id]["x2"], x+w)
        lines[line_id]["y2"] = max(lines[line_id]["y2"], y+h)

    # 5. Trả kết quả
    return lines


def run_ocr_on_image(image: Image.Image):
    """Chạy OCR trên một ảnh vùng (PIL.Image)."""
    return _image_to_lines(image)


def run_ocr():
    # 1. Chụp màn hình
    screenshot = ImageGrab.grab()
    return _image_to_lines(screenshot)

# # 5. Print kết quả
# print("Kết quả OCR (lọc conf > 70):")
# for line in lines.values():
#     txt = " ".join(line["text"])
#     bbox = (line["x1"], line["y1"], line["x2"], line["y2"])
#     print(f"{txt} -> bbox={bbox}")
if __name__ == "__main__":
    # Gọi OCR từ main
    result = run_ocr()
    print("Kết quả OCR (conf > 50):")
    for line in result.values():
        txt = " ".join(line["text"])
        bbox = (line["x1"], line["y1"], line["x2"], line["y2"])
        print(f"{txt} -> bbox={bbox}")