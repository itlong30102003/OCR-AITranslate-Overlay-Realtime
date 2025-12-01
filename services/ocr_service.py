"""OCR Service - Handles OCR processing logic"""

import asyncio
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from PIL import Image
from ocr.ocr import run_ocr_on_image
from ocr.text_classifier import WindowTextClassifier, TextBlock, BlockType


@dataclass
class TextBox:
    """Data structure for text with bounding box and position information"""
    text: str  # Extracted text
    bbox: Tuple[int, int, int, int]  # Relative bbox (x1, y1, x2, y2) within region
    abs_bbox: Tuple[int, int, int, int]  # Absolute screen bbox (x1, y1, x2, y2)
    region_idx: int  # Region index
    region_coords: Tuple[int, int, int, int]  # Region's absolute screen coordinates


@dataclass
class ClassifiedTextBox(TextBox):
    """TextBox with classification information"""
    block_type: BlockType = BlockType.MIXED  # Type of text block
    confidence: float = 0.5  # Classification confidence (0-1)


class OCRService:
    """Service for handling OCR operations"""

    def __init__(self):
        """Initialize OCR Service"""
        self.classifier = WindowTextClassifier()
        print("[OCR Service] Initialized with Text Classifier")

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

    def classify_text_blocks(self, ocr_results: Dict) -> List[TextBlock]:
        """
        Classify OCR results into text blocks

        Args:
            ocr_results: OCR results dict from run_ocr_on_image()

        Returns:
            List of classified TextBlock objects
        """
        try:
            blocks = self.classifier.classify_window(ocr_results)
            return blocks
        except Exception as e:
            print(f"[OCR Service] Error classifying text blocks: {e}")
            import traceback
            traceback.print_exc()
            return []

    def process_image_with_classification(
        self,
        img: Image.Image,
        region_idx: int,
        region_coords: Tuple[int, int, int, int],
        scan_counter: int
    ) -> List[ClassifiedTextBox]:
        """
        Process image with OCR and text classification

        Args:
            img: PIL Image to process
            region_idx: Region index
            region_coords: Region's absolute screen coordinates (x1, y1, x2, y2)
            scan_counter: Scan counter for logging

        Returns:
            List of ClassifiedTextBox objects with block type and confidence
        """
        try:
            # Run OCR
            ocr_results = run_ocr_on_image(img)
            if not ocr_results:
                return []

            # Classify text blocks
            blocks = self.classify_text_blocks(ocr_results)

            print(f"[OCR+Classification] Region {region_idx} @ scan {scan_counter}:")
            classified_boxes = []

            # Extract region position
            region_x1, region_y1, region_x2, region_y2 = region_coords

            # Convert blocks to ClassifiedTextBox objects
            for block in blocks:
                for text_line in block.lines:
                    # Calculate absolute coordinates
                    rel_bbox = text_line.bbox
                    abs_x1 = region_x1 + rel_bbox[0]
                    abs_y1 = region_y1 + rel_bbox[1]
                    abs_x2 = region_x1 + rel_bbox[2]
                    abs_y2 = region_y1 + rel_bbox[3]
                    abs_bbox = (abs_x1, abs_y1, abs_x2, abs_y2)

                    # Create ClassifiedTextBox
                    classified_box = ClassifiedTextBox(
                        text=text_line.text,
                        bbox=rel_bbox,
                        abs_bbox=abs_bbox,
                        region_idx=region_idx,
                        region_coords=region_coords,
                        block_type=block.type,
                        confidence=block.confidence
                    )
                    classified_boxes.append(classified_box)

                    print(f"  [{block.type.value.upper()}] {text_line.text} -> abs_bbox={abs_bbox} (conf: {block.confidence:.2f})")

            return classified_boxes

        except Exception as e:
            print(f"[OCR Service] Error processing with classification: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def process_image_with_classification_async(
        self,
        img: Image.Image,
        region_idx: int,
        region_coords: Tuple[int, int, int, int],
        scan_counter: int
    ) -> List[ClassifiedTextBox]:
        """
        Async version - Process image with OCR and classification in thread pool

        Args:
            img: PIL Image to process
            region_idx: Region index
            region_coords: Region's absolute screen coordinates (x1, y1, x2, y2)
            scan_counter: Scan counter for logging

        Returns:
            List of ClassifiedTextBox objects
        """
        # Run CPU-bound OCR+classification in thread pool
        return await asyncio.to_thread(
            self.process_image_with_classification,
            img,
            region_idx,
            region_coords,
            scan_counter
        )
