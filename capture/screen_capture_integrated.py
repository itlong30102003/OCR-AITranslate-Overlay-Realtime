"""Integrated Screen Capture - PyQt6 version without Tkinter windows"""

import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel
from PyQt6.QtCore import Qt, QTimer, QPoint, QRect, pyqtSignal, QObject
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QScreen
import threading
import time
from PIL import ImageGrab, Image
from typing import Callable, Tuple, List, Optional
from capture.screen_capture import MultiRegionMonitor


class RegionSelectionOverlay(QWidget):
    """Overlay widget for region selection using PyQt6"""

    region_selected = pyqtSignal(tuple)  # (x1, y1, x2, y2)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        # Get screen geometry
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        self.setGeometry(screen_geometry)

        self.start_pos = None
        self.current_pos = None
        self.selecting = False

        # Show overlay
        self.show()
        self.raise_()
        self.activateWindow()

    def paintEvent(self, event):
        """Paint the selection rectangle"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Semi-transparent black overlay
        painter.fillRect(self.rect(), QColor(0, 0, 0, 128))

        if self.selecting and self.start_pos and self.current_pos:
            # Clear the selection area
            selection_rect = QRect(self.start_pos, self.current_pos).normalized()
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(selection_rect, QColor(0, 0, 0, 0))

            # Draw selection border
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            pen = QPen(QColor(255, 0, 0), 2)
            painter.setPen(pen)
            painter.drawRect(selection_rect)

    def mousePressEvent(self, event):
        """Start selection"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.pos()
            self.current_pos = event.pos()
            self.selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        """Update selection rectangle"""
        if self.selecting:
            self.current_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        """Finish selection"""
        if event.button() == Qt.MouseButton.LeftButton and self.selecting:
            self.selecting = False

            if self.start_pos and self.current_pos:
                # Convert to screen coordinates
                screen_pos = self.mapToGlobal(QPoint(0, 0))
                x1 = min(self.start_pos.x(), self.current_pos.x()) + screen_pos.x()
                y1 = min(self.start_pos.y(), self.current_pos.y()) + screen_pos.y()
                x2 = max(self.start_pos.x(), self.current_pos.x()) + screen_pos.x()
                y2 = max(self.start_pos.y(), self.current_pos.y()) + screen_pos.y()

                self.region_selected.emit((x1, y1, x2, y2))

            self.close()


class IntegratedScreenCapture(QObject):
    """Integrated screen capture using PyQt6 instead of Tkinter"""

    # Signal emitted when snapshot monitoring is complete
    snapshot_completed = pyqtSignal()

    def __init__(self, on_region_selected: Callable[[Tuple[int, int, int, int]], None] = None,
                 on_region_change: Callable[[int, Image.Image, int], None] = None,
                 on_scan: Callable[[int], None] = None):
        super().__init__()
        self.on_region_selected = on_region_selected
        self.on_region_change = on_region_change
        self.on_scan = on_scan

        self.monitor: Optional[MultiRegionMonitor] = None
        self.overlay: Optional[RegionSelectionOverlay] = None

    def start_region_selection(self):
        """Start region selection process"""
        self.overlay = RegionSelectionOverlay()
        self.overlay.region_selected.connect(self._on_region_selected)

    def _on_region_selected(self, coords: Tuple[int, int, int, int]):
        """Handle region selection completion"""
        # Close the overlay
        if self.overlay:
            self.overlay.close()
            self.overlay = None

        if self.on_region_selected:
            self.on_region_selected(coords)

    def start_monitoring(self, regions: List[Tuple[int, int, int, int]], scan_mode: str = "realtime"):
        """Start monitoring the selected regions"""
        if not regions:
            return

        # Get logical screen size for DPI scaling
        screen = QApplication.primaryScreen()
        logical_size = screen.geometry()
        logical_screen_size = (logical_size.width(), logical_size.height())

        self.monitor = MultiRegionMonitor(
            regions=regions,
            fps=15,
            on_region_change=self._on_region_change,
            on_scan=self._on_scan,
            logical_screen_size=logical_screen_size,
            sensitivity=0.6,
            scan_mode=scan_mode
        )

        # Store completion callback for snapshot mode
        if scan_mode == "snapshot":
            self.monitor.set_completion_callback(self._on_snapshot_complete)

        self.monitor.start()

    def _on_snapshot_complete(self):
        """Called when snapshot monitoring is complete"""
        print("[IntegratedScreenCapture] Snapshot monitoring complete")
        # Emit signal to notify completion
        if hasattr(self, 'snapshot_completed'):
            self.snapshot_completed.emit()

    def stop_monitoring(self):
        """Stop monitoring"""
        if self.monitor:
            self.monitor.stop(join=False)  # Don't join to avoid blocking
            self.monitor = None

    def _on_region_change(self, idx: int, img: Image.Image, scan_counter: int, coords: tuple = None):
        """Forward region change to callback"""
        if self.on_region_change:
            self.on_region_change(idx, img, scan_counter, coords)

    def _on_scan(self, scan_counter: int):
        """Forward scan update to callback"""
        if self.on_scan:
            self.on_scan(scan_counter)
