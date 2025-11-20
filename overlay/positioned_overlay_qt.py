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
        self.position_timer = QTimer(self)
        self.position_timer.timeout.connect(self.update_position)
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

        # Start position tracking timer (60 FPS)
        self.position_timer.start(1000 // 60)  # ~16.67ms

    def update_position(self):
        """Update overlay position to track window movement"""
        if not self.region_boxes:
            return

        # Get current region coordinates from first box
        first_box = self.region_boxes[0]
        phys_x1, phys_y1, phys_x2, phys_y2 = first_box.region_coords

        # Convert to logical coordinates
        x1 = int(phys_x1 / self.device_pixel_ratio)
        y1 = int(phys_y1 / self.device_pixel_ratio)
        x2 = int(phys_x2 / self.device_pixel_ratio)
        y2 = int(phys_y2 / self.device_pixel_ratio)

        # Update position if changed
        if x1 != self.region_x or y1 != self.region_y:
            self.region_x = x1
            self.region_y = y1
            self.setGeometry(x1, y1, self.width, self.height)
            # Trigger repaint to update text positions
            self.update()

    def paintEvent(self, _event):
        """Custom paint event - draw individual text boxes with their own backgrounds (subtitle style)"""
        print(f"[RegionOverlay] paintEvent called - drawing {len(self.region_boxes)} text boxes")

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw each text box individually with its own background
        for tbox in self.region_boxes:
            # Get absolute bbox
            abs_x1, abs_y1, abs_x2, abs_y2 = tbox.abs_bbox

            # Convert to logical coordinates
            x1 = int(abs_x1 / self.device_pixel_ratio)
            y1 = int(abs_y1 / self.device_pixel_ratio)
            x2 = int(abs_x2 / self.device_pixel_ratio)
            y2 = int(abs_y2 / self.device_pixel_ratio)

            # Convert to local coordinates (relative to overlay window)
            local_x1 = x1 - self.region_x
            local_y1 = y1 - self.region_y
            local_x2 = x2 - self.region_x
            local_y2 = y2 - self.region_y

            box_width = local_x2 - local_x1
            box_height = local_y2 - local_y1

            # Set font size (smaller, fixed)
            font_size = 12  # Fixed small font size
            font = QFont('Arial', font_size, QFont.Weight.Bold)
            painter.setFont(font)

            # Get text metrics
            metrics = QFontMetrics(font)
            text = tbox.translated_text

            # Calculate text bounding box with padding
            text_width = metrics.horizontalAdvance(text)
            text_height = metrics.height()

            # Padding around text
            padding_x = 6
            padding_y = 3

            # Background rect (fit to text, not full bbox)
            bg_width = text_width + 2 * padding_x
            bg_height = text_height + 2 * padding_y

            # Center background on original bbox
            bg_x = local_x1 + (box_width - bg_width) / 2
            bg_y = local_y1 + (box_height - bg_height) / 2

            # Draw semi-transparent black background (only around text)
            bg_rect = QRectF(bg_x, bg_y, bg_width, bg_height)
            painter.fillRect(bg_rect, QColor(0, 0, 0, 180))  # 70% opacity

            # Text position (centered in background)
            text_x = bg_x + padding_x
            text_y = bg_y + padding_y + metrics.ascent()

            # Draw text with shadow for better readability
            # Shadow
            painter.setPen(QColor(0, 0, 0, 255))
            painter.drawText(int(text_x + 1), int(text_y + 1), text)

            # Main text (white)
            painter.setPen(QColor(255, 255, 255, 255))
            painter.drawText(int(text_x), int(text_y), text)

        print(f"[RegionOverlay] Drew {len(self.region_boxes)} text boxes")
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
        """Slot to handle text box updates on main thread - OPTIMIZED to avoid recreating all widgets"""
        # Group translated boxes by region
        regions = {}
        for tbox in translated_boxes:
            region_idx = tbox.region_idx
            if region_idx not in regions:
                regions[region_idx] = []
            regions[region_idx].append(tbox)

        # SMART UPDATE: Only recreate changed regions
        # Build mapping of existing widgets by region
        existing_regions = {}
        for widget in self.region_widgets:
            if hasattr(widget, 'text_boxes') and len(widget.text_boxes) > 0:
                region_idx = widget.text_boxes[0].region_idx
                existing_regions[region_idx] = widget

        # Remove widgets for regions that no longer exist
        widgets_to_keep = []
        for region_idx, widget in existing_regions.items():
            if region_idx not in regions:
                widget.hide()
                widget.deleteLater()
            else:
                widgets_to_keep.append(widget)

        self.region_widgets = widgets_to_keep

        # Update or create widgets for each region
        for region_idx, boxes in regions.items():
            if region_idx in existing_regions:
                # Region exists - just update its boxes
                widget = existing_regions[region_idx]
                widget.text_boxes = boxes
                widget.update()  # Trigger repaint
            else:
                # New region - create widget
                widget = RegionOverlay(boxes, device_pixel_ratio=self.device_pixel_ratio)
                widget.show()
                widget.raise_()
                widget.activateWindow()
                self.region_widgets.append(widget)

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
