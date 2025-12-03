"""Language Detector - Character-based language detection for OCR text"""

import re
from typing import Dict


class LanguageDetector:
    """Detect language from text using character-based heuristics"""
    
    def __init__(self):
        """Initialize language detector with regex patterns"""
        # Japanese characters (Hiragana + Katakana)
        self.japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF]')
        
        # Chinese characters (Han/Hanzi)
        self.chinese_pattern = re.compile(r'[\u4E00-\u9FFF]')
        
        # Vietnamese-specific diacritics
        self.vietnamese_pattern = re.compile(
            r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]',
            re.IGNORECASE
        )
        
        # French-specific accents (excluding Vietnamese)
        self.french_pattern = re.compile(r'[àâæçéèêëïîôùûüÿœ]', re.IGNORECASE)
    
    def detect(self, text: str) -> str:
        """
        Detect the primary language of the given text
        
        Args:
            text: Input text to analyze
            
        Returns:
            Language code: 'japanese', 'chinese', 'vietnamese', 'french', or 'english'
        """
        if not text or not text.strip():
            return 'english'
        
        total_chars = len(text)
        
        # Count Japanese characters (Hiragana/Katakana)
        japanese_count = len(self.japanese_pattern.findall(text))
        
        # Count Chinese characters (excluding Japanese Kanji)
        chinese_chars = len(self.chinese_pattern.findall(text))
        chinese_only_count = chinese_chars - japanese_count  # Exclude Kanji used in Japanese
        
        # Count Vietnamese diacritics
        vietnamese_count = len(self.vietnamese_pattern.findall(text))
        
        # Count French accents
        french_count = len(self.french_pattern.findall(text))
        
        # Decision logic with thresholds
        # Japanese: If >20% of text is Hiragana/Katakana
        if japanese_count > total_chars * 0.2:
            return 'japanese'
        
        # Chinese: If >30% is Han characters (excluding Japanese)
        if chinese_only_count > total_chars * 0.3:
            return 'chinese'
        
        # Vietnamese: If has Vietnamese-specific diacritics
        if vietnamese_count > 0:
            return 'vietnamese'
        
        # French: If has French accents (and not Vietnamese)
        if french_count > 0:
            return 'french'
        
        # Default to English
        return 'english'
    
    def detect_with_confidence(self, text: str) -> Dict[str, float]:
        """
        Detect language with confidence scores for all languages
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary mapping language codes to confidence scores (0-1)
        """
        if not text or not text.strip():
            return {'english': 1.0}
        
        total_chars = max(len(text), 1)  # Avoid division by zero
        
        # Calculate confidence scores
        japanese_count = len(self.japanese_pattern.findall(text))
        chinese_chars = len(self.chinese_pattern.findall(text))
        chinese_only_count = max(chinese_chars - japanese_count, 0)
        vietnamese_count = len(self.vietnamese_pattern.findall(text))
        french_count = len(self.french_pattern.findall(text))
        
        scores = {
            'japanese': min(japanese_count / total_chars * 5, 1.0),  # Boost Japanese
            'chinese': min(chinese_only_count / total_chars * 3, 1.0),
            'vietnamese': min(vietnamese_count / total_chars * 10, 1.0),  # Diacritics are strong signal
            'french': min(french_count / total_chars * 10, 1.0),
            'english': 0.5  # Baseline confidence
        }
        
        # Normalize scores
        total_score = sum(scores.values())
        if total_score > 0:
            scores = {lang: score / total_score for lang, score in scores.items()}
        
        return scores


if __name__ == "__main__":
    # Test the language detector
    detector = LanguageDetector()
    
    test_cases = [
        ("これは日本語です", "japanese"),
        ("这是中文", "chinese"),
        ("Đây là tiếng Việt", "vietnamese"),
        ("C'est français", "french"),
        ("This is English", "english"),
        ("日本語とEnglishの混合", "japanese"),  # Mixed
    ]
    
    print("Language Detection Test:")
    print("-" * 60)
    for text, expected in test_cases:
        detected = detector.detect(text)
        confidence = detector.detect_with_confidence(text)
        status = "✓" if detected == expected else "✗"
        print(f"{status} '{text}'")
        print(f"  Expected: {expected}, Detected: {detected}")
        print(f"  Confidence: {confidence}")
        print()
