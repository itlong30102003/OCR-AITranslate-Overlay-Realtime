"""OCR Tokenization Helper - Provides easy-to-use tokenization for OCR results"""

from ocr.language_detector import LanguageDetector
from ocr.text_tokenizer import MultiLanguageTokenizer


# Singleton instances (lazy-loaded)
_language_detector = None
_tokenizer = None


def get_language_detector():
    """Get the singleton LanguageDetector instance"""
    global _language_detector
    if _language_detector is None:
        _language_detector = LanguageDetector()
    return _language_detector


def get_tokenizer(option: int = 1):
    """Get the singleton MultiLanguageTokenizer instance"""
    global _tokenizer
    if _tokenizer is None:
        _tokenizer = MultiLanguageTokenizer(option=option)
    return _tokenizer


def tokenize_text(text: str, enable_tokenization: bool = True, option: int = 1) -> str:
    """
    Apply language-specific tokenization to text
    
    Args:
        text: Input text from OCR
        enable_tokenization: Whether to apply tokenization (default: True)
        option: Tokenizer option (1=lightweight, 2/3=full)
    
    Returns:
        Tokenized text optimized for translation
    """
    if not enable_tokenization or not text or not text.strip():
        return text
    
    try:
        detector = get_language_detector()
        tokenizer = get_tokenizer(option)
        
        # Detect language
        language = detector.detect(text)
        
        # Apply tokenization
        tokenized = tokenizer.tokenize(text, language)
        
        # Log if different from original
        if tokenized != text:
            print(f"[Tokenizer] {language.upper()}: '{text}' → '{tokenized}'")
        
        return tokenized
    except Exception as e:
        print(f"[Tokenizer] Error during tokenization: {e}")
        return text  # Fallback to original text


def tokenize_lines(lines_dict: dict, enable_tokenization: bool = True, option: int = 1) -> dict:
    """
    Apply tokenization to OCR lines dictionary
   
    Args:
        lines_dict: OCR lines dictionary from run_ocr_on_image()
        enable_tokenization: Whether to apply tokenization
        option: Tokenizer option
    
    Returns:
        Lines dictionary with tokenized text
    """
    if not enable_tokenization or not lines_dict:
        return lines_dict
    
    import copy
    tokenized_lines = copy.deepcopy(lines_dict)
    
    for line_id, line_data in tokenized_lines.items():
        # Get combined text
        if isinstance(line_data['text'], list):
            combined_text = ' '.join(line_data['text'])
        else:
            combined_text = line_data['text']
        
        # Tokenize
        tokenized_text = tokenize_text(combined_text, enable_tokenization=True, option=option)
        
        # Update text (keep as list if it was a list)
        if isinstance(line_data['text'], list):
            tokenized_lines[line_id]['text'] = [tokenized_text]
        else:
            tokenized_lines[line_id]['text'] = tokenized_text
    
    return tokenized_lines
