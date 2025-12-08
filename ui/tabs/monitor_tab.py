"""Monitor Tab - Simplified window monitoring UI"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGridLayout, QFrame, QScrollArea,
                             QMessageBox, QComboBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPen, QColor
from PIL import Image
import threading
import time
from typing import List, Tuple, Optional, Dict
from capture.window_capture import WindowRegionMonitor, WindowCapture


class RegionThumbnail(QFrame):
    """Widget hiển thị thumbnail cho một region với nút stop"""

    from PyQt6.QtCore import pyqtSignal
    stop_requested = pyqtSignal(int)  # Emit region_id when stop is clicked

    def __init__(self, region_id: int, coords: Tuple[int, int, int, int]):
        super().__init__()
        self.region_id = region_id  # Use region_id instead of region_idx
        self.coords = coords
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(2)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title layout with stop button
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)

        # Region title
        title = QLabel(f"Vùng {region_id + 1}")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        title.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 14px; padding: 5px;")
        title_layout.addWidget(title)

        # Spacer
        title_layout.addStretch()

        # Stop button
        stop_btn = QPushButton("✕")
        stop_btn.setFixedSize(24, 24)
        stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border-radius: 12px;
                font-weight: bold;
                font-size: 16px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
            QPushButton:pressed {
                background-color: #b91c1c;
            }
        """)
        stop_btn.setToolTip("Dừng theo dõi vùng này")
        stop_btn.clicked.connect(lambda: self.stop_requested.emit(self.region_id))
        title_layout.addWidget(stop_btn)

        layout.addLayout(title_layout)

        # Thumbnail label
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(300, 225)
        self.thumbnail_label.setStyleSheet("border: 1px solid #374151; background-color: #1f2937;")
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.thumbnail_label)

        # Status label
        self.status_label = QLabel("Đang giám sát")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #10b981; font-size: 13px; padding: 3px;")
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
        try:
            pil_image = pil_image.copy()
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Resize maintaining aspect ratio
            pil_image.thumbnail((300, 225), Image.LANCZOS)

            # Get actual size after thumbnail
            width, height = pil_image.size

            # Convert to QImage with correct stride
            img_data = pil_image.tobytes('raw', 'RGB')
            bytes_per_line = width * 3  # RGB = 3 bytes per pixel
            qimage = QImage(img_data, width, height, bytes_per_line, QImage.Format.Format_RGB888)

            # Make a deep copy to ensure data persists
            qimage = qimage.copy()

            pixmap = QPixmap.fromImage(qimage)
            self.thumbnail_label.setPixmap(pixmap)
        except Exception as e:
            print(f"[RegionThumbnail] Error updating thumbnail: {e}")


