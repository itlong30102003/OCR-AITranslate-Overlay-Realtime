"""
OCR module for OCR-AITranslate-Overlay-Realtime
Contains OCR functionality using Tesseract
"""

from .ocr import run_ocr_on_image, run_ocr

__all__ = ['run_ocr_on_image', 'run_ocr']
