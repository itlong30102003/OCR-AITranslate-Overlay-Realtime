"""Test language detection for Japanese processing"""

from services.ocr_service import OCRService, TextBox

# Create service
service = OCRService()

# Test 1: English text (should NOT be processed)
print("=" * 60)
print("TEST 1: English Text")
print("=" * 60)

english_boxes = [
    TextBox(text="Hello", bbox=(0, 0, 50, 30), abs_bbox=(100, 100, 150, 130), region_idx=0, region_coords=(100, 100, 500, 300)),
    TextBox(text="World", bbox=(60, 0, 120, 30), abs_bbox=(160, 100, 220, 130), region_idx=0, region_coords=(100, 100, 500, 300)),
]

has_jp = service._has_japanese_characters(english_boxes)
print(f"Has Japanese: {has_jp}")
print(f"Expected: False")
print()

# Test 2: Japanese text (should be processed)
print("=" * 60)
print("TEST 2: Japanese Text")
print("=" * 60)

japanese_boxes = [
    TextBox(text="ユー", bbox=(0, 0, 30, 30), abs_bbox=(100, 100, 130, 130), region_idx=0, region_coords=(100, 100, 500, 300)),
    TextBox(text="ザー", bbox=(35, 0, 65, 30), abs_bbox=(135, 100, 165, 130), region_idx=0, region_coords=(100, 100, 500, 300)),
    TextBox(text="は", bbox=(70, 0, 90, 30), abs_bbox=(170, 100, 190, 130), region_idx=0, region_coords=(100, 100, 500, 300)),
]

has_jp = service._has_japanese_characters(japanese_boxes)
print(f"Has Japanese: {has_jp}")
print(f"Expected: True")
print()

# Test 3: Mixed (mostly English with some Japanese) - should NOT be processed
print("=" * 60)
print("TEST 3: Mostly English with少し Japanese")
print("=" * 60)

mixed_boxes = [
    TextBox(text="The", bbox=(0, 0, 30, 30), abs_bbox=(100, 100, 130, 130), region_idx=0, region_coords=(100, 100, 500, 300)),
    TextBox(text="quick", bbox=(35, 0, 70, 30), abs_bbox=(135, 100, 170, 130), region_idx=0, region_coords=(100, 100, 500, 300)),
    TextBox(text="brown", bbox=(75, 0, 120, 30), abs_bbox=(175, 100, 220, 130), region_idx=0, region_coords=(100, 100, 500, 300)),
    TextBox(text="犬", bbox=(125, 0, 145, 30), abs_bbox=(225, 100, 245, 130), region_idx=0, region_coords=(100, 100, 500, 300)),
]

has_jp = service._has_japanese_characters(mixed_boxes)
print(f"Has Japanese: {has_jp}")
print(f"Expected: False (only ~15% is Japanese)")
print()

print("=" * 60)
print("✓ Language detection test complete!")
print("=" * 60)
