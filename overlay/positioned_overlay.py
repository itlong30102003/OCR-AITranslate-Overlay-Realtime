"""Positioned Overlay - Fullscreen transparent overlay with text at bbox positions"""

import tkinter as tk
from typing import List, Dict, Optional, Tuple
import threading


class PositionedOverlay:
    """Fullscreen transparent overlay that displays translated text at exact bbox positions"""

    def __init__(self):
        """Initialize the positioned overlay"""
        self.window: Optional[tk.Toplevel] = None
        self.canvas: Optional[tk.Canvas] = None
        self.visible = True
        self.text_items: List[int] = []  # Canvas item IDs
        self.bg_items: List[int] = []  # Background rectangle IDs

        # Visual settings
        self.font_size = 12
        self.font_family = "Arial"
        self.bg_opacity = 0.85
        self.show_bbox = True  # Show bounding box rectangles

        # Thread safety
        self.lock = threading.Lock()

        print("[Positioned Overlay] Initialized")

    def _get_confidence_color(self, confidence: float) -> str:
        """Get color based on translation confidence score"""
        if confidence >= 0.8:
            return "#00FF00"  # Green - High confidence
        elif confidence >= 0.5:
            return "#FFFF00"  # Yellow - Medium confidence
        else:
            return "#FF6600"  # Orange - Low confidence

    def _calculate_font_size(self, bbox: Tuple[int, int, int, int], text_length: int) -> int:
        """Calculate appropriate font size based on bbox dimensions"""
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1

        # Base font size on bbox height
        estimated_font_size = max(8, min(int(height * 0.6), 32))

        # Adjust for text length to prevent overflow
        if text_length > 0:
            max_width_based = max(8, int(width / text_length * 1.5))
            estimated_font_size = min(estimated_font_size, max_width_based)

        return estimated_font_size

    def _create_window(self):
        """Create the fullscreen transparent overlay window"""
        if self.window:
            return

        # Create toplevel window
        self.window = tk.Toplevel()
        self.window.title("Positioned Overlay")

        # Make it fullscreen
        self.window.attributes('-fullscreen', True)

        # Make it transparent and always on top
        self.window.attributes('-alpha', self.bg_opacity)
        self.window.attributes('-topmost', True)

        # Remove window decorations
        self.window.overrideredirect(True)

        # Create canvas with transparent background
        self.canvas = tk.Canvas(
            self.window,
            bg='black',
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Make black color transparent (click-through)
        self.window.attributes('-transparentcolor', 'black')

        # Bind hotkey for show/hide toggle
        self.window.bind('<F9>', lambda e: self.toggle_visibility())

        # Bind Escape to close
        self.window.bind('<Escape>', lambda e: self.hide())

        print("[Positioned Overlay] Window created (Press F9 to toggle, ESC to hide)")

    def show(self):
        """Show the overlay window"""
        if not self.window:
            self._create_window()

        # Always ensure window is visible and on top
        self.visible = True
        if self.window:
            self.window.deiconify()  # Make sure window is not withdrawn
            self.window.lift()  # Bring to front
            self.window.attributes('-topmost', True)  # Keep on top
            print("[Positioned Overlay] Shown")

    def hide(self):
        """Hide the overlay window"""
        if self.window:
            self.window.withdraw()
            self.visible = False
            print("[Positioned Overlay] Hidden")

    def toggle_visibility(self):
        """Toggle overlay visibility"""
        if self.visible:
            self.hide()
        else:
            self.show()

    def clear(self):
        """Clear all text from overlay"""
        with self.lock:
            if not self.canvas:
                return

            # Delete all canvas items
            for item_id in self.text_items + self.bg_items:
                self.canvas.delete(item_id)

            self.text_items.clear()
            self.bg_items.clear()

    def update_text_boxes(self, translated_boxes: List):
        """
        Update overlay with translated text boxes

        Args:
            translated_boxes: List of TranslatedTextBox objects
        """
        if not self.window:
            self._create_window()

        with self.lock:
            # Clear existing items
            self.clear()

            if not translated_boxes:
                return

            print(f"[Positioned Overlay] Rendering {len(translated_boxes)} text boxes...")

            # Render each text box
            for i, tbox in enumerate(translated_boxes):
                self._render_text_box(tbox)

            # Ensure window is visible (important!)
            self.show()

    def _render_text_box(self, tbox):
        """Render a single translated text box on canvas - COVERING original text"""
        if not self.canvas:
            return

        # Get absolute bbox coordinates
        x1, y1, x2, y2 = tbox.abs_bbox
        bbox_width = x2 - x1
        bbox_height = y2 - y1

        # Calculate appropriate font size to fit bbox height
        font_size = self._calculate_font_size(tbox.abs_bbox, len(tbox.translated_text))

        # Get color based on confidence
        text_color = self._get_confidence_color(tbox.confidence)

        # Step 1: Draw SOLID/OPAQUE rectangle to cover original text completely
        bg_rect = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill='#1E1E1E',  # Solid dark background (OPAQUE - covers original text)
            outline=text_color,
            width=1
        )
        self.bg_items.append(bg_rect)

        # Step 2: Draw translated text LEFT-ALIGNED at top-left of bbox
        # Add small padding from edges
        text_x = x1 + 4
        text_y = y1 + 4

        text_item = self.canvas.create_text(
            text_x,
            text_y,
            text=tbox.translated_text,
            font=(self.font_family, font_size, 'bold'),
            fill=text_color,
            anchor='nw',  # North-west (top-left) anchor
            justify='left',
            width=bbox_width - 8  # Wrap text if too long, with padding
        )
        self.text_items.append(text_item)

        try:
            print(f"  Rendered: {tbox.translated_text} at bbox ({x1}, {y1}, {x2}, {y2})")
        except UnicodeEncodeError:
            print(f"  Rendered text at bbox ({x1}, {y1}, {x2}, {y2})")

    def destroy(self):
        """Destroy the overlay window"""
        with self.lock:
            if self.window:
                self.window.destroy()
                self.window = None
                self.canvas = None
                print("[Positioned Overlay] Destroyed")

    def set_font_size(self, size: int):
        """Set font size for text"""
        self.font_size = max(8, min(size, 48))
        print(f"[Positioned Overlay] Font size set to {self.font_size}")

    def set_show_bbox(self, show: bool):
        """Toggle bbox rectangle visibility"""
        self.show_bbox = show
        print(f"[Positioned Overlay] Show bbox: {show}")

    def set_opacity(self, opacity: float):
        """Set overlay opacity (0.0 to 1.0)"""
        self.bg_opacity = max(0.0, min(opacity, 1.0))
        if self.window:
            self.window.attributes('-alpha', self.bg_opacity)
        print(f"[Positioned Overlay] Opacity set to {self.bg_opacity}")


# Thread-safe update wrapper
def update_positioned_overlay_safe(overlay: PositionedOverlay, translated_boxes: List):
    """Thread-safe wrapper for updating positioned overlay"""
    def update():
        overlay.update_text_boxes(translated_boxes)

    # Schedule on main thread
    if overlay.window:
        overlay.window.after(0, update)
