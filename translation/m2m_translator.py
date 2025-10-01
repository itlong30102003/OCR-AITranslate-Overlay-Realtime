"""
Meta M2M-100 Translator Module
Direct translation between 100 languages without intermediate language
"""

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from typing import Dict, Optional
import torch
from .base_translator import BaseTranslator


class M2MTranslator(BaseTranslator):
    """Meta M2M-100 translator - Direct translation between 100 languages"""
    
    def __init__(self, model_size: str = "418M"):
        super().__init__(f"m2m100-{model_size}")
        
        self.model_size = model_size
        self.model_path = f"facebook/m2m100_{model_size}"
        
        try:
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_path)
            
            # Set device
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model.to(self.device)
            
            self.is_available = True
            print(f"M2M-100 loaded successfully on {self.device}")
            
        except Exception as e:
            print(f"Failed to initialize M2M-100: {e}")
            self.is_available = False
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> Optional[Dict]:
        """
        Translate using M2M-100
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Dict with translation result or None if failed
        """
        if not self.is_available:
            return None
        
        # Language mapping for M2M-100
        lang_map = {
            'en': 'en', 'ja': 'ja', 'zh': 'zh', 'vi': 'vi', 'fr': 'fr'
        }
        
        src = lang_map.get(source_lang, source_lang)
        tgt = lang_map.get(target_lang, target_lang)
        
        try:
            # Set source language
            self.tokenizer.src_lang = src
            
            # Tokenize input
            inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
            
            # Generate translation
            with torch.no_grad():
                generated_tokens = self.model.generate(
                    **inputs,
                    forced_bos_token_id=self.tokenizer.get_lang_id(tgt),
                    max_length=512,
                    num_beams=4,
                    early_stopping=True
                )
            
            # Decode output
            translated_text = self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
            
            return {
                'text': translated_text.strip(),
                'confidence': 0.7,
                'model': self.model_name,
                'cost': 0,  # FREE
                'source_lang': source_lang,
                'target_lang': target_lang
            }
            
        except Exception as e:
            print(f"M2M-100 translation failed: {e}")
            return None
    
    def get_model_info(self) -> Dict:
        """Get M2M-100 model information"""
        info = super().get_model_info()
        info.update({
            'provider': 'Meta',
            'cost': 'Free',
            'quota': 'Unlimited',
            'offline': True,
            'quality': 'Good',
            'languages': '100',
            'model_size': self.model_size,
            'device': str(self.device) if self.is_available else 'N/A',
            'direct_translation': True
        })
        return info
