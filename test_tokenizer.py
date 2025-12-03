"""Test Multi-Language Tokenizer - Verify tokenization works correctly"""

from ocr.language_detector import LanguageDetector
from ocr.text_tokenizer import MultiLanguageTokenizer
from ocr.tokenization_helper import tokenize_text


def test_language_detection():
    """Test language detection accuracy"""
    print("="*60)
    print("Testing Language Detection")
    print("="*60)
    
    detector = LanguageDetector()
    
    test_cases = [
        ("これは日本語です", "japanese"),
        ("这是中文文本", "chinese"),  
        ("Đây là tiếng Việt", "vietnamese"),
        ("C'est français", "french"),
        ("This is English", "english"),
        ("日本語とEnglishの混合", "japanese"),  # Mixed - should detect Japanese
    ]
    
    passed = 0
    for text, expected in test_cases:
        detected = detector.detect(text)
        status = "✓ PASS" if detected == expected else "✗ FAIL"
        print(f"{status} | Expected: {expected:12} | Detected: {detected:12} | Text: '{text}'")
        if detected == expected:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(test_cases)}")
    print()


def test_tokenization():
    """Test tokenization for各languages"""
    print("="*60)
    print("Testing Tokenization (Option 1 - Lightweight)")
    print("="*60)
    
    tokenizer = MultiLanguageTokenizer(option=1)
    
    test_cases = [
        ("これは日本語です", "japanese", "Expected: separate words"),
        ("这是中文文本", "chinese", "Expected: separate words"),
        ("Đây là tiếng Việt", "vietnamese", "Expected: normalized spaces"),
        ("This  is   English", "english", "Expected: normalized spaces"),
    ]
    
    for text, language, note in test_cases:
        tokenized = tokenizer.tokenize(text, language)
        changed = "↻ CHANGED" if tokenized != text else "= SAME"
        print(f"{changed} [{language.upper():10}] {note}")
        print(f"   Input:  '{text}'")
        print(f"   Output: '{tokenized}'")
        print()


def test_helper_function():
    """Test the tokenize_text helper function"""
    print("="*60)
    print("Testing Helper Function (Auto-detect + Tokenize)")
    print("="*60)
    
    test_cases = [
        "これは日本語です",
        "这是中文文本",
        "Đây là tiếng Việt",
        "This is English with  extra   spaces",
    ]
    
    for text in test_cases:
        result = tokenize_text(text, enable_tokenization=True)
        changed = "↻" if result != text else "="
        print(f"{changed} '{text}' → '{result}'")
    
    print()


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print(" MULTI-LANGUAGE TOKENIZER TEST SUITE")
    print("="*60 + "\n")
    
    try:
        test_language_detection()
        test_tokenization()
        test_helper_function()
        
        print("="*60)
        print("✓ All tests completed!")
        print("="*60)
        print("\nNote: fugashi and jieba will only work after installing:")
        print("  pip install 'fugashi[unidic-lite]' jieba")
        print("\nIf not installed, tokenization will gracefully fall back to whitespace normalization.")
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
