"""
Test script for OCR Text Classification Integration
"""

from services.ocr_service import OCRService, ClassifiedTextBox
from ocr.text_classifier import WindowTextClassifier, BlockType
from PIL import Image
import numpy as np

def test_classifier_direct():
    """Test WindowTextClassifier directly with demo data"""
    print("=" * 60)
    print("TEST 1: WindowTextClassifier Direct Test")
    print("=" * 60)
    
    # Demo OCR results - better structured
    ocr_results = {
        # Menu horizontal (top bar)
        'line_1': {'text': ['Home'], 'bbox': (10, 10, 80, 40)},
        'line_2': {'text': ['About'], 'bbox': (100, 10, 170, 40)},
        'line_3': {'text': ['Contact'], 'bbox': (190, 10, 280, 40)},
        
        # Heading
        'line_4': {'text': ['Welcome', 'to', 'our', 'website'], 'bbox': (10, 80, 400, 110)},
        
        # Paragraph (3+ lines, long text)
        'line_5': {'text': ['This', 'is', 'a', 'paragraph', 'of', 'text', 'that', 'contains', 'important', 'information.'], 'bbox': (10, 130, 400, 155)},
        'line_6': {'text': ['It', 'spans', 'multiple', 'lines', 'and', 'provides', 'detailed', 'content.'], 'bbox': (10, 160, 400, 185)},
        'line_7': {'text': ['This', 'is', 'the', 'final', 'sentence', 'of', 'the', 'paragraph.'], 'bbox': (10, 190, 400, 215)},
        
        # Vertical menu (sidebar)
        'line_8': {'text': ['Dashboard'], 'bbox': (500, 80, 600, 105)},
        'line_9': {'text': ['Settings'], 'bbox': (500, 110, 600, 135)},
        'line_10': {'text': ['Profile'], 'bbox': (500, 140, 600, 165)},
        
        # Buttons (horizontal)
        'line_11': {'text': ['Save'], 'bbox': (50, 300, 120, 330)},
        'line_12': {'text': ['Cancel'], 'bbox': (150, 300, 240, 330)},
    }
    
    classifier = WindowTextClassifier()
    blocks = classifier.classify_window(ocr_results)
    
    print(f"\nDetected {len(blocks)} blocks:\n")
    for i, block in enumerate(blocks, 1):
        print(f"Block {i}: {block.type.value.upper()}")
        print(f"  Confidence: {block.confidence:.2f}")
        print(f"  Text: {block.get_full_text()}")
        print(f"  Số dòng: {len(block.lines)}")
        print(f"  Bbox: {block.bbox}")
        print()
    
    return blocks


def test_ocr_service_classification():
    """Test OCRService.classify_text_blocks method"""
    print("\n" + "=" * 60)
    print("TEST 2: OCRService Classification Method")
    print("=" * 60)
    
    # Same demo data
    ocr_results = {
        'line_1': {'text': ['Home'], 'bbox': (10, 10, 80, 40)},
        'line_2': {'text': ['Products'], 'bbox': (100, 10, 190, 40)},
        'line_3': {'text': ['Support'], 'bbox': (210, 10, 300, 40)},
        'line_4': {'text': ['Learn', 'More', 'About', 'Our', 'Services'], 'bbox': (10, 80, 350, 110)},
        'line_5': {'text': ['We', 'offer', 'comprehensive', 'solutions.'], 'bbox': (10, 130, 400, 155)},
        'line_6': {'text': ['Our', 'team', 'is', 'here', 'to', 'help.'], 'bbox': (10, 160, 400, 185)},
        'line_7': {'text': ['Contact', 'us', 'today', 'for', 'more', 'details.'], 'bbox': (10, 190, 400, 215)},
    }
    
    ocr_service = OCRService()
    blocks = ocr_service.classify_text_blocks(ocr_results)
    
    print(f"\nClassified {len(blocks)} blocks:\n")
    for i, block in enumerate(blocks, 1):
        print(f"Block {i}: {block.type.value.upper()}")
        print(f"  Confidence: {block.confidence:.2f}")
        print(f"  Text: {block.get_full_text()}")
        print()
    
    # Verify expected types
    types_found = [b.type for b in blocks]
    print(f"Block types detected: {[t.value for t in types_found]}")
    
    # Check for expected patterns
    has_menu = any(t in [BlockType.MENU_HORIZONTAL, BlockType.MENU_VERTICAL] for t in types_found)
    has_heading = BlockType.HEADING in types_found
    has_paragraph = BlockType.PARAGRAPH in types_found
    
    print(f"\nValidation:")
    print(f"  ✓ Has Menu: {'YES' if has_menu else 'NO'}")
    print(f"  ✓ Has Heading: {'YES' if has_heading else 'NO'}")
    print(f"  ✓ Has Paragraph: {'YES' if has_paragraph else 'NO'}")
    
    return blocks


def test_ocr_format_compatibility():
    """Test that classifier handles both old and new OCR formats"""
    print("\n" + "=" * 60)
    print("TEST 3: OCR Format Compatibility")
    print("=" * 60)
    
    # Old format (x1, y1, x2, y2 as separate keys)
    old_format = {
        'line_1': {'text': ['Test'], 'x1': 10, 'y1': 10, 'x2': 80, 'y2': 40},
    }
    
    # New format (bbox tuple)
    new_format = {
        'line_1': {'text': ['Test'], 'bbox': (10, 10, 80, 40)},
    }
    
    classifier = WindowTextClassifier()
    
    try:
        blocks_old = classifier.classify_window(old_format)
        print("✓ Old format works")
    except Exception as e:
        print(f"✗ Old format failed: {e}")
    
    try:
        blocks_new = classifier.classify_window(new_format)
        print("✓ New format works")
    except Exception as e:
        print(f"✗ New format failed: {e}")


def test_edge_cases():
    """Test edge cases"""
    print("\n" + "=" * 60)
    print("TEST 4: Edge Cases")
    print("=" * 60)
    
    classifier = WindowTextClassifier()
    
    # Empty input
    print("\nTest 4.1: Empty OCR results")
    blocks = classifier.classify_window({})
    print(f"  Result: {len(blocks)} blocks (expected: 0)")
    
    # Single button
    print("\nTest 4.2: Single short text (button)")
    blocks = classifier.classify_window({
        'line_1': {'text': ['OK'], 'bbox': (10, 10, 50, 35)}
    })
    if blocks:
        print(f"  Result: {blocks[0].type.value} (expected: ui_button)")
        print(f"  Confidence: {blocks[0].confidence:.2f}")
    
    # Numbers only (should be filtered)
    print("\nTest 4.3: Numbers only (should be filtered)")
    blocks = classifier.classify_window({
        'line_1': {'text': ['123'], 'bbox': (10, 10, 50, 35)},
        'line_2': {'text': ['456'], 'bbox': (10, 40, 50, 65)}
    })
    print(f"  Result: {len(blocks)} blocks (expected: 0, filtered as noise)")


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 8 + "OCR TEXT CLASSIFICATION TEST SUITE" + " " * 16 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    try:
        # Run tests
        test_classifier_direct()
        test_ocr_service_classification()
        test_ocr_format_compatibility()
        test_edge_cases()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED ✓")
        print("=" * 60)
        print("\nNext Steps:")
        print("  1. Tích hợp vào app thực tế (main_with_ui.py)")
        print("  2. Test với real screenshots")
        print("  3. Fine-tune config thresholds nếu cần")
        print()
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
