"""Positioned Overlay - PyQt6 implementation for individual text box overlays"""

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer, QRectF, pyqtSignal, QObject
from PyQt6.QtGui import QPainter, QColor, QFont, QFontMetrics
from typing import List
import sys
import threading


class OverlaySignals(QObject):
    """Signals for thread-safe communication"""
    update_boxes = pyqtSignal(list)
    show_window = pyqtSignal()
    hide_window = pyqtSignal()
    clear_boxes = pyqtSignal()


class RegionOverlay(QWidget):
    """Overlay widget for entire region - draws background and all text boxes"""

    def __init__(self, region_boxes, device_pixel_ratio=1.0, parent=None):
        super().__init__(parent)
        self.region_boxes = region_boxes  # List of TranslatedTextBox for this region
        self.device_pixel_ratio = device_pixel_ratio
        self.setup_ui()

    def setup_ui(self):
        """Setup the region overlay"""
        if not self.region_boxes:
            return

        # Get region coordinates from first box (all boxes in same region)
        first_box = self.region_boxes[0]
        phys_x1, phys_y1, phys_x2, phys_y2 = first_box.region_coords

        print(f"[RegionOverlay] Physical coords: ({phys_x1}, {phys_y1}, {phys_x2}, {phys_y2})")
        print(f"[RegionOverlay] Device pixel ratio: {self.device_pixel_ratio}")

        # Convert physical to logical coordinates
        x1 = int(phys_x1 / self.device_pixel_ratio)
        y1 = int(phys_y1 / self.device_pixel_ratio)
        x2 = int(phys_x2 / self.device_pixel_ratio)
        y2 = int(phys_y2 / self.device_pixel_ratio)

        self.region_x = x1
        self.region_y = y1
        self.width = x2 - x1
        self.height = y2 - y1

        print(f"[RegionOverlay] Logical position: ({x1}, {y1}), size: {self.width}x{self.height}")

        # Window flags for overlay
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput  # Click-through
        )

        # Transparent background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Set geometry to cover entire region
        self.setGeometry(x1, y1, self.width, self.height)

    def paintEvent(self, _event):
        """Custom paint event - draw background for region, then combined text for all boxes"""
        print(f"[RegionOverlay] paintEvent called - drawing overlay at ({self.region_x}, {self.region_y}), size {self.width}x{self.height}")

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Step 1: Draw semi-transparent black background for entire region
        bg_rect = QRectF(0, 0, self.width, self.height)
        painter.fillRect(bg_rect, QColor(0, 0, 0, 204))  # 80% opacity black
        print(f"[RegionOverlay] Drew background rect")

        # Step 2: Combine all translated texts in the region into one string
        combined_text = "\n".join(tbox.translated_text for tbox in self.region_boxes)

        # Auto-scale font size to fit all text with readable minimum
        min_font_size = 10  # Minimum readable font size (increased from 6 to 10)
        max_font_size = 20  # Maximum font size

        # Available area for text (with padding)
        padding_ratio = 0.05
        available_width = int(self.width * (1 - 2 * padding_ratio))
        available_height = int(self.height * (1 - 2 * padding_ratio))

        # Try to find optimal font size that fits all text
        best_font_size = min_font_size
        for test_size in range(max_font_size, min_font_size - 1, -1):
            font = QFont('Arial', test_size, QFont.Weight.Bold)
            metrics = QFontMetrics(font)
            text_rect_needed = metrics.boundingRect(
                0, 0, available_width, 0,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                combined_text
            )

            # Check if text fits within available space
            if text_rect_needed.width() <= available_width and text_rect_needed.height() <= available_height:
                best_font_size = test_size
                break

        # Use the best font size found
        font_size = best_font_size
        font = QFont('Arial', font_size, QFont.Weight.Bold)
        painter.setFont(font)

        # If font is at minimum and text still doesn't fit, expand the overlay vertically
        metrics = QFontMetrics(font)
        text_rect_needed = metrics.boundingRect(
            0, 0, available_width, 0,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
            combined_text
        )

        # Calculate actual needed height
        needed_height = text_rect_needed.height() + int(self.height * 2 * padding_ratio)

        # If text needs more height and we're at minimum font size, expand overlay
        if font_size == min_font_size and needed_height > self.height:
            # Expand overlay height to fit all text
            self.setGeometry(self.region_x, self.region_y, self.width, needed_height)
            self.height = needed_height

        # Text rect for the entire region with padding
        padding_x = self.width * padding_ratio
        padding_y = self.height * padding_ratio
        text_rect = QRectF(padding_x, padding_y, self.width - 2 * padding_x, self.height - 2 * padding_y)

        # Draw text with slight outline for better visibility and word wrap
        # First draw black outline (shadow effect)
        painter.setPen(QColor(0, 0, 0, 180))
        for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            shadow_rect = text_rect.adjusted(dx, dy, dx, dy)
            painter.drawText(
                shadow_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                combined_text
            )

        # Then draw white text on top with word wrap
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
            combined_text
        )

        print(f"[RegionOverlay] Drew text: '{combined_text[:50]}...' at font size {font_size}")

        painter.end()


