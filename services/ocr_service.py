"""OCR Service - Handles OCR processing logic"""

import asyncio
from typing import List, Dict, Tuple
from dataclasses import dataclass
from PIL import Image
from ocr.ocr import run_ocr_on_image


@dataclass
class TextBox:
    """Data structure for text with bounding box and position information"""
    text: str  # Extracted text
    bbox: Tuple[int, int, int, int]  # Relative bbox (x1, y1, x2, y2) within region
    abs_bbox: Tuple[int, int, int, int]  # Absolute screen bbox (x1, y1, x2, y2)
    region_idx: int  # Region index
    region_coords: Tuple[int, int, int, int]  # Region's absolute screen coordinates


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

    def process_image_with_boxes(
        self,
        img: Image.Image,
        region_idx: int,
        region_coords: Tuple[int, int, int, int],
        scan_counter: int
    ) -> List[TextBox]:
        """
        Process image and extract text with bounding boxes (for positioned overlay)

        Args:
            img: PIL Image to process
            region_idx: Region index
            region_coords: Region's absolute screen coordinates (x1, y1, x2, y2)
            scan_counter: Scan counter for logging

        Returns:
            List of TextBox objects with absolute screen coordinates
        """
        try:
            # Run OCR
            lines = run_ocr_on_image(img)
            if not lines:
                return []

            print(f"[OCR] Region {region_idx} @ scan {scan_counter} (Positioned Mode):")
            text_boxes = []

            # Extract region position
            region_x1, region_y1, region_x2, region_y2 = region_coords

            for line in lines.values():
                txt = " ".join(line["text"]).strip()
                if not txt:
                    continue

                # Relative bbox (within cropped region)
                rel_bbox = (line["x1"], line["y1"], line["x2"], line["y2"])

                # Calculate absolute screen coordinates
                abs_x1 = region_x1 + line["x1"]
                abs_y1 = region_y1 + line["y1"]
                abs_x2 = region_x1 + line["x2"]
                abs_y2 = region_y1 + line["y2"]
                abs_bbox = (abs_x1, abs_y1, abs_x2, abs_y2)

                # Create TextBox
                text_box = TextBox(
                    text=txt,
                    bbox=rel_bbox,
                    abs_bbox=abs_bbox,
                    region_idx=region_idx,
                    region_coords=region_coords
                )
                text_boxes.append(text_box)

                print(f"  {txt} -> abs_bbox={abs_bbox}")

            return text_boxes

        except Exception as e:
            print(f"[OCR Service] Error processing region {region_idx} with boxes: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def process_image_with_boxes_async(
        self,
        img: Image.Image,
        region_idx: int,
        region_coords: Tuple[int, int, int, int],
        scan_counter: int
    ) -> List[TextBox]:
        """
        Async version - Process image and extract text boxes in thread pool

        Args:
            img: PIL Image to process
            region_idx: Region index
            region_coords: Region's absolute screen coordinates (x1, y1, x2, y2)
            scan_counter: Scan counter for logging

        Returns:
            List of TextBox objects with absolute screen coordinates
        """
        # Run CPU-bound OCR in thread pool to avoid blocking event loop
        return await asyncio.to_thread(
            self.process_image_with_boxes,
            img,
            region_idx,
            region_coords,
            scan_counter
        )
