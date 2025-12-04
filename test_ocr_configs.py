"""Test OCR Configs for Different Languages
Compare Auto vs Optimized configs for each language
"""

import pytesseract
from PIL import Image, ImageDraw, ImageFont
import os
import sys

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Output file
OUTPUT_FILE = "ocr_config_test_results.txt"

# Test configs
CONFIGS = {
    'auto': r'--oem 1 --psm 6 -l eng+vie+jpn+chi_sim+fra',
    'jpn_optimized': r'--oem 3 --psm 11 -l jpn+eng',
    'chi_optimized': r'--oem 3 --psm 6 -l chi_sim+eng',
    'eng_optimized': r'--oem 1 --psm 6 -l eng',
    'vie_optimized': r'--oem 1 --psm 6 -l vie+eng',
}

# Test texts
TEST_TEXTS = {
    'japanese': 'ユーザーはテストを希望し、オーバーレイをテストするためにアプリを実行しました。',
    'chinese': '用户希望测试，并运行应用程序来测试覆盖层。',
    'english': 'The user wants to test the overlay functionality.',
    'vietnamese': 'Người dùng muốn kiểm tra chức năng overlay.',
}

def create_test_image(text, filename, font_size=30):
    """Create test image with text"""
    # Create white image
    img = Image.new('RGB', (1200, 150), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        # Try to use a Unicode font
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Draw text
    draw.text((20, 50), text, fill='black', font=font)
    
    # Save
    img.save(filename)
    print(f"✓ Created: {filename}")
    return img

def test_config(image, config_name, config):
    """Test OCR with specific config"""
    try:
        text = pytesseract.image_to_string(image, config=config)
        return text.strip()
    except Exception as e:
        return f"ERROR: {e}"

def compare_configs(language, text):
    """Compare all configs for a language"""
    print("\n" + "="*80)
    print(f"TESTING: {language.upper()}")
    print("="*80)
    print(f"Expected: {text}")
    print("-"*80)
    
    # Create test image
    filename = f"test_{language}.png"
    img = create_test_image(text, filename)
    
    # Test all configs
    results = {}
    for config_name, config in CONFIGS.items():
        print(f"\nTesting {config_name}...")
        result = test_config(img, config_name, config)
        results[config_name] = result
        print(f"Result: {result}")
    
    # Find best match
    print("\n" + "-"*80)
    print("COMPARISON:")
    print("-"*80)
    
    best_config = None
    best_similarity = 0
    
    for config_name, result in results.items():
        # Simple similarity check (character overlap)
        similarity = sum(1 for a, b in zip(text, result) if a == b) / max(len(text), len(result))
        match_percent = similarity * 100
        
        print(f"{config_name:20} : {match_percent:5.1f}% match")
        
        if similarity > best_similarity:
            best_similarity = similarity
            best_config = config_name
    
    print(f"\n✓ Best config: {best_config} ({best_similarity*100:.1f}% match)")
    
    # Clean up
    if os.path.exists(filename):
        os.remove(filename)
    
    return best_config, results

def main():
    """Run all tests"""
    output = []
    
    def log(msg):
        """Log to both console and output list"""
        print(msg)
        output.append(msg)
    
    log("="*80)
    log(" OCR CONFIG COMPARISON TEST")
    log("="*80)
    log("\nTesting different Tesseract configs for each language...")
    log("This will help determine the best config for each language.\n")
    
    recommendations = {}
    
    # Test Japanese
    log("\n### TESTING JAPANESE ###")
    best, results = compare_configs('japanese', TEST_TEXTS['japanese'], log)
    recommendations['Japanese'] = best
    
    # Test Chinese
    log("\n### TESTING CHINESE ###")
    best, results = compare_configs('chinese', TEST_TEXTS['chinese'], log)
    recommendations['Chinese'] = best
    
    # Test English
    log("\n### TESTING ENGLISH ###")
    best, results = compare_configs('english', TEST_TEXTS['english'], log)
    recommendations['English'] = best
    
    # Test Vietnamese
    log("\n### TESTING VIETNAMESE ###")
    best, results = compare_configs('vietnamese', TEST_TEXTS['vietnamese'], log)
    recommendations['Vietnamese'] = best
    
    # Summary
    log("\n" + "="*80)
    log(" SUMMARY & RECOMMENDATIONS")
    log("="*80)
    
    for lang, config in recommendations.items():
        log(f"{lang:15} → {config}")
    
    log("\n" + "="*80)
    log("NOTE: 'auto' should work for all languages but may not be optimal.")
    log("Optimized configs should give better accuracy for specific languages.")
    log("="*80)
    
    # Write to file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    
    print(f"\n✓ Results saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
