"""Settings Tab - Application settings and preferences"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGroupBox, QComboBox, QFrame,
                             QScrollArea, QCheckBox, QSlider, QMessageBox)
from PyQt6.QtCore import Qt
from config.theme_config import theme_config


class SettingsTab(QWidget):
    """Tab for application settings"""
    
    def __init__(self, app_instance):
        super().__init__()
        self.app = app_instance
        self.init_ui()
    
    def init_ui(self):
        """Initialize settings UI"""
        # Main layout with scroll
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        # Content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("⚙️ Cài đặt")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(header)
        
        # === OCR SETTINGS ===
        ocr_group = QGroupBox("📷 OCR")
        ocr_layout = QVBoxLayout()
        
        ocr_info = QLabel("Các tùy chọn OCR sẽ được cập nhật sau")
        ocr_info.setStyleSheet("font-size: 13px; font-style: italic;")
        ocr_layout.addWidget(ocr_info)
        
        ocr_group.setLayout(ocr_layout)
        layout.addWidget(ocr_group)
        
        # === THEME SETTINGS ===
        theme_group = QGroupBox("🎨 Giao diện")
        theme_layout = QVBoxLayout()
        
        # Theme selector
        theme_row = QHBoxLayout()
        theme_label = QLabel("Theme:")
        theme_label.setStyleSheet("font-size: 14px;")
        theme_row.addWidget(theme_label)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setCurrentText(theme_config.current_theme)
        self.theme_combo.setMinimumWidth(200)
        theme_row.addWidget(self.theme_combo)
        theme_row.addStretch()
        theme_layout.addLayout(theme_row)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # === OVERLAY CUSTOMIZATION ===
        overlay_group = QGroupBox("📐 Tùy chỉnh Overlay")
        overlay_layout = QVBoxLayout()
        overlay_layout.setSpacing(12)
        
        # Font family
        font_row = QHBoxLayout()
        font_label = QLabel("Font:")
        font_label.setStyleSheet("font-size: 14px;")
        font_label.setFixedWidth(120)
        font_row.addWidget(font_label)
        
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Times New Roman", "Arial", "Segoe UI", "Courier New", "Georgia"])
        font_row.addWidget(self.font_combo)
        font_row.addStretch()
        overlay_layout.addLayout(font_row)
        
        # Font size
        size_row = QHBoxLayout()
        size_label = QLabel("Font Size:")
        size_label.setStyleSheet("font-size: 14px;")
        size_label.setFixedWidth(120)
        size_row.addWidget(size_label)
        
        self.font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_size_slider.setMinimum(8)
        self.font_size_slider.setMaximum(24)
        self.font_size_slider.setValue(12)
        size_row.addWidget(self.font_size_slider)
        
        self.font_size_value = QLabel("12")
        self.font_size_value.setStyleSheet("font-size: 14px; font-weight: bold; min-width: 30px;")
        self.font_size_slider.valueChanged.connect(lambda v: self.font_size_value.setText(str(v)))
        size_row.addWidget(self.font_size_value)
        overlay_layout.addLayout(size_row)
        
        # Background opacity
        opacity_row = QHBoxLayout()
        opacity_label = QLabel("BG Opacity:")
        opacity_label.setStyleSheet("font-size: 14px;")
        opacity_label.setFixedWidth(120)
        opacity_row.addWidget(opacity_label)
        
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(90)
        opacity_row.addWidget(self.opacity_slider)
        
        self.opacity_value = QLabel("90%")
        self.opacity_value.setStyleSheet("font-size: 14px; font-weight: bold; min-width: 40px;")
        self.opacity_slider.valueChanged.connect(lambda v: self.opacity_value.setText(f"{v}%"))
        opacity_row.addWidget(self.opacity_value)
        overlay_layout.addLayout(opacity_row)
        
        # Color scheme
        color_row = QHBoxLayout()
        color_label = QLabel("Color Scheme:")
        color_label.setStyleSheet("font-size: 14px;")
        color_label.setFixedWidth(120)
        color_row.addWidget(color_label)
        
        self.color_combo = QComboBox()
        self.color_combo.addItems(["White on Black", "Black on White", "Yellow on Purple", "Blue on Dark"])
        self.color_combo.setCurrentText("Black on White")
        color_row.addWidget(self.color_combo)
        color_row.addStretch()
        overlay_layout.addLayout(color_row)
        
        overlay_group.setLayout(overlay_layout)
        layout.addWidget(overlay_group)
        
        # Apply button
        colors = theme_config.get_colors()
        apply_btn = QPushButton("✓ Apply All Settings")
        apply_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['success']};
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
        """)
        apply_btn.clicked.connect(self._apply_all_settings)
        layout.addWidget(apply_btn)
        
        # Stretch at bottom
        layout.addStretch()
        
        # Set scroll content
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
    
    def _apply_all_settings(self):
        """Apply all settings (theme + overlay) when Apply button clicked"""
        from config.overlay_config import overlay_config
        from PyQt6.QtWidgets import QApplication
        
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
        
        # Apply theme stylesheet to entire application
        app = QApplication.instance()
        if app:
            stylesheet = theme_config.get_stylesheet()
            app.setStyleSheet(stylesheet)
            print(f"[SettingsTab] Applied {theme_name} theme to entire application")
        
        # Force overlay refresh if exists
        if hasattr(self.app, 'overlay_service') and self.app.overlay_service:
            overlay = self.app.overlay_service.positioned_overlay
            if overlay and hasattr(overlay, 'region_widgets'):
                for widget in overlay.region_widgets:
                    widget.update()
                print(f"[SettingsTab] Applied overlay settings: {font_family} {font_size}pt, {color_scheme}, {opacity}%")
        
        # Show confirmation
        QMessageBox.information(self, "Settings Applied", 
                               f"All settings updated!\n\nTheme: {theme_name}\nFont: {font_family} {font_size}pt\nColors: {color_scheme}\nOpacity: {opacity}%")
