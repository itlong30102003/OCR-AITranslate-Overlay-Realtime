"""
OCR Text Classifier cho Window Screenshot
Tự động phân loại văn bản thành: Paragraph, Menu/Button, Heading, List
"""

import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

class BlockType(Enum):
    PARAGRAPH = "paragraph"          # Đoạn văn nhiều dòng
    UI_BUTTON = "ui_button"          # Button, label đơn lẻ
    MENU_HORIZONTAL = "menu_horizontal"  # Menu items nằm ngang
    MENU_VERTICAL = "menu_vertical"      # Menu items nằm dọc
    HEADING = "heading"              # Tiêu đề
    LIST_ITEM = "list_item"          # Item trong danh sách
    MIXED = "mixed"                  # Không rõ ràng

@dataclass
class TextLine:
    """Một dòng text từ OCR"""
    id: str
    text: str
    bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2)
    
    @property
    def center_x(self):
        return (self.bbox[0] + self.bbox[2]) / 2
    
    @property
    def center_y(self):
        return (self.bbox[1] + self.bbox[3]) / 2
    
    @property
    def width(self):
        return self.bbox[2] - self.bbox[0]
    
    @property
    def height(self):
        return self.bbox[3] - self.bbox[1]

@dataclass
class TextBlock:
    """Một khối văn bản đã được phân loại"""
    type: BlockType
    lines: List[TextLine]
    bbox: Tuple[float, float, float, float]
    confidence: float  # 0-1
    
    def get_full_text(self) -> str:
        return ' '.join([line.text for line in self.lines])


