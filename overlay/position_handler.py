"""
Overlay Position Handler - Xử lý vị trí overlay translation chính xác
Giải quyết các vấn đề: DPI scaling, window coords, multi-monitor, text alignment
"""

import ctypes
from dataclasses import dataclass
from typing import Tuple, Optional, List
from enum import Enum
import platform


class OverlayStrategy(Enum):
    """Các chiến lược hiển thị overlay"""
    REPLACE = "replace"      # Thay thế text gốc (đè lên)
    BELOW = "below"          # Hiển thị bên dưới
    ABOVE = "above"          # Hiển thị bên trên
    SIDE = "side"            # Hiển thị bên cạnh
    TOOLTIP = "tooltip"      # Hiển thị dạng tooltip khi hover


class TextAlignment(Enum):
    """Căn chỉnh text trong overlay"""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


@dataclass
class WindowInfo:
    """Thông tin về window đang capture"""
    hwnd: int                    # Window handle
    x: int                       # Window position X (screen coords)
    y: int                       # Window position Y (screen coords)
    width: int                   # Window width
    height: int                  # Window height
    dpi_scale: float             # DPI scaling factor (1.0 = 100%, 1.5 = 150%)
    titlebar_height: int         # Chiều cao titlebar
    border_width: int            # Độ rộng border


@dataclass
class OverlayBox:
    """Thông tin về một overlay translation"""
    original_bbox: Tuple[float, float, float, float]  # OCR bbox (x1,y1,x2,y2)
    screen_bbox: Tuple[int, int, int, int]            # Screen coordinates
    translation: str
    original_text: str
    block_type: str              # paragraph, button, menu, etc.
    font_size: int
    alignment: TextAlignment
    background_color: Tuple[int, int, int, int]  # RGBA
    text_color: Tuple[int, int, int]             # RGB


