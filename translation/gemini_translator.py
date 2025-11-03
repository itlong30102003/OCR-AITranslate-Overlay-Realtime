"""
Google Gemini 2.0 Flash-Lite Translator Module
Free translation service with high quality and speed
"""

import google.generativeai as genai
from typing import Dict, Optional
import time
from .base_translator import BaseTranslator


class GeminiTranslator(BaseTranslator):
    """Google Gemini 2.0 Flash-Lite translator - FREE with high quality and speed"""

    def __init__(self, api_key: str = None):
        super().__init__("gemini-2.0-flash-lite")

        # Rate limiting: 15 requests/minute = 1 request per 4 seconds
        self.rate_limit_delay = 4.0  # seconds between requests
        self.last_request_time = 0
        self.cooldown_until = 0  # Timestamp when rate limit cooldown ends

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
        Translate using Gemini 2.0 Flash-Lite with rate limiting

        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            Dict with translation result or None if failed
        """
        if not self.is_available:
            return None

        # Check if in cooldown period
        current_time = time.time()
        if current_time < self.cooldown_until:
            remaining = int(self.cooldown_until - current_time)
            print(f"[Gemini] Rate limit cooldown active. Available in {remaining}s")
            return None

        # Rate limiting: Wait if needed
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            wait_time = self.rate_limit_delay - time_since_last
            print(f"[Gemini] Rate limiting: waiting {wait_time:.1f}s")
            time.sleep(wait_time)

        lang_names = {
            'en': 'English', 'ja': 'Japanese', 'zh': 'Chinese',
            'vi': 'Vietnamese', 'fr': 'French'
        }

        try:
            prompt = f"""Translate the following text from {lang_names.get(source_lang, source_lang)} to {lang_names.get(target_lang, target_lang)}.
            Maintain the original meaning and context. Return only the translation:

            {text}"""

            self.last_request_time = time.time()
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
            error_str = str(e)
            # Check for rate limit error (429)
            if '429' in error_str or 'Resource exhausted' in error_str:
                # Enter cooldown for 60 seconds
                self.cooldown_until = time.time() + 60
                print(f"[Gemini] Rate limit hit (429). Entering 60s cooldown. Will use fallback models.")
                return None
            else:
                print(f"[Gemini] Translation failed: {e}")
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
