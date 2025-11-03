"""Translation Service - Handles translation operations"""

import asyncio
from typing import Optional, Dict, List
from translation import TranslationManager
from translation.config import TranslationConfig


class TranslationService:
    """Service for handling translation operations"""

    def __init__(self, config: TranslationConfig):
        """
        Initialize Translation Service

        Args:
            config: TranslationConfig instance
        """
        self.config = config
        self.translation_manager: Optional[TranslationManager] = None
        self.source_lang = 'auto'
        self.target_lang = config.get('default_target_lang', 'vi')
        self.preferred_model: Optional[str] = None

        self._initialize()

    def _initialize(self):
        """Initialize translation manager"""
        try:
            self.translation_manager = TranslationManager({
                'gemini_api_key': self.config.get_api_key('gemini')
            })
            print("[Translation Service] Initialized successfully")
            print(f"[Translation Service] Available models: {self.get_available_models()}")
        except Exception as e:
            print(f"[Translation Service] Failed to initialize: {e}")
            self.translation_manager = None

    def is_available(self) -> bool:
        """Check if translation service is available"""
        return self.translation_manager is not None

    def translate(self, text: str, region_idx: int, scan_counter: int) -> Optional[Dict]:
        """
        Translate text

        Args:
            text: Text to translate
            region_idx: Region index for logging
            scan_counter: Scan counter for logging

        Returns:
            Dictionary with translation result or None
        """
        if not self.translation_manager:
            return None

        try:
            # Use preferred model if specified
            result = None
            if self.preferred_model:
                res_specific = self.translation_manager.translate_with_model(
                    text, self.source_lang, self.target_lang, self.preferred_model
                )
                if res_specific:
                    result = res_specific
                else:
                    print(f"[Translation Service] Preferred model '{self.preferred_model}' failed. Falling back...")

            # Fallback to auto model selection
            if result is None:
                result = self.translation_manager.translate(text, self.source_lang, self.target_lang)

            if result:
                translated_text = result['text']
                model_used = result.get('model_used', 'unknown')
                confidence = result.get('confidence', 0)

                try:
                    print(f"[Translation Service] Region {region_idx}:")
                    print(f"  Original: {text}")
                    print(f"  Translated: {translated_text}")
                    print(f"  Model: {model_used}, Confidence: {confidence:.2f}")
                except UnicodeEncodeError:
                    # Fallback for console encoding issues
                    print(f"[Translation Service] Region {region_idx}: Translation completed")
                    print(f"  Model: {model_used}, Confidence: {confidence:.2f}")

                return {
                    'original': text,
                    'translated': translated_text,
                    'model': model_used,
                    'confidence': confidence,
                    'scan': scan_counter
                }
            else:
                print(f"[Translation Service] Failed to translate region {region_idx}")
                return None

        except Exception as e:
            print(f"[Translation Service] Error translating region {region_idx}: {e}")
            return None

    def get_available_models(self) -> List[str]:
        """Get list of available translation models"""
        if not self.translation_manager:
            return []
        return self.translation_manager.get_available_models() or []

    def get_model_info(self, model: str) -> Dict:
        """Get information about a specific model"""
        if not self.translation_manager:
            return {}
        return self.translation_manager.get_model_info(model)

    def set_languages(self, source_lang: str, target_lang: str):
        """
        Set source and target languages

        Args:
            source_lang: Source language code
            target_lang: Target language code
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        print(f"[Translation Service] Languages set: {source_lang} -> {target_lang}")

    def set_preferred_model(self, model: Optional[str]):
        """
        Set preferred translation model

        Args:
            model: Model name or None for auto
        """
        self.preferred_model = model
        print(f"[Translation Service] Preferred model: {model or 'auto'}")

    def get_settings(self) -> Dict:
        """Get current translation settings"""
        return {
            'source_lang': self.source_lang,
            'target_lang': self.target_lang,
            'preferred_model': self.preferred_model,
            'available': self.is_available()
        }

    async def translate_async(self, text: str, region_idx: int, scan_counter: int) -> Optional[Dict]:
        """
        Async version - Translate text without blocking

        Args:
            text: Text to translate
            region_idx: Region index for logging
            scan_counter: Scan counter for logging

        Returns:
            Dictionary with translation result or None
        """
        # Run translation in thread pool to avoid blocking event loop
        return await asyncio.to_thread(self.translate, text, region_idx, scan_counter)