class OverlayPositionHandler:
    """
    Xử lý chuyển đổi coordinates và positioning cho overlay
    """
    
    def __init__(self, window_info: Optional[WindowInfo] = None):
        self.window_info = window_info
        self.screen_width, self.screen_height = self._get_screen_size()
        
    def _get_screen_size(self) -> Tuple[int, int]:
        """Lấy kích thước màn hình"""
        if platform.system() == "Windows":
            try:
                user32 = ctypes.windll.user32
                return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
            except:
                return 1920, 1080
        else:
            # macOS/Linux - default fallback
            return 1920, 1080
    
    def _get_dpi_scale(self) -> float:
        """
        Lấy DPI scaling factor của window
        Windows có thể scale 100%, 125%, 150%, 200%
        """
        if platform.system() == "Windows":
            try:
                user32 = ctypes.windll.user32
                shcore = ctypes.windll.shcore
                
                # Set DPI awareness
                shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
                
                # Get DPI
                hdc = user32.GetDC(0)
                dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
                user32.ReleaseDC(0, hdc)
                
                return dpi / 96.0  # 96 DPI = 100% scale
            except:
                return 1.0
        return 1.0
    
    def image_to_window_coords(
        self, 
        bbox: Tuple[float, float, float, float],
        image_size: Tuple[int, int],
        capture_region: Optional[Tuple[int, int, int, int]] = None
    ) -> Tuple[int, int, int, int]:
        """
        Chuyển đổi coordinates từ image space sang window space
        
        Args:
            bbox: (x1, y1, x2, y2) trong image coordinates
            image_size: (width, height) của image được OCR
            capture_region: (x, y, w, h) vùng được capture (nếu không capture full window)
        
        Returns:
            (x1, y1, x2, y2) trong window coordinates
        """
        img_w, img_h = image_size
        x1, y1, x2, y2 = bbox
        
        # Nếu có capture_region, tính offset
        offset_x = 0
        offset_y = 0
        scale_x = 1.0
        scale_y = 1.0
        
        if capture_region:
            offset_x, offset_y, region_w, region_h = capture_region
            # Tính scale nếu image bị resize
            scale_x = region_w / img_w if img_w > 0 else 1.0
            scale_y = region_h / img_h if img_h > 0 else 1.0
        elif self.window_info:
            # Capture full window
            scale_x = self.window_info.width / img_w if img_w > 0 else 1.0
            scale_y = self.window_info.height / img_h if img_h > 0 else 1.0
        
        # Transform coordinates
        win_x1 = int(x1 * scale_x + offset_x)
        win_y1 = int(y1 * scale_y + offset_y)
        win_x2 = int(x2 * scale_x + offset_x)
        win_y2 = int(y2 * scale_y + offset_y)
        
        return (win_x1, win_y1, win_x2, win_y2)
    
    def window_to_screen_coords(
        self, 
        bbox: Tuple[int, int, int, int]
    ) -> Tuple[int, int, int, int]:
        """
        Chuyển đổi window coordinates sang screen coordinates
        
        Args:
            bbox: (x1, y1, x2, y2) trong window coordinates
        
        Returns:
            (x1, y1, x2, y2) trong screen coordinates
        """
        if not self.window_info:
            # No window info, assume bbox is already in screen coords
            return bbox
            
        win_x1, win_y1, win_x2, win_y2 = bbox
        
        # Thêm window position và compensate cho titlebar/border
        screen_x1 = self.window_info.x + win_x1 + self.window_info.border_width
        screen_y1 = self.window_info.y + win_y1 + self.window_info.titlebar_height
        screen_x2 = self.window_info.x + win_x2 + self.window_info.border_width
        screen_y2 = self.window_info.y + win_y2 + self.window_info.titlebar_height
        
        # Apply DPI scaling
        dpi = self.window_info.dpi_scale
        screen_x1 = int(screen_x1 * dpi)
        screen_y1 = int(screen_y1 * dpi)
        screen_x2 = int(screen_x2 * dpi)
        screen_y2 = int(screen_y2 * dpi)
        
        return (screen_x1, screen_y1, screen_x2, screen_y2)
    
    def calculate_overlay_position(
        self,
        original_bbox: Tuple[int, int, int, int],
        translation_text: str,
        original_text: str,
        block_type: str,
        strategy: OverlayStrategy = OverlayStrategy.REPLACE,
        padding: int = 5
    ) -> OverlayBox:
        """
        Tính toán vị trí và style cho overlay dựa trên strategy
        
        Returns:
            OverlayBox với đầy đủ thông tin để render
        """
        x1, y1, x2, y2 = original_bbox
        width = x2 - x1
        height = y2 - y1
        
        # Estimate font size dựa trên original text height
        font_size = max(10, int(height * 0.7))
        
        # Calculate text dimensions (ước tính)
        trans_width = self._estimate_text_width(translation_text, font_size)
        trans_height = font_size + padding * 2
        
        # Determine overlay position based on strategy
        overlay_x1, overlay_y1 = x1, y1
        overlay_x2, overlay_y2 = x2, y2
        
        if strategy == OverlayStrategy.REPLACE:
            # Đè lên text gốc
            overlay_x1 = x1
            overlay_y1 = y1
            overlay_x2 = max(x2, x1 + trans_width + padding * 2)
            overlay_y2 = y2
            
        elif strategy == OverlayStrategy.BELOW:
            # Hiển thị bên dưới
            overlay_x1 = x1
            overlay_y1 = y2 + 2  # Gap 2px
            overlay_x2 = x1 + trans_width + padding * 2
            overlay_y2 = overlay_y1 + trans_height
            
        elif strategy == OverlayStrategy.ABOVE:
            # Hiển thị bên trên
            overlay_x1 = x1
            overlay_y2 = y1 - 2
            overlay_y1 = overlay_y2 - trans_height
            overlay_x2 = x1 + trans_width + padding * 2
            
        elif strategy == OverlayStrategy.SIDE:
            # Hiển thị bên cạnh (phải)
            overlay_x1 = x2 + 5
            overlay_y1 = y1
            overlay_x2 = overlay_x1 + trans_width + padding * 2
            overlay_y2 = y1 + trans_height
        
        # Check bounds và adjust nếu ra ngoài screen
        overlay_x1, overlay_y1, overlay_x2, overlay_y2 = self._adjust_to_screen_bounds(
            overlay_x1, overlay_y1, overlay_x2, overlay_y2
        )
        
        # Chọn style dựa trên block type
        bg_color, text_color, alignment = self._get_style_for_block_type(block_type)
        
        return OverlayBox(
            original_bbox=original_bbox,
            screen_bbox=(overlay_x1, overlay_y1, overlay_x2, overlay_y2),
            translation=translation_text,
            original_text=original_text,
            block_type=block_type,
            font_size=font_size,
            alignment=alignment,
            background_color=bg_color,
            text_color=text_color
        )
    
    def _estimate_text_width(self, text: str, font_size: int) -> int:
        """
        Ước tính chiều rộng text (rough estimation)
        Có thể cải thiện bằng cách dùng font metrics thực tế
        """
        # Ước tính: mỗi ký tự ~ 0.6 * font_size
        # Tiếng Việt thường rộng hơn
        avg_char_width = font_size * 0.65
        return int(len(text) * avg_char_width)
    
    def _adjust_to_screen_bounds(
        self, 
        x1: int, y1: int, x2: int, y2: int
    ) -> Tuple[int, int, int, int]:
        """
        Điều chỉnh overlay nếu ra ngoài màn hình
        """
        width = x2 - x1
        height = y2 - y1
        
        # Check right edge
        if x2 > self.screen_width:
            x2 = self.screen_width - 5
            x1 = x2 - width
        
        # Check left edge
        if x1 < 0:
            x1 = 5
            x2 = x1 + width
        
        # Check bottom edge
        if y2 > self.screen_height:
            y2 = self.screen_height - 5
            y1 = y2 - height
        
        # Check top edge
        if y1 < 0:
            y1 = 5
            y2 = y1 + height
        
        return (x1, y1, x2, y2)
    
    def _get_style_for_block_type(
        self, 
        block_type: str
    ) -> Tuple[Tuple[int,int,int,int], Tuple[int,int,int], TextAlignment]:
        """
        Trả về style (bg_color, text_color, alignment) cho từng loại block
        """
        styles = {
            'paragraph': (
                (255, 255, 255, 230),  # White background, semi-transparent
                (0, 0, 0),             # Black text
                TextAlignment.LEFT
            ),
            'ui_button': (
                (70, 130, 180, 240),   # Steel blue, more opaque
                (255, 255, 255),       # White text
                TextAlignment.CENTER
            ),
            'menu_horizontal': (
                (50, 50, 50, 200),     # Dark gray
                (255, 255, 255),       # White text
                TextAlignment.CENTER
            ),
            'menu_vertical': (
                (50, 50, 50, 200),     # Dark gray
                (255, 255, 255),       # White text
                TextAlignment.LEFT
            ),
            'heading': (
                (255, 215, 0, 220),    # Gold
                (0, 0, 0),             # Black text
                TextAlignment.CENTER
            ),
            'list_item': (
                (240, 240, 240, 210),  # Light gray
                (0, 0, 0),             # Black text
                TextAlignment.LEFT
            ),
        }
        
        return styles.get(block_type, (
            (255, 255, 255, 200),  # Default white
            (0, 0, 0),
            TextAlignment.LEFT
        ))
    
    def create_overlay_boxes(
        self,
        classified_blocks: List,  # List[TextBlock] from classifier
        translations: dict,        # {original_text: translation}
        image_size: Tuple[int, int],
        strategy: OverlayStrategy = OverlayStrategy.REPLACE
    ) -> List[OverlayBox]:
        """
        Tạo tất cả overlay boxes cho toàn bộ classified blocks
        """
        overlay_boxes = []
        
        for block in classified_blocks:
            original_text = block.get_full_text()
            translation = translations.get(original_text, original_text)
            
            # Convert coordinates
            win_bbox = self.image_to_window_coords(
                block.bbox, 
                image_size
            )
            screen_bbox = self.window_to_screen_coords(win_bbox)
            
            # Create overlay box
            overlay = self.calculate_overlay_position(
                screen_bbox,
                translation,
                original_text,
                block.type.value,
                strategy
            )
            
            overlay_boxes.append(overlay)
        
        return overlay_boxes


