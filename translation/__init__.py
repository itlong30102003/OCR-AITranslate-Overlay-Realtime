"""
Translation module for OCR-AITranslate-Overlay-Realtime
Contains all translation models and management system
"""

from .translation_manager import TranslationManager
from .base_translator import BaseTranslator

__all__ = ['TranslationManager', 'BaseTranslator']
