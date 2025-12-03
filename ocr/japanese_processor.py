"""Japanese OCR Processor - Fix character-level splitting issue"""

import re
from typing import List, Tuple, Optional


class JapaneseOCRProcessor:
    """
    Process Japanese OCR output to fix character-level splitting
    
    Problem: OCR splits Japanese into individual characters (ユー, ザー, は...)
    Solution: Group by Y coordinate → merge characters → tokenize with fugashi
    """
    
    def __init__(self):
        """Initialize with fugashi tagger (lazy loading)"""
        self._tagger = None
        print("[Japanese Processor] Initialized (lazy loading)")
    
    @property
    def tagger(self):
        """Lazy-load fugashi tagger"""
        if self._tagger is None:
            try:
                from fugashi import Tagger
                self._tagger = Tagger()
                print("[Japanese Processor] fugashi loaded")
            except ImportError:
                print("[Japanese Processor] Warning: fugashi not installed")
                print("  Install with: pip install 'fugashi[unidic-lite]'")
                self._tagger = False
            except Exception as e:
                print(f"[Japanese Processor] Error loading fugashi: {e}")
                self._tagger = False
        
        return self._tagger if self._tagger is not False else None
    
    def extract_text_from_ocr_output(self, ocr_output: str, y_tolerance: int = 20) -> List[str]:
        """
        Extract text from OCR output string and group by Y coordinate
        
        Args:
            ocr_output: OCR output with format "text -> abs_bbox=(...)"
            y_tolerance: Max Y distance to consider same line
            
        Returns:
            List of lines (merged characters)
        """
        lines = []
        current_line = []
        last_y = None
        
        for line in ocr_output.strip().split('\n'):
            # Skip non-OCR lines
            if '->' not in line or 'abs_bbox=' not in line:
                continue
            
            # Extract text and bbox
            parts = line.split('->')
            if len(parts) < 2:
                continue
            
            text = parts[0].strip()
            
            # Extract Y coordinate from bbox
            bbox_match = re.search(r'abs_bbox=\(([^,]+),\s*([^,]+)', parts[1])
            if bbox_match:
                try:
                    x = float(bbox_match.group(1))
                    y = float(bbox_match.group(2))
                    
                    # If Y changes significantly = new line
                    if last_y is None or abs(y - last_y) > y_tolerance:
                        if current_line:
                            lines.append(''.join(current_line))
                        current_line = [text]
                        last_y = y
                    else:
                        current_line.append(text)
                except ValueError:
                    continue
        
        # Add final line
        if current_line:
            lines.append(''.join(current_line))
        
        return lines
    
    def clean_japanese_text(self, text: str) -> str:
        """
        Clean Japanese text by removing spaces between Japanese characters
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text with no spaces between Japanese chars
        """
        # Remove spaces between Japanese characters
        # Japanese ranges: Hiragana, Katakana, Kanji
        text = re.sub(
            r'(?<=[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF])\s+(?=[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF])',
            '',
            text
        )
        return text.strip()
    
    def tokenize_with_fugashi(self, text: str) -> str:
        """
        Tokenize Japanese text with fugashi
        
        Args:
            text: Input Japanese text
            
        Returns:
            Space-separated tokens
        """
        if not self.tagger:
            return text
        
        try:
            # Remove all spaces first
            text_no_space = ''.join(text.split())
            
            # Tokenize
            words = [word.surface for word in self.tagger(text_no_space)]
            
            return ' '.join(words)
        except Exception as e:
            print(f"[Japanese Processor] Tokenize error: {e}")
            return text
    
    def process_ocr_output(self, ocr_output: str, use_tokenizer: bool = True) -> List[str]:
        """
        Process complete OCR output
        
        Args:
            ocr_output: String containing OCR output
            use_tokenizer: True to use fugashi tokenize, False to just merge
            
        Returns:
            List of processed lines
        """
        # Step 1: Extract text by line (using Y coordinate)
        lines = self.extract_text_from_ocr_output(ocr_output)
        
        # Step 2: Process each line
        processed_lines = []
        for line in lines:
            # Clean
            cleaned = self.clean_japanese_text(line)
            
            # Tokenize if needed
            if use_tokenizer and self.tagger:
                processed = self.tokenize_with_fugashi(cleaned)
            else:
                processed = cleaned
            
            if processed:  # Only add non-empty lines
                processed_lines.append(processed)
        
        return processed_lines
    
    def process_and_translate_ready(self, ocr_output: str, verbose: bool = False) -> str:
        """
        Process and return text ready for translation
        
        Args:
            ocr_output: OCR output string
            verbose: Print processing details
            
        Returns:
            Full processed text joined by newlines
        """
        lines = self.process_ocr_output(ocr_output, use_tokenizer=True)
        
        if verbose:
            print("=" * 60)
            print("Text processed (ready for translation):")
            print("=" * 60)
            for i, line in enumerate(lines, 1):
                print(f"{i}. {line}")
            print("=" * 60)
        
        return '\n'.join(lines)
    
    def process_textbox_list(self, textboxes: List, y_tolerance: int = 20) -> List[str]:
        """
        Process list of TextBox objects from OCR service
        
        Args:
            textboxes: List of TextBox/ClassifiedTextBox objects
            y_tolerance: Max Y distance to consider same line
            
        Returns:
            List of processed lines
        """
        if not textboxes:
            return []
        
        # Group by Y coordinate
        lines = []
        current_line = []
        last_y = None
        
        # Sort by Y then X
        sorted_boxes = sorted(textboxes, key=lambda box: (box.abs_bbox[1], box.abs_bbox[0]))
        
        for box in sorted_boxes:
            y = box.abs_bbox[1]  # top Y coordinate
            
            # If Y changes significantly = new line
            if last_y is None or abs(y - last_y) > y_tolerance:
                if current_line:
                    merged = ''.join(current_line)
                    lines.append(merged)
                current_line = [box.text]
                last_y = y
            else:
                current_line.append(box.text)
        
        # Add final line
        if current_line:
            merged = ''.join(current_line)
            lines.append(merged)
        
        # Process each line
        processed_lines = []
        for line in lines:
            cleaned = self.clean_japanese_text(line)
            if self.tagger:
                tokenized = self.tokenize_with_fugashi(cleaned)
                processed_lines.append(tokenized)
            else:
                processed_lines.append(cleaned)
        
        return processed_lines