# ============ WINDOWS-SPECIFIC UTILITIES ============

class WindowsWindowInfo:
    """
    Utility để lấy thông tin window trên Windows
    """
    
    @staticmethod
    def get_window_info(hwnd: int) -> WindowInfo:
        """
        Lấy thông tin chi tiết về window
        
        Args:
            hwnd: Window handle (có thể lấy từ win32gui.FindWindow)
        """
        if platform.system() != "Windows":
            raise NotImplementedError("Chỉ support Windows")
        
        try:
            import win32gui
            import win32api
        except ImportError:
            raise ImportError("Cần cài pywin32: pip install pywin32")
        
        # Get window rect
        rect = win32gui.GetWindowRect(hwnd)
        x, y, right, bottom = rect
        width = right - x
        height = bottom - y
        
        # Get client rect (exclude titlebar/borders)
        client_rect = win32gui.GetClientRect(hwnd)
        client_width = client_rect[2]
        client_height = client_rect[3]
        
        # Calculate titlebar and border
        border_width = (width - client_width) // 2
        titlebar_height = height - client_height - border_width
        
        # Get DPI
        try:
            dpi = win32api.GetDpiForWindow(hwnd)
            dpi_scale = dpi / 96.0
        except:
            dpi_scale = 1.0
        
        return WindowInfo(
            hwnd=hwnd,
            x=x,
            y=y,
            width=width,
            height=height,
            dpi_scale=dpi_scale,
            titlebar_height=max(0, titlebar_height),
            border_width=max(0, border_width)
        )


