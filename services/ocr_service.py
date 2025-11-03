"""OCR Service - Handles OCR processing logic"""

import asyncio
from typing import List, Dict, Tuple
from PIL import Image
from ocr.ocr import run_ocr_on_image


class OCRService:
    """Service for handling OCR operations"""

    def __init__(self):
        """Initialize OCR Service"""
        print("[OCR Service] Initialized")

    def process_image(self, img: Image.Image, region_idx: int, scan_counter: int) -> str:
        """
        Process image and extract text using OCR

        Args:
            img: PIL Image to process
            region_idx: Region index for logging
            scan_counter: Scan counter for logging

        Returns:
            Combined text from all detected lines
        """
        try:
            # Run OCR
            lines = run_ocr_on_image(img)
            if not lines:
                return ""

            print(f"[OCR] Region {region_idx} @ scan {scan_counter}:")
            all_text = []

            for line in lines.values():
                txt = " ".join(line["text"]).strip()
                if not txt:
                    continue
                bbox = (line["x1"], line["y1"], line["x2"], line["y2"])
                print(f"  {txt} -> bbox={bbox}")
                all_text.append(txt)

            # Combine all text
            combined_text = " ".join(all_text).strip()
            return combined_text

        except Exception as e:
            print(f"[OCR Service] Error processing region {region_idx}: {e}")
            return ""

    def extract_text_with_boxes(self, img: Image.Image) -> List[Dict]:
        """
        Extract text with bounding boxes

        Args:
            img: PIL Image to process

        Returns:
            List of dictionaries with text and bbox info
        """
        try:
            lines = run_ocr_on_image(img)
            if not lines:
                return []

            results = []
            for line in lines.values():
                txt = " ".join(line["text"]).strip()
                if not txt:
                    continue

                results.append({
                    'text': txt,
                    'bbox': (line["x1"], line["y1"], line["x2"], line["y2"])
                })

            return results

        except Exception as e:
            print(f"[OCR Service] Error extracting text with boxes: {e}")
            return []

    async def process_image_async(self, img: Image.Image, region_idx: int, scan_counter: int) -> str:
        """
        Async version - Process image and extract text using OCR in thread pool

        Args:
            img: PIL Image to process
            region_idx: Region index for logging
            scan_counter: Scan counter for logging

        Returns:
            Combined text from all detected lines
        """
        # Run CPU-bound OCR in thread pool to avoid blocking event loop
        return await asyncio.to_thread(self.process_image, img, region_idx, scan_counter)
