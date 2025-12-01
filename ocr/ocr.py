import pytesseract
from PIL import ImageGrab, Image
import re
from ocr.smart_menu_detector import SmartMenuDetector

# Đường dẫn Tesseract.exe
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Initialize Smart Menu Detector (singleton)
_menu_detector = None

def get_menu_detector():
    global _menu_detector
    if _menu_detector is None:
        _menu_detector = SmartMenuDetector()
    return _menu_detector

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

        # Bộ lọc chống tạp nham - loại bỏ icon và ký hiệu nhỏ
        if w < 8 or h < 8:  # Bỏ bbox quá nhỏ (icon, ký hiệu)
            continue

        # Regex giữ lại Latin (có dấu), Nhật/Trung, số, dấu câu, symbol phổ biến
        pattern = (
            r'[A-Za-zÀ-ỹ'                      # Latin + Tiếng Việt/French accents
            r'\u4E00-\u9FFF\u3400-\u4DBF'      # Chinese Hanzi (basic + Ext A)
            r'一-龯ぁ-んァ-ヶー々〆〤'            # Japanese Kanji + Hiragana + Katakana
            r'0-9'                             # Số
            r'。、！？：；「」『』（）［］｛｝'         # Dấu câu Nhật/Trung
            r'.,!\?;:()–—"\'""'''               # Dấu câu Latin
            r'=_%#@\*\[\]{}<>/\\\-\+_\s]'        # Symbol phổ biến + space (bao gồm - = _ + space)
        )

        # Lọc bỏ emoji khỏi text nhưng vẫn giữ lại chữ
        icon_pattern = r'[\u2190-\u21FF\u2600-\u26FF\u2700-\u27BF\U0001F300-\U0001FAFF]'
        text = re.sub(icon_pattern, '', text).strip()
        
        # Nếu sau khi lọc icon mà text rỗng → bỏ
        if not text:
            continue
            
        # Nếu text không chứa ký tự hợp lệ → bỏ
        if not re.search(pattern, text):
            continue

        # Loại text quá ngắn không hợp lệ
        text_stripped = text.strip()
        if len(text_stripped) < 2:
            # Giữ lại nếu là chữ cái, số, hoặc chữ Nhật/Trung
            if not re.search(r'[A-Za-zÀ-ỹ0-9\u4E00-\u9FFFぁ-んァ-ヶ]', text_stripped):
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


def run_ocr_on_image(image: Image.Image, enable_menu_detection: bool = True):
    """Chạy OCR trên một ảnh vùng (PIL.Image)."""
    lines = _image_to_lines(image)
    
    # Pre-process với Smart Menu Detector
    if enable_menu_detection and lines:
        detector = get_menu_detector()
        # Convert format for detector
        ocr_for_detector = {}
        for line_id, line_data in lines.items():
            ocr_for_detector[str(line_id)] = {
                'text': line_data['text'],
                'bbox': (line_data['x1'], line_data['y1'], line_data['x2'], line_data['y2'])
            }
        
        # Process with menu detector (threshold=0.5)
        processed = detector.process_ocr_results(ocr_for_detector, threshold=0.5)
        
        # Convert back to original format
        new_lines = {}
        for line_id, line_data in processed.items():
            # Handle both list and string text format
            text_list = line_data['text'] if isinstance(line_data['text'], list) else [line_data['text']]
            bbox = line_data['bbox']
            
            new_lines[line_id] = {
                'text': text_list,
                'x1': bbox[0],
                'y1': bbox[1],
                'x2': bbox[2],
                'y2': bbox[3]
            }
        
        return new_lines
    
    return lines


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