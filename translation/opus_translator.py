"""
Helsinki-NLP OPUS-MT Translator Module
Lightweight translation models for specific language pairs
"""

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from typing import Dict, Optional
import torch
from .base_translator import BaseTranslator


class OpusTranslator(BaseTranslator):
    """Helsinki-NLP OPUS-MT translator - Lightweight for specific pairs"""
    
    def __init__(self):
        super().__init__("opus-mt")
        
        self.loaded_models = {}  # Cache for loaded models
        self.is_available = True
    
    def _get_model_name(self, source_lang: str, target_lang: str) -> str:
        """Get OPUS-MT model name for language pair"""
        return f"Helsinki-NLP/opus-mt-{source_lang}-{target_lang}"
    
    def _load_model(self, source_lang: str, target_lang: str):
        """Load OPUS-MT model for specific language pair"""
        model_name = self._get_model_name(source_lang, target_lang)
        
        if model_name in self.loaded_models:
            return self.loaded_models[model_name]
        
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            
            # Set device
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            model.to(device)
            
            self.loaded_models[model_name] = (tokenizer, model, device)
            print(f"OPUS-MT model loaded: {model_name}")
            
            return self.loaded_models[model_name]
            
        except Exception as e:
            print(f"Failed to load OPUS-MT model {model_name}: {e}")
            return None
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> Optional[Dict]:
        """
        Translate using OPUS-MT
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Dict with translation result or None if failed
        """
        if not self.is_available:
            return None
        
        # Load model for this language pair
        model_data = self._load_model(source_lang, target_lang)
        if model_data is None:
            return None
        
        tokenizer, model, device = model_data
        
        try:
            # Tokenize input
            inputs = tokenizer(text, return_tensors="pt").to(device)
            
            # Generate translation
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_length=512,
                    num_beams=4,
                    early_stopping=True
                )
            
            # Decode output
            translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            return {
                'text': translated_text.strip(),
                'confidence': 0.75,
                'model': f"opus-mt-{source_lang}-{target_lang}",
                'cost': 0,  # FREE
                'source_lang': source_lang,
                'target_lang': target_lang
            }
            
        except Exception as e:
            print(f"OPUS-MT translation failed: {e}")
            return None
    
    def get_model_info(self) -> Dict:
        """Get OPUS-MT model information"""
        info = super().get_model_info()
        info.update({
            'provider': 'Helsinki-NLP',
            'cost': 'Free',
            'quota': 'Unlimited',
            'offline': True,
            'quality': 'Good',
            'languages': 'Multiple pairs',
            'loaded_models': len(self.loaded_models),
            'lightweight': True
        })
        return info
