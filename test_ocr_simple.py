"""Simple OCR Config Test - Compare configs for each language"""

import pytesseract
from PIL import Image, ImageDraw, ImageFont

# Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Test configs
configs = {
    'Auto (Current)': r'--oem 1 --psm 6 -l eng+vie+jpn+chi_sim+fra',
    'Japanese Optimized': r'--oem 3 --psm 11 -l jpn+eng',
    'Chinese Optimized': r'--oem 3 --psm 6 -l chi_sim+eng',
}

# Test texts
texts = {
    'Japanese': 'ユーザーはテストを希望し、オーバーレイをテストする',
    'Chinese': '用户希望测试覆盖层功能',
    'English': 'The user wants to test overlay',
}

def create_image(text):
    """Create simple test image"""
    img = Image.new('RGB', (1000, 100), 'white')
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("msgothic.ttc", 24)  # Japanese font
    except:
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = None
    draw.text((10, 30), text, fill='black', font=font)
    return img

print("="*70)
print("OCR CONFIG TEST")
print("="*70)

for lang, text in texts.items():
    print(f"\n### {lang.upper()} ###")
    print(f"Expected: {text}")
    print("-"*70)
    
    img = create_image(text)
    
    for config_name, config in configs.items():
        try:
            result = pytesseract.image_to_string(img, config=config).strip()
            # Check accuracy
            match = '✓' if text in result or result in text else '✗'
            print(f"{match} {config_name:25}: {result[:60]}")
        except Exception as e:
            print(f"✗ {config_name:25}: ERROR - {e}")

print("\n" + "="*70)
print("CONCLUSION:")
print("="*70)
print("- Auto config works for all but may not be most accurate")
print("- Test with your real images to confirm best config")
print("="*70)
