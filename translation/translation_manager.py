"""
Translation Manager
Manages and selects the best translation model for each language pair
"""

from typing import Dict, List, Optional, Tuple
from collections import OrderedDict
import os
from .base_translator import BaseTranslator
from .gemini_translator import GeminiTranslator
from .nllb_translator import NLLBTranslator
from .opus_translator import OpusTranslator


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
        self.cache_enabled = True
        self.cache_capacity = int((self.config or {}).get('cache_size', 512))
        self._cache: OrderedDict[Tuple[str, str, str], Dict] = OrderedDict()
        self.quality_matrix = self._setup_quality_matrix()
        self._initialize_models()
    
    def _setup_quality_matrix(self) -> Dict[Tuple[str, str], List[str]]:
        """Setup quality matrix for language pairs - Based on actual performance testing"""
        return {
            # European languages - M2M best, Gemini fallback
            ('en', 'fr'): ['gemini', 'nllb', 'opus'],
            ('fr', 'en'): ['gemini', 'nllb', 'opus'],
            ('fr', 'vi'): ['nllb', 'gemini', 'opus'],
            ('vi', 'en'): ['nllb', 'gemini', 'opus'],
            ('vi', 'fr'): ['nllb', 'gemini', 'opus'],

            # Asian languages - NLLB dominates
            ('ja', 'zh'): ['nllb', 'gemini'],
            ('zh', 'ja'): ['nllb', 'gemini'],
            ('ja', 'vi'): ['nllb', 'gemini', 'opus'],
            ('vi', 'ja'): ['nllb', 'gemini', 'opus'],
            ('zh', 'vi'): ['nllb', 'gemini', 'opus'],
            ('vi', 'zh'): ['nllb', 'gemini', 'opus'],

            # Cross-language pairs
            ('en', 'ja'): ['nllb', 'gemini'],
            ('ja', 'en'): ['nllb', 'gemini', 'opus'],
            ('en', 'zh'): ['nllb', 'gemini'],
            ('zh', 'en'): ['nllb', 'gemini', 'opus'],
            ('fr', 'ja'): ['nllb', 'gemini'],
            ('ja', 'fr'): ['nllb', 'gemini', 'opus'],
            ('fr', 'zh'): ['nllb', 'gemini'],
            ('zh', 'fr'): ['nllb', 'gemini', 'opus'],
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

        # Cache lookup
        if self.cache_enabled:
            key = (text, source_lang, target_lang)
            cached = self._cache.get(key)
            if cached:
                # move to end (MRU)
                self._cache.move_to_end(key)
                return dict(cached)
        
        # Get preferred models for this language pair
        preferred_models = self.quality_matrix.get(
            (source_lang, target_lang), 
            ['gemini', 'nllb', 'opus']  # Broader default fallback
        )
        
        # Try each model in order of preference, track best result even if confidence < threshold
        best_result = None
        best_model = None
        best_conf = -1.0
        for model_name in preferred_models:
            if model_name not in self.models:
                print(f"Model {model_name} not initialized; skipping")
                continue
            model = self.models[model_name]
            if not model.is_model_available():
                print(f"Model {model_name} not available; skipping")
                continue
            try:
                result = model.translate(text, source_lang, target_lang)
                if result:
                    conf = float(result.get('confidence', 0) or 0)
                    if conf >= 0.7:
                        result['model_used'] = model_name
                        if self.cache_enabled:
                            self._remember_cache((text, source_lang, target_lang), result)
                        return result
                    if conf > best_conf:
                        best_conf = conf
                        best_result = result
                        best_model = model_name
            except Exception as e:
                print(f"Model {model_name} failed: {e}")
                continue
        
        # Final fallback - try any available model
        for model_name, model in self.models.items():
            if model.is_model_available():
                try:
                    result = model.translate(text, source_lang, target_lang)
                    if result:
                        result['model_used'] = model_name
                        if self.cache_enabled:
                            self._remember_cache((text, source_lang, target_lang), result)
                        return result
                except Exception as e:
                    print(f"Fallback model {model_name} failed: {e}")
                    continue

        # If we had a sub-threshold best result, return it as last resort
        if best_result is not None:
            best_result['model_used'] = best_model
            print(f"Using best available sub-threshold result from {best_model} (confidence={best_conf:.2f})")
            if self.cache_enabled and best_result is not None:
                self._remember_cache((text, source_lang, target_lang), best_result)
            return best_result
        
        return None

    def _remember_cache(self, key: Tuple[str, str, str], value: Dict):
        try:
            self._cache[key] = dict(value)
            self._cache.move_to_end(key)
            while len(self._cache) > self.cache_capacity:
                self._cache.popitem(last=False)
        except Exception:
            pass
    
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
        
        result = self.models[model_name].translate(text, source_lang, target_lang)
        if result:
            result['model_used'] = model_name
        return result
    
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