# ============ HELPER FUNCTIONS ============

def create_simple_overlay_box(
    text: str,
    bbox: Tuple[int, int, int, int],
    block_type: str = "paragraph",
    original_text: str = ""
) -> OverlayBox:
    """
    Helper function để tạo OverlayBox đơn giản
    
    Args:
        text: Translation text
        bbox: Screen coordinates (x1, y1, x2, y2)
        block_type: Type of block
        original_text: Original text (optional)
    
    Returns:
        OverlayBox ready to render
    """
    handler = OverlayPositionHandler()
    
    return handler.calculate_overlay_position(
        original_bbox=bbox,
        translation_text=text,
        original_text=original_text or text,
        block_type=block_type,
        strategy=OverlayStrategy.REPLACE
    )


# ============ DEMO USAGE ============

def demo_overlay_positioning():
    """
    Ví dụ sử dụng với window thực tế
    """
    
    # 1. Lấy thông tin window (giả sử)
    window_info = WindowInfo(
        hwnd=12345,
        x=100, y=100,
        width=1200, height=800,
        dpi_scale=1.5,  # 150% scaling
        titlebar_height=30,
        border_width=8
    )
    
    # 2. Khởi tạo handler
    handler = OverlayPositionHandler(window_info)
    
    # 3. Giả sử có OCR bbox từ image (800x600)
    ocr_bbox = (50, 100, 300, 130)  # x1, y1, x2, y2 trong image
    image_size = (800, 600)
    
    # 4. Convert sang window coordinates
    win_bbox = handler.image_to_window_coords(ocr_bbox, image_size)
    print(f"Window coords: {win_bbox}")
    
    # 5. Convert sang screen coordinates
    screen_bbox = handler.window_to_screen_coords(win_bbox)
    print(f"Screen coords: {screen_bbox}")
    
    # 6. Calculate overlay position
    overlay = handler.calculate_overlay_position(
        screen_bbox,
        translation_text="Xin chào",
        original_text="Hello",
        block_type="ui_button",
        strategy=OverlayStrategy.REPLACE
    )
    
    print(f"\nOverlay info:")
    print(f"  Position: {overlay.screen_bbox}")
    print(f"  Font size: {overlay.font_size}")
    print(f"  Background: {overlay.background_color}")
    print(f"  Text color: {overlay.text_color}")
    print(f"  Alignment: {overlay.alignment.value}")
    print(f"  Translation: {overlay.translation}")


if __name__ == "__main__":
    demo_overlay_positioning()
