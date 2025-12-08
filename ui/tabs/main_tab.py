"""Main Tab - Combined monitoring and control panel with two-panel layout"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGridLayout, QFrame, QScrollArea,
                             QMessageBox, QComboBox, QGroupBox, QProgressBar)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPen, QColor
from PIL import Image
import threading
import time
from typing import Tuple, Dict, Optional

from ui.components.modern_toggle import ModernToggle
from config import new_theme as theme
from capture.window_capture import WindowRegionMonitor, WindowCapture
from services.system_monitor import get_system_monitor
from config.language_config import LanguageConfig


class RegionOverlayBox(QWidget):
    """Widget overlay hiển thị box và nút close trực tiếp trên preview cho một region"""

    close_requested = pyqtSignal(int)

    def __init__(self, region_id: int, parent=None):
        super().__init__(parent)
        self.region_id = region_id
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setStyleSheet("background: transparent;")

        # Close button ở góc phải trên
        self.close_btn = QPushButton("✕", self)
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.ERROR};
                color: white;
                border-radius: 10px;
                font-weight: bold;
                font-size: 12px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: #b91c1c;
            }}
        """)
        self.close_btn.setToolTip(f"Xóa vùng {region_id + 1}")
        self.close_btn.clicked.connect(lambda: self.close_requested.emit(self.region_id))

    def resizeEvent(self, event):
        """Đặt nút close ở góc phải trên của box"""
        super().resizeEvent(event)
        # Position close button at top-right corner
        btn_x = self.width() - self.close_btn.width() - 2
        btn_y = 2
        self.close_btn.move(btn_x, btn_y)

    def paintEvent(self, event):
        """Vẽ viền cho region box"""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(theme.ACCENT_PRIMARY), 2)
        painter.setPen(pen)
        painter.drawRect(1, 1, self.width() - 2, self.height() - 2)
        painter.end()


