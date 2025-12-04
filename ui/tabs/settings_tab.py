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
