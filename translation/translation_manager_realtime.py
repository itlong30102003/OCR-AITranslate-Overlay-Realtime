"""
Realtime Translation Manager
Optimized for fast, parallel translation with layered model loading
"""

from typing import Dict, List, Optional, Tuple
from collections import OrderedDict
import os
import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from .base_translator import BaseTranslator
from .gemini_translator import GeminiTranslator
from .nllb_translator import NLLBTranslator
from .opus_translator import OpusTranslator


class RealtimeTranslationManager:
    """Optimized translation manager for realtime performance"""

    def __init__(self, config: Dict = None, realtime_mode: bool = True):
        """
        Initialize RealtimeTranslationManager with optimizations

        Args:
            config: Configuration dictionary with API keys and settings
            realtime_mode: Enable realtime optimizations (lower confidence, parallel execution)
        """
        self.config = config or {}
        self.realtime_mode = realtime_mode
        self.models = {}
        self.cache_enabled = True
        self.cache_capacity = int((self.config or {}).get('cache_size', 512))
        self._cache: OrderedDict[Tuple[str, str, str], Dict] = OrderedDict()
        self._cache_lock = threading.Lock()  # Thread-safe cache
        self._detection_cache: Dict[str, str] = {}  # Language detection cache
        self._detection_lock = threading.Lock()

        # Realtime settings
        self.confidence_threshold = 0.6 if realtime_mode else 0.7
        self.max_workers = 4  # Parallel model execution
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)

        self.quality_matrix = self._setup_quality_matrix()
        self._initialize_models()

    def _setup_quality_matrix(self) -> Dict[Tuple[str, str], List[str]]:
        """Setup quality matrix optimized for realtime performance"""
        return {
            # High-frequency pairs - prioritize speed
            ('en', 'vi'): ['gemini', 'nllb', 'opus'],
            ('vi', 'en'): ['gemini', 'nllb', 'opus'],
            ('en', 'zh'): ['gemini', 'nllb', 'opus'],
            ('zh', 'en'): ['gemini', 'nllb', 'opus'],

            # Medium-frequency pairs
            ('en', 'fr'): ['gemini', 'nllb', 'opus'],
            ('fr', 'en'): ['gemini', 'nllb', 'opus'],
            ('en', 'ja'): ['gemini', 'nllb', 'opus'],
            ('ja', 'en'): ['gemini', 'nllb', 'opus'],

            # Low-frequency pairs - use pivot translation
            ('vi', 'zh'): ['nllb', 'gemini', 'pivot'],
            ('zh', 'vi'): ['nllb', 'gemini', 'pivot'],
            ('vi', 'fr'): ['nllb', 'gemini', 'pivot'],
            ('fr', 'vi'): ['nllb', 'gemini', 'pivot'],
            ('vi', 'ja'): ['nllb', 'gemini', 'pivot'],
            ('ja', 'vi'): ['nllb', 'gemini', 'pivot'],
            ('fr', 'zh'): ['nllb', 'gemini', 'pivot'],
            ('zh', 'fr'): ['nllb', 'gemini', 'pivot'],
            ('fr', 'ja'): ['nllb', 'gemini', 'pivot'],
            ('ja', 'fr'): ['nllb', 'gemini', 'pivot'],
        }

    def _initialize_models(self):
        """Initialize all available translation models with optimizations"""
        print("Initializing realtime translation models...")

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

        # Initialize NLLB-200 (always available, fast for realtime)
        try:
            self.models['nllb'] = NLLBTranslator()
            print("[OK] NLLB-200 translator initialized")
        except Exception as e:
            print(f"[ERROR] Failed to initialize NLLB-200: {e}")

        # Initialize OPUS-MT with layered loading
        try:
            self.models['opus'] = OpusTranslator(layered_loading=True)
            print("[OK] OPUS-MT translator initialized with layered loading")
        except Exception as e:
            print(f"[ERROR] Failed to initialize OPUS-MT: {e}")

        print(f"Total models initialized: {len(self.models)}")

    def translate(self, text: str, source_lang: str = 'auto', target_lang: str = 'vi') -> Optional[Dict]:
        """
        Translate text using optimized realtime algorithm

        Args:
            text: Text to translate
            source_lang: Source language code or 'auto' for auto-detection
            target_lang: Target language code

        Returns:
            Dict with translation result or None if failed
        """
        if not text.strip():
            return None

        # Auto-detect language if needed (with caching)
        if source_lang == 'auto':
            source_lang = self._detect_language_cached(text)

        # Cache lookup (thread-safe)
        if self.cache_enabled:
            key = (text, source_lang, target_lang)
            with self._cache_lock:
                cached = self._cache.get(key)
                if cached:
                    self._cache.move_to_end(key)
                    return dict(cached)

        # Get preferred models for this language pair
        preferred_models = self.quality_matrix.get(
            (source_lang, target_lang),
            ['gemini', 'nllb', 'opus']  # Default fallback
        )

        # Parallel model execution for realtime performance
        result = self._translate_parallel(text, source_lang, target_lang, preferred_models)

        if result:
            result['model_used'] = result.get('model_used', 'unknown')
            if self.cache_enabled:
                self._remember_cache((text, source_lang, target_lang), result)
            return result

        return None

    def _translate_parallel(self, text: str, source_lang: str, target_lang: str, preferred_models: List[str]) -> Optional[Dict]:
        """Execute translation in parallel across models for maximum speed"""
        futures = {}
        results = []

        # Submit all translation tasks in parallel
        for model_name in preferred_models:
            if model_name not in self.models:
                continue
            if model_name == 'pivot':
                # Handle pivot translation separately
                future = self.executor.submit(self._translate_pivot, text, source_lang, target_lang)
            else:
                model = self.models[model_name]
                if not model.is_model_available():
                    continue
                future = self.executor.submit(self._translate_single, model, model_name, text, source_lang, target_lang)
            futures[future] = model_name

        # Collect results as they complete (first good result wins)
        for future in as_completed(futures, timeout=30.0):  # 30 second timeout for slower models
            try:
                result = future.result()
                if result:
                    conf = float(result.get('confidence', 0) or 0)
                    if conf >= self.confidence_threshold:
                        # Cancel remaining futures
                        for f in futures:
                            if not f.done():
                                f.cancel()
                        return result
                    # Keep sub-threshold results as fallback
                    results.append((conf, result))
            except Exception as e:
                print(f"Parallel translation error: {e}")
                continue

        # Return best sub-threshold result if available
        if results:
            results.sort(key=lambda x: x[0], reverse=True)
            best_conf, best_result = results[0]
            best_result['model_used'] = best_result.get('model_used', 'unknown')
            print(f"Using best available sub-threshold result (confidence={best_conf:.2f})")
            return best_result

        return None

    def _translate_single(self, model: BaseTranslator, model_name: str, text: str, source_lang: str, target_lang: str) -> Optional[Dict]:
        """Translate using a single model"""
        try:
            result = model.translate(text, source_lang, target_lang)
            if result:
                result['model_used'] = model_name
            return result
        except Exception as e:
            print(f"Model {model_name} failed: {e}")
            return None

    def _translate_pivot(self, text: str, source_lang: str, target_lang: str) -> Optional[Dict]:
        """Translate using English as pivot for unsupported pairs"""
        try:
            # Step 1: source -> English
            if source_lang != 'en':
                step1 = self.translate(text, source_lang, 'en')
                if not step1 or not step1.get('text', '').strip():
                    return None
                intermediate_text = step1['text']
            else:
                intermediate_text = text

            # Step 2: English -> target
            if target_lang != 'en':
                step2 = self.translate(intermediate_text, 'en', target_lang)
                if not step2 or not step2.get('text', '').strip():
                    return None
                final_result = step2
            else:
                final_result = {'text': intermediate_text, 'confidence': 0.7}

            final_result['model_used'] = 'pivot'
            final_result['source_lang'] = source_lang
            final_result['target_lang'] = target_lang
            return final_result

        except Exception as e:
            print(f"Pivot translation failed: {e}")
            return None

    def _remember_cache(self, key: Tuple[str, str, str], value: Dict):
        """Thread-safe cache storage"""
        try:
            with self._cache_lock:
                self._cache[key] = dict(value)
                self._cache.move_to_end(key)
                while len(self._cache) > self.cache_capacity:
                    self._cache.popitem(last=False)
        except Exception:
            pass

    def _detect_language_cached(self, text: str) -> str:
        """Detect language with caching for performance"""
        # Check cache first
        with self._detection_lock:
            if text in self._detection_cache:
                return self._detection_cache[text]

        # Detect and cache
        detected = self._detect_language(text)
        with self._detection_lock:
            self._detection_cache[text] = detected

        return detected

    def _detect_language(self, text: str) -> str:
        """Detect language of input text"""
        try:
            import langdetect
            detected = langdetect.detect(text)
            lang_map = {
                'en': 'en', 'ja': 'ja', 'zh-cn': 'zh', 'zh-tw': 'zh',
                'vi': 'vi', 'fr': 'fr'
            }
            return lang_map.get(detected, detected)
        except:
            return 'en'  # Default fallback

    # Async support for non-blocking translation
    async def translate_async(self, text: str, source_lang: str = 'auto', target_lang: str = 'vi') -> Optional[Dict]:
        """Async translation method for non-blocking calls"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.translate, text, source_lang, target_lang)

    async def translate_batch_async(self, texts: List[str], source_lang: str = 'auto', target_lang: str = 'vi') -> List[Optional[Dict]]:
        """Async batch translation for multiple texts"""
        tasks = [self.translate_async(text, source_lang, target_lang) for text in texts]
        return await asyncio.gather(*tasks)

    def translate_batch(self, texts: List[str], source_lang: str = 'auto', target_lang: str = 'vi') -> List[Optional[Dict]]:
        """Synchronous batch translation"""
        return [self.translate(text, source_lang, target_lang) for text in texts]

    # Rest of the methods remain similar but optimized
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
        """Translate using a specific model"""
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
            'cache_size': len(self._cache),
            'detection_cache_size': len(self._detection_cache),
            'realtime_mode': self.realtime_mode,
            'confidence_threshold': self.confidence_threshold,
            'models': {}
        }

        for name, model in self.models.items():
            stats['models'][name] = {
                'available': model.is_model_available(),
                'type': model.__class__.__name__
            }

        return stats

    def preload_common_models(self):
        """Preload Layer 1 OPUS models for instant translation"""
        if 'opus' in self.models:
            print("Preloading Layer 1 OPUS models...")
            # Only preload the 5 core language pairs for OCR
            layer1_pairs = [
                ('en', 'vi'), ('vi', 'en'),
                ('en', 'zh'), ('zh', 'en'),
                ('en', 'ja'), ('ja', 'en'),
                ('en', 'fr'), ('fr', 'en')
            ]
            for src, tgt in layer1_pairs:
                try:
                    self.models['opus'].preload_model(src, tgt)
                    print(f"[OK] Preloaded OPUS {src}-{tgt}")
                except Exception as e:
                    print(f"[ERROR] Failed to preload OPUS {src}-{tgt}: {e}")

    def shutdown(self):
        """Cleanup resources"""
        self.executor.shutdown(wait=True)
        print("RealtimeTranslationManager shutdown complete")
