"""Settings Tab - Application settings and preferences"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGroupBox, QComboBox, QFrame,
                             QScrollArea, QCheckBox)
from PyQt6.QtCore import Qt
from config.language_config import LanguageConfig


class SettingsTab(QWidget):
    """Tab for application settings"""
    
    def __init__(self, app_instance):
        super().__init__()
        self.app = app_instance
        self.init_ui()
    
    def init_ui(self):
        """Initialize settings UI"""
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
        
        # Main layout with scroll
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        # Content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("⚙️ Cài đặt")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        layout.addWidget(header)
        
        # === LANGUAGE SETTINGS ===
        lang_group = QGroupBox("🌐 Ngôn ngữ")
        lang_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
                border: 2px solid #374151;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #1e293b;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
        """)
        lang_layout = QVBoxLayout()
        lang_layout.setSpacing(15)
        
        # Source language
        source_row = QHBoxLayout()
        source_label = QLabel("Ngôn ngữ nguồn (OCR):")
        source_label.setStyleSheet("color: #e5e7eb; font-size: 14px; font-weight: normal;")
        source_row.addWidget(source_label)
        
        self.source_lang_combo = QComboBox()
        self.source_lang_combo.addItems(LanguageConfig.get_source_languages())
        self.source_lang_combo.setCurrentText("Auto (Detect)")
        self.source_lang_combo.setStyleSheet("""
            QComboBox {
                background-color: #1f2937;
                color: #ffffff;
                border: 1px solid #374151;
                border-radius: 5px;
                padding: 8px 12px;
                min-width: 200px;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #1f2937;
                color: #ffffff;
                border: 1px solid #374151;
                selection-background-color: #3b82f6;
                padding: 5px;
            }
        """)
        self.source_lang_combo.currentTextChanged.connect(self._on_source_language_changed)
        source_row.addWidget(self.source_lang_combo)
        source_row.addStretch()
        
        lang_layout.addLayout(source_row)
        
        # Source language description
        source_desc = QLabel("💡 Auto: Tự động phát hiện | Japanese: Tối ưu cho Manga/Game | Chinese: Tối ưu cho Document")
        source_desc.setStyleSheet("color: #9ca3af; font-size: 12px; font-weight: normal; padding-left: 20px;")
        source_desc.setWordWrap(True)
        lang_layout.addWidget(source_desc)
        
        # Target language
        target_row = QHBoxLayout()
        target_label = QLabel("Ngôn ngữ đích (Dịch):")
        target_label.setStyleSheet("color: #e5e7eb; font-size: 14px; font-weight: normal;")
        target_row.addWidget(target_label)
        
        self.target_lang_combo = QComboBox()
        self.target_lang_combo.addItems(LanguageConfig.get_target_languages())
        self.target_lang_combo.setCurrentText("Vietnamese")
        self.target_lang_combo.setStyleSheet("""
            QComboBox {
                background-color: #1f2937;
                color: #ffffff;
                border: 1px solid #374151;
                border-radius: 5px;
                padding: 8px 12px;
                min-width: 200px;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #1f2937;
                color: #ffffff;
                border: 1px solid #374151;
                selection-background-color: #3b82f6;
                padding: 5px;
            }
        """)
        self.target_lang_combo.currentTextChanged.connect(self._on_target_language_changed)
        target_row.addWidget(self.target_lang_combo)
        target_row.addStretch()
        
        lang_layout.addLayout(target_row)
        
        lang_group.setLayout(lang_layout)
        layout.addWidget(lang_group)
        
        # === OCR SETTINGS ===
        ocr_group = QGroupBox("📷 OCR")
        ocr_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
                border: 2px solid #374151;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #1e293b;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
        """)
        ocr_layout = QVBoxLayout()
        
        # Tokenization checkbox
        self.tokenization_check = QCheckBox("Bật tách từ đa ngôn ngữ (Tokenization)")
        self.tokenization_check.setChecked(True)
        self.tokenization_check.setStyleSheet("""
            QCheckBox {
                color: #e5e7eb;
                font-size: 14px;
                font-weight: normal;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #374151;
                border-radius: 4px;
                background-color: #1f2937;
            }
            QCheckBox::indicator:checked {
                background-color: #3b82f6;
                border-color: #3b82f6;
            }
        """)
        ocr_layout.addWidget(self.tokenization_check)
        
        # Japanese processing checkbox
        self.japanese_check = QCheckBox("Bật xử lý đặc biệt cho tiếng Nhật")
        self.japanese_check.setChecked(True)
        self.japanese_check.setStyleSheet("""
            QCheckBox {
                color: #e5e7eb;
                font-size: 14px;
                font-weight: normal;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #374151;
                border-radius: 4px;
                background-color: #1f2937;
            }
            QCheckBox::indicator:checked {
                background-color: #3b82f6;
                border-color: #3b82f6;
            }
        """)
        ocr_layout.addWidget(self.japanese_check)
        
        ocr_group.setLayout(ocr_layout)
        layout.addWidget(ocr_group)
        
        # === THEME SETTINGS ===
        theme_group = QGroupBox("🎨 Giao diện")
        theme_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
                border: 2px solid #374151;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #1e293b;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
        """)
        theme_layout = QVBoxLayout()
        
        # Theme selector
        theme_row = QHBoxLayout()
        theme_label = QLabel("Theme:")
        theme_label.setStyleSheet("color: #e5e7eb; font-size: 14px; font-weight: normal;")
        theme_row.addWidget(theme_label)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setCurrentText("Dark")
        self.theme_combo.setStyleSheet("""
            QComboBox {
                background-color: #1f2937;
                color: #ffffff;
                border: 1px solid #374151;
                border-radius: 5px;
                padding: 8px 12px;
                min-width: 200px;
            }
        """)
        theme_row.addWidget(self.theme_combo)
        theme_row.addStretch()
        theme_layout.addLayout(theme_row)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # === OVERLAY CUSTOMIZATION ===
        overlay_group = QGroupBox("📐 Tùy chỉnh Overlay")
        overlay_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
                border: 2px solid #374151;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #1e293b;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
        """)
        overlay_layout = QVBoxLayout()
        overlay_layout.setSpacing(12)
        
        # Font family
        font_row = QHBoxLayout()
        font_label = QLabel("Font:")
        font_label.setStyleSheet("color: #e5e7eb; font-size: 14px; font-weight: normal;")
        font_label.setFixedWidth(120)
        font_row.addWidget(font_label)
        
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Times New Roman", "Arial", "Segoe UI", "Courier New", "Georgia"])
        self.font_combo.setStyleSheet("""
            QComboBox {
                background-color: #1f2937;
                color: #ffffff;
                border: 1px solid #374151;
                border-radius: 5px;
                padding: 6px 10px;
            }
        """)
        font_row.addWidget(self.font_combo)
        font_row.addStretch()
        overlay_layout.addLayout(font_row)
        
        # Font size
        from PyQt6.QtWidgets import QSlider
        size_row = QHBoxLayout()
        size_label = QLabel("Font Size:")
        size_label.setStyleSheet("color: #e5e7eb; font-size: 14px; font-weight: normal;")
        size_label.setFixedWidth(120)
        size_row.addWidget(size_label)
        
        self.font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_size_slider.setMinimum(8)
        self.font_size_slider.setMaximum(24)
        self.font_size_slider.setValue(12)
        self.font_size_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #374151;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #3b82f6;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
        """)
        size_row.addWidget(self.font_size_slider)
        
        self.font_size_value = QLabel("12")
        self.font_size_value.setStyleSheet("color: #3b82f6; font-size: 14px; font-weight: bold; min-width: 30px;")
        self.font_size_slider.valueChanged.connect(lambda v: self.font_size_value.setText(str(v)))
        size_row.addWidget(self.font_size_value)
        overlay_layout.addLayout(size_row)
        
        # Background opacity
        opacity_row = QHBoxLayout()
        opacity_label = QLabel("BG Opacity:")
        opacity_label.setStyleSheet("color: #e5e7eb; font-size: 14px; font-weight: normal;")
        opacity_label.setFixedWidth(120)
        opacity_row.addWidget(opacity_label)
        
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(90)
        self.opacity_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #374151;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #10b981;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
        """)
        opacity_row.addWidget(self.opacity_slider)
        
        self.opacity_value = QLabel("90%")
        self.opacity_value.setStyleSheet("color: #10b981; font-size: 14px; font-weight: bold; min-width: 40px;")
        self.opacity_slider.valueChanged.connect(lambda v: self.opacity_value.setText(f"{v}%"))
        opacity_row.addWidget(self.opacity_value)
        overlay_layout.addLayout(opacity_row)
        
        # Color scheme
        color_row = QHBoxLayout()
        color_label = QLabel("Color Scheme:")
        color_label.setStyleSheet("color: #e5e7eb; font-size: 14px; font-weight: normal;")
        color_label.setFixedWidth(120)
        color_row.addWidget(color_label)
        
        self.color_combo = QComboBox()
        self.color_combo.addItems(["White on Black", "Black on White", "Yellow on Purple", "Blue on Dark"])
        self.color_combo.setCurrentText("Black on White")
        self.color_combo.setStyleSheet("""
            QComboBox {
                background-color: #1f2937;
                color: #ffffff;
                border: 1px solid #374151;
                border-radius: 5px;
                padding: 6px 10px;
            }
        """)
        color_row.addWidget(self.color_combo)
        color_row.addStretch()
        overlay_layout.addLayout(color_row)
        
        overlay_group.setLayout(overlay_layout)
        layout.addWidget(overlay_group)
        
        # Apply button for theme and overlay settings
        apply_btn = QPushButton("✓ Apply All Settings")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
        """)
        apply_btn.clicked.connect(self._apply_all_settings)
        layout.addWidget(apply_btn)
        
        # Stretch at bottom
        layout.addStretch()
        
        # Set scroll content
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
    
    def _on_source_language_changed(self, lang_name: str):
        """Handle source language change"""
        lang_code = LanguageConfig.get_language_code(lang_name)
        
        # Update OCR service
        if hasattr(self.app, 'ocr_service') and self.app.ocr_service:
            self.app.ocr_service.set_source_language(lang_code)
        
        print(f"[SettingsTab] Source language: {lang_name} ({lang_code})")
    
    def _on_target_language_changed(self, lang_name: str):
        """Handle target language change"""
        lang_code = LanguageConfig.get_language_code(lang_name)
        trans_code = LanguageConfig.get_translation_code(lang_code)
        
        # Update translation service
        if hasattr(self.app, 'translation_service') and self.app.translation_service:
            # Set target language for translation
            self.app.translation_service.target_lang = trans_code
            print(f"[SettingsTab] Translation target: {lang_name} ({lang_code} → {trans_code})")
        
        print(f"[SettingsTab] Target language: {lang_name} ({lang_code})")
    
    def _on_theme_changed(self, theme_name: str):
        """Handle theme change"""
        from config.theme_config import theme_config
        
        # Update theme config
        theme_config.set_theme(theme_name)
        print(f"[SettingsTab] Theme selected: {theme_name}")
    
    def _apply_all_settings(self):
        """Apply all settings (theme + overlay) when Apply button clicked"""
        from config.overlay_config import overlay_config
        from config.theme_config import theme_config
        from PyQt6.QtWidgets import QMessageBox
        
        # Get theme value
        theme_name = self.theme_combo.currentText()
        
        # Get overlay values
        font_family = self.font_combo.currentText()
        font_size = self.font_size_slider.value()
        color_scheme = self.color_combo.currentText()
        opacity = self.opacity_slider.value()
        
        # Update theme config
        theme_config.set_theme(theme_name)
        
        # Update overlay config
        overlay_config.update_font(font_family, font_size)
        overlay_config.update_colors(color_scheme, opacity)
        
        # Apply theme to entire application
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.setStyleSheet(theme_config.get_stylesheet())
            print(f"[SettingsTab] Applied {theme_name} theme to entire application")
        
        # Force main window repaint
        if hasattr(self.app, 'main_window'):
            self.app.main_window.update()
        
        # Force overlay refresh if exists
        if hasattr(self.app, 'overlay_service') and self.app.overlay_service:
            overlay = self.app.overlay_service.positioned_overlay
            if overlay and hasattr(overlay, 'region_widgets'):
                for widget in overlay.region_widgets:
                    widget.update()  # Trigger Qt repaint
                print(f"[SettingsTab] Applied overlay settings: {font_family} {font_size}pt, {color_scheme}, {opacity}%")
        
        # Show confirmation
        QMessageBox.information(self, "Settings Applied", 
                               f"All settings updated!\n\nTheme: {theme_name}\nFont: {font_family} {font_size}pt\nColors: {color_scheme}\nOpacity: {opacity}%")
