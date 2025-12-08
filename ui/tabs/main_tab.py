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


class RegionThumbnail(QFrame):
    """Widget hiển thị thumbnail cho một region với nút stop"""

    stop_requested = pyqtSignal(int)

    def __init__(self, region_id: int, coords: Tuple[int, int, int, int]):
        super().__init__()
        self.region_id = region_id
        self.coords = coords
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(2)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title layout with stop button
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel(f"Vùng {region_id + 1}")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        title.setStyleSheet(f"font-weight: bold; color: {theme.TEXT_PRIMARY}; font-size: 13px; padding: 5px;")
        title_layout.addWidget(title)

        title_layout.addStretch()

        # Stop button
        stop_btn = QPushButton("✕")
        stop_btn.setFixedSize(22, 22)
        stop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.ERROR};
                color: white;
                border-radius: 11px;
                font-weight: bold;
                font-size: 14px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: #b91c1c;
            }}
        """)
        stop_btn.setToolTip("Dừng theo dõi vùng này")
        stop_btn.clicked.connect(lambda: self.stop_requested.emit(self.region_id))
        title_layout.addWidget(stop_btn)

        layout.addLayout(title_layout)

        # Thumbnail label
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(200, 150)
        self.thumbnail_label.setStyleSheet(f"border: 1px solid {theme.BORDER_DEFAULT}; background-color: {theme.BG_PRIMARY};")
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.thumbnail_label)

        # Status label
        self.status_label = QLabel("Đang giám sát")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(f"color: {theme.SUCCESS}; font-size: 11px; padding: 2px;")
        layout.addWidget(self.status_label)

        self.setStyleSheet(f"""
            RegionThumbnail {{
                background-color: {theme.BG_SECONDARY};
                border: 1px solid {theme.BORDER_DEFAULT};
                border-radius: 6px;
            }}
        """)

    def update_thumbnail(self, pil_image: Image.Image):
        """Cập nhật thumbnail từ PIL Image"""
        try:
            pil_image = pil_image.copy()
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            pil_image.thumbnail((200, 150), Image.LANCZOS)
            width, height = pil_image.size

            img_data = pil_image.tobytes('raw', 'RGB')
            bytes_per_line = width * 3
            qimage = QImage(img_data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            qimage = qimage.copy()

            pixmap = QPixmap.fromImage(qimage)
            self.thumbnail_label.setPixmap(pixmap)
        except Exception as e:
            print(f"[RegionThumbnail] Error updating thumbnail: {e}")


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
        self.region_widgets: Dict[int, RegionThumbnail] = {}
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

        # Thumbnail update timer
        self.thumbnail_update_timer = QTimer()
        self.thumbnail_update_timer.timeout.connect(self._update_thumbnails)
        self.thumbnail_update_timer.setInterval(50)

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
        """Create right panel with preview and regions"""
        panel = QWidget()
        panel.setStyleSheet(f"background-color: {theme.BG_PRIMARY};")

        layout = QVBoxLayout(panel)
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

        # Continue button
        self.continue_btn = QPushButton("▶ Bắt đầu")
        self.continue_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.ACCENT_PRIMARY};
                color: white;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {theme.ACCENT_SECONDARY};
            }}
            QPushButton:disabled {{
                background-color: {theme.BG_TERTIARY};
                color: {theme.TEXT_MUTED};
            }}
        """)
        self.continue_btn.clicked.connect(self.confirm_window_selection)
        self.continue_btn.setEnabled(False)

        header_layout.addWidget(preview_label)
        header_layout.addStretch()
        header_layout.addWidget(target_label)
        header_layout.addWidget(self.window_combo)
        header_layout.addWidget(self.refresh_btn)
        header_layout.addWidget(self.continue_btn)

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
        self.instruction_label = QLabel("📍 Chọn cửa sổ, sau đó click 'Bắt đầu' để xem preview và chọn vùng")
        self.instruction_label.setStyleSheet(f"""
            color: {theme.INFO};
            font-size: 12px;
            padding: 10px;
            background-color: #1e3a5f;
            border-radius: 5px;
        """)
        self.instruction_label.setWordWrap(True)
        preview_section_layout.addWidget(self.instruction_label)

        # Preview scroll area
        preview_scroll = QScrollArea()
        preview_scroll.setWidgetResizable(False)
        preview_scroll.setMinimumHeight(300)
        preview_scroll.setMaximumHeight(400)
        preview_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {theme.BORDER_DEFAULT};
                border-radius: 8px;
                background-color: {theme.BG_SECONDARY};
            }}
        """)

        self.window_preview = QLabel()
        self.window_preview.setStyleSheet(f"background-color: {theme.BG_SECONDARY}; min-height: 250px;")
        self.window_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.window_preview.setText("Chọn cửa sổ để xem preview")
        self.window_preview.setScaledContents(False)
        self.window_preview.mousePressEvent = self.on_preview_mouse_press
        self.window_preview.mouseMoveEvent = self.on_preview_mouse_move
        self.window_preview.mouseReleaseEvent = self.on_preview_mouse_release

        preview_scroll.setWidget(self.window_preview)
        preview_section_layout.addWidget(preview_scroll)

        self.preview_section.setVisible(True)
        layout.addWidget(self.preview_section)

        # Selection tracking
        self.selection_start = None
        self.selection_current = None
        self.preview_pixmap = None
        self.preview_scale = 1.0
        self.original_window_image = None

        # Add region button
        self.add_region_btn = QPushButton("➕ Chọn vùng mới")
        self.add_region_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.SUCCESS};
                color: white;
                font-size: 13px;
                font-weight: bold;
                padding: 10px 16px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
        """)
        self.add_region_btn.clicked.connect(self.add_new_region)
        self.add_region_btn.setVisible(False)
        layout.addWidget(self.add_region_btn)

        # Regions display area
        regions_title = QLabel("Các vùng đang giám sát:")
        regions_title.setStyleSheet(f"color: {theme.TEXT_PRIMARY}; font-size: 14px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(regions_title)

        self.regions_scroll = QScrollArea()
        self.regions_scroll.setWidgetResizable(True)
        self.regions_scroll.setMinimumHeight(200)
        self.regions_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {theme.BORDER_DEFAULT};
                border-radius: 8px;
                background-color: {theme.BG_SECONDARY};
            }}
        """)

        self.regions_container = QWidget()
        self.regions_layout = QGridLayout(self.regions_container)
        self.regions_layout.setContentsMargins(15, 15, 15, 15)
        self.regions_layout.setSpacing(15)

        self.regions_scroll.setWidget(self.regions_container)
        layout.addWidget(self.regions_scroll)

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

    def _update_thumbnails(self):
        """Update thumbnails from main thread"""
        try:
            for region_id, image in self.latest_region_images.items():
                if image and region_id in self.region_widgets:
                    self.region_widgets[region_id].update_thumbnail(image)
        except Exception as e:
            print(f"[MainTab] Error in _update_thumbnails: {e}")

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
        """Enable continue button when window is selected"""
        try:
            if index < 0:
                self.continue_btn.setEnabled(False)
                return

            data = self.window_combo.itemData(index)
            if not data:
                self.continue_btn.setEnabled(False)
                return

            self.continue_btn.setEnabled(True)
            hwnd, window_title = data
            self.status_label.setText(f"Đã chọn: {window_title[:40]}...")

        except Exception as e:
            print(f"[MainTab] Error: {e}")

    def confirm_window_selection(self):
        """User clicked Continue - capture and show preview"""
        try:
            index = self.window_combo.currentIndex()
            if index < 0:
                return

            data = self.window_combo.itemData(index)
            if not data:
                return

            hwnd, window_title = data
            self.selected_hwnd = hwnd
            self.selected_window_title = window_title

            self.selection_start = None
            self.selection_current = None

            print(f"[MainTab] Confirmed window: {window_title}")

            self.instruction_label.setText("📍 Click và kéo trên preview để chọn vùng")
            self.instruction_label.setStyleSheet(f"""
                color: {theme.SUCCESS};
                font-size: 12px;
                padding: 10px;
                background-color: #064e3b;
                border-radius: 5px;
            """)

            self.update_window_preview()
            self.continue_btn.setEnabled(False)

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
                self.continue_btn.setEnabled(True)
                self.continue_btn.setText("🔄 Thử lại")
                return

            self.original_window_image = pil_image.copy()

            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            max_width = 700
            max_height = 380
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
            self.window_preview.setMinimumSize(display_width, display_height)
            self.window_preview.setMaximumSize(display_width, display_height)

            self.continue_btn.setText("▶ Bắt đầu")
            print(f"[MainTab] Preview updated: {display_width}x{display_height}")

        except Exception as e:
            print(f"[MainTab] Error updating preview: {e}")
            import traceback
            traceback.print_exc()

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

        if not self.is_monitoring:
            reply = QMessageBox.question(
                self,
                "Chọn vùng",
                f"Đã chọn {len(self.regions)} vùng.\n\nBạn có muốn chọn thêm vùng khác không?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.instruction_label.setText(f"📍 Click và kéo để chọn vùng {len(self.regions) + 1}")
            else:
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

            widget = RegionThumbnail(region_id, region_bbox)
            widget.stop_requested.connect(self.stop_region)
            self.region_widgets[region_id] = widget

            self.latest_region_images[region_id] = None

            grid_position = len(self.region_widgets) - 1
            row = grid_position // 3
            col = grid_position % 3
            self.regions_layout.addWidget(widget, row, col)

            print(f"[MainTab] ✓ Added region ID={region_id}")

            if self.is_monitoring:
                self.status_label.setText(f"Đang giám sát {len(self.regions)} vùng")

        except Exception as e:
            print(f"[MainTab] Error adding region: {e}")
            QMessageBox.critical(self, "Lỗi", f"Không thể thêm vùng: {e}")

    def add_new_region(self):
        """Add new region while monitoring"""
        print("[MainTab] Add new region clicked")
        self.preview_section.setVisible(True)
        self.instruction_label.setText("📍 Click và kéo để chọn vùng mới")
        self.update_window_preview()

    def stop_region(self, region_id: int):
        """Stop monitoring a specific region"""
        print(f"[MainTab] Stopping region ID={region_id}")

        try:
            if region_id in self.region_monitors:
                del self.region_monitors[region_id]

            if region_id in self.regions:
                del self.regions[region_id]

            if region_id in self.latest_region_images:
                del self.latest_region_images[region_id]

            self.app.overlay_service.clear_region_overlay(region_id)

            if region_id in self.region_widgets:
                widget = self.region_widgets[region_id]
                self.regions_layout.removeWidget(widget)
                widget.deleteLater()
                del self.region_widgets[region_id]

            self._relayout_widgets()

            remaining = len(self.region_monitors)
            self.status_label.setText(f"Đang giám sát {remaining} vùng")

            if remaining == 0:
                self.stop_monitoring()

        except Exception as e:
            print(f"[MainTab] Error stopping region: {e}")

    def _relayout_widgets(self):
        """Re-arrange widgets in grid"""
        for widget in self.region_widgets.values():
            self.regions_layout.removeWidget(widget)

        for i, widget in enumerate(self.region_widgets.values()):
            row = i // 3
            col = i % 3
            self.regions_layout.addWidget(widget, row, col)

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
            self.add_region_btn.setVisible(True)
            self.status_label.setText(f"Đang giám sát {len(self.regions)} vùng")
            self.instruction_label.setText(f"✓ Đang giám sát {len(self.regions)} vùng")
            self.instruction_label.setStyleSheet(f"""
                color: {theme.SUCCESS};
                font-size: 12px;
                padding: 10px;
                background-color: #064e3b;
                border-radius: 5px;
            """)

            self.thumbnail_update_timer.start()
            self._start_monitoring_loop()

            time.sleep(0.5)
            self.preview_section.setVisible(False)
            self.window().hide()

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
                        current_image = monitor.capture_current()
                        if current_image and region_id in self.latest_region_images:
                            self.latest_region_images[region_id] = current_image.copy()

                        has_changed, changed_image = monitor.check_and_capture()

                        if has_changed and changed_image:
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
            self.thumbnail_update_timer.stop()

            self.region_monitors.clear()
            self.regions.clear()
            self.latest_region_images.clear()

            for widget in self.region_widgets.values():
                self.regions_layout.removeWidget(widget)
                widget.deleteLater()
            self.region_widgets.clear()

            self.app.overlay_service.clear_positioned_overlay()

            self.window().showNormal()
            self.window().raise_()
            self.window().activateWindow()

            self.add_region_btn.setVisible(False)
            self.status_label.setText("Đã dừng giám sát")
            self.instruction_label.setText("📍 Chọn cửa sổ và click 'Bắt đầu' để giám sát")
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
