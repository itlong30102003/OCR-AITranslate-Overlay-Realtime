"""Multi-Language Text Tokenizer - Handles tokenization for various languages"""

import re
from typing import Optional


class MultiLanguageTokenizer:
    """
    Multi-language tokenizer with lazy loading
    
    Supports:
    - Japanese: fugashi (MeCab-based tokenization)
    - Chinese: jieba (word segmentation)
    - Vietnamese/English/French: Whitespace normalization
    """
    
    def __init__(self, option: int = 1):
        """
        Initialize tokenizer with lazy loading
        
        Args:
            option: Implementation option (1=lightweight, 2/3=full with Vietnamese)
        """
        self.option = option
        
        # Lazy-loaded tokenizers (initialized on first use)
        self._japanese_tagger = None
        self._jieba_initialized = False
        self._vietnamese_tokenizer = None
        
        print(f"[Tokenizer] Initialized (Option {option} - Lazy Loading)")
    
    def _init_japanese(self):
        """Lazy-load Japanese tokenizer (fugashi)"""
        if self._japanese_tagger is None:
            try:
                from fugashi import Tagger
                self._japanese_tagger = Tagger()
                print("[Tokenizer] Japanese tokenizer (fugashi) loaded")
            except ImportError:
                print("[Tokenizer] Warning: fugashi not installed. Japanese tokenization disabled.")
                print("  Install with: pip install 'fugashi[unidic-lite]'")
                self._japanese_tagger = False  # Mark as failed
            except Exception as e:
                print(f"[Tokenizer] Error loading fugashi: {e}")
                self._japanese_tagger = False
        
        return self._japanese_tagger if self._japanese_tagger is not False else None
    
    def _init_chinese(self):
        """Lazy-load Chinese tokenizer (jieba)"""
        if not self._jieba_initialized:
            try:
                import jieba
                # Disable jieba logging
                import logging
                jieba.setLogLevel(logging.INFO)
                self._jieba_initialized = True
                print("[Tokenizer] Chinese tokenizer (jieba) loaded")
            except ImportError:
                print("[Tokenizer] Warning: jieba not installed. Chinese tokenization disabled.")
                print("  Install with: pip install jieba")
                self._jieba_initialized = False
            except Exception as e:
                print(f"[Tokenizer] Error loading jieba: {e}")
                self._jieba_initialized = False
        
        return self._jieba_initialized
    
    def _init_vietnamese(self):
        """Lazy-load Vietnamese tokenizer (underthesea) - Option 2/3 only"""
        if self.option == 1:
            return None  # Not available in Option 1
        
        if self._vietnamese_tokenizer is None:
            try:
                from underthesea import word_tokenize
                self._vietnamese_tokenizer = word_tokenize
                print("[Tokenizer] Vietnamese tokenizer (underthesea) loaded")
            except ImportError:
                print("[Tokenizer] Warning: underthesea not installed. Vietnamese tokenization disabled.")
                print("  Install with: pip install underthesea")
                self._vietnamese_tokenizer = False
            except Exception as e:
                print(f"[Tokenizer] Error loading underthesea: {e}")
                self._vietnamese_tokenizer = False
        
        return self._vietnamese_tokenizer if self._vietnamese_tokenizer is not False else None
    
    def tokenize_japanese(self, text: str) -> str:
        """
        Tokenize Japanese text using fugashi
        
        Args:
            text: Input Japanese text (may have OCR-induced spaces)
            
        Returns:
            Tokenized text with proper word boundaries
        """
        tagger = self._init_japanese()
        if not tagger:
            # Fallback: just normalize whitespace
            return ' '.join(text.split())
        
        try:
            # Remove all spaces first (OCR often adds incorrect spaces)
            text_no_space = ''.join(text.split())
            
            # Tokenize with fugashi
            words = [word.surface for word in tagger(text_no_space)]
            
            # Return space-separated words
            return ' '.join(words)
        except Exception as e:
            print(f"[Tokenizer] Error tokenizing Japanese: {e}")
            return ' '.join(text.split())  # Fallback
    
    def tokenize_chinese(self, text: str) -> str:
        """
        Tokenize Chinese text using jieba
        
        Args:
            text: Input Chinese text (may have OCR-induced spaces)
            
        Returns:
            Segmented text with proper word boundaries
        """
        if not self._init_chinese():
            # Fallback: just normalize whitespace
            return ' '.join(text.split())
        
        try:
            import jieba
            
            # Remove all spaces first (OCR often adds incorrect spaces)
            text_no_space = ''.join(text.split())
            
            # Segment with jieba
            words = jieba.cut(text_no_space)
            
            # Return space-separated words
            return ' '.join(words)
        except Exception as e:
            print(f"[Tokenizer] Error tokenizing Chinese: {e}")
            return ' '.join(text.split())  # Fallback
    
    def tokenize_vietnamese(self, text: str) -> str:
        """
        Tokenize Vietnamese text using underthesea (Option 2/3 only)
        
        Args:
            text: Input Vietnamese text
            
        Returns:
            Text with compound words properly handled
        """
        tokenizer = self._init_vietnamese()
        if not tokenizer:
            # Fallback: just normalize whitespace
            return ' '.join(text.split())
        
        try:
            # underthesea handles compound words like "học sinh"
            return tokenizer(text, format="text")
        except Exception as e:
            print(f"[Tokenizer] Error tokenizing Vietnamese: {e}")
            return ' '.join(text.split())  # Fallback
    
    def tokenize(self, text: str, language: str) -> str:
        """
        Apply language-specific tokenization
        
        Args:
            text: Input text from OCR
            language: Detected language code
            
        Returns:
            Tokenized text optimized for translation
        """
        if not text or not text.strip():
            return ""
        
        # Apply tokenization based on language
        if language == 'japanese':
            return self.tokenize_japanese(text)
        
        elif language == 'chinese':
            return self.tokenize_chinese(text)
        
        elif language == 'vietnamese':
            if self.option >= 2:
                return self.tokenize_vietnamese(text)
            else:
                # Option 1: Just normalize whitespace
                return ' '.join(text.split())
        
        else:
            # English, French, and other languages: normalize whitespace
            return ' '.join(text.split())


if __name__ == "__main__":
    # Test the tokenizer
    tokenizer = MultiLanguageTokenizer(option=1)
    
    test_cases = [
        ("これは日本語です", "japanese"),
        ("这是中文文本", "chinese"),
        ("Đây là tiếng Việt", "vietnamese"),
        ("This is English text", "english"),
    ]
    
    print("Tokenization Test:")
    print("-" * 60)
    for text, language in test_cases:
        tokenized = tokenizer.tokenize(text, language)
        print(f"[{language.upper()}]")
        print(f"  Input:  '{text}'")
        print(f"  Output: '{tokenized}'")
        print()