class MainTab(QWidget):
    """Main tab with two-panel layout - Controls on left, Preview on right"""

    scan_counter_updated = pyqtSignal(int)

    def __init__(self, app_instance):
        super().__init__()
        self.app = app_instance

        # Window capture variables
        self.selected_hwnd = None
        self.selected_window_title = None

        # Region monitoring - support multiple regions with stable IDs
        self.region_id_counter = 0
        self.region_monitors: Dict[int, WindowRegionMonitor] = {}
        self.regions: Dict[int, Tuple[int, int, int, int]] = {}
        self.region_overlay_boxes: Dict[int, RegionOverlayBox] = {}  # Overlay boxes on preview
        self.scan_counter = 0

        # Store latest captured images for thumbnail updates
        self.latest_region_images: Dict[int, Optional[Image.Image]] = {}

        # Monitoring state
        self.is_monitoring = False
        self.monitoring_thread = None

        # Performance metrics (will be updated from SystemMonitor)
        self.translation_speed_ms = 0
        self.memory_percent = 0
        self.cpu_percent = 0
        self.gpu_percent = 0

        # Live preview timer - updates preview in real-time
        self.live_preview_timer = QTimer()
        self.live_preview_timer.timeout.connect(self._update_live_preview)
        self.live_preview_timer.setInterval(500)  # Update every 500ms
        self.is_live_preview_enabled = False
        
        # Set to track regions pending deletion (to handle race conditions)
        self.pending_delete_regions: set = set()

        # Start system monitor and connect signal
        self.system_monitor = get_system_monitor()
        self.system_monitor.start()
        self.system_monitor.metrics_updated.connect(self._on_metrics_updated)

        self.init_ui()

    def init_ui(self):
        """Initialize two-panel UI"""
        self.setStyleSheet(f"background-color: {theme.BG_PRIMARY};")

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left panel - Settings/Controls
        left_panel = self._create_left_panel()
        main_layout.addWidget(left_panel)

        # Right panel - Preview
        right_panel = self._create_right_panel()
        main_layout.addWidget(right_panel, 1)

        # Connect signals
        self.scan_counter_updated.connect(self._update_scan_label)

        # Auto-refresh window list
        QTimer.singleShot(100, self.refresh_window_list)

    def _create_left_panel(self):
        """Create left panel with controls"""
        panel = QWidget()
        panel.setFixedWidth(theme.LEFT_PANEL_WIDTH)
        panel.setStyleSheet(f"background-color: {theme.BG_PRIMARY}; border-right: 1px solid {theme.BORDER_DEFAULT};")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(25)

        # Performance section
        perf_group = self._create_performance_section()
        layout.addWidget(perf_group)

        # Translation modes section
        modes_group = self._create_modes_section()
        layout.addWidget(modes_group)

        # Language section
        lang_group = self._create_language_section()
        layout.addWidget(lang_group)

        layout.addStretch()

        scroll.setWidget(content)

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.addWidget(scroll)

        return panel

    def _create_performance_section(self):
        """Create performance metrics section"""
        group = QGroupBox("Điều khiển")
        group.setStyleSheet(theme.get_group_box_style())

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Performance mode toggle
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Chế độ hiệu suất")
        mode_label.setStyleSheet(f"font-size: 12px; color: {theme.TEXT_SECONDARY}; font-weight: normal;")
        self.perf_toggle = ModernToggle()
        self.perf_toggle.setChecked(True)
        mode_layout.addWidget(mode_label)
        mode_layout.addStretch()
        mode_layout.addWidget(self.perf_toggle)
        layout.addLayout(mode_layout)

        # Performance metrics
        metrics = [
            ("Hiệu suất dịch", f"{self.translation_speed_ms}ms", 0, theme.ACCENT_PRIMARY),
            ("Bộ nhớ (RAM)", f"{self.memory_percent}%", 0, theme.SUCCESS),
            ("Tải CPU", f"{self.cpu_percent}%", 0, theme.INFO),
            ("Tài nguyên GPU", f"{self.gpu_percent}%", 0, theme.ACCENT_PURPLE)
        ]

        self.metric_labels = {}
        self.metric_bars = {}

        for name, value, progress, color in metrics:
            metric_layout = QVBoxLayout()
            metric_layout.setSpacing(6)

            header = QHBoxLayout()
            name_label = QLabel(name)
            name_label.setStyleSheet(f"font-size: 12px; color: {theme.TEXT_PRIMARY}; font-weight: normal;")
            value_label = QLabel(value)
            value_label.setStyleSheet(f"font-size: 12px; color: {color}; font-weight: normal;")
            self.metric_labels[name] = value_label
            header.addWidget(name_label)
            header.addStretch()
            header.addWidget(value_label)

            progress_bar = QProgressBar()
            progress_bar.setMaximum(100)
            progress_bar.setValue(progress)
            progress_bar.setTextVisible(False)
            progress_bar.setFixedHeight(6)
            progress_bar.setStyleSheet(theme.get_progress_bar_style(color))
            self.metric_bars[name] = progress_bar

            metric_layout.addLayout(header)
            metric_layout.addWidget(progress_bar)
            layout.addLayout(metric_layout)

        group.setLayout(layout)
        return group

    def _create_modes_section(self):
        """Create translation modes section"""
        group = QGroupBox("Chế độ dịch")
        group.setStyleSheet(theme.get_group_box_style())

        layout = QVBoxLayout()
        layout.setSpacing(10)

        modes = [
            ("Dịch tức thời", True, True),
            ("Dịch theo vùng", False, False),  # Disabled
            ("Dịch từng từ", True, True)
        ]

        self.mode_toggles = {}

        for mode_name, checked, enabled in modes:
            mode_widget = QFrame()
            mode_widget.setStyleSheet(f"""
                QFrame {{
                    background-color: {theme.BG_SECONDARY};
                    border-radius: 6px;
                }}
                QFrame:hover {{
                    background-color: {theme.BG_TERTIARY if enabled else theme.BG_SECONDARY};
                }}
            """)

            mode_layout = QHBoxLayout(mode_widget)
            mode_layout.setContentsMargins(12, 8, 12, 8)

            label = QLabel(mode_name)
            label_color = theme.TEXT_PRIMARY if enabled else theme.TEXT_MUTED
            label.setStyleSheet(f"font-size: 13px; color: {label_color}; font-weight: normal;")

            toggle = ModernToggle()
            toggle.setChecked(checked)
            toggle.setEnabled(enabled)
            self.mode_toggles[mode_name] = toggle

            mode_layout.addWidget(label)
            mode_layout.addStretch()
            mode_layout.addWidget(toggle)

            layout.addWidget(mode_widget)

        group.setLayout(layout)
        return group

    def _create_language_section(self):
        """Create language selection section"""
        group = QGroupBox("Ngôn ngữ")
        group.setStyleSheet(theme.get_group_box_style())

        layout = QHBoxLayout()
        layout.setSpacing(15)

        # Source language
        source_layout = QVBoxLayout()
        source_label = QLabel("Ngôn ngữ nguồn")
        source_label.setStyleSheet(f"font-size: 11px; color: {theme.TEXT_SECONDARY}; margin-bottom: 5px; font-weight: normal;")
        self.source_combo = QComboBox()
        self.source_combo.addItems(LanguageConfig.get_source_languages())
        self.source_combo.setCurrentText("Auto (Detect)")
        self.source_combo.setStyleSheet(theme.get_combo_box_style())
        self.source_combo.currentTextChanged.connect(self._on_source_language_changed)
        source_layout.addWidget(source_label)
        source_layout.addWidget(self.source_combo)

        # Target language
        target_layout = QVBoxLayout()
        target_label = QLabel("Ngôn ngữ đích")
        target_label.setStyleSheet(f"font-size: 11px; color: {theme.TEXT_SECONDARY}; margin-bottom: 5px; font-weight: normal;")
        self.target_combo = QComboBox()
        self.target_combo.addItems(LanguageConfig.get_target_languages())
        self.target_combo.setCurrentText("Vietnamese")
        self.target_combo.setStyleSheet(theme.get_combo_box_style())
        self.target_combo.currentTextChanged.connect(self._on_target_language_changed)
        target_layout.addWidget(target_label)
        target_layout.addWidget(self.target_combo)

        layout.addLayout(source_layout)
        layout.addLayout(target_layout)

        group.setLayout(layout)
        return group

    def _create_right_panel(self):
        """Create right panel with preview and regions - scrollable"""
        # Main panel container
        panel = QWidget()
        panel.setStyleSheet(f"background-color: {theme.BG_PRIMARY};")
        
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)
        
        # Scrollable content area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {theme.BG_PRIMARY};
            }}
        """)
        
        # Content widget inside scroll area
        content_widget = QWidget()
        content_widget.setStyleSheet(f"background-color: {theme.BG_PRIMARY};")
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # Header with target window selector
        header_layout = QHBoxLayout()

        preview_label = QLabel("Xem trước")
        preview_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {theme.TEXT_PRIMARY};")

        target_label = QLabel("Target window:")
        target_label.setStyleSheet(f"font-size: 12px; color: {theme.TEXT_SECONDARY};")

        self.window_combo = QComboBox()
        self.window_combo.setFixedWidth(300)
        self.window_combo.setStyleSheet(theme.get_combo_box_style())
        self.window_combo.currentIndexChanged.connect(self.on_window_combo_changed)

        # Refresh button
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(35, 35)
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.BG_TERTIARY};
                color: white;
                font-size: 14px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {theme.ACCENT_PRIMARY};
            }}
        """)
        self.refresh_btn.clicked.connect(self.refresh_window_list)

        # Live preview toggle button
        self.live_preview_btn = QPushButton("📺 Live")
        self.live_preview_btn.setFixedHeight(35)
        self.live_preview_btn.setCheckable(True)
        self.live_preview_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.BG_TERTIARY};
                color: white;
                font-size: 12px;
                padding: 0 12px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {theme.ACCENT_PRIMARY};
            }}
            QPushButton:checked {{
                background-color: {theme.SUCCESS};
            }}
        """)
        self.live_preview_btn.clicked.connect(self._toggle_live_preview)

        header_layout.addWidget(preview_label)
        header_layout.addStretch()
        header_layout.addWidget(target_label)
        header_layout.addWidget(self.window_combo)
        header_layout.addWidget(self.refresh_btn)
        header_layout.addWidget(self.live_preview_btn)

        layout.addLayout(header_layout)

        # Status label
        self.status_label = QLabel("Chọn cửa sổ để bắt đầu")
        self.status_label.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(self.status_label)

        # Scan counter
        self.scan_label = QLabel("Scan: 0")
        self.scan_label.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-size: 11px;")

        # Preview section
        self.preview_section = QWidget()
        preview_section_layout = QVBoxLayout(self.preview_section)
        preview_section_layout.setContentsMargins(0, 0, 0, 0)

        # Instruction label
        self.instruction_label = QLabel("📍 Chọn cửa sổ, bật Live preview rồi kéo thả để chọn vùng")
        self.instruction_label.setStyleSheet(f"""
            color: {theme.INFO};
            font-size: 12px;
            padding: 10px;
            background-color: #1e3a5f;
            border-radius: 5px;
        """)
        self.instruction_label.setWordWrap(True)
        preview_section_layout.addWidget(self.instruction_label)

        # Preview container (no scroll - fits to content)
        preview_container = QWidget()
        preview_container.setStyleSheet(f"""
            background-color: {theme.BG_SECONDARY};
            border: 1px solid {theme.BORDER_DEFAULT};
            border-radius: 8px;
        """)
        preview_container_layout = QVBoxLayout(preview_container)
        preview_container_layout.setContentsMargins(0, 0, 0, 0)  # No padding to avoid offset
        
        self.window_preview = QLabel()
        self.window_preview.setStyleSheet(f"background-color: {theme.BG_SECONDARY};")
        self.window_preview.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)  # Align top-left for accurate selection
        self.window_preview.setText("Chọn cửa sổ để xem preview")
        self.window_preview.setScaledContents(False)
        self.window_preview.mousePressEvent = self.on_preview_mouse_press
        self.window_preview.mouseMoveEvent = self.on_preview_mouse_move
        self.window_preview.mouseReleaseEvent = self.on_preview_mouse_release

        preview_container_layout.addWidget(self.window_preview)
        preview_section_layout.addWidget(preview_container)

        self.preview_section.setVisible(True)
        layout.addWidget(self.preview_section)

        # Selection tracking
        self.selection_start = None
        self.selection_current = None
        self.preview_pixmap = None
        self.preview_scale = 1.0
        self.original_window_image = None

        # Selection hint label
        self.selection_hint = QLabel("💡 Kéo thả trên màn hình preview để chọn vùng theo dõi")
        self.selection_hint.setStyleSheet(f"""
            color: {theme.TEXT_SECONDARY};
            font-size: 12px;
            padding: 8px 12px;
            background-color: {theme.BG_SECONDARY};
            border-radius: 5px;
            margin-top: 5px;
        """)
        self.selection_hint.setWordWrap(True)
        layout.addWidget(self.selection_hint)
        
        # Add stretch at end to push content to top
        layout.addStretch()

        scroll_area.setWidget(content_widget)
        panel_layout.addWidget(scroll_area)

        return panel

    # === Language handling ===
    def _on_source_language_changed(self, lang_name: str):
        """Handle source language change"""
        lang_code = LanguageConfig.get_language_code(lang_name)
        
        if hasattr(self.app, 'ocr_service') and self.app.ocr_service:
            self.app.ocr_service.set_source_language(lang_code)
        
        print(f"[MainTab] Source language: {lang_name} ({lang_code})")

    def _on_target_language_changed(self, lang_name: str):
        """Handle target language change"""
        lang_code = LanguageConfig.get_language_code(lang_name)
        trans_code = LanguageConfig.get_translation_code(lang_code)
        
        if hasattr(self.app, 'translation_service') and self.app.translation_service:
            self.app.translation_service.target_lang = trans_code
        
        print(f"[MainTab] Target language: {lang_name} ({lang_code})")

    def _update_scan_label(self, counter: int):
        """Update scan label"""
        self.scan_label.setText(f"Scan: {counter}")

    def _on_metrics_updated(self, metrics):
        """Handle system metrics update from SystemMonitor"""
        try:
            # Update stored values
            self.cpu_percent = metrics.cpu_percent
            self.memory_percent = metrics.memory_percent
            self.gpu_percent = metrics.gpu_percent
            self.translation_speed_ms = metrics.translation_speed_ms

            # Update UI labels and bars
            if "Tải CPU" in self.metric_labels:
                self.metric_labels["Tải CPU"].setText(f"{self.cpu_percent:.0f}%")
                self.metric_bars["Tải CPU"].setValue(int(self.cpu_percent))

            if "Bộ nhớ (RAM)" in self.metric_labels:
                self.metric_labels["Bộ nhớ (RAM)"].setText(f"{self.memory_percent:.0f}%")
                self.metric_bars["Bộ nhớ (RAM)"].setValue(int(self.memory_percent))

            if "Tài nguyên GPU" in self.metric_labels:
                self.metric_labels["Tài nguyên GPU"].setText(f"{self.gpu_percent:.0f}%")
                self.metric_bars["Tài nguyên GPU"].setValue(int(self.gpu_percent))

            if "Hiệu suất dịch" in self.metric_labels:
                speed_text = f"{self.translation_speed_ms}ms" if self.translation_speed_ms > 0 else "--"
                self.metric_labels["Hiệu suất dịch"].setText(speed_text)
                # Map speed to progress: 0ms = 100%, 100ms = 0%
                speed_progress = max(0, min(100, 100 - self.translation_speed_ms))
                self.metric_bars["Hiệu suất dịch"].setValue(speed_progress)



        except Exception as e:
            print(f"[MainTab] Error updating metrics: {e}")

    def _get_preview_dimensions(self):
        """Get fixed preview dimensions based on window state"""
        try:
            main_window = self.window()
            if main_window and main_window.isMaximized():
                # Maximized window: larger preview
                return 1000, 600
            else:
                # Normal window: standard preview
                return 700, 420
        except:
            # Fallback to normal size
            return 700, 420

    # === Window capture methods (migrated from MonitorTab) ===
    def refresh_window_list(self):
        """Refresh window list"""
        try:
            self.window_combo.clear()
            windows = WindowCapture.list_all_windows()

            if not windows:
                self.window_combo.addItem("Không tìm thấy cửa sổ nào")
                return

            ignore_keywords = [
                "Program Manager", "Windows Input Experience",
                "Microsoft Text Input Application", "Settings",
                "MSCTFIME UI", "Default IME", "OleMainThreadWndName"
            ]

            filtered_windows = []
            for hwnd, title in windows:
                if not title or len(title) < 2:
                    continue
                if any(keyword.lower() in title.lower() for keyword in ignore_keywords):
                    continue
                if "OCR" in title and "Translate" in title:
                    continue
                filtered_windows.append((hwnd, title))

            if not filtered_windows:
                self.window_combo.addItem("Không tìm thấy cửa sổ phù hợp")
                return

            for hwnd, title in filtered_windows:
                display_title = title[:50] + "..." if len(title) > 50 else title
                self.window_combo.addItem(f"{display_title}", (hwnd, title))

            print(f"[MainTab] Refreshed: {len(filtered_windows)} windows")

        except Exception as e:
            print(f"[MainTab] Error refreshing: {e}")

    def on_window_combo_changed(self, index: int):
        """Handle window selection change"""
        try:
            if index < 0:
                return

            data = self.window_combo.itemData(index)
            if not data:
                return

            hwnd, window_title = data
            self.status_label.setText(f"Đã chọn: {window_title[:40]}...")

        except Exception as e:
            print(f"[MainTab] Error: {e}")

        except Exception as e:
            print(f"[MainTab] Error: {e}")

        except Exception as e:
            print(f"[MainTab] Error: {e}")

    def update_window_preview(self):
        """Capture and display window preview"""
        try:
            if not self.selected_hwnd:
                return

            import win32gui
            import win32con

            # Check if minimized
            placement = win32gui.GetWindowPlacement(self.selected_hwnd)
            if placement[1] == win32con.SW_SHOWMINIMIZED:
                win32gui.ShowWindow(self.selected_hwnd, win32con.SW_RESTORE)
                time.sleep(0.3)

            if not win32gui.IsWindowVisible(self.selected_hwnd):
                win32gui.ShowWindow(self.selected_hwnd, win32con.SW_SHOW)
                time.sleep(0.3)

            # Hide app window temporarily
            main_window = self.window()
            was_visible = main_window.isVisible()
            if was_visible:
                main_window.hide()
                time.sleep(0.2)

            try:
                window_capture = WindowCapture(hwnd=self.selected_hwnd)
                pil_image = window_capture.capture_window()
            finally:
                if was_visible:
                    main_window.show()
                    main_window.raise_()

            if not pil_image:
                self.window_preview.setText("❌ Không thể capture window")
                return

            self.original_window_image = pil_image.copy()

            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Get dynamic preview dimensions based on panel size
            max_width, max_height = self._get_preview_dimensions()
            img_width, img_height = pil_image.size

            self.preview_scale = min(max_width / img_width, max_height / img_height, 1.0)
            display_width = int(img_width * self.preview_scale)
            display_height = int(img_height * self.preview_scale)

            pil_image = pil_image.resize((display_width, display_height), Image.Resampling.LANCZOS)

            img_data = pil_image.tobytes('raw', 'RGB')
            bytes_per_line = pil_image.width * 3
            qimage = QImage(img_data, pil_image.width, pil_image.height, bytes_per_line, QImage.Format.Format_RGB888)
            qimage = qimage.copy()

            self.preview_pixmap = QPixmap.fromImage(qimage)

            self.window_preview.setText("")
            self.window_preview.setStyleSheet(f"""
                QLabel {{
                    border: 2px solid {theme.SUCCESS};
                    border-radius: 5px;
                    background-color: {theme.BG_SECONDARY};
                }}
            """)

            self.window_preview.setPixmap(self.preview_pixmap)
            # Don't set fixed size - let it fit within the scroll area
            
            # Update overlay boxes positions after scale change
            self._update_all_overlay_boxes()

            print(f"[MainTab] Preview updated: {display_width}x{display_height}")

        except Exception as e:
            print(f"[MainTab] Error updating preview: {e}")
            import traceback
            traceback.print_exc()

    def _toggle_live_preview(self, checked: bool):
        """Toggle live preview mode"""
        self.is_live_preview_enabled = checked
        
        if checked:
            # Start live preview - need to have a selected window first
            index = self.window_combo.currentIndex()
            if index >= 0:
                data = self.window_combo.itemData(index)
                if data:
                    hwnd, window_title = data
                    self.selected_hwnd = hwnd
                    self.selected_window_title = window_title
                    self.live_preview_timer.start()
                    self.live_preview_btn.setText("📺 Live ON")
                    print(f"[MainTab] Live preview started for: {window_title}")
                    # Do initial capture
                    self._update_live_preview()
                else:
                    self.live_preview_btn.setChecked(False)
                    self.is_live_preview_enabled = False
            else:
                self.live_preview_btn.setChecked(False)
                self.is_live_preview_enabled = False
        else:
            self.live_preview_timer.stop()
            self.live_preview_btn.setText("📺 Live")
            print("[MainTab] Live preview stopped")

    def _update_live_preview(self):
        """Update preview in real-time without hiding main window"""
        try:
            if not self.selected_hwnd or not self.is_live_preview_enabled:
                return

            import win32gui

            # Check if window still exists
            if not win32gui.IsWindow(self.selected_hwnd):
                self.live_preview_timer.stop()
                self.live_preview_btn.setChecked(False)
                self.is_live_preview_enabled = False
                self.window_preview.setText("❌ Cửa sổ đã bị đóng")
                return

            # Capture window directly without hiding main window
            window_capture = WindowCapture(hwnd=self.selected_hwnd)
            pil_image = window_capture.capture_window()

            if not pil_image:
                return  # Skip this frame if capture failed

            self.original_window_image = pil_image.copy()

            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Get dynamic preview dimensions based on panel size
            max_width, max_height = self._get_preview_dimensions()
            img_width, img_height = pil_image.size

            self.preview_scale = min(max_width / img_width, max_height / img_height, 1.0)
            display_width = int(img_width * self.preview_scale)
            display_height = int(img_height * self.preview_scale)

            pil_image = pil_image.resize((display_width, display_height), Image.Resampling.LANCZOS)

            img_data = pil_image.tobytes('raw', 'RGB')
            bytes_per_line = pil_image.width * 3
            qimage = QImage(img_data, pil_image.width, pil_image.height, bytes_per_line, QImage.Format.Format_RGB888)
            qimage = qimage.copy()

            self.preview_pixmap = QPixmap.fromImage(qimage)

            self.window_preview.setText("")
            self.window_preview.setStyleSheet(f"""
                QLabel {{
                    border: 2px solid {theme.SUCCESS};
                    border-radius: 5px;
                    background-color: {theme.BG_SECONDARY};
                }}
            """)

            self.window_preview.setPixmap(self.preview_pixmap)
            # Don't set fixed size - let it fit within the scroll area
            
            # Update overlay boxes positions after scale change
            self._update_all_overlay_boxes()

        except Exception as e:
            print(f"[MainTab] Error in live preview: {e}")

    # === Mouse events for region selection ===
    def on_preview_mouse_press(self, event):
        if not self.preview_pixmap:
            return
        self.selection_start = event.pos()
        self.selection_current = event.pos()

    def on_preview_mouse_move(self, event):
        if not self.selection_start:
            return
        self.selection_current = event.pos()
        self.draw_selection_rectangle()

    def on_preview_mouse_release(self, event):
        if not self.selection_start:
            return

        self.selection_current = event.pos()

        x1 = int(min(self.selection_start.x(), self.selection_current.x()) / self.preview_scale)
        y1 = int(min(self.selection_start.y(), self.selection_current.y()) / self.preview_scale)
        x2 = int(max(self.selection_start.x(), self.selection_current.x()) / self.preview_scale)
        y2 = int(max(self.selection_start.y(), self.selection_current.y()) / self.preview_scale)

        width = x2 - x1
        height = y2 - y1

        if width < 10 or height < 10:
            QMessageBox.warning(self, "Cảnh báo", "Vùng chọn quá nhỏ.")
            self.selection_start = None
            self.selection_current = None
            if self.preview_pixmap:
                self.window_preview.setPixmap(self.preview_pixmap)
            return

        region_bbox = (x1, y1, width, height)
        print(f"[MainTab] Region selected: {region_bbox}")

        self.draw_selection_rectangle()
        self.add_region(region_bbox)

        self.selection_start = None
        self.selection_current = None

        # Auto-start monitoring after first region (no popup needed - preview stays visible for more regions)
        if not self.is_monitoring:
            self.start_monitoring()

    def draw_selection_rectangle(self):
        """Draw selection rectangle on preview"""
        if not self.preview_pixmap or not self.selection_start or not self.selection_current:
            return

        pixmap = self.preview_pixmap.copy()
        painter = QPainter(pixmap)
        pen = QPen(QColor(theme.ACCENT_PRIMARY), 2)
        painter.setPen(pen)

        x1 = min(self.selection_start.x(), self.selection_current.x())
        y1 = min(self.selection_start.y(), self.selection_current.y())
        x2 = max(self.selection_start.x(), self.selection_current.x())
        y2 = max(self.selection_start.y(), self.selection_current.y())

        painter.drawRect(x1, y1, x2 - x1, y2 - y1)
        painter.end()

        self.window_preview.setPixmap(pixmap)

    # === Region management ===
    def add_region(self, region_bbox: Tuple[int, int, int, int]):
        """Add new region"""
        try:
            region_id = self.region_id_counter
            self.region_id_counter += 1

            print(f"[MainTab] Adding region ID={region_id}...")

            monitor = WindowRegionMonitor(
                hwnd=self.selected_hwnd,
                region_bbox=region_bbox
            )
            self.region_monitors[region_id] = monitor
            self.regions[region_id] = region_bbox

            self.latest_region_images[region_id] = None

            # Create overlay box on preview
            overlay_box = RegionOverlayBox(region_id, self.window_preview)
            overlay_box.close_requested.connect(self.stop_region)
            self.region_overlay_boxes[region_id] = overlay_box
            self._update_overlay_box_position(region_id)
            overlay_box.show()

            print(f"[MainTab] Added region ID={region_id}")

            if self.is_monitoring:
                self.status_label.setText(f"Đang giám sát {len(self.regions)} vùng")

        except Exception as e:
            print(f"[MainTab] Error adding region: {e}")
            QMessageBox.critical(self, "Lỗi", f"Không thể thêm vùng: {e}")

    def stop_region(self, region_id: int):
        """Stop monitoring a specific region"""
        print(f"[MainTab] Stopping region ID={region_id}")

        # Mark as pending deletion to prevent race conditions
        self.pending_delete_regions.add(region_id)

        try:
            # Clear overlay FIRST to prevent it from being recreated
            self.app.overlay_service.clear_region_overlay(region_id)
            
            if region_id in self.region_monitors:
                del self.region_monitors[region_id]

            if region_id in self.regions:
                del self.regions[region_id]

            if region_id in self.latest_region_images:
                del self.latest_region_images[region_id]

            # Remove overlay box from preview
            if region_id in self.region_overlay_boxes:
                overlay_box = self.region_overlay_boxes[region_id]
                overlay_box.hide()
                overlay_box.deleteLater()
                del self.region_overlay_boxes[region_id]

            remaining = len(self.region_monitors)
            self.status_label.setText(f"Đang giám sát {remaining} vùng")

            if remaining == 0:
                self.stop_monitoring()

        except Exception as e:
            print(f"[MainTab] Error stopping region: {e}")
        finally:
            # Remove from pending after a short delay to ensure all async operations complete
            QTimer.singleShot(500, lambda: self.pending_delete_regions.discard(region_id))

    def _update_overlay_box_position(self, region_id: int):
        """Update overlay box position based on current preview scale"""
        if region_id not in self.region_overlay_boxes or region_id not in self.regions:
            return
        
        overlay_box = self.region_overlay_boxes[region_id]
        region_bbox = self.regions[region_id]  # (x, y, width, height) in original image coords
        
        # Scale to preview coordinates
        x = int(region_bbox[0] * self.preview_scale)
        y = int(region_bbox[1] * self.preview_scale)
        w = int(region_bbox[2] * self.preview_scale)
        h = int(region_bbox[3] * self.preview_scale)
        
        overlay_box.setGeometry(x, y, w, h)

    def _update_all_overlay_boxes(self):
        """Update all overlay boxes positions after preview scale changes"""
        for region_id in self.region_overlay_boxes.keys():
            self._update_overlay_box_position(region_id)

    # === Monitoring control ===
    def start_monitoring(self):
        """Start monitoring all regions"""
        print(f"[MainTab] Starting monitoring for {len(self.region_monitors)} regions")

        if not self.region_monitors:
            QMessageBox.warning(self, "Cảnh báo", "Chưa có vùng nào được chọn.")
            return

        try:
            if not self.app.async_service.is_running():
                self.app.async_service.start()
                time.sleep(0.3)

            self.is_monitoring = True
            self.status_label.setText(f"Đang giám sát {len(self.regions)} vùng")
            # Hide instruction label to avoid duplicate with status_label
            self.instruction_label.setVisible(False)

            self._start_monitoring_loop()

            time.sleep(0.5)
            # Removed: self.preview_section.setVisible(False) - Keep preview visible for selecting more regions
            # Removed: self.window().hide() - UI should only hide/show via toggle button

            print(f"[MainTab] ✓ Monitoring started")

        except Exception as e:
            print(f"[MainTab] Error starting monitoring: {e}")
            self.is_monitoring = False
            self.window().showNormal()

    def _start_monitoring_loop(self):
        """Monitoring loop for all regions"""
        def monitoring_thread():
            fps = 25
            frame_interval = 1.0 / fps
            scan_counter = 0

            print(f"[MonitoringThread] Started at {fps} FPS")

            while self.is_monitoring:
                start_time = time.time()

                try:
                    monitors_snapshot = dict(self.region_monitors)

                    if not monitors_snapshot:
                        time.sleep(frame_interval)
                        continue

                    for region_id, monitor in monitors_snapshot.items():
                        # Skip regions pending deletion
                        if region_id in self.pending_delete_regions:
                            continue
                            
                        current_image = monitor.capture_current()
                        if current_image and region_id in self.latest_region_images:
                            self.latest_region_images[region_id] = current_image.copy()

                        has_changed, changed_image = monitor.check_and_capture()

                        if has_changed and changed_image:
                            # Double-check region not pending deletion before processing
                            if region_id in self.pending_delete_regions:
                                continue
                                
                            scan_counter += 1
                            abs_bbox = monitor.get_absolute_bbox()

                            if abs_bbox:
                                abs_x, abs_y, abs_w, abs_h = abs_bbox
                                region_coords = (abs_x, abs_y, abs_x + abs_w, abs_y + abs_h)

                                self.app.on_region_change(region_id, changed_image, scan_counter, region_coords)

                            self.scan_counter = scan_counter
                            self.scan_counter_updated.emit(scan_counter)

                    elapsed = time.time() - start_time
                    to_sleep = frame_interval - elapsed
                    if to_sleep > 0:
                        time.sleep(to_sleep)

                except Exception as e:
                    print(f"[MonitoringThread] Error: {e}")
                    break

            print(f"[MonitoringThread] Ended. Total scans: {scan_counter}")

        self.monitoring_thread = threading.Thread(target=monitoring_thread, daemon=True)
        self.monitoring_thread.start()

    def stop_monitoring(self):
        """Stop monitoring"""
        try:
            self.is_monitoring = False

            self.region_monitors.clear()
            self.regions.clear()
            self.latest_region_images.clear()
            self.pending_delete_regions.clear()

            # Clear overlay boxes on preview
            for overlay_box in self.region_overlay_boxes.values():
                overlay_box.hide()
                overlay_box.deleteLater()
            self.region_overlay_boxes.clear()

            self.app.overlay_service.clear_positioned_overlay()

            self.window().showNormal()
            self.window().raise_()
            self.window().activateWindow()

            self.status_label.setText("Đã dừng giám sát")
            # Show instruction label again
            self.instruction_label.setVisible(True)
            self.instruction_label.setText("📍 Bật Live preview và kéo thả để chọn vùng theo dõi")
            self.instruction_label.setStyleSheet(f"""
                color: {theme.INFO};
                font-size: 12px;
                padding: 10px;
                background-color: #1e3a5f;
                border-radius: 5px;
            """)
            self.scan_label.setText("Scan: 0")
            self.scan_counter = 0

            print("[MainTab] Monitoring stopped")

        except Exception as e:
            print(f"[MainTab] Error stopping: {e}")
            self.window().showNormal()