# ===== DEMO =====
if __name__ == "__main__":
    # Sample OCR output from user
    ocr_output = """
    ユー -> abs_bbox=(61.0, 424, 97.63636363636364, 463)
    ザー -> abs_bbox=(115.95454545454545, 424, 152.5909090909091, 463)
    は -> abs_bbox=(170.9090909090909, 424, 189.22727272727272, 463)
    テス -> abs_bbox=(207.54545454545456, 424, 244.1818181818182, 463)
    ト -> abs_bbox=(262.5, 424, 280.8181818181818, 463)
    を -> abs_bbox=(299.1363636363636, 424, 317.45454545454544, 463)
    行い -> abs_bbox=(335.77272727272725, 424, 372.4090909090909, 463)
    た -> abs_bbox=(390.72727272727275, 424, 409.04545454545456, 463)
    いと -> abs_bbox=(427.3636363636364, 424, 464.0, 463)
    考え -> abs_bbox=(482.3181818181818, 424, 518.9545454545455, 463)
    て -> abs_bbox=(537.2727272727273, 424, 555.5909090909091, 463)
    いま -> abs_bbox=(573.9090909090909, 424, 610.5454545454545, 463)
    す -> abs_bbox=(628.8636363636364, 424, 647.1818181818182, 463)
    オ -> abs_bbox=(665.5, 424, 683.8181818181818, 463)
    バ -> abs_bbox=(702.1363636363636, 424, 720.4545454545455, 463)
    レ -> abs_bbox=(738.7727272727273, 424, 757.0909090909091, 463)
    イ -> abs_bbox=(775.4090909090909, 424, 793.7272727272727, 463)
    を -> abs_bbox=(812.0454545454545, 424, 830.3636363636364, 463)
    テ -> abs_bbox=(848.6818181818182, 424, 867.0, 463)
    スト -> abs_bbox=(62.0, 468, 98.46511627906978, 507)
    する -> abs_bbox=(116.69767441860465, 468, 153.16279069767444, 507)
    た -> abs_bbox=(171.3953488372093, 468, 189.6279069767442, 507)
    め -> abs_bbox=(207.86046511627907, 468, 226.09302325581396, 507)
    に -> abs_bbox=(244.32558139534885, 468, 262.5581395348837, 507)
    アプ -> abs_bbox=(280.7906976744186, 468, 317.2558139534884, 507)
    リ -> abs_bbox=(335.48837209302326, 468, 353.72093023255815, 507)
    を -> abs_bbox=(371.95348837209303, 468, 390.1860465116279, 507)
    実行 -> abs_bbox=(408.4186046511628, 468, 444.8837209302325, 507)
    し -> abs_bbox=(463.1162790697675, 468, 481.3488372093023, 507)
    ます -> abs_bbox=(499.5813953488372, 468, 536.046511627907, 507)
    """
    
    # Initialize processor
    processor = JapaneseOCRProcessor()
    
    # Process
    print("\n" + "="*60)
    print("JAPANESE OCR PROCESSOR - DEMO")
    print("="*60)
    
    result = processor.process_and_translate_ready(ocr_output, verbose=True)
    
    print("\n📝 Full text for translation:")
    print(result)
    
    # Compare with/without tokenizer
    print("\n" + "="*60)
    print("COMPARISON: Without tokenizer vs With tokenizer")
    print("="*60)
    
    lines_no_token = processor.process_ocr_output(ocr_output, use_tokenizer=False)
    lines_with_token = processor.process_ocr_output(ocr_output, use_tokenizer=True)
    
    for i, (no_token, with_token) in enumerate(zip(lines_no_token, lines_with_token), 1):
        print(f"\nLine {i}:")
        print(f"  No tokenize:  {no_token}")
        print(f"  With tokenize: {with_token}")