class WindowTextClassifier:
    """
    Phân loại văn bản trong toàn bộ window screenshot
    """
    
    def __init__(self):
        # Ngưỡng có thể điều chỉnh
        self.config = {
            'vertical_spacing_threshold': 1.5,    # Tỉ lệ so với line height
            'horizontal_spacing_threshold': 2.0,  # Tỉ lệ so với avg width
            'min_paragraph_lines': 3,
            'min_paragraph_chars': 80,
            'max_button_chars': 30,
            'menu_alignment_tolerance': 10,  # pixels
        }
    
    def classify_window(self, ocr_results: Dict) -> List[TextBlock]:
        """
        Main function: Phân loại toàn bộ text trong window
        
        Args:
            ocr_results: Dict với format {line_id: {'text': [...], 'bbox': (x1,y1,x2,y2)}}
        
        Returns:
            List of TextBlock đã phân loại
        """
        # 1. Convert sang TextLine objects
        lines = self._parse_ocr_results(ocr_results)
        
        if not lines:
            return []
        
        # 2. Lọc bỏ noise (số, ký tự đơn lẻ, v.v.)
        lines = self._filter_noise(lines)
        
        # 3. Spatial clustering: nhóm các dòng gần nhau
        clusters = self._spatial_clustering(lines)
        
        # 4. Phân loại từng cluster
        blocks = []
        for cluster in clusters:
            block = self._classify_cluster(cluster)
            blocks.append(block)
        
        # 5. Post-processing: merge/refine blocks
        blocks = self._post_process_blocks(blocks)
        
        return blocks
    
    def _parse_ocr_results(self, ocr_results: Dict) -> List[TextLine]:
        """Convert OCR dict sang TextLine objects"""
        lines = []
        for line_id, data in ocr_results.items():
            # Handle cả list of words hoặc single string
            if isinstance(data['text'], list):
                text = ' '.join(data['text']).strip()
            else:
                text = data['text'].strip()
            
            if not text:
                continue
            
            # Handle bbox format - có thể là dict hoặc tuple
            if isinstance(data.get('bbox'), tuple):
                bbox = data['bbox']
            else:
                # Format cũ: x1, y1, x2, y2
                bbox = (data['x1'], data['y1'], data['x2'], data['y2'])
                
            lines.append(TextLine(
                id=str(line_id),
                text=text,
                bbox=tuple(bbox)
            ))
        return lines
    
    def _filter_noise(self, lines: List[TextLine]) -> List[TextLine]:
        """Lọc bỏ các dòng không có ý nghĩa"""
        filtered = []
        for line in lines:
            # Skip nếu:
            # - Chỉ có số
            if line.text.replace(' ', '').replace('.', '').replace(',', '').isdigit():
                continue
            
            # - Quá ngắn (1-2 ký tự) trừ khi là chữ cái
            if len(line.text) <= 2 and not line.text.isalpha():
                continue
            
            # - Chỉ có ký tự đặc biệt
            if all(not c.isalnum() for c in line.text):
                continue
            
            filtered.append(line)
        
        return filtered
    
    def _spatial_clustering(self, lines: List[TextLine]) -> List[List[TextLine]]:
        """
        Nhóm các dòng text gần nhau trong không gian 2D
        Xử lý cả vertical và horizontal proximity
        """
        if not lines:
            return []
        
        # Sort theo vị trí (top to bottom, left to right)
        sorted_lines = sorted(lines, key=lambda l: (l.bbox[1], l.bbox[0]))
        
        clusters = []
        current_cluster = [sorted_lines[0]]
        
        for i in range(1, len(sorted_lines)):
            current_line = sorted_lines[i]
            prev_line = current_cluster[-1]
            
            # Tính khoảng cách vertical và horizontal
            v_gap = current_line.bbox[1] - prev_line.bbox[3]  # y1_current - y2_prev
            h_gap = abs(current_line.center_x - prev_line.center_x)
            
            avg_height = (current_line.height + prev_line.height) / 2
            
            # Quyết định có merge vào cluster hiện tại không
            should_merge = False
            
            # Case 1: Cùng dòng ngang (menu items)
            if v_gap < avg_height * 0.5 and h_gap < current_line.width * 3:
                should_merge = True
            
            # Case 2: Cùng cột dọc (paragraph hoặc vertical menu)
            elif (v_gap < avg_height * self.config['vertical_spacing_threshold'] and
                  h_gap < current_line.width * 0.3):
                should_merge = True
            
            # Case 3: Indent nhẹ (list items)
            elif (v_gap < avg_height * 1.2 and 
                  0 < (current_line.bbox[0] - prev_line.bbox[0]) < avg_height * 2):
                should_merge = True
            
            if should_merge:
                current_cluster.append(current_line)
            else:
                # Start new cluster
                clusters.append(current_cluster)
                current_cluster = [current_line]
        
        # Add last cluster
        if current_cluster:
            clusters.append(current_cluster)
        
        return clusters
    
    def _classify_cluster(self, lines: List[TextLine]) -> TextBlock:
        """
        Phân loại một cluster thành BlockType cụ thể
        """
        if not lines:
            return None
        
        # Tính các features
        num_lines = len(lines)
        total_text = ' '.join([l.text for l in lines])
        total_chars = len(total_text)
        avg_chars_per_line = total_chars / num_lines
        
        # Geometric features
        is_horizontally_aligned = self._check_horizontal_alignment(lines)
        is_vertically_aligned = self._check_vertical_alignment(lines)
        avg_spacing = self._calculate_avg_spacing(lines)
        
        # Text features
        has_sentence_ending = any(
            line.text.strip()[-1] in '.!?。！？'
            for line in lines if line.text.strip()
        )
        has_list_markers = any(
            line.text.strip()[0] in '•-–—·*►▪▫' or
            line.text.strip()[:2] in ['- ', '* ', '+ ']
            for line in lines if line.text.strip()
        )
        all_short = all(len(l.text) < self.config['max_button_chars'] for l in lines)
        
        # Classification logic
        block_type = BlockType.MIXED
        confidence = 0.5
        
        # 1. Menu horizontal (items nằm ngang cùng 1 dòng)
        if is_horizontally_aligned and num_lines >= 2 and all_short:
            block_type = BlockType.MENU_HORIZONTAL
            confidence = 0.9
        
        # 2. Single short line -> Button/Label
        elif num_lines == 1 and total_chars < self.config['max_button_chars']:
            block_type = BlockType.UI_BUTTON
            confidence = 0.85
        
        # 3. Paragraph (nhiều dòng, văn bản dài)
        elif (num_lines >= self.config['min_paragraph_lines'] and
              is_vertically_aligned and
              total_chars > self.config['min_paragraph_chars'] and
              has_sentence_ending):
            block_type = BlockType.PARAGRAPH
            confidence = 0.95
        
        # 4. Heading (1-2 dòng, khá dài, không có dấu chấm)
        elif (num_lines <= 2 and 
              30 < total_chars < 100 and
              not has_sentence_ending):
            block_type = BlockType.HEADING
            confidence = 0.8
        
        # 5. List items (có markers hoặc indent)
        elif has_list_markers or (num_lines >= 2 and self._check_list_pattern(lines)):
            if is_vertically_aligned:
                block_type = BlockType.MENU_VERTICAL
            else:
                block_type = BlockType.LIST_ITEM
            confidence = 0.85
        
        # 6. Vertical menu (nhiều dòng ngắn, align dọc)
        elif (num_lines >= 2 and 
              is_vertically_aligned and 
              all_short and
              avg_spacing < lines[0].height * 2):
            block_type = BlockType.MENU_VERTICAL
            confidence = 0.8
        
        # Calculate bounding box for entire block
        all_x1 = [l.bbox[0] for l in lines]
        all_y1 = [l.bbox[1] for l in lines]
        all_x2 = [l.bbox[2] for l in lines]
        all_y2 = [l.bbox[3] for l in lines]
        
        block_bbox = (min(all_x1), min(all_y1), max(all_x2), max(all_y2))
        
        return TextBlock(
            type=block_type,
            lines=lines,
            bbox=block_bbox,
            confidence=confidence
        )
    
    def _check_horizontal_alignment(self, lines: List[TextLine]) -> bool:
        """Check xem các dòng có nằm ngang cùng hàng không"""
        if len(lines) < 2:
            return False
        
        y_coords = [l.center_y for l in lines]
        y_variance = np.var(y_coords)
        avg_height = np.mean([l.height for l in lines])
        
        # Nếu variance nhỏ -> align horizontal
        return y_variance < (avg_height * 0.3) ** 2
    
    def _check_vertical_alignment(self, lines: List[TextLine]) -> bool:
        """Check xem các dòng có align dọc không"""
        if len(lines) < 2:
            return True
        
        x_starts = [l.bbox[0] for l in lines]
        x_variance = np.var(x_starts)
        
        # Nếu các dòng bắt đầu ở vị trí x gần giống nhau
        return x_variance < 100  # pixels squared
    
    def _calculate_avg_spacing(self, lines: List[TextLine]) -> float:
        """Tính khoảng cách trung bình giữa các dòng"""
        if len(lines) < 2:
            return 0
        
        sorted_lines = sorted(lines, key=lambda l: l.bbox[1])
        spacings = []
        
        for i in range(len(sorted_lines) - 1):
            gap = sorted_lines[i+1].bbox[1] - sorted_lines[i].bbox[3]
            spacings.append(gap)
        
        return np.mean(spacings) if spacings else 0
    
    def _check_list_pattern(self, lines: List[TextLine]) -> bool:
        """Check xem có phải pattern của list không"""
        if len(lines) < 2:
            return False
        
        # Check indent pattern
        x_starts = [l.bbox[0] for l in lines]
        indent_diffs = [x_starts[i+1] - x_starts[i] for i in range(len(x_starts)-1)]
        
        # Nếu có indent nhất quán
        return len(set([round(d, -1) for d in indent_diffs])) <= 2
    
    def _post_process_blocks(self, blocks: List[TextBlock]) -> List[TextBlock]:
        """
        Post-processing: merge blocks tương tự, tách blocks phức tạp
        """
        # TODO: Có thể thêm logic merge các button gần nhau thành menu
        # hoặc tách paragraph quá dài thành nhiều phần
        
        return blocks


