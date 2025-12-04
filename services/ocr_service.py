"""OCR Service - Handles OCR processing logic"""

import asyncio
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from PIL import Image
from ocr.ocr import run_ocr_on_image
from ocr.text_classifier import WindowTextClassifier, TextBlock, BlockType
from ocr.tokenization_helper import tokenize_text
from ocr.japanese_processor import JapaneseOCRProcessor


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

    def __init__(self, enable_tokenization: bool = True, enable_japanese_processing: bool = False, source_lang: str = 'auto'):
        """
        Initialize OCR Service
        
        Args:
            enable_tokenization: Whether to enable multi-language tokenization (default: True)
            enable_japanese_processing: Whether to enable Japanese character grouping (default: True)
            source_lang: Source language for OCR optimization (auto, jpn, chi, eng, vie, fra)
        """
        self.classifier = WindowTextClassifier()
        self.enable_tokenization = enable_tokenization
        self.enable_japanese_processing = enable_japanese_processing
        self.source_lang = source_lang
        
        # Lazy-load Japanese processor
        self._japanese_processor = None
        
        print(f"[OCR Service] Initialized (Tokenization: {'ON' if enable_tokenization else 'OFF'}, Japanese Processing: {'ON' if enable_japanese_processing else 'OFF'}, Language: {source_lang})")
    
    def set_source_language(self, lang: str):
        """Update source language for OCR optimization"""
        self.source_lang = lang
        print(f"[OCR Service] Source language changed to: {lang}")
    
    @property
    def japanese_processor(self):
        """Lazy-load Japanese processor"""
        if self._japanese_processor is None and self.enable_japanese_processing:
            self._japanese_processor = JapaneseOCRProcessor()
        return self._japanese_processor

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
            
            # Apply tokenization if enabled
            if self.enable_tokenization and combined_text:
                combined_text = tokenize_text(combined_text, enable_tokenization=True)
            
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
            # Run OCR with source language
            lines = run_ocr_on_image(img, source_lang=self.source_lang)
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

            # Apply Japanese processing if enabled (groups by Y coordinate + tokenizes)
            if self.enable_japanese_processing and text_boxes:
                text_boxes = self._apply_japanese_processing(text_boxes)
            
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
    
    def _has_japanese_characters(self, text_boxes: List[TextBox]) -> bool:
        """
        Check if text boxes contain Japanese characters
        
        Args:
            text_boxes: List of TextBox objects
            
        Returns:
            True if Japanese characters detected
        """
        import re
        
        # Combine all text
        all_text = ' '.join(box.text for box in text_boxes)
        
        # Check for Japanese characters (Hiragana, Katakana, Kanji)
        japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]')
        has_japanese = bool(japanese_pattern.search(all_text))
        
        if has_japanese:
            # Count Japanese vs total characters
            japanese_chars = len(japanese_pattern.findall(all_text))
            total_chars = len(all_text.replace(' ', ''))
            
            # Only process if >20% is Japanese
            if total_chars > 0 and japanese_chars / total_chars > 0.2:
                print(f"  [Language Detection] Japanese detected ({japanese_chars}/{total_chars} chars)")
                return True
        
        return False
    
    def _apply_japanese_processing(self, text_boxes: List[TextBox]) -> List[TextBox]:
        """
        Apply Japanese post-processing to text boxes
        Groups characters by Y coordinate and applies tokenization
        ONLY APPLIED IF JAPANESE CHARACTERS DETECTED
        
        Args:
            text_boxes: List of TextBox objects
            
        Returns:
            List of processed TextBox objects with merged and tokenized text
        """
        if not self.japanese_processor or not text_boxes:
            return text_boxes
        
        # ⚠️ CRITICAL: Only process if Japanese detected
        if not self._has_japanese_characters(text_boxes):
            print(f"  [Japanese Processing] Skipped - no Japanese detected")
            return text_boxes
        
        try:
            # Use Japanese processor to group by Y coordinate
            processed_lines = self.japanese_processor.process_textbox_list(text_boxes)
            
            if not processed_lines:
                return text_boxes
            
            # Create new text boxes with merged text (one per line)
            # Use the bounding box of the first text box in each line
            new_boxes = []
            
            # Group original boxes by Y coordinate to match processed lines
            lines_by_y = {}
            for box in sorted(text_boxes, key=lambda b: (b.abs_bbox[1], b.abs_bbox[0])):
                y = box.abs_bbox[1]
                
                # Find matching Y group
                matched = False
                for line_y in lines_by_y.keys():
                    if abs(y - line_y) < 20:  # Same tolerance as processor
                        lines_by_y[line_y].append(box)
                        matched = True
                        break
                
                if not matched:
                    lines_by_y[y] = [box]
            
            # Create merged boxes
            for i, (line_y, boxes_in_line) in enumerate(sorted(lines_by_y.items())):
                if i < len(processed_lines):
                    # Get bounding box that covers all boxes in this line
                    min_x = min(box.abs_bbox[0] for box in boxes_in_line)
                    min_y = min(box.abs_bbox[1] for box in boxes_in_line)
                    max_x = max(box.abs_bbox[2] for box in boxes_in_line)
                    max_y = max(box.abs_bbox[3] for box in boxes_in_line)
                    
                    # Use first box's region info
                    first_box = boxes_in_line[0]
                    
                    # Calculate relative bbox
                    region_x1, region_y1, _, _ = first_box.region_coords
                    rel_x1 = min_x - region_x1
                    rel_y1 = min_y - region_y1
                    rel_x2 = max_x - region_x1
                    rel_y2 = max_y - region_y1
                    
                    merged_box = TextBox(
                        text=processed_lines[i],
                        bbox=(rel_x1, rel_y1, rel_x2, rel_y2),
                        abs_bbox=(min_x, min_y, max_x, max_y),
                        region_idx=first_box.region_idx,
                        region_coords=first_box.region_coords
                    )
                    new_boxes.append(merged_box)
                    
                    print(f"  [JP Processed] {processed_lines[i]} -> abs_bbox={merged_box.abs_bbox}")
            
            return new_boxes if new_boxes else text_boxes
            
        except Exception as e:
            print(f"[OCR Service] Error in Japanese processing: {e}")
            import traceback
            traceback.print_exc()
            return text_boxes

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
            # Run OCR with source language
            ocr_results = run_ocr_on_image(img, source_lang=self.source_lang)
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
