"""
Meta NLLB-200 Translator Module
Offline translation with 200+ languages support
"""

import os
# Suppress TensorFlow and absl warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from typing import Dict, Optional
import torch
import threading
from .base_translator import BaseTranslator


class NLLBTranslator(BaseTranslator):
    """Meta NLLB-200 translator - Offline with 200+ languages"""

    def __init__(self, model_size: str = "600M"):
        super().__init__(f"nllb-200-distilled-{model_size}")

        self.model_size = model_size
        self.model_path = f"facebook/nllb-200-distilled-{model_size}"

        # Thread lock for GPU access (prevents "Already borrowed" errors)
        self._gpu_lock = threading.Lock()

        try:
            # Force GPU usage if available, otherwise fail
            if not torch.cuda.is_available():
                raise RuntimeError("GPU not available. NLLB-200 requires GPU for optimal performance.")

            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_path)

            # Force GPU device
            self.device = torch.device("cuda")
            self.model.to(self.device)

            self.is_available = True
            print(f"NLLB-200 loaded successfully on {self.device} (thread-safe GPU access)")

        except Exception as e:
            print(f"Failed to initialize NLLB-200: {e}")
            self.is_available = False
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> Optional[Dict]:
        """
        Translate using NLLB-200 with thread-safe GPU access

        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            Dict with translation result or None if failed
        """
        if not self.is_available:
            return None

        # ACQUIRE GPU LOCK - Prevents concurrent GPU access
        with self._gpu_lock:
            # Language mapping for NLLB-200 - Core 5 languages for OCR
            # Updated with correct NLLB-200 language codes
            lang_map = {
                'en': 'eng_Latn',
                'ja': 'jpn_Jpan',  # Supports Hiragana, Katakana, Kanji
                'zh': 'zho_Hans',  # Supports Traditional and Simplified Chinese
                'vi': 'vie_Latn',
                'fr': 'fra_Latn'
            }

            src = lang_map.get(source_lang, source_lang)
            tgt = lang_map.get(target_lang, target_lang)

            # Validate source and target using convert_tokens_to_ids (no lang_code_to_id)
            try:
                self.tokenizer.convert_tokens_to_ids(src)
            except KeyError:
                print(f"Warning: Source language '{src}' not supported, using 'eng_Latn'")
                src = 'eng_Latn'
            try:
                self.tokenizer.convert_tokens_to_ids(tgt)
            except KeyError:
                print(f"Warning: Target language '{tgt}' not supported, using 'eng_Latn'")
                tgt = 'eng_Latn'

            try:
                # Set source language for tokenizer
                self.tokenizer.src_lang = src

                # Tokenize input
                inputs = self.tokenizer(text, return_tensors="pt").to(self.device)

                # Generate translation
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        forced_bos_token_id=self.tokenizer.convert_tokens_to_ids(tgt),
                        max_length=512,
                        num_beams=4,
                        early_stopping=True
                    )

                # Decode output
                translated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

                return {
                    'text': translated_text.strip(),
                    'confidence': 0.8,
                    'model': self.model_name,
                    'cost': 0,  # FREE
                    'source_lang': source_lang,
                    'target_lang': target_lang
                }

            except Exception as e:
                # With lock, we should not get "Already borrowed" errors anymore
                print(f"NLLB-200 translation failed: {e}")
                return None
    
    def get_model_info(self) -> Dict:
        """Get NLLB-200 model information"""
        info = super().get_model_info()
        info.update({
            'provider': 'Meta',
            'cost': 'Free',
            'quota': 'Unlimited',
            'offline': True,
            'quality': 'Good',
            'languages': '200+',
            'model_size': self.model_size,
            'device': str(self.device) if self.is_available else 'N/A'
        })
        return info
