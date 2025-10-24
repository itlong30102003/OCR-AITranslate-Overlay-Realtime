"""
Meta NLLB-200 Translator Module
Offline translation with 200+ languages support
"""

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from typing import Dict, Optional
import torch
from .base_translator import BaseTranslator


class NLLBTranslator(BaseTranslator):
    """Meta NLLB-200 translator - Offline with 200+ languages"""
    
    def __init__(self, model_size: str = "600M"):
        super().__init__(f"nllb-200-distilled-{model_size}")
        
        self.model_size = model_size
        self.model_path = f"facebook/nllb-200-distilled-{model_size}"
        
        try:
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_path)
            
            # Set device
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model.to(self.device)
            
            self.is_available = True
            print(f"NLLB-200 loaded successfully on {self.device}")
            
        except Exception as e:
            print(f"Failed to initialize NLLB-200: {e}")
            self.is_available = False
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> Optional[Dict]:
        """
        Translate using NLLB-200
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Dict with translation result or None if failed
        """
        if not self.is_available:
            return None
        
        # Language mapping for NLLB-200
        lang_map = {
            'en': 'eng_Latn', 'ja': 'jpn_Jpan', 
            'zh': 'zho_Hans', 'vi': 'vie_Latn', 'fr': 'fra_Latn'
        }
        
        src = lang_map.get(source_lang, source_lang)
        tgt = lang_map.get(target_lang, target_lang)
            
        try:
            # Set source language for tokenizer
            self.tokenizer.src_lang = src
            
            # Tokenize input
            inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
            
            # Generate translation
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    forced_bos_token_id=self.tokenizer.convert_tokens_to_ids(f"__{tgt}__"),
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
