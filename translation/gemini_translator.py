"""
Google Gemini 2.0 Flash-Lite Translator Module
Free translation service with high quality and speed
"""

import google.generativeai as genai
from typing import Dict, Optional
from .base_translator import BaseTranslator


class GeminiTranslator(BaseTranslator):
    """Google Gemini 2.0 Flash-Lite translator - FREE with high quality and speed"""
    
    def __init__(self, api_key: str = None):
        super().__init__("gemini-2.0-flash-lite")
        
        # Setup Gemini API
        if api_key:
            genai.configure(api_key=api_key)
        else:
            # Try to use default API key from environment
            import os
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
            else:
                print("Warning: No Gemini API key found. Please set GEMINI_API_KEY environment variable.")
                self.is_available = False
                return
        
        try:
            self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
            self.is_available = True
        except Exception as e:
            print(f"Failed to initialize Gemini: {e}")
            self.is_available = False
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> Optional[Dict]:
        """
        Translate using Gemini 2.0 Flash-Lite
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Dict with translation result or None if failed
        """
        if not self.is_available:
            return None
        
        lang_names = {
            'en': 'English', 'ja': 'Japanese', 'zh': 'Chinese',
            'vi': 'Vietnamese', 'fr': 'French'
        }
        
        try:
            prompt = f"""Translate the following text from {lang_names.get(source_lang, source_lang)} to {lang_names.get(target_lang, target_lang)}. 
            Maintain the original meaning and context. Return only the translation:
            
            {text}"""
            
            response = self.model.generate_content(prompt)
            
            return {
                'text': response.text.strip(),
                'confidence': 0.95,
                'model': self.model_name,
                'cost': 0,  # FREE
                'source_lang': source_lang,
                'target_lang': target_lang
            }
            
        except Exception as e:
            print(f"Gemini translation failed: {e}")
            return None
    
    def get_model_info(self) -> Dict:
        """Get Gemini model information"""
        info = super().get_model_info()
        info.update({
            'provider': 'Google',
            'cost': 'Free',
            'quota': '15 requests/minute, 1M tokens/day',
            'offline': False,
            'quality': 'High',
            'speed': 'Very Fast',
            'model': 'gemini-2.0-flash-lite'
        })
        return info
