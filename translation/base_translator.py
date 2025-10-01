"""
Base translator class that all translation models should inherit from
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
import langdetect


class BaseTranslator(ABC):
    """Base class for all translation models"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.is_available = True
    
    @abstractmethod
    def translate(self, text: str, source_lang: str, target_lang: str) -> Optional[Dict]:
        """
        Translate text from source language to target language
        
        Args:
            text: Text to translate
            source_lang: Source language code (e.g., 'en', 'vi', 'ja')
            target_lang: Target language code (e.g., 'en', 'vi', 'ja')
            
        Returns:
            Dict with keys: text, confidence, model, cost
            None if translation failed
        """
        pass
    
    def detect_language(self, text: str) -> str:
        """Detect language of input text"""
        try:
            detected = langdetect.detect(text)
            lang_map = {
                'en': 'en', 'ja': 'ja', 'zh-cn': 'zh', 
                'vi': 'vi', 'fr': 'fr'
            }
            return lang_map.get(detected, detected)
        except:
            return 'en'  # Default fallback
    
    def is_model_available(self) -> bool:
        """Check if model is available for use"""
        return self.is_available
    
    def get_model_info(self) -> Dict:
        """Get model information"""
        return {
            'name': self.model_name,
            'available': self.is_available,
            'type': self.__class__.__name__
        }
