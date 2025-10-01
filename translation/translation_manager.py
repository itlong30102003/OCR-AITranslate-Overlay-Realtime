"""
Translation Manager
Manages and selects the best translation model for each language pair
"""

from typing import Dict, List, Optional, Tuple
import os
from .base_translator import BaseTranslator
from .gemini_translator import GeminiTranslator
from .nllb_translator import NLLBTranslator
from .opus_translator import OpusTranslator
from .m2m_translator import M2MTranslator


class TranslationManager:
    """Manages all translation models and selects the best one for each task"""
    
    def __init__(self, config: Dict = None):
        """
        Initialize TranslationManager with configuration
        
        Args:
            config: Configuration dictionary with API keys and settings
        """
        self.config = config or {}
        self.models = {}
        self.quality_matrix = self._setup_quality_matrix()
        self._initialize_models()
    
    def _setup_quality_matrix(self) -> Dict[Tuple[str, str], List[str]]:
        """Setup quality matrix for language pairs"""
        return {
            # European languages - Gemini excels
            ('en', 'fr'): ['gemini', 'nllb', 'opus'],
            ('fr', 'en'): ['gemini', 'nllb', 'opus'],
            ('en', 'vi'): ['gemini', 'nllb', 'opus'],
            ('vi', 'en'): ['gemini', 'nllb', 'opus'],
            ('fr', 'vi'): ['gemini', 'nllb', 'opus'],
            ('vi', 'fr'): ['gemini', 'nllb', 'opus'],
            
            # Asian languages - Gemini excels
            ('ja', 'zh'): ['gemini', 'm2m', 'nllb'],
            ('zh', 'ja'): ['gemini', 'm2m', 'nllb'],
            ('vi', 'ja'): ['gemini', 'nllb', 'opus'],
            ('ja', 'vi'): ['gemini', 'nllb', 'opus'],
            ('zh', 'vi'): ['gemini', 'nllb', 'opus'],
            ('vi', 'zh'): ['gemini', 'nllb', 'opus'],
            ('en', 'ja'): ['gemini', 'nllb', 'opus'],
            ('ja', 'en'): ['gemini', 'nllb', 'opus'],
            ('en', 'zh'): ['gemini', 'nllb', 'opus'],
            ('zh', 'en'): ['gemini', 'nllb', 'opus'],
            ('fr', 'ja'): ['gemini', 'nllb', 'opus'],
            ('ja', 'fr'): ['gemini', 'nllb', 'opus'],
            ('fr', 'zh'): ['gemini', 'nllb', 'opus'],
            ('zh', 'fr'): ['gemini', 'nllb', 'opus'],
        }
    
    def _initialize_models(self):
        """Initialize all available translation models"""
        print("Initializing translation models...")
        
        # Initialize Gemini (if API key available)
        gemini_key = self.config.get('gemini_api_key') or os.getenv('GEMINI_API_KEY')
        if gemini_key:
            try:
                self.models['gemini'] = GeminiTranslator(gemini_key)
                print("[OK] Gemini translator initialized")
            except Exception as e:
                print(f"[ERROR] Failed to initialize Gemini: {e}")
        else:
            print("[WARNING] Gemini API key not found, skipping Gemini")
        
        # Initialize NLLB-200 (always available)
        try:
            self.models['nllb'] = NLLBTranslator()
            print("[OK] NLLB-200 translator initialized")
        except Exception as e:
            print(f"[ERROR] Failed to initialize NLLB-200: {e}")
        
        # Initialize OPUS-MT (always available)
        try:
            self.models['opus'] = OpusTranslator()
            print("[OK] OPUS-MT translator initialized")
        except Exception as e:
            print(f"[ERROR] Failed to initialize OPUS-MT: {e}")
        
        # Initialize M2M-100 (always available)
        try:
            self.models['m2m'] = M2MTranslator()
            print("[OK] M2M-100 translator initialized")
        except Exception as e:
            print(f"[ERROR] Failed to initialize M2M-100: {e}")
        
        print(f"Total models initialized: {len(self.models)}")
    
    def translate(self, text: str, source_lang: str = 'auto', target_lang: str = 'vi') -> Optional[Dict]:
        """
        Translate text using the best available model
        
        Args:
            text: Text to translate
            source_lang: Source language code or 'auto' for auto-detection
            target_lang: Target language code
            
        Returns:
            Dict with translation result or None if failed
        """
        if not text.strip():
            return None
        
        # Auto-detect language if needed
        if source_lang == 'auto':
            source_lang = self._detect_language(text)
        
        # Get preferred models for this language pair
        preferred_models = self.quality_matrix.get(
            (source_lang, target_lang), 
            ['gemini', 'nllb', 'opus']  # Default fallback
        )
        
        # Try each model in order of preference
        for model_name in preferred_models:
            if model_name in self.models and self.models[model_name].is_model_available():
                try:
                    result = self.models[model_name].translate(text, source_lang, target_lang)
                    if result and result.get('confidence', 0) > 0.7:
                        return result
                except Exception as e:
                    print(f"Model {model_name} failed: {e}")
                    continue
        
        # Final fallback - try any available model
        for model_name, model in self.models.items():
            if model.is_model_available():
                try:
                    result = model.translate(text, source_lang, target_lang)
                    if result:
                        return result
                except Exception as e:
                    print(f"Fallback model {model_name} failed: {e}")
                    continue
        
        return None
    
    def _detect_language(self, text: str) -> str:
        """Detect language of input text"""
        try:
            import langdetect
            detected = langdetect.detect(text)
            lang_map = {
                'en': 'en', 'ja': 'ja', 'zh-cn': 'zh', 
                'vi': 'vi', 'fr': 'fr'
            }
            return lang_map.get(detected, detected)
        except:
            return 'en'  # Default fallback
    
    def get_available_models(self) -> List[str]:
        """Get list of available model names"""
        return [name for name, model in self.models.items() if model.is_model_available()]
    
    def get_model_info(self, model_name: str = None) -> Dict:
        """Get information about models"""
        if model_name:
            if model_name in self.models:
                return self.models[model_name].get_model_info()
            else:
                return {'error': f'Model {model_name} not found'}
        else:
            return {
                name: model.get_model_info() 
                for name, model in self.models.items()
            }
    
    def translate_with_model(self, text: str, source_lang: str, target_lang: str, model_name: str) -> Optional[Dict]:
        """
        Translate using a specific model
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            model_name: Name of the model to use
            
        Returns:
            Dict with translation result or None if failed
        """
        if model_name not in self.models:
            print(f"Model {model_name} not available")
            return None
        
        if not self.models[model_name].is_model_available():
            print(f"Model {model_name} is not available")
            return None
        
        return self.models[model_name].translate(text, source_lang, target_lang)
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        return ['en', 'ja', 'zh', 'vi', 'fr']
    
    def get_supported_pairs(self) -> List[Tuple[str, str]]:
        """Get list of supported language pairs"""
        return list(self.quality_matrix.keys())
    
    def add_model(self, name: str, model: BaseTranslator):
        """Add a new translation model"""
        self.models[name] = model
        print(f"Added model: {name}")
    
    def remove_model(self, name: str):
        """Remove a translation model"""
        if name in self.models:
            del self.models[name]
            print(f"Removed model: {name}")
    
    def update_quality_matrix(self, pair: Tuple[str, str], models: List[str]):
        """Update quality matrix for a language pair"""
        self.quality_matrix[pair] = models
        print(f"Updated quality matrix for {pair}: {models}")
    
    def get_stats(self) -> Dict:
        """Get translation statistics"""
        stats = {
            'total_models': len(self.models),
            'available_models': len(self.get_available_models()),
            'supported_languages': len(self.get_supported_languages()),
            'supported_pairs': len(self.get_supported_pairs()),
            'models': {}
        }
        
        for name, model in self.models.items():
            stats['models'][name] = {
                'available': model.is_model_available(),
                'type': model.__class__.__name__
            }
        
        return stats
