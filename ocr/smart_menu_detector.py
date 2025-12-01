"""
Smart OCR Menu Detector - Language-Agnostic
Không cần hardcode keywords, sử dụng ML và heuristics thông minh
"""

import re
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
import numpy as np


@dataclass
class SplitItem:
    """Một item sau khi tách"""
    text: str
    bbox: Tuple[float, float, float, float]
    confidence: float
    item_type: str


class SmartMenuDetector:
    """
    Language-agnostic menu detection
    Sử dụng: geometric features, statistical patterns, NLP
    """
    
    def __init__(self):
        self.config = {
            'menu_separators': [';', '|', '/', '·', '•', '→', '>', '–', '—', '»'],
            'min_item_length': 2,
            'max_item_length': 30,
            'aspect_ratio_threshold': 8.0,
            
            # Statistical thresholds
            'uniformity_threshold': 0.7,      # Độ đồng đều của word lengths
            'capitalization_ratio': 0.5,      # Tỉ lệ từ viết hoa
            'word_length_variance_max': 50,   # Variance thấp = menu
        }
    
    # ============ METHOD 1: GEOMETRIC FEATURES ============
    
    def extract_geometric_features(self, text: str, bbox: Tuple) -> dict:
        """
        Extract các features hình học không phụ thuộc ngôn ngữ
        """
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        
        words = text.split()
        
        return {
            'aspect_ratio': width / height if height > 0 else 0,
            'word_count': len(words),
            'char_count': len(text),
            'avg_word_length': sum(len(w) for w in words) / len(words) if words else 0,
            'word_length_variance': np.var([len(w) for w in words]) if words else 0,
            'has_large_gaps': '  ' in text or '\t' in text,
            'bbox_area': width * height,
            'text_density': len(text) / (width * height) if width * height > 0 else 0
        }
    
    # ============ METHOD 2: STATISTICAL PATTERNS ============
    
    def analyze_word_patterns(self, text: str) -> dict:
        """
        Phân tích patterns thống kê của words (language-independent)
        """
        words = text.split()
        
        if not words:
            return {'is_uniform': False, 'uniformity_score': 0, 'capitalization_ratio': 0, 
                    'alpha_ratio': 0, 'digit_ratio': 0, 'length_variance': 0}
        
        # 1. Word length distribution
        lengths = [len(w) for w in words]
        length_variance = np.var(lengths)
        length_mean = np.mean(lengths)
        
        # Menu items thường có độ dài tương tự nhau
        # Coefficient of variation: std/mean
        cv = np.std(lengths) / length_mean if length_mean > 0 else float('inf')
        
        # 2. Capitalization pattern
        capitalized = sum(1 for w in words if w and w[0].isupper())
        cap_ratio = capitalized / len(words)
        
        # 3. Character type distribution
        alpha_ratio = sum(c.isalpha() for c in text) / len(text) if text else 0
        digit_ratio = sum(c.isdigit() for c in text) / len(text) if text else 0
        
        return {
            'is_uniform': cv < 0.5,  # Low variance → uniform → likely menu
            'uniformity_score': 1 - min(cv, 1.0),  # 0-1 scale
            'length_variance': length_variance,
            'capitalization_ratio': cap_ratio,
            'alpha_ratio': alpha_ratio,
            'digit_ratio': digit_ratio
        }
    
    # ============ METHOD 3: SEPARATOR DETECTION ============
    
    def detect_separator(self, text: str) -> Optional[str]:
        """
        Auto-detect separator được sử dụng
        """
        # Count các ký tự nghi ngờ
        potential_seps = {}
        
        for sep in self.config['menu_separators']:
            count = text.count(sep)
            if count >= 1:  # Xuất hiện ít nhất 1 lần
                potential_seps[sep] = count
        
        if not potential_seps:
            return None
        
        # Return separator xuất hiện nhiều nhất
        return max(potential_seps.items(), key=lambda x: x[1])[0]
    
    # ============ METHOD 4: SPACING ANALYSIS ============
    
    def analyze_spacing(self, text: str) -> dict:
        """
        Phân tích pattern của khoảng trắng
        """
        # Find all whitespace sequences
        space_pattern = r'\s+'
        spaces = re.findall(space_pattern, text)
        
        if not spaces:
            return {'has_uniform_spacing': False, 'avg_gap_size': 0, 'has_large_gaps': False,
                    'gap_variance': 0, 'large_gap_count': 0}
        
        # Tính độ dài của mỗi gap
        gap_sizes = [len(s) for s in spaces]
        
        gap_variance = np.var(gap_sizes)
        avg_gap = np.mean(gap_sizes)
        
        # Check if có nhiều gaps lớn (>= 2 spaces)
        large_gaps = sum(1 for g in gap_sizes if g >= 2)
        has_large_gaps = large_gaps >= 2
        
        return {
            'has_uniform_spacing': gap_variance < 0.5,
            'avg_gap_size': avg_gap,
            'has_large_gaps': has_large_gaps,
            'gap_variance': gap_variance,
            'large_gap_count': large_gaps
        }
    
    # ============ METHOD 5: ML-BASED SCORING ============
    
    def calculate_menu_probability(self, text: str, bbox: Tuple) -> float:
        """
        Tính xác suất là menu dựa trên tất cả features
        Không cần ML model, dùng weighted scoring
        """
        geo_features = self.extract_geometric_features(text, bbox)
        word_patterns = self.analyze_word_patterns(text)
        spacing_analysis = self.analyze_spacing(text)
        
        score = 0.0
        
        # Feature 1: Aspect ratio (weight: 0.3)
        if geo_features['aspect_ratio'] > self.config['aspect_ratio_threshold']:
            score += 0.3
        elif geo_features['aspect_ratio'] > 5:
            score += 0.15
        
        # Feature 2: Word uniformity (weight: 0.25)
        score += word_patterns['uniformity_score'] * 0.25
        
        # Feature 3: Capitalization (weight: 0.15)
        cap_ratio = word_patterns['capitalization_ratio']
        if 0.5 <= cap_ratio <= 1.0:  # Title Case or ALL CAPS
            score += 0.15
        elif cap_ratio == 0.0:  # All lowercase (also common for menus)
            score += 0.1
        
        # Feature 4: Large gaps (weight: 0.2)
        if spacing_analysis['has_large_gaps']:
            score += 0.2
        
        # Feature 5: Word count (weight: 0.1)
        word_count = geo_features['word_count']
        if 2 <= word_count <= 8:
            score += 0.1
        
        # Bonus: Has separator (strong signal)
        if self.detect_separator(text):
            score += 0.3
        
        return min(score, 1.0)  # Cap at 1.0
    
    # ============ MAIN DETECTION ============
    
    def is_horizontal_menu(self, text: str, bbox: Tuple, threshold: float = 0.5) -> bool:
        """
        Detect menu dựa trên ML-style scoring
        
        Args:
            threshold: Confidence threshold (0-1). Default 0.5
        """
        probability = self.calculate_menu_probability(text, bbox)
        return probability >= threshold
    
    # ============ SPLITTING METHODS ============
    
    def split_by_separator(self, text: str) -> Optional[List[str]]:
        """Tách theo separator"""
        separator = self.detect_separator(text)
        
        if not separator:
            return None
        
        items = [item.strip() for item in text.split(separator)]
        items = [item for item in items if item and len(item) >= self.config['min_item_length']]
        
        return items if len(items) >= 2 else None
    
    def split_by_spacing(self, text: str) -> Optional[List[str]]:
        """Tách theo large gaps"""
        spacing = self.analyze_spacing(text)
        
        if not spacing['has_large_gaps']:
            return None
        
        # Split by 2+ consecutive spaces
        items = re.split(r'\s{2,}', text)
        items = [item.strip() for item in items if item.strip()]
        
        if len(items) < 2:
            return None
        
        # Validate: items phải có độ dài hợp lý
        avg_len = sum(len(item) for item in items) / len(items)
        if avg_len > self.config['max_item_length']:
            return None
        
        return items
    
    def split_by_capitalization(self, text: str) -> Optional[List[str]]:
        """Tách theo TitleCase pattern"""
        # Pattern 1: "HomeAboutContact" → ["Home", "About", "Contact"]
        pattern1 = r'([A-Z][a-z]+)'
        matches1 = re.findall(pattern1, text)
        
        if len(matches1) >= 2:
            return matches1
        
        # Pattern 2: "Home About Contact" (already has spaces)
        words = text.split()
        if len(words) >= 2 and all(w[0].isupper() for w in words if w):
            return words
        
        return None
    
    def split_by_equal_width(self, text: str, bbox: Tuple) -> Optional[List[str]]:
        """
        Advanced: Nếu text có vẻ là menu nhưng không có separator rõ ràng,
        thử ước tính số items dựa trên bbox width và avg char width
        """
        words = text.split()
        
        if len(words) < 2:
            return None
        
        # Estimate số items dựa trên word count và spacing
        word_patterns = self.analyze_word_patterns(text)
        
        if word_patterns['is_uniform']:
            # Words có độ dài tương tự → likely menu items
            return words
        
        return None
    
    def smart_split(self, text: str, bbox: Tuple) -> Optional[List[str]]:
        """
        Thử tất cả các phương pháp split, return best result
        """
        # Method 1: Separator (highest confidence)
        items = self.split_by_separator(text)
        if items:
            return items
        
        # Method 2: Large spacing
        items = self.split_by_spacing(text)
        if items:
            return items
        
        # Method 3: Capitalization
        items = self.split_by_capitalization(text)
        if items:
            return items
        
        # Method 4: Advanced - Equal-width splitting
        items = self.split_by_equal_width(text, bbox)
        if items:
            return items
        
        return None
    
    # ============ BBOX ESTIMATION ============
    
    def estimate_item_bboxes(
        self, 
        items: List[str], 
        original_bbox: Tuple[float, float, float, float],
        original_text: str
    ) -> List[Tuple[float, float, float, float]]:
        """Ước tính bbox cho từng item"""
        x1, y1, x2, y2 = original_bbox
        total_width = x2 - x1
        
        # Strategy: Phân chia dựa trên vị trí trong text
        item_positions = []
        current_pos = 0
        
        for item in items:
            start_pos = original_text.find(item, current_pos)
            if start_pos == -1:
                # Fallback: estimate based on previous positions
                start_pos = current_pos
            end_pos = start_pos + len(item)
            item_positions.append((start_pos, end_pos))
            current_pos = end_pos
        
        # Convert positions to bboxes
        text_len = len(original_text)
        bboxes = []
        
        for start_pos, end_pos in item_positions:
            # Calculate x coordinates based on text position
            start_ratio = start_pos / text_len if text_len > 0 else 0
            end_ratio = end_pos / text_len if text_len > 0 else 0
            
            item_x1 = x1 + start_ratio * total_width
            item_x2 = x1 + end_ratio * total_width
            
            bboxes.append((item_x1, y1, item_x2, y2))
        
        return bboxes
    
    # ============ MAIN ENTRY POINT ============
    
    def split_horizontal_menu(
        self,
        text: str,
        bbox: Tuple[float, float, float, float],
        confidence: float = 1.0,
        threshold: float = 0.5
    ) -> List[SplitItem]:
        """
        Main function: Detect và split menu
        
        Args:
            threshold: Menu detection threshold (0-1)
        """
        # Check if là menu
        if not self.is_horizontal_menu(text, bbox, threshold):
            return [SplitItem(text, bbox, confidence, 'text')]
        
        # Try split
        items = self.smart_split(text, bbox)
        
        if items is None or len(items) < 2:
            return [SplitItem(text, bbox, confidence, 'text')]
        
        # Estimate bboxes
        item_bboxes = self.estimate_item_bboxes(items, bbox, text)
        
        # Create SplitItems
        split_items = []
        for item_text, item_bbox in zip(items, item_bboxes):
            split_items.append(SplitItem(
                text=item_text,
                bbox=item_bbox,
                confidence=confidence * 0.9,  # Slightly lower confidence after split
                item_type='menu'
            ))
        
        print(f"[SmartMenuDetector] Split '{text}' into {len(split_items)} items")
        for i, item in enumerate(split_items):
            print(f"  [{i}] {item.text}")
        
        return split_items
    
    def process_ocr_results(self, ocr_results: Dict, threshold: float = 0.5) -> Dict:
        """
        Process toàn bộ OCR results - pre-process trước khi classify
        
        Args:
            ocr_results: OCR dict {line_id: {'text': ..., 'bbox': ...}}
            threshold: Menu detection threshold
            
        Returns:
            Processed OCR dict với menu items đã được tách
        """
        new_results = {}
        
        for line_id, data in ocr_results.items():
            # Parse text
            if isinstance(data['text'], list):
                text = ' '.join(data['text'])
            else:
                text = data['text']
            
            # Get bbox
            if isinstance(data.get('bbox'), tuple):
                bbox = data['bbox']
            else:
                bbox = (data['x1'], data['y1'], data['x2'], data['y2'])
            
            confidence = data.get('confidence', 1.0)
            
            # Try split
            split_items = self.split_horizontal_menu(text, bbox, confidence, threshold)
            
            # If no split OR split failed, keep original
            if len(split_items) == 1 and split_items[0].text == text:
                new_results[line_id] = data
            else:
                # Add split items as separate lines
                for i, item in enumerate(split_items):
                    new_id = f"{line_id}_split_{i}"
                    new_results[new_id] = {
                        'text': [item.text] if isinstance(data['text'], list) else item.text,
                        'bbox': item.bbox,
                        'x1': item.bbox[0],
                        'y1': item.bbox[1],
                        'x2': item.bbox[2],
                        'y2': item.bbox[3],
                        'confidence': item.confidence,
                        'item_type': item.item_type,
                        'original_line': line_id
                    }
        
        return new_results


# ============ DEMO USAGE ============

def demo_firebase_case():
    """Test với case Firebase menu"""
    detector = SmartMenuDetector()
    
    # Case from user
    text = "Firebase Build Run Solutions Pricing More"
    bbox = (85, 155, 770, 185)
    
    print("="*80)
    print("TEST: Firebase Menu Detection")
    print("="*80)
    print(f"Text: {text}")
    print(f"Bbox: {bbox}")
    print()
    
    # Calculate probability
    probability = detector.calculate_menu_probability(text, bbox)
    print(f"Menu Probability: {probability:.2f}")
    
    # Check if is menu
    is_menu = detector.is_horizontal_menu(text, bbox)
    print(f"Is Menu: {is_menu}")
    print()
    
    # Try split
    split_items = detector.split_horizontal_menu(text, bbox)
    
    print(f"\nResult: {len(split_items)} items")
    for i, item in enumerate(split_items):
        print(f"  {i+1}. {item.text}")
        print(f"     Bbox: {item.bbox}")
        print(f"     Type: {item.item_type}")


if __name__ == "__main__":
    demo_firebase_case()
