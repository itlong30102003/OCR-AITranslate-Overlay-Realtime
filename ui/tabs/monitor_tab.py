"""Monitor Tab - Simplified window monitoring UI"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGridLayout, QFrame, QScrollArea,
                             QMessageBox, QComboBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPen, QColor
from PIL import Image
import threading
import time
from typing import List, Tuple, Optional
from capture.window_capture import WindowRegionMonitor, WindowCapture


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
        self.status_label = QLabel("Đang giám sát")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #10b981; font-size: 12px;")
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
        pil_image = pil_image.copy()
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        pil_image.thumbnail((200, 150), Image.BILINEAR)
        img_data = pil_image.tobytes('raw', 'RGB')
        qimage = QImage(img_data, pil_image.width, pil_image.height, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)
        self.thumbnail_label.setPixmap(pixmap.scaled(200, 150, Qt.AspectRatioMode.KeepAspectRatio))


class MonitorTab(QWidget):
    """Tab Giám sát - Simplified workflow"""

    def __init__(self, app_instance):
        super().__init__()
        self.app = app_instance

        # Window capture variables
        self.selected_hwnd = None
        self.selected_window_title = None

        # Region monitoring - support multiple regions
        self.region_monitors: List[WindowRegionMonitor] = []
        self.regions: List[Tuple[int, int, int, int]] = []
        self.region_widgets: List[RegionThumbnail] = []
        self.scan_counter = 0

        # Monitoring state
        self.is_monitoring = False
        self.monitoring_thread = None

        self.init_ui()

    def init_ui(self):
        """Khởi tạo UI đơn giản"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header = QLabel("Giám sát cửa sổ")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        layout.addWidget(header)

        # Window selection with buttons
        window_select_layout = QHBoxLayout()

        window_select_label = QLabel("Bước 1: Chọn cửa sổ")
        window_select_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold;")
        window_select_layout.addWidget(window_select_label)

        self.window_combo = QComboBox()
        self.window_combo.setStyleSheet("""
            QComboBox {
                background-color: #1f2937;
                color: #ffffff;
                border: 1px solid #374151;
                border-radius: 5px;
                padding: 8px;
                min-width: 400px;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #ffffff;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #1f2937;
                color: #ffffff;
                border: 1px solid #374151;
                selection-background-color: #3b82f6;
            }
        """)
        # Remove auto-update on combo change
        window_select_layout.addWidget(self.window_combo)

        self.refresh_windows_btn = QPushButton("🔄")
        self.refresh_windows_btn.setStyleSheet("""
            QPushButton {
                background-color: #374151;
                color: white;
                font-size: 14px;
                padding: 8px 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        self.refresh_windows_btn.setToolTip("Làm mới danh sách cửa sổ")
        self.refresh_windows_btn.clicked.connect(self.refresh_window_list)
        window_select_layout.addWidget(self.refresh_windows_btn)

        # Continue button (confirm window selection)
        self.continue_btn = QPushButton("▶️ Tiếp tục")
        self.continue_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 20px;
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
        self.continue_btn.clicked.connect(self.confirm_window_selection)
        self.continue_btn.setEnabled(False)
        window_select_layout.addWidget(self.continue_btn)

        # Add region button (only visible during monitoring)
        self.add_region_btn = QPushButton("➕ Chọn vùng mới")
        self.add_region_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:disabled {
                background-color: #374151;
                color: #6b7280;
            }
        """)
        self.add_region_btn.clicked.connect(self.add_new_region)
        self.add_region_btn.setVisible(False)  # Hidden initially
        window_select_layout.addWidget(self.add_region_btn)

        window_select_layout.addStretch()
        layout.addLayout(window_select_layout)

        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Trạng thái: Chọn cửa sổ để bắt đầu")
        self.status_label.setStyleSheet("color: #9ca3af; font-size: 14px;")
        status_layout.addWidget(self.status_label)

        self.scan_label = QLabel("Scan: 0")
        self.scan_label.setStyleSheet("color: #9ca3af; font-size: 14px;")
        status_layout.addWidget(self.scan_label)

        status_layout.addStretch()
        layout.addLayout(status_layout)

        # Instruction label
        self.instruction_label = QLabel("📍 Bước 2: Sau khi chọn cửa sổ, click 'Tiếp tục' để xem preview và chọn vùng")
        self.instruction_label.setStyleSheet("""
            color: #60a5fa;
            font-size: 13px;
            padding: 10px;
            background-color: #1e3a5f;
            border-radius: 5px;
            border: 1px solid #3b82f6;
        """)
        self.instruction_label.setWordWrap(True)
        layout.addWidget(self.instruction_label)

        # Window preview area (with scroll)
        self.preview_section = QWidget()
        preview_section_layout = QVBoxLayout(self.preview_section)
        preview_section_layout.setContentsMargins(0, 0, 0, 0)

        preview_label = QLabel("Xem trước cửa sổ:")
        preview_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold;")
        preview_section_layout.addWidget(preview_label)

        preview_scroll = QScrollArea()
        preview_scroll.setWidgetResizable(False)
        preview_scroll.setMinimumHeight(350)
        preview_scroll.setMaximumHeight(550)
        preview_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        preview_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        preview_scroll.setStyleSheet("""
            QScrollArea {
                border: 2px solid #374151;
                border-radius: 5px;
                background-color: #1f2937;
            }
        """)

        self.window_preview = QLabel()
        self.window_preview.setStyleSheet("""
            QLabel {
                background-color: #1f2937;
                min-height: 300px;
            }
        """)
        self.window_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.window_preview.setText("Chọn cửa sổ để xem preview")
        self.window_preview.setScaledContents(False)
        self.window_preview.mousePressEvent = self.on_preview_mouse_press
        self.window_preview.mouseMoveEvent = self.on_preview_mouse_move
        self.window_preview.mouseReleaseEvent = self.on_preview_mouse_release

        preview_scroll.setWidget(self.window_preview)
        preview_section_layout.addWidget(preview_scroll)

        # Hide preview section initially
        self.preview_section.setVisible(False)
        layout.addWidget(self.preview_section)

        # Selection tracking
        self.selection_start = None
        self.selection_current = None
        self.preview_pixmap = None
        self.preview_scale = 1.0
        self.original_window_image = None

        # Regions display area (thumbnails of monitored regions)
        regions_title = QLabel("Các vùng đang giám sát:")
        regions_title.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(regions_title)

        self.regions_scroll = QScrollArea()
        self.regions_scroll.setWidgetResizable(True)
        self.regions_scroll.setMaximumHeight(200)
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

        layout.addStretch()

        # Connect combo box to enable continue button
        self.window_combo.currentIndexChanged.connect(self.on_window_combo_changed)

        # Auto-refresh window list on load
        QTimer.singleShot(100, self.refresh_window_list)

    def refresh_window_list(self):
        """Tự động refresh danh sách cửa sổ"""
        try:
            self.window_combo.clear()
            windows = WindowCapture.list_all_windows()

            if not windows:
                self.window_combo.addItem("Không tìm thấy cửa sổ nào")
                return

            for hwnd, title in windows:
                display_title = title[:60] + "..." if len(title) > 60 else title
                self.window_combo.addItem(f"{display_title}", (hwnd, title))

            print(f"[MonitorTab] Refreshed window list: {len(windows)} windows found")

        except Exception as e:
            print(f"[MonitorTab] Error refreshing window list: {e}")

    def on_window_combo_changed(self, index: int):
        """Enable continue button when window is selected"""
        try:
            if index < 0:
                self.continue_btn.setEnabled(False)
                return

            data = self.window_combo.itemData(index)
            if not data:
                self.continue_btn.setEnabled(False)
                return

            # Enable continue button
            self.continue_btn.setEnabled(True)
            hwnd, window_title = data
            self.status_label.setText(f"Đã chọn: {window_title[:50]}... - Click 'Tiếp tục' để xem preview")

        except Exception as e:
            print(f"[MonitorTab] Error handling window selection: {e}")

    def confirm_window_selection(self):
        """User clicked 'Tiếp tục' - capture and show preview"""
        try:
            index = self.window_combo.currentIndex()
            if index < 0:
                return

            data = self.window_combo.itemData(index)
            if not data:
                return

            hwnd, window_title = data

            # Store selected window
            self.selected_hwnd = hwnd
            self.selected_window_title = window_title

            # Reset region selection for new window
            self.selection_start = None
            self.selection_current = None

            print(f"[MonitorTab] Confirmed window: {window_title} (HWND: {hwnd})")

            # Update instruction
            self.instruction_label.setText("📍 Bước 3: Click và kéo trên preview để chọn vùng")
            self.instruction_label.setStyleSheet("""
                color: #10b981;
                font-size: 13px;
                padding: 10px;
                background-color: #064e3b;
                border-radius: 5px;
                border: 1px solid #10b981;
            """)

            # Show preview section and capture
            self.preview_section.setVisible(True)
            self.update_window_preview()

            # Disable continue button, enable only after selecting window again
            self.continue_btn.setEnabled(False)

        except Exception as e:
            print(f"[MonitorTab] Error confirming window selection: {e}")

    def update_window_preview(self):
        """Capture và hiển thị window preview"""
        try:
            if not self.selected_hwnd:
                return

            print(f"[MonitorTab] Capturing window preview for hwnd: {self.selected_hwnd}")

            window_capture = WindowCapture(hwnd=self.selected_hwnd)
            pil_image = window_capture.capture_window()

            if not pil_image:
                self.window_preview.setText("Không thể capture cửa sổ\n(Window có thể đang bị minimize)")
                self.window_preview.setStyleSheet("""
                    QLabel {
                        border: 2px solid #ef4444;
                        border-radius: 5px;
                        background-color: #1f2937;
                        min-height: 300px;
                        color: #ef4444;
                    }
                """)
                return

            # Store original image
            self.original_window_image = pil_image.copy()

            # Convert to RGB
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Scale to fit preview area
            max_width = 800
            max_height = 500
            img_width, img_height = pil_image.size

            self.preview_scale = min(max_width / img_width, max_height / img_height, 1.0)
            display_width = int(img_width * self.preview_scale)
            display_height = int(img_height * self.preview_scale)

            # Resize for display
            pil_image = pil_image.resize((display_width, display_height), Image.Resampling.LANCZOS)

            # Convert to QPixmap
            img_data = pil_image.tobytes('raw', 'RGB')
            qimage = QImage(img_data, pil_image.width, pil_image.height, QImage.Format.Format_RGB888)
            self.preview_pixmap = QPixmap.fromImage(qimage)

            # Display preview
            self.window_preview.setText("")
            self.window_preview.setStyleSheet("""
                QLabel {
                    border: 2px solid #10b981;
                    border-radius: 5px;
                    background-color: #1f2937;
                }
            """)
            self.window_preview.setPixmap(self.preview_pixmap)
            self.window_preview.setFixedSize(display_width, display_height)

            print(f"[MonitorTab] Preview updated successfully: {img_width}x{img_height} -> {display_width}x{display_height}")

        except Exception as e:
            print(f"[MonitorTab] Error updating preview: {e}")
            import traceback
            traceback.print_exc()

    def on_preview_mouse_press(self, event):
        """Bắt đầu chọn vùng"""
        if not self.preview_pixmap:
            return

        self.selection_start = event.pos()
        self.selection_current = event.pos()

    def on_preview_mouse_move(self, event):
        """Cập nhật vùng chọn"""
        if not self.selection_start:
            return

        self.selection_current = event.pos()
        self.draw_selection_rectangle()

    def on_preview_mouse_release(self, event):
        """Hoàn tất chọn vùng - tự động hỏi có chọn thêm không"""
        if not self.selection_start:
            return

        self.selection_current = event.pos()

        # Calculate region bbox
        x1 = int(min(self.selection_start.x(), self.selection_current.x()) / self.preview_scale)
        y1 = int(min(self.selection_start.y(), self.selection_current.y()) / self.preview_scale)
        x2 = int(max(self.selection_start.x(), self.selection_current.x()) / self.preview_scale)
        y2 = int(max(self.selection_start.y(), self.selection_current.y()) / self.preview_scale)

        width = x2 - x1
        height = y2 - y1

        # Validate size
        if width < 10 or height < 10:
            QMessageBox.warning(self, "Cảnh báo", "Vùng chọn quá nhỏ. Vui lòng chọn lại.")
            self.selection_start = None
            self.selection_current = None
            if self.preview_pixmap:
                self.window_preview.setPixmap(self.preview_pixmap)
            return

        region_bbox = (x1, y1, width, height)
        print(f"[MonitorTab] Region selected: {region_bbox}")

        # Draw final selection
        self.draw_selection_rectangle()

        # Add region and create monitor
        self.add_region(region_bbox)

        # Ask if user wants to add more regions
        reply = QMessageBox.question(
            self,
            "Chọn thêm vùng?",
            f"✓ Đã chọn vùng {len(self.regions)} ({width}x{height})\n\n"
            "Bạn có muốn chọn thêm vùng nữa không?\n\n"
            "• Chọn 'Yes' để tiếp tục chọn vùng\n"
            "• Chọn 'No' để bắt đầu giám sát ngay",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Reset selection, allow selecting more regions
            self.selection_start = None
            self.selection_current = None
            # Restore clean preview
            self.window_preview.setPixmap(self.preview_pixmap)
            self.status_label.setText(f"Đã chọn {len(self.regions)} vùng - Chọn thêm vùng nữa")
        else:
            # Auto-start monitoring
            self.start_monitoring()

    def add_region(self, region_bbox: Tuple[int, int, int, int]):
        """Thêm region mới vào danh sách"""
        try:
            # Create monitor for this region
            monitor = WindowRegionMonitor(
                hwnd=self.selected_hwnd,
                region_bbox=region_bbox
            )
            self.region_monitors.append(monitor)
            self.regions.append(region_bbox)

            # Add widget
            idx = len(self.region_widgets)
            widget = RegionThumbnail(idx, region_bbox)
            self.region_widgets.append(widget)

            # Add to grid
            row = idx // 3
            col = idx % 3
            self.regions_layout.addWidget(widget, row, col)

            print(f"[MonitorTab] Added region {idx + 1}: {region_bbox}")

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể thêm vùng: {e}")
            print(f"[MonitorTab] Error adding region: {e}")

    def add_new_region(self):
        """Thêm vùng mới trong khi đang monitoring"""
        self.instruction_label.setText("📍 Click và kéo trên preview để chọn vùng mới")
        self.instruction_label.setStyleSheet("""
            color: #fbbf24;
            font-size: 13px;
            padding: 10px;
            background-color: #451a03;
            border-radius: 5px;
            border: 1px solid #f59e0b;
        """)
        # Update preview to show current window
        self.update_window_preview()

    def draw_selection_rectangle(self):
        """Vẽ khung chọn trên preview"""
        if not self.preview_pixmap or not self.selection_start or not self.selection_current:
            return

        pixmap = self.preview_pixmap.copy()
        painter = QPainter(pixmap)
        pen = QPen(QColor(255, 0, 0), 2)
        painter.setPen(pen)

        x1 = min(self.selection_start.x(), self.selection_current.x())
        y1 = min(self.selection_start.y(), self.selection_current.y())
        x2 = max(self.selection_start.x(), self.selection_current.x())
        y2 = max(self.selection_start.y(), self.selection_current.y())

        painter.drawRect(x1, y1, x2 - x1, y2 - y1)
        painter.end()

        self.window_preview.setPixmap(pixmap)

    def start_monitoring(self):
        """Tự động bắt đầu giám sát tất cả các vùng"""
        if not self.region_monitors:
            QMessageBox.warning(self, "Cảnh báo", "Chưa có vùng nào được chọn.")
            return

        try:
            # Start async service if not running
            if not self.app.async_service.is_running():
                print("[MonitorTab] Starting async service...")
                self.app.async_service.start()
                time.sleep(0.3)

            # Update UI state
            self.is_monitoring = True
            self.add_region_btn.setVisible(True)
            self.status_label.setText(f"Đang giám sát {len(self.regions)} vùng")
            self.instruction_label.setText(f"✓ Đang giám sát {len(self.regions)} vùng - Click 'Chọn vùng mới' để thêm vùng")
            self.instruction_label.setStyleSheet("""
                color: #10b981;
                font-size: 13px;
                padding: 10px;
                background-color: #064e3b;
                border-radius: 5px;
                border: 1px solid #10b981;
            """)

            # Hide main window
            self.window().hide()

            # Update floating control
            if hasattr(self.window(), 'floating_control') and self.window().floating_control:
                self.window().floating_control.set_monitoring_state(True)

            # Start monitoring loop
            self._start_monitoring_loop()

            print(f"[MonitorTab] Monitoring started for {len(self.regions)} regions")

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể bắt đầu giám sát: {e}")
            self.window().showNormal()

    def _start_monitoring_loop(self):
        """Monitoring loop cho tất cả các vùng"""
        def monitoring_thread():
            fps = 15
            frame_interval = 1.0 / fps
            scan_counter = 0

            while self.is_monitoring and self.region_monitors:
                start_time = time.time()

                try:
                    # Monitor all regions
                    for idx, monitor in enumerate(self.region_monitors):
                        has_changed, image = monitor.check_and_capture()

                        if has_changed and image:
                            scan_counter += 1
                            abs_bbox = monitor.get_absolute_bbox()

                            if abs_bbox:
                                # Convert abs_bbox (x, y, w, h) to region_coords (x1, y1, x2, y2)
                                abs_x, abs_y, abs_w, abs_h = abs_bbox
                                region_coords = (abs_x, abs_y, abs_x + abs_w, abs_y + abs_h)

                                # Send to processing
                                self.app.on_region_change(idx, image, scan_counter, region_coords)

                            # Update scan counter (thread-safe)
                            self.scan_counter = scan_counter
                            try:
                                from PyQt6.QtCore import QMetaObject
                                QMetaObject.invokeMethod(
                                    self.scan_label,
                                    "setText",
                                    Qt.ConnectionType.QueuedConnection,
                                    f"Scan: {scan_counter}"
                                )
                            except Exception as ui_error:
                                print(f"[MonitorTab] UI update error: {ui_error}")

                    # Maintain FPS
                    elapsed = time.time() - start_time
                    to_sleep = frame_interval - elapsed
                    if to_sleep > 0:
                        time.sleep(to_sleep)

                except Exception as e:
                    print(f"[MonitorTab] Error in monitoring loop: {e}")
                    break

            print("[MonitorTab] Monitoring loop ended")

        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=monitoring_thread, daemon=True)
        self.monitoring_thread.start()

    def stop_monitoring(self):
        """Dừng giám sát (được gọi từ floating control hoặc user)"""
        try:
            self.is_monitoring = False

            # Clear monitors
            self.region_monitors.clear()
            self.regions.clear()

            # Clear widgets
            for widget in self.region_widgets:
                self.regions_layout.removeWidget(widget)
                widget.deleteLater()
            self.region_widgets.clear()

            # Clear overlay
            self.app.overlay_service.clear_positioned_overlay()

            # Restore window
            self.window().showNormal()
            self.window().raise_()
            self.window().activateWindow()

            # Update UI
            self.add_region_btn.setVisible(False)
            self.status_label.setText("Đã dừng giám sát")
            self.instruction_label.setText("📍 Hướng dẫn: Chọn cửa sổ → Click và kéo để chọn vùng → Overlay tự động bắt đầu")
            self.instruction_label.setStyleSheet("""
                color: #60a5fa;
                font-size: 13px;
                padding: 10px;
                background-color: #1e3a5f;
                border-radius: 5px;
                border: 1px solid #3b82f6;
            """)
            self.scan_label.setText("Scan: 0")
            self.scan_counter = 0

            # Update floating control
            if hasattr(self.window(), 'floating_control') and self.window().floating_control:
                self.window().floating_control.set_monitoring_state(False)

            print("[MonitorTab] Monitoring stopped")

        except Exception as e:
            print(f"[MonitorTab] Error stopping monitoring: {e}")
            self.window().showNormal()
