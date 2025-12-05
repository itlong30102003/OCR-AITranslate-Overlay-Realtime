"""Translation Service - Handles translation operations"""

import asyncio
import time
from typing import Optional, Dict, List
from dataclasses import dataclass
from translation import TranslationManager
from translation.config import TranslationConfig


@dataclass
class TranslatedTextBox:
    """Data structure for translated text with position information"""
    original_text: str
    translated_text: str
    bbox: tuple  # Relative bbox (x1, y1, x2, y2)
    abs_bbox: tuple  # Absolute screen bbox (x1, y1, x2, y2)
    region_idx: int
    region_coords: tuple
    model: str
    confidence: float
    block_type: str = "mixed"  # Type from classifier: paragraph, ui_button, menu_horizontal, etc.
    text_alignment: str = "left"  # Alignment: left, center, right


class TranslationService:
    """Service for handling translation operations"""

    def __init__(self, config: TranslationConfig):
        """
        Initialize Translation Service

        Args:
            config: TranslationConfig instance
        """
        self.config = config
        self.translation_manager: Optional[TranslationManager] = None
        self.source_lang = 'auto'
        self.target_lang = config.get('default_target_lang', 'vi')
        self.preferred_model: Optional[str] = None

        self._initialize()

    def _initialize(self):
        """Initialize translation manager"""
        try:
            self.translation_manager = TranslationManager({
                'gemini_api_key': self.config.get_api_key('gemini')
            })
            # print("[Translation Service] Initialized successfully")
            # print(f"[Translation Service] Available models: {self.get_available_models()}")
        except Exception as e:
            print(f"[Translation Service] Failed to initialize: {e}")
            self.translation_manager = None

    def is_available(self) -> bool:
        """Check if translation service is available"""
        return self.translation_manager is not None

    def translate(self, text: str, region_idx: int, scan_counter: int) -> Optional[Dict]:
        """
        Translate text

        Args:
            text: Text to translate
            region_idx: Region index for logging
            scan_counter: Scan counter for logging

        Returns:
            Dictionary with translation result or None
        """
        if not self.translation_manager:
            return None

        try:
            # Use preferred model if specified
            result = None
            if self.preferred_model:
                res_specific = self.translation_manager.translate_with_model(
                    text, self.source_lang, self.target_lang, self.preferred_model
                )
                if res_specific:
                    result = res_specific
                else:
                    print(f"[Translation Service] Preferred model '{self.preferred_model}' failed. Falling back...")

            # Fallback to auto model selection
            if result is None:
                result = self.translation_manager.translate(text, self.source_lang, self.target_lang)

            if result:
                translated_text = result['text']
                model_used = result.get('model_used', 'unknown')
                confidence = result.get('confidence', 0)

                try:
                    print(f"[Translation Service] Region {region_idx}:")
                    print(f"  Original: {text}")
                    print(f"  Translated: {translated_text}")
                    print(f"  Model: {model_used}, Confidence: {confidence:.2f}")
                except UnicodeEncodeError:
                    # Fallback for console encoding issues
                    print(f"[Translation Service] Region {region_idx}: Translation completed")
                    print(f"  Model: {model_used}, Confidence: {confidence:.2f}")

                return {
                    'original': text,
                    'translated': translated_text,
                    'model': model_used,
                    'confidence': confidence,
                    'scan': scan_counter
                }
            else:
                print(f"[Translation Service] Failed to translate region {region_idx}")
                return None

        except Exception as e:
            print(f"[Translation Service] Error translating region {region_idx}: {e}")
            return None

    def get_available_models(self) -> List[str]:
        """Get list of available translation models"""
        if not self.translation_manager:
            return []
        return self.translation_manager.get_available_models() or []

    def get_model_info(self, model: str) -> Dict:
        """Get information about a specific model"""
        if not self.translation_manager:
            return {}
        return self.translation_manager.get_model_info(model)

    def set_languages(self, source_lang: str, target_lang: str):
        """
        Set source and target languages

        Args:
            source_lang: Source language code
            target_lang: Target language code
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        print(f"[Translation Service] Languages set: {source_lang} -> {target_lang}")

    def set_preferred_model(self, model: Optional[str]):
        """
        Set preferred translation model

        Args:
            model: Model name or None for auto
        """
        self.preferred_model = model
        print(f"[Translation Service] Preferred model: {model or 'auto'}")

    def get_settings(self) -> Dict:
        """Get current translation settings"""
        return {
            'source_lang': self.source_lang,
            'target_lang': self.target_lang,
            'preferred_model': self.preferred_model,
            'available': self.is_available()
        }

    async def translate_async(self, text: str, region_idx: int, scan_counter: int) -> Optional[Dict]:
        """
        Async version - Translate text without blocking

        Args:
            text: Text to translate
            region_idx: Region index for logging
            scan_counter: Scan counter for logging

        Returns:
            Dictionary with translation result or None
        """
        # Run translation in thread pool to avoid blocking event loop
        return await asyncio.to_thread(self.translate, text, region_idx, scan_counter)

    def translate_single_box(self, text: str) -> Optional[Dict]:
        """
        Translate a single text box without logging

        Args:
            text: Text to translate

        Returns:
            Dictionary with translation result or None
        """
        if not self.translation_manager:
            return None

        try:
            # Start timing
            start_time = time.time()
            
            # Use preferred model if specified
            result = None
            if self.preferred_model:
                result = self.translation_manager.translate_with_model(
                    text, self.source_lang, self.target_lang, self.preferred_model
                )

            # Fallback to auto model selection
            if result is None:
                result = self.translation_manager.translate(text, self.source_lang, self.target_lang)

            # Record translation time to SystemMonitor
            elapsed_ms = int((time.time() - start_time) * 1000)
            try:
                from services.system_monitor import get_system_monitor
                monitor = get_system_monitor()
                if monitor:
                    monitor.record_translation_time(elapsed_ms)
            except:
                pass

            return result

        except Exception as e:
            print(f"[Translation Service] Error translating text box: {e}")
            return None
    
    def _group_text_boxes_into_paragraphs(self, text_boxes: List) -> List:
        """
        Group consecutive text boxes into paragraphs based on Y-coordinate proximity
        
        Args:
            text_boxes: List of TextBox objects
            
        Returns:
            List of TextBox objects with merged text for paragraphs
        """
        if not text_boxes:
            return []
        
        # Sort by Y coordinate (top to bottom)
        sorted_boxes = sorted(text_boxes, key=lambda box: box.abs_bbox[1])
        
        groups = []
        current_group = [sorted_boxes[0]]
        
        # Threshold for Y distance to consider same paragraph (pixels)
        Y_THRESHOLD = 20  # Looser grouping - merge more lines together
        
        for i in range(1, len(sorted_boxes)):
            prev_box = sorted_boxes[i-1]
            curr_box = sorted_boxes[i]
            
            # Calculate Y distance between bottom of previous box and top of current box
            prev_bottom = prev_box.abs_bbox[3]
            curr_top = curr_box.abs_bbox[1]
            y_distance = curr_top - prev_bottom
            
            # If close enough, add to current group
            if y_distance <= Y_THRESHOLD:
                current_group.append(curr_box)
            else:
                # Start new group
                groups.append(current_group)
                current_group = [curr_box]
        
        # Add last group
        if current_group:
            groups.append(current_group)
        
        # Merge each group into single TextBox
        merged_boxes = []
        for group in groups:
            if len(group) == 1:
                merged_boxes.append(group[0])
            else:
                # Merge text
                merged_text = ' '.join(box.text for box in group)
                
                # Calculate bounding box that covers all boxes in group
                min_x = min(box.abs_bbox[0] for box in group)
                min_y = min(box.abs_bbox[1] for box in group)
                max_x = max(box.abs_bbox[2] for box in group)
                max_y = max(box.abs_bbox[3] for box in group)
                
                # Create merged TextBox (reuse first box's structure)
                first_box = group[0]
                from dataclasses import replace
                merged_box = replace(
                    first_box,
                    text=merged_text,
                    abs_bbox=(min_x, min_y, max_x, max_y)
                )
                merged_boxes.append(merged_box)
                
                print(f"[Translation Service] Merged {len(group)} lines into paragraph: {merged_text[:50]}...")
        
        return merged_boxes

    async def translate_text_boxes_async(self, text_boxes: List, scan_counter: int) -> List[TranslatedTextBox]:
        """
        Translate multiple text boxes in parallel (for positioned overlay mode)

        Args:
            text_boxes: List of TextBox objects from OCR
            scan_counter: Scan counter for logging

        Returns:
            List of TranslatedTextBox objects with translation results
        """
        if not self.translation_manager or not text_boxes:
            return []

        # Group text boxes into paragraphs before translation
        grouped_boxes = self._group_text_boxes_into_paragraphs(text_boxes)
        
        # print(f"[Translation Service] Translating {len(text_boxes)} text boxes @ scan {scan_counter}...")
        # print(f"[Translation Service] Grouped into {len(grouped_boxes)} paragraphs")

        async def translate_box(text_box):
            """Translate a single TextBox"""
            try:
                # Run translation in thread pool
                result = await asyncio.to_thread(self.translate_single_box, text_box.text)

                if result:
                    return TranslatedTextBox(
                        original_text=text_box.text,
                        translated_text=result['text'],
                        bbox=text_box.bbox,
                        abs_bbox=text_box.abs_bbox,
                        region_idx=text_box.region_idx,
                        region_coords=text_box.region_coords,
                        model=result.get('model_used', 'unknown'),
                        confidence=result.get('confidence', 0.0)
                    )
                else:
                    # Translation failed, return with original text
                    return TranslatedTextBox(
                        original_text=text_box.text,
                        translated_text=text_box.text,  # Fallback to original
                        bbox=text_box.bbox,
                        abs_bbox=text_box.abs_bbox,
                        region_idx=text_box.region_idx,
                        region_coords=text_box.region_coords,
                        model='none',
                        confidence=0.0
                    )

            except Exception as e:
                print(f"[Translation Service] Error translating text box: {e}")
                # Return original text on error
                return TranslatedTextBox(
                    original_text=text_box.text,
                    translated_text=text_box.text,
                    bbox=text_box.bbox,
                    abs_bbox=text_box.abs_bbox,
                    region_idx=text_box.region_idx,
                    region_coords=text_box.region_coords,
                    model='error',
                    confidence=0.0
                )

        # Translate all grouped text boxes in parallel
        tasks = [translate_box(box) for box in grouped_boxes]
        translated_boxes = await asyncio.gather(*tasks)

        # Log results
        # print(f"[Translation Service] Successfully translated {len(translated_boxes)} text boxes")
        # for i, tbox in enumerate(translated_boxes):
        #     try:
        #         print(f"  [{i}] {tbox.original_text} -> {tbox.translated_text} ({tbox.model}, {tbox.confidence:.2f})")
        #     except UnicodeEncodeError:
        #         print(f"  [{i}] Translation completed ({tbox.model}, {tbox.confidence:.2f})")

        return translated_boxes