# ============ DEMO USAGE ============

def demo_usage():
    """
    Ví dụ sử dụng với OCR results giả định
    """
    
    # Giả sử đây là output từ run_ocr_on_image()
    ocr_results = {
        'line_1': {
            'text': ['Home'],
            'bbox': (10, 10, 80, 40)
        },
        'line_2': {
            'text': ['About'],
            'bbox': (100, 10, 170, 40)
        },
        'line_3': {
            'text': ['Contact'],
            'bbox': (190, 10, 280, 40)
        },
        'line_4': {
            'text': ['Welcome', 'to', 'our', 'website'],
            'bbox': (10, 100, 400, 140)
        },
        'line_5': {
            'text': ['This', 'is', 'a', 'paragraph', 'of', 'text.'],
            'bbox': (10, 150, 400, 180)
        },
        'line_6': {
            'text': ['It', 'contains', 'multiple', 'lines.'],
            'bbox': (10, 185, 400, 215)
        },
        'line_7': {
            'text': ['And', 'provides', 'information', 'to', 'users.'],
            'bbox': (10, 220, 400, 250)
        },
        'line_8': {
            'text': ['Save'],
            'bbox': (50, 300, 120, 340)
        },
        'line_9': {
            'text': ['Cancel'],
            'bbox': (150, 300, 240, 340)
        },
    }
    
    # Sử dụng classifier
    classifier = WindowTextClassifier()
    blocks = classifier.classify_window(ocr_results)
    
    # In kết quả
    print("=== PHÂN LOẠI VĂN BẢN ===\n")
    for i, block in enumerate(blocks, 1):
        print(f"Block {i}: {block.type.value.upper()}")
        print(f"  Confidence: {block.confidence:.2f}")
        print(f"  Text: {block.get_full_text()}")
        print(f"  Bbox: {block.bbox}")
        print(f"  Số dòng: {len(block.lines)}")
        print()


if __name__ == "__main__":
    demo_usage()