class MonitorTab(QWidget):
    """Tab Giám sát - Simplified workflow"""

    # Define signals for thread-safe UI updates
    from PyQt6.QtCore import pyqtSignal
    scan_counter_updated = pyqtSignal(int)

    def __init__(self, app_instance):
        super().__init__()
        self.app = app_instance

        # Window capture variables
        self.selected_hwnd = None
        self.selected_window_title = None

        # Region monitoring - support multiple regions with stable IDs
        self.region_id_counter = 0  # Counter for generating unique region IDs
        self.region_monitors: Dict[int, WindowRegionMonitor] = {}  # {region_id: monitor}
        self.regions: Dict[int, Tuple[int, int, int, int]] = {}  # {region_id: bbox}
        self.region_widgets: Dict[int, RegionThumbnail] = {}  # {region_id: widget}
        self.scan_counter = 0

        # Store latest captured images for thumbnail updates
        self.latest_region_images: Dict[int, Optional[Image.Image]] = {}  # {region_id: image}

        # Monitoring state
        self.is_monitoring = False
        self.monitoring_thread = None

        # Thumbnail update timer (runs in main thread)
        self.thumbnail_update_timer = QTimer()
        self.thumbnail_update_timer.timeout.connect(self._update_thumbnails)
        self.thumbnail_update_timer.setInterval(50)  # Update every 50ms for smoother display

        self.init_ui()
    
    def _on_source_language_changed(self, lang_name: str):
        """Handle source language change"""
        from config.language_config import LanguageConfig
        lang_code = LanguageConfig.get_language_code(lang_name)
        
        # Update OCR service
        if hasattr(self.app, 'ocr_service') and self.app.ocr_service:
            self.app.ocr_service.set_source_language(lang_code)
        
        print(f"[MonitorTab] Source language changed to: {lang_name} ({lang_code})")
    
    def _on_target_language_changed(self, lang_name: str):
        """Handle target language change"""
        from config.language_config import LanguageConfig
        lang_code = LanguageConfig.get_language_code(lang_name)
        trans_code = LanguageConfig.get_translation_code(lang_code)
        
        # Update translation service (if exists)
        if hasattr(self.app, 'translation_service') and self.app.translation_service:
            self.app.translation_service.target_lang = trans_code
            print(f"[MonitorTab] Translation target: {lang_name} ({lang_code} → {trans_code})")
        
        print(f"[MonitorTab] Target language changed to: {lang_name} ({lang_code})")

    def init_ui(self):
        """Khởi tạo UI đơn giản"""
        # Set background gradient
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0f172a,
                    stop:1 #1e293b
                );
            }
        """)
        
        # Main layout for the tab (contains scroll area)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create scroll area for all content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        # Create container widget for scrollable content
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
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
        self.refresh_windows_btn.setObjectName("refresh_btn")
        self.refresh_windows_btn.setFixedSize(40, 40)  # Kích thước cố định
        self.refresh_windows_btn.setStyleSheet("""
            QPushButton#refresh_btn {
                background-color: #374151;
                color: #FFFFFF;
                font-size: 22px;
                border-radius: 5px;
                padding: 2px;
            }
            QPushButton#refresh_btn:hover {
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
        regions_title.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold; margin-top: 15px; margin-bottom: 5px;")
        layout.addWidget(regions_title)

        self.regions_scroll = QScrollArea()
        self.regions_scroll.setWidgetResizable(True)
        self.regions_scroll.setMinimumHeight(350)
        self.regions_scroll.setMaximumHeight(550)
        self.regions_scroll.setStyleSheet("""
            QScrollArea {
                border: 2px solid #374151;
                border-radius: 5px;
                background-color: #1f2937;
            }
        """)

        self.regions_container = QWidget()
        self.regions_layout = QGridLayout(self.regions_container)
        self.regions_layout.setContentsMargins(15, 15, 15, 15)
        self.regions_layout.setSpacing(15)

        self.regions_scroll.setWidget(self.regions_container)
        layout.addWidget(self.regions_scroll)

        layout.addStretch()

        # Set scroll content and add to main layout
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # Connect combo box to enable continue button
        self.window_combo.currentIndexChanged.connect(self.on_window_combo_changed)

        # Connect signals for thread-safe UI updates
        self.scan_counter_updated.connect(self._update_scan_label)

        # Auto-refresh window list on load
        QTimer.singleShot(100, self.refresh_window_list)

    def _update_scan_label(self, counter: int):
        """Update scan label (called from main thread via signal)"""
        self.scan_label.setText(f"Scan: {counter}")

    def refresh_window_list(self):
        """Tự động refresh danh sách cửa sổ"""
        try:
            self.window_combo.clear()
            windows = WindowCapture.list_all_windows()

            if not windows:
                self.window_combo.addItem("Không tìm thấy cửa sổ nào")
                return

            # Filter out system windows and common invisible windows
            filtered_windows = []
            ignore_keywords = [
                "Program Manager",
                "Windows Input Experience",
                "Microsoft Text Input Application",
                "Settings",
                "MSCTFIME UI",
                "Default IME",
                "OleMainThreadWndName"
            ]

            for hwnd, title in windows:
                # Skip empty or very short titles
                if not title or len(title) < 2:
                    continue

                # Skip windows with ignore keywords
                if any(keyword.lower() in title.lower() for keyword in ignore_keywords):
                    continue

                # Skip our own application
                if "OCR" in title and "Translate" in title:
                    continue

                filtered_windows.append((hwnd, title))

            if not filtered_windows:
                self.window_combo.addItem("Không tìm thấy cửa sổ phù hợp")
                return

            for hwnd, title in filtered_windows:
                display_title = title[:60] + "..." if len(title) > 60 else title
                self.window_combo.addItem(f"{display_title}", (hwnd, title))

            print(f"[MonitorTab] Refreshed window list: {len(filtered_windows)}/{len(windows)} windows")

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

            # Try to restore window if minimized
            import win32gui
            import win32con
            import time

            # Get window info for debugging
            window_text = win32gui.GetWindowText(self.selected_hwnd)
            print(f"[MonitorTab] Target window: {window_text}")

            # Check if window is minimized
            placement = win32gui.GetWindowPlacement(self.selected_hwnd)
            if placement[1] == win32con.SW_SHOWMINIMIZED:
                print("[MonitorTab] Window is minimized, attempting to restore...")
                # Restore window but don't activate/focus it
                win32gui.ShowWindow(self.selected_hwnd, win32con.SW_RESTORE)
                time.sleep(0.3)  # Wait for restore

            # Make sure window is visible
            if not win32gui.IsWindowVisible(self.selected_hwnd):
                print("[MonitorTab] Window is not visible, showing it...")
                win32gui.ShowWindow(self.selected_hwnd, win32con.SW_SHOW)
                time.sleep(0.3)

            # IMPORTANT: Hide our app window temporarily to avoid capturing it in the screenshot
            print("[MonitorTab] Hiding app window to avoid capture interference...")
            main_window = self.window()
            was_visible = main_window.isVisible()
            if was_visible:
                main_window.hide()
                time.sleep(0.2)  # Wait for window to disappear

            try:
                # Capture window (will try all methods with automatic fallback)
                window_capture = WindowCapture(hwnd=self.selected_hwnd)
                pil_image = window_capture.capture_window()
            finally:
                # Always restore app window visibility
                if was_visible:
                    main_window.show()
                    main_window.raise_()
                    print("[MonitorTab] App window restored")

            if not pil_image:
                # ALL capture methods failed - show detailed error
                try:
                    rect = win32gui.GetWindowRect(self.selected_hwnd)
                    client_rect = win32gui.GetClientRect(self.selected_hwnd)
                    window_text = win32gui.GetWindowText(self.selected_hwnd)
                    is_visible = win32gui.IsWindowVisible(self.selected_hwnd)

                    error_msg = f"❌ Không thể capture: {window_text}\n\n"
                    error_msg += f"🔍 Thông tin window:\n"
                    error_msg += f"• Visible: {is_visible}\n"
                    error_msg += f"• Window size: {rect[2]-rect[0]}x{rect[3]-rect[1]}\n"
                    error_msg += f"• Client size: {client_rect[2]}x{client_rect[3]}\n\n"
                    error_msg += "🚫 Đã thử 4 phương thức capture:\n"
                    error_msg += "• Client Area (BitBlt) - Failed\n"
                    error_msg += "• Full Window (GetWindowDC) - Failed\n"
                    error_msg += "• PrintWindow API - Failed\n"
                    error_msg += "• Screenshot & Crop - Failed\n\n"
                    error_msg += "💡 Window này có thể:\n"
                    error_msg += "• Bị hidden hoàn toàn (không visible trên màn hình)\n"
                    error_msg += "• Có size = 0 (minimized or off-screen)\n"
                    error_msg += "• Được bảo vệ đặc biệt\n\n"
                    error_msg += "Hãy thử:\n"
                    error_msg += "1. Maximize window đó\n"
                    error_msg += "2. Đưa window lên foreground\n"
                    error_msg += "3. Click nút 'Làm mới' và chọn lại"
                except Exception as e:
                    error_msg = f"❌ Lỗi nghiêm trọng\n\nKhông thể capture window.\nLỗi: {str(e)}"

                self.window_preview.setText(error_msg)
                self.window_preview.setStyleSheet("""
                    QLabel {
                        border: 2px solid #ef4444;
                        border-radius: 5px;
                        background-color: #1f2937;
                        min-height: 300px;
                        color: #ef4444;
                        font-size: 10px;
                        padding: 20px;
                    }
                """)
                print(f"[MonitorTab] All capture methods failed!")
                print(f"[MonitorTab] {error_msg}")

                # Re-enable continue button to allow retry
                self.continue_btn.setEnabled(True)
                self.continue_btn.setText("🔄 Thử lại")
                return

            # Store original image
            self.original_window_image = pil_image.copy()

            # DEBUG: Save original image to verify capture works
            try:
                import os
                debug_path = os.path.join(os.getcwd(), "debug_capture.png")
                pil_image.save(debug_path)
                print(f"[MonitorTab] DEBUG: Saved captured image to {debug_path}")
            except Exception as save_err:
                print(f"[MonitorTab] DEBUG: Could not save debug image: {save_err}")

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

            # Convert to QPixmap with correct stride
            img_data = pil_image.tobytes('raw', 'RGB')
            bytes_per_line = pil_image.width * 3  # RGB = 3 bytes per pixel
            qimage = QImage(img_data, pil_image.width, pil_image.height, bytes_per_line, QImage.Format.Format_RGB888)

            # Check if QImage is valid
            if qimage.isNull():
                print("[MonitorTab] ERROR: QImage is null!")
                return

            # Make a deep copy to ensure data persists
            qimage = qimage.copy()

            self.preview_pixmap = QPixmap.fromImage(qimage)

            # Check if QPixmap is valid
            if self.preview_pixmap.isNull():
                print("[MonitorTab] ERROR: QPixmap is null!")
                return

            print(f"[MonitorTab] QImage created: {qimage.width()}x{qimage.height()}, format: {qimage.format()}")
            print(f"[MonitorTab] QPixmap created: {self.preview_pixmap.width()}x{self.preview_pixmap.height()}")

            # Display preview
            self.window_preview.setText("")
            self.window_preview.setStyleSheet("""
                QLabel {
                    border: 2px solid #10b981;
                    border-radius: 5px;
                    background-color: #1f2937;
                }
            """)

            # Set pixmap and size
            print(f"[MonitorTab] Setting pixmap to QLabel...")
            self.window_preview.setPixmap(self.preview_pixmap)
            print(f"[MonitorTab] Pixmap set. Has pixmap: {not self.window_preview.pixmap().isNull()}")

            self.window_preview.setMinimumSize(display_width, display_height)
            self.window_preview.setMaximumSize(display_width, display_height)
            self.window_preview.resize(display_width, display_height)

            # Force update geometry
            self.window_preview.updateGeometry()
            self.window_preview.update()

            # Make sure it's visible
            self.window_preview.setVisible(True)
            self.window_preview.show()

            print(f"[MonitorTab] QLabel visible: {self.window_preview.isVisible()}")
            print(f"[MonitorTab] QLabel size: {self.window_preview.size()}")
            print(f"[MonitorTab] QLabel geometry: {self.window_preview.geometry()}")
            print(f"[MonitorTab] Preview section visible: {self.preview_section.isVisible()}")

            # Reset continue button text (in case it was "Thử lại")
            self.continue_btn.setText("▶️ Tiếp tục")

            print(f"[MonitorTab] ✅ Preview updated successfully: {img_width}x{img_height} -> {display_width}x{display_height}")

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

        # Reset selection for next region
        self.selection_start = None
        self.selection_current = None

        # Ask if user wants to add more regions
        if not self.is_monitoring:
            reply = QMessageBox.question(
                self,
                "Chọn vùng",
                f"Đã chọn {len(self.regions)} vùng.\n\nBạn có muốn chọn thêm vùng khác không?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Show preview again for selecting another region
                self.instruction_label.setText(f"📍 Click và kéo trên preview để chọn vùng {len(self.regions) + 1}")
                self.instruction_label.setStyleSheet("""
                    color: #fbbf24;
                    font-size: 13px;
                    padding: 10px;
                    background-color: #451a03;
                    border-radius: 5px;
                    border: 1px solid #f59e0b;
                """)
            else:
                # User done selecting, start monitoring
                self.start_monitoring()
        else:
            print(f"[MonitorTab] Added region while monitoring - total regions: {len(self.region_monitors)}")

    def add_region(self, region_bbox: Tuple[int, int, int, int]):
        """Thêm region mới vào danh sách với unique ID (thread-safe)"""
        try:
            # Generate unique region ID
            region_id = self.region_id_counter
            self.region_id_counter += 1

            print(f"[MonitorTab] Adding region ID={region_id} (Display: Vùng {len(self.region_widgets) + 1})...")
            print(f"  - HWND: {self.selected_hwnd}")
            print(f"  - Bbox: {region_bbox}")
            print(f"  - Current monitors: {len(self.region_monitors)}")
            print(f"  - Is monitoring: {self.is_monitoring}")

            # Create monitor for this region
            monitor = WindowRegionMonitor(
                hwnd=self.selected_hwnd,
                region_bbox=region_bbox
            )
            self.region_monitors[region_id] = monitor
            self.regions[region_id] = region_bbox

            # Add widget with region_id
            widget = RegionThumbnail(region_id, region_bbox)
            # Connect stop signal
            widget.stop_requested.connect(self.stop_region)
            self.region_widgets[region_id] = widget

            # Add placeholder for latest image
            self.latest_region_images[region_id] = None

            # Add to grid
            grid_position = len(self.region_widgets) - 1
            row = grid_position // 3
            col = grid_position % 3
            self.regions_layout.addWidget(widget, row, col)

            print(f"[MonitorTab] ✓ Added region ID={region_id}: {region_bbox}")
            print(f"  - Total regions: {len(self.regions)}")
            print(f"  - Total monitors: {len(self.region_monitors)}")
            print(f"  - Total widgets: {len(self.region_widgets)}")
            print(f"  - Total image placeholders: {len(self.latest_region_images)}")

            # Update status label if monitoring
            if self.is_monitoring:
                self.status_label.setText(f"Đang giám sát {len(self.regions)} vùng")
                self.instruction_label.setText(f"✓ Đang giám sát {len(self.regions)} vùng - Click 'Chọn vùng mới' để thêm vùng")

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[MonitorTab] ❌ ERROR adding region:")
            print(error_trace)
            QMessageBox.critical(self, "Lỗi", f"Không thể thêm vùng: {e}\n\nXem console để biết chi tiết.")

    def add_new_region(self):
        """Thêm vùng mới trong khi đang monitoring"""
        print("[MonitorTab] Add new region button clicked - showing preview...")

        # Show preview section (was hidden during monitoring)
        self.preview_section.setVisible(True)

        # Update instruction
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

        print("[MonitorTab] Preview section shown for region selection")

    def stop_region(self, region_id: int):
        """
        Stop monitoring a specific region (called when stop button clicked)

        Args:
            region_id: Region ID to stop
        """
        print(f"\n[MonitorTab] ========== STOP REGION ID={region_id} ==========")

        try:
            # 1. Remove monitor
            if region_id in self.region_monitors:
                del self.region_monitors[region_id]
                print(f"[MonitorTab] Removed monitor for region {region_id}")
            else:
                print(f"[MonitorTab] Warning: Region {region_id} monitor not found")

            # 2. Remove region bbox
            if region_id in self.regions:
                del self.regions[region_id]
                print(f"[MonitorTab] Removed region {region_id} bbox")

            # 3. Remove latest image
            if region_id in self.latest_region_images:
                del self.latest_region_images[region_id]
                print(f"[MonitorTab] Removed region {region_id} image")

            # 4. Clear overlay for this region
            self.app.overlay_service.clear_region_overlay(region_id)

            # 5. Remove widget from UI
            if region_id in self.region_widgets:
                widget = self.region_widgets[region_id]
                self.regions_layout.removeWidget(widget)
                widget.deleteLater()
                del self.region_widgets[region_id]
                print(f"[MonitorTab] Removed region {region_id} widget")

            # 6. Re-layout remaining widgets in grid
            self._relayout_widgets()

            # 7. Update status
            remaining = len(self.region_monitors)
            self.status_label.setText(f"Đang giám sát {remaining} vùng")
            self.instruction_label.setText(f"✓ Đang giám sát {remaining} vùng - Click 'Chọn vùng mới' để thêm vùng")

            print(f"[MonitorTab] Region {region_id} stopped. Remaining: {remaining}")

            # 8. Stop all monitoring if no regions left
            if remaining == 0:
                print("[MonitorTab] No regions left, stopping monitoring...")
                self.stop_monitoring()
            else:
                print(f"[MonitorTab] ✓ Successfully stopped region {region_id}")
                print(f"[MonitorTab] ==========================================\n")

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[MonitorTab] ❌ ERROR stopping region {region_id}:")
            print(error_trace)
            QMessageBox.critical(self, "Lỗi", f"Không thể dừng vùng {region_id}: {e}\n\nXem console để biết chi tiết.")

    def _relayout_widgets(self):
        """Re-arrange widgets in grid after removal"""
        try:
            # Remove all widgets from layout
            for widget in self.region_widgets.values():
                self.regions_layout.removeWidget(widget)

            # Re-add in grid (3 columns)
            for i, widget in enumerate(self.region_widgets.values()):
                row = i // 3
                col = i % 3
                self.regions_layout.addWidget(widget, row, col)

            print(f"[MonitorTab] Re-laid out {len(self.region_widgets)} widgets")

        except Exception as e:
            print(f"[MonitorTab] Error re-laying out widgets: {e}")

    def _update_thumbnails(self):
        """Update thumbnails from main thread (called by QTimer)"""
        try:
            # Iterate Dict by region_id
            for region_id, image in self.latest_region_images.items():
                if image and region_id in self.region_widgets:
                    self.region_widgets[region_id].update_thumbnail(image)
        except Exception as e:
            print(f"[MonitorTab] Error in _update_thumbnails: {e}")

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
        print(f"\n[MonitorTab] ========== START MONITORING ==========")
        print(f"[MonitorTab] Region monitors: {len(self.region_monitors)}")
        print(f"[MonitorTab] Regions: {len(self.regions)}")
        print(f"[MonitorTab] Widgets: {len(self.region_widgets)}")

        if not self.region_monitors:
            QMessageBox.warning(self, "Cảnh báo", "Chưa có vùng nào được chọn.")
            return

        try:
            # Start async service if not running
            print("[MonitorTab] Checking async service...")
            if not self.app.async_service.is_running():
                print("[MonitorTab] Async service not running, starting...")
                self.app.async_service.start()
                time.sleep(0.3)
            else:
                print("[MonitorTab] Async service already running")

            # Update UI state
            print("[MonitorTab] Updating UI state...")
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

            # Start thumbnail update timer (main thread)
            print("[MonitorTab] Starting thumbnail update timer...")
            self.thumbnail_update_timer.start()

            # Start monitoring loop
            print("[MonitorTab] Starting monitoring loop...")
            self._start_monitoring_loop()

            # Wait a bit to ensure monitoring thread started
            time.sleep(0.5)

            # Hide preview section (no longer needed)
            print("[MonitorTab] Hiding preview section...")
            self.preview_section.setVisible(False)

            # Hide main window AFTER everything is set up
            print("[MonitorTab] Hiding main window...")
            self.window().hide()

            print(f"[MonitorTab] ✓ Monitoring started successfully for {len(self.regions)} regions")
            print(f"[MonitorTab] ==========================================\n")

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[MonitorTab] ❌ ERROR starting monitoring:")
            print(error_trace)
            QMessageBox.critical(self, "Lỗi", f"Không thể bắt đầu giám sát: {e}\n\nXem console để biết chi tiết.")
            self.is_monitoring = False
            self.window().showNormal()

    def _start_monitoring_loop(self):
        """Monitoring loop cho tất cả các vùng"""
        def monitoring_thread():
            fps = 25  # Increased from 15 to 25 for smoother monitoring
            frame_interval = 1.0 / fps
            scan_counter = 0

            print(f"\n[MonitoringThread] ========== THREAD STARTED ==========")
            print(f"[MonitoringThread] Monitoring {len(self.region_monitors)} regions at {fps} FPS")
            print(f"[MonitoringThread] Frame interval: {frame_interval:.3f}s")
            print(f"[MonitoringThread] is_monitoring flag: {self.is_monitoring}")

            loop_count = 0
            while self.is_monitoring:
                loop_count += 1
                start_time = time.time()

                try:
                    # Create snapshot of monitors to avoid race conditions when adding/removing regions
                    monitors_snapshot = dict(self.region_monitors)  # Dict copy, not list!

                    if not monitors_snapshot:
                        print(f"[MonitoringThread] No monitors found, waiting...")
                        time.sleep(frame_interval)
                        continue

                    # Debug: Print loop info every 50 frames (~2 seconds at 25 fps)
                    if loop_count % 50 == 1:
                        print(f"[MonitoringThread] Loop #{loop_count}, monitoring {len(monitors_snapshot)} regions...")

                    # Monitor all regions (iterate Dict by region_id)
                    for region_id, monitor in monitors_snapshot.items():
                        # Always capture current frame for thumbnail display
                        current_image = monitor.capture_current()
                        if current_image and region_id in self.latest_region_images:
                            # Store latest image for thumbnail update (thread-safe dict write)
                            self.latest_region_images[region_id] = current_image.copy()

                        # Check for changes
                        has_changed, changed_image = monitor.check_and_capture()

                        # Only process when changed
                        if has_changed and changed_image:
                            scan_counter += 1
                            abs_bbox = monitor.get_absolute_bbox()

                            print(f"\n[MonitoringThread] 🔥 Region ID={region_id} CHANGED! Scan: {scan_counter}")

                            if abs_bbox:
                                # Convert abs_bbox (x, y, w, h) to region_coords (x1, y1, x2, y2)
                                abs_x, abs_y, abs_w, abs_h = abs_bbox
                                region_coords = (abs_x, abs_y, abs_x + abs_w, abs_y + abs_h)

                                print(f"[MonitoringThread] Sending to OCR processing...")
                                print(f"  - Region ID: {region_id}")
                                print(f"  - Image size: {changed_image.size}")
                                print(f"  - Region coords: {region_coords}")

                                # Send to processing (using region_id instead of idx)
                                self.app.on_region_change(region_id, changed_image, scan_counter, region_coords)

                            # Update scan counter (thread-safe via signal)
                            self.scan_counter = scan_counter
                            self.scan_counter_updated.emit(scan_counter)

                    # Maintain FPS
                    elapsed = time.time() - start_time
                    to_sleep = frame_interval - elapsed
                    if to_sleep > 0:
                        time.sleep(to_sleep)

                except Exception as e:
                    import traceback
                    error_trace = traceback.format_exc()
                    print(f"\n[MonitoringThread] ❌ ERROR in monitoring loop:")
                    print(error_trace)
                    break

            print(f"\n[MonitoringThread] ========== THREAD ENDED ==========")
            print(f"[MonitoringThread] Total loops executed: {loop_count}")
            print(f"[MonitoringThread] Total scans: {scan_counter}\n")

        # Start monitoring thread
        print("[MonitorTab] Creating monitoring thread...")
        self.monitoring_thread = threading.Thread(target=monitoring_thread, daemon=True)
        self.monitoring_thread.start()
        print("[MonitorTab] Monitoring thread started!")

    def stop_monitoring(self):
        """Dừng giám sát (được gọi từ floating control hoặc user)"""
        try:
            self.is_monitoring = False

            # Stop thumbnail update timer
            self.thumbnail_update_timer.stop()

            # Clear monitors
            self.region_monitors.clear()
            self.regions.clear()

            # Clear latest images
            self.latest_region_images.clear()

            # Clear widgets (iterate Dict values)
            for widget in self.region_widgets.values():
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
