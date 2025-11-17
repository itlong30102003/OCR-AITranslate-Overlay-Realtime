"""Monitor Tab - Integrated region monitoring UI"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGridLayout, QFrame, QScrollArea,
                             QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt6.QtGui import QPixmap, QImage
from PIL import Image
import threading
from typing import List, Tuple, Optional
from capture.screen_capture_integrated import IntegratedScreenCapture


class RegionThumbnail(QFrame):
    """Widget hiển thị thumbnail cho một region"""

    def __init__(self, region_idx: int, coords: Tuple[int, int, int, int]):
        super().__init__()
        self.region_idx = region_idx
        self.coords = coords
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(2)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Region title
        title = QLabel(f"Vùng {region_idx + 1}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-weight: bold; color: #ffffff;")
        layout.addWidget(title)

        # Thumbnail label
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(200, 150)
        self.thumbnail_label.setStyleSheet("border: 1px solid #374151; background-color: #1f2937;")
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.thumbnail_label)

        # Status label
        self.status_label = QLabel("Chờ...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #9ca3af; font-size: 12px;")
        layout.addWidget(self.status_label)

        # Set background
        self.setStyleSheet("""
            RegionThumbnail {
                background-color: #252a3a;
                border: 2px solid #374151;
                border-radius: 5px;
            }
        """)

    def update_thumbnail(self, pil_image: Image.Image):
        """Cập nhật thumbnail từ PIL Image"""
        # IMPORTANT: Create a COPY to avoid modifying the original image
        pil_image = pil_image.copy()

        # Convert PIL to QPixmap
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')

        # Resize to fit (now modifying the copy, not original)
        pil_image.thumbnail((200, 150), Image.BILINEAR)

        # Convert to QImage
        img_data = pil_image.tobytes('raw', 'RGB')
        qimage = QImage(img_data, pil_image.width, pil_image.height, QImage.Format.Format_RGB888)

        # Convert to QPixmap
        pixmap = QPixmap.fromImage(qimage)

        self.thumbnail_label.setPixmap(pixmap.scaled(200, 150, Qt.AspectRatioMode.KeepAspectRatio))
        self.status_label.setText("Đang giám sát")
        self.status_label.setStyleSheet("color: #10b981; font-size: 12px;")


class MonitorTab(QWidget):
    """Tab Giám sát - Tích hợp region monitoring vào main UI"""

    def __init__(self, app_instance):
        super().__init__()
        self.app = app_instance
        self.integrated_capture = None
        self.regions: List[Tuple[int, int, int, int]] = []
        self.region_widgets: List[RegionThumbnail] = []
        self.scan_counter = 0

        self.init_ui()

    def init_ui(self):
        """Khởi tạo UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header = QLabel("Giám sát vùng màn hình")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        layout.addWidget(header)

        # Control buttons
        controls_layout = QHBoxLayout()

        self.select_region_btn = QPushButton("📦 Chọn vùng")
        self.select_region_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.select_region_btn.clicked.connect(self.select_region)
        controls_layout.addWidget(self.select_region_btn)

        self.start_monitor_btn = QPushButton("▶️ Bắt đầu giám sát")
        self.start_monitor_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:disabled {
                background-color: #374151;
                color: #6b7280;
            }
        """)
        self.start_monitor_btn.clicked.connect(self.start_monitoring)
        self.start_monitor_btn.setEnabled(False)
        controls_layout.addWidget(self.start_monitor_btn)

        self.stop_monitor_btn = QPushButton("⏹️ Dừng giám sát")
        self.stop_monitor_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
            QPushButton:disabled {
                background-color: #374151;
                color: #6b7280;
            }
        """)
        self.stop_monitor_btn.clicked.connect(self.stop_monitoring)
        self.stop_monitor_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_monitor_btn)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Status bar
        status_layout = QHBoxLayout()

        self.status_label = QLabel("Trạng thái: Chưa bắt đầu")
        self.status_label.setStyleSheet("color: #9ca3af; font-size: 14px;")
        status_layout.addWidget(self.status_label)

        self.scan_label = QLabel("Scan: 0")
        self.scan_label.setStyleSheet("color: #9ca3af; font-size: 14px;")
        status_layout.addWidget(self.scan_label)

        status_layout.addStretch()
        layout.addLayout(status_layout)

        # Regions display area
        self.regions_scroll = QScrollArea()
        self.regions_scroll.setWidgetResizable(True)
        self.regions_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #374151;
                border-radius: 5px;
                background-color: #1f2937;
            }
        """)

        self.regions_container = QWidget()
        self.regions_layout = QGridLayout(self.regions_container)
        self.regions_layout.setContentsMargins(10, 10, 10, 10)
        self.regions_layout.setSpacing(10)

        self.regions_scroll.setWidget(self.regions_container)
        layout.addWidget(self.regions_scroll)

        # Progress bar for selection
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #374151;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #10b981;
            }
        """)
        layout.addWidget(self.progress_bar)

    def select_region(self):
        """Chọn vùng màn hình"""
        try:
            self.integrated_capture = IntegratedScreenCapture(
                on_region_selected=self.on_region_selected,
                on_region_change=self.on_region_change,
                on_scan=self.on_scan_update
            )
            self.integrated_capture.start_region_selection()
            self.status_label.setText("Trạng thái: Đang chọn vùng...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể bắt đầu chọn vùng: {e}")

    def on_region_selected(self, coords: Tuple[int, int, int, int]):
        """Callback khi chọn xong một vùng"""
        self.regions.append(coords)
        self.add_region_widget(len(self.regions) - 1, coords)
        self.start_monitor_btn.setEnabled(True)
        self.status_label.setText(f"Trạng thái: Đã chọn {len(self.regions)} vùng")
        self.progress_bar.setVisible(False)

        # Hỏi có muốn chọn thêm vùng không (vẫn ẩn UI)
        reply = QMessageBox.question(
            self,
            "Tiếp tục?",
            "Bạn có muốn chọn vùng tiếp theo không?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.select_region()
        else:
            self.status_label.setText(f"Trạng thái: Sẵn sàng giám sát {len(self.regions)} vùng")
            # Auto start monitoring for snapshot mode
            overlay_mode = self.app.overlay_service.get_overlay_mode()
            if overlay_mode == "positioned":
                self.start_monitoring()

    def add_region_widget(self, idx: int, coords: Tuple[int, int, int, int]):
        """Thêm widget hiển thị cho region mới"""
        widget = RegionThumbnail(idx, coords)
        self.region_widgets.append(widget)

        # Calculate grid position
        row = idx // 3
        col = idx % 3

        self.regions_layout.addWidget(widget, row, col)

    def start_monitoring(self):
        """Bắt đầu giám sát các vùng đã chọn"""
        if not self.regions:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn ít nhất một vùng trước khi bắt đầu giám sát.")
            return

        try:
            # Verify async processing service is running
            if not self.app.async_service.is_running():
                print("[MonitorTab] WARNING: Async service not running, starting now...")
                self.app.async_service.start()
                # Give more time for event loop to be ready
                import time
                time.sleep(0.5)
            else:
                print("[MonitorTab] Async service already running - OK")

            # Set scan mode based on overlay mode
            overlay_mode = self.app.overlay_service.get_overlay_mode()
            scan_mode = "realtime" if overlay_mode == "list" else "snapshot"

            # Hide main window completely to avoid capturing it during monitoring
            self.window().hide()

            self.integrated_capture.start_monitoring(self.regions, scan_mode=scan_mode)

            # Connect signal for snapshot completion
            if scan_mode == "snapshot":
                self.integrated_capture.snapshot_completed.connect(self._restore_window_after_snapshot)
                # Clear completion callback after connecting signal
                if self.integrated_capture.monitor:
                    self.integrated_capture.monitor.clear_completion_callback()

            # Update UI state
            self.start_monitor_btn.setEnabled(False)
            self.stop_monitor_btn.setEnabled(True)
            self.select_region_btn.setEnabled(False)
            self.status_label.setText(f"Trạng thái: Đang giám sát ({scan_mode} mode)")

            # Update floating control state
            if hasattr(self.window(), 'floating_control'):
                self.window().floating_control.set_monitoring_state(True)

            # For snapshot mode, wait for translations to complete before restoring window
            if scan_mode == "snapshot":
                QTimer.singleShot(3000, self._restore_window_after_snapshot)  # Wait 3 seconds for translations

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể bắt đầu giám sát: {e}")
            # Restore window if error
            self.window().showNormal()

    def _restore_window_after_snapshot(self):
        """Restore window after snapshot capture and translations are complete"""
        try:
            # Restore main window
            main_window = self.window()
            if main_window and not main_window.isVisible():
                main_window.showNormal()
                main_window.raise_()
                main_window.activateWindow()
                print("[MonitorTab] Window restored after snapshot completion")

            # Update floating control state
            if hasattr(main_window, 'floating_control'):
                main_window.floating_control.set_monitoring_state(False)

            # Auto stop async service after translations are complete
            if self.app.async_service.is_running():
                print("[MonitorTab] Auto-stopping async service after translations complete")
                self.app.async_service.stop()

        except Exception as e:
            print(f"[MonitorTab] Error restoring window: {e}")

    def stop_monitoring(self):
        """Dừng giám sát - xóa tất cả vùng đang giám sát"""
        try:
            if self.integrated_capture:
                self.integrated_capture.stop_monitoring()

            # Clear all regions
            self.regions.clear()

            # Remove all region widgets
            for widget in self.region_widgets:
                self.regions_layout.removeWidget(widget)
                widget.deleteLater()
            self.region_widgets.clear()

            # Restore main window
            self.window().showNormal()
            self.window().raise_()
            self.window().activateWindow()

            # Update floating control state
            if hasattr(self.window(), 'floating_control'):
                self.window().floating_control.set_monitoring_state(False)

            # Reset UI state
            self.start_monitor_btn.setEnabled(False)
            self.stop_monitor_btn.setEnabled(False)
            self.select_region_btn.setEnabled(True)
            self.status_label.setText("Trạng thái: Đã dừng giám sát - tất cả vùng đã xóa")
            self.scan_label.setText("Scan: 0")
            self.scan_counter = 0

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi khi dừng giám sát: {e}")
            # Restore window even if error
            self.window().showNormal()

    def on_region_change(self, idx: int, img: Image.Image, scan_counter: int, region_coords: tuple = None):
        """Callback khi region thay đổi"""
        print(f"[MonitorTab] on_region_change: region={idx}, scan={scan_counter}")

        if 0 <= idx < len(self.region_widgets):
            self.region_widgets[idx].update_thumbnail(img)

        # Forward to app for processing
        self.app.on_region_change(idx, img, scan_counter, region_coords)

    def on_scan_update(self, scan_counter: int):
        """Cập nhật số lần scan"""
        self.scan_counter = scan_counter
        self.scan_label.setText(f"Scan: {scan_counter}")
