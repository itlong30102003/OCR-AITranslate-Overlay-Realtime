"""Language Configuration Module
Central configuration for language settings and OCR optimization
"""

from typing import Dict, Optional


class LanguageConfig:
    """Language configuration and OCR optimization mapping"""
    
    # Language codes to display names
    LANGUAGES = {
        'auto': 'Auto (Detect)',
        'jpn': 'Japanese',
        'chi': 'Chinese',
        'eng': 'English',
        'vie': 'Vietnamese',
        'fra': 'French'
    }
    
    # Display names to language codes (reverse mapping)
    LANGUAGE_CODES = {v: k for k, v in LANGUAGES.items()}
    
    # Tesseract OCR configurations optimized for each language
    OCR_CONFIGS = {
        'auto': r'--oem 1 --psm 6 -l eng+vie+jpn+chi_sim+fra',  # Default: works for all
        'jpn':  r'--oem 1 --psm 6 -l jpn',                      # Japanese: dense text/documents  
        'chi':  r'--oem 3 --psm 6 -l chi_sim+eng',              # Chinese: documents
        'eng':  r'--oem 1 --psm 6 -l eng',                      # English: clean text
        'vie':  r'--oem 1 --psm 6 -l vie+eng',                  # Vietnamese: documents
        'fra':  r'--oem 1 --psm 6 -l fra+eng'                   # French: documents
    }

    
    # Translation language codes for translation services
    TRANSLATION_CODES = {
        'auto': None,  # Auto-detect
        'jpn': 'ja',   # Japanese
        'chi': 'zh',   # Chinese (simplified)
        'eng': 'en',   # English
        'vie': 'vi',   # Vietnamese
        'fra': 'fr'    # French
    }
    
    @staticmethod
    def get_ocr_config(source_lang: str) -> str:
        """
        Get optimized Tesseract OCR config for source language
        
        Args:
            source_lang: Language code (auto, jpn, chi, eng, vie, fra)
            
        Returns:
            Tesseract config string
        """
        return LanguageConfig.OCR_CONFIGS.get(source_lang, LanguageConfig.OCR_CONFIGS['auto'])
    
    @staticmethod
    def get_translation_code(lang: str) -> Optional[str]:
        """
        Get translation service language code
        
        Args:
            lang: Language code
            
        Returns:
            Translation service language code (ISO 639-1) or None for auto
        """
        return LanguageConfig.TRANSLATION_CODES.get(lang)
    
    @staticmethod
    def get_language_name(code: str) -> str:
        """
        Get display name for language code
        
        Args:
            code: Language code
            
        Returns:
            Display name
        """
        return LanguageConfig.LANGUAGES.get(code, 'Auto (Detect)')
    
    @staticmethod
    def get_language_code(name: str) -> str:
        """
        Get language code from display name
        
        Args:
            name: Display name
            
        Returns:
            Language code
        """
        return LanguageConfig.LANGUAGE_CODES.get(name, 'auto')
    
    @staticmethod
    def get_source_languages() -> list:
        """Get list of source language display names"""
        return [
            'Auto (Detect)',
            'Japanese',
            'Chinese',
            'English',
            'Vietnamese',
            'French'
        ]
    
    @staticmethod
    def get_target_languages() -> list:
        """Get list of target language display names (no Auto)"""
        return [
            'Vietnamese',
            'English',
            'Japanese',
            'Chinese',
            'French'
        ]


# Default settings
DEFAULT_SOURCE_LANG = 'auto'
DEFAULT_TARGET_LANG = 'vie'


if __name__ == "__main__":
    # Test the configuration
    print("Language Configuration Test")
    print("="*60)
    
    print("\nSource Languages:")
    for lang in LanguageConfig.get_source_languages():
        code = LanguageConfig.get_language_code(lang)
        config = LanguageConfig.get_ocr_config(code)
        print(f"  {lang:20} ({code:4}) → {config[:40]}...")
    
    print("\nTarget Languages:")
    for lang in LanguageConfig.get_target_languages():
        code = LanguageConfig.get_language_code(lang)
        trans_code = LanguageConfig.get_translation_code(code)
        print(f"  {lang:20} ({code:4}) → Translation: {trans_code}")
    
    print("\n" + "="*60)
    print("✓ Configuration loaded successfully")