class PositionedOverlayQt(QWidget):
    """Manager for region overlays - creates one overlay per region"""

    def __init__(self):
        # Ensure QApplication exists
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
            # Suppress Qt warnings
            self.app.setQuitOnLastWindowClosed(False)
        else:
            self.app = QApplication.instance()

        super().__init__()

        self.region_widgets: List = []
        self.visible = True

        # Get device pixel ratio for DPI scaling correction
        screen = self.app.primaryScreen()
        self.device_pixel_ratio = screen.devicePixelRatio()
        # print(f"[Positioned Overlay Qt] Device Pixel Ratio: {self.device_pixel_ratio}")

        # Signals for thread-safe updates
        self.signals = OverlaySignals()
        self.signals.update_boxes.connect(self._update_boxes_slot)
        self.signals.show_window.connect(self._show_slot)
        self.signals.hide_window.connect(self._hide_slot)
        self.signals.clear_boxes.connect(self._clear_slot)

        # Hidden parent window (required for QLabel children)
        self.setWindowFlags(Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(1, 1)
        self.hide()

        # print("[Positioned Overlay Qt] Initialized - Individual text box mode")

    def update_text_boxes(self, translated_boxes: List):
        """
        Update overlay with translated text boxes (Thread-safe)

        Args:
            translated_boxes: List of TranslatedTextBox objects
        """
        # Use signal for thread-safe update
        self.signals.update_boxes.emit(translated_boxes)

    def _clear_widgets(self):
        """Clear all region widgets"""
        for widget in self.region_widgets:
            try:
                widget.hide()
                widget.deleteLater()
            except Exception:
                pass
        self.region_widgets.clear()

    def _update_boxes_slot(self, translated_boxes: List):
        """Slot to handle text box updates on main thread"""
        print(f"[Positioned Overlay Qt] _update_boxes_slot called with {len(translated_boxes)} boxes")

        # Clear existing widgets first to hide old overlays
        self._clear_widgets()

        # Group translated boxes by region
        regions = {}
        for tbox in translated_boxes:
            region_idx = tbox.region_idx
            if region_idx not in regions:
                regions[region_idx] = []
            regions[region_idx].append(tbox)

        print(f"[Positioned Overlay Qt] Creating {len(regions)} region overlays...")

        # Create one overlay widget per region
        for region_idx, boxes in regions.items():
            print(f"[Positioned Overlay Qt] Creating overlay for region {region_idx} with {len(boxes)} boxes")
            widget = RegionOverlay(boxes, device_pixel_ratio=self.device_pixel_ratio)
            widget.show()
            widget.raise_()
            widget.activateWindow()
            self.region_widgets.append(widget)
            pos = widget.pos()
            size = widget.size()
            print(f"[Positioned Overlay Qt] Widget shown: visible={widget.isVisible()}")
            print(f"[Positioned Overlay Qt]   Position: x={pos.x()}, y={pos.y()}")
            print(f"[Positioned Overlay Qt]   Size: {size.width()}x{size.height()}")
            print(f"[Positioned Overlay Qt]   WindowFlags: {widget.windowFlags()}")
            print(f"[Positioned Overlay Qt]   WindowState: {widget.windowState()}")

        print(f"[Positioned Overlay Qt] ✓ Created {len(regions)} region overlays")

    def show(self):
        """Show all text boxes (Thread-safe)"""
        self.signals.show_window.emit()

    def _show_slot(self):
        """Slot to show all region overlays on main thread"""
        self.visible = True
        for widget in self.region_widgets:
            widget.show()
            widget.raise_()
            widget.activateWindow()
        # print(f"[Positioned Overlay Qt] Showing {len(self.region_widgets)} region overlays")

    def hide(self):
        """Hide all region overlays (Thread-safe)"""
        self.signals.hide_window.emit()

    def _hide_slot(self):
        """Slot to hide all region overlays on main thread"""
        self.visible = False
        for widget in self.region_widgets:
            widget.hide()
        # print("[Positioned Overlay Qt] Hidden")

    def toggle_visibility(self):
        """Toggle overlay visibility"""
        if self.visible:
            self.hide()
        else:
            self.show()

    def clear(self):
        """Clear all text boxes (Thread-safe)"""
        self.signals.clear_boxes.emit()

    def _clear_slot(self):
        """Slot to clear text boxes on main thread"""
        self._clear_widgets()

    def set_subtitle_position(self, position: str):
        """
        Set subtitle position (deprecated - kept for compatibility)

        Args:
            position: "top", "center", or "bottom"
        """
        # print(f"[Positioned Overlay Qt] set_subtitle_position is deprecated in individual mode")


# Singleton instance
_overlay_instance = None


def get_positioned_overlay_qt():
    """Get or create the positioned overlay Qt instance (Singleton)"""
    global _overlay_instance

    if _overlay_instance is None:
        # Ensure QApplication exists
        if not QApplication.instance():
            QApplication(sys.argv)

        _overlay_instance = PositionedOverlayQt()
        # print("[Positioned Overlay Qt] Singleton instance created - Individual text box mode")

    return _overlay_instance


def run_qt_app():
    """Run Qt event loop (should be called on main thread)"""
    if QApplication.instance():
        QApplication.instance().exec()
