"""Theme configuration for app-wide theming"""

class ThemeConfig:
    """Singleton config for app theme"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.current_theme = "Dark"  # Default theme
        
        # Dark theme colors
        self.DARK_THEME = {
            'bg_primary': '#0f172a',      # Very dark blue-gray
            'bg_secondary': '#1e293b',     # Dark slate
            'bg_tertiary': '#1f2937',      # Slightly lighter
            'border': '#374151',           # Border color
            'text_primary': '#ffffff',     # White text
            'text_secondary': '#e5e7eb',   # Light gray
            'text_muted': '#9ca3af',       # Muted gray
            'accent': '#3b82f6',           # Blue accent
            'accent_hover': '#2563eb',     # Darker blue
            'success': '#10b981',          # Green
            'danger': '#dc2626',           # Red
        }
        
        # Light theme colors
        self.LIGHT_THEME = {
            'bg_primary': '#ffffff',       # White
            'bg_secondary': '#f9fafb',     # Very light gray
            'bg_tertiary': '#f3f4f6',      # Light gray
            'border': '#e5e7eb',           # Light border
            'text_primary': '#111827',     # Almost black
            'text_secondary': '#374151',   # Dark gray
            'text_muted': '#6b7280',       # Medium gray
            'accent': '#3b82f6',           # Blue accent (same)
            'accent_hover': '#2563eb',     # Darker blue (same)
            'success': '#10b981',          # Green (same)
            'danger': '#dc2626',           # Red (same)
        }
        
        self._initialized = True
    
    def get_colors(self):
        """Get current theme colors"""
        if self.current_theme == "Light":
            return self.LIGHT_THEME
        return self.DARK_THEME
    
    def set_theme(self, theme_name: str):
        """Set theme (Dark/Light)"""
        if theme_name in ["Dark", "Light"]:
            self.current_theme = theme_name
            print(f"[ThemeConfig] Theme set to: {theme_name}")
            return True
        return False
    
    def get_stylesheet(self):
        """Generate complete stylesheet for current theme"""
        colors = self.get_colors()
        
        return f"""
            /* Main Window */
            QMainWindow {{
                background-color: {colors['bg_primary']};
                color: {colors['text_primary']};
            }}
            
            /* General Widgets */
            QWidget {{
                background-color: {colors['bg_primary']};
                color: {colors['text_primary']};
            }}
            
            /* Labels */
            QLabel {{
                color: {colors['text_primary']};
                background-color: transparent;
            }}
            
            /* GroupBox */
            QGroupBox {{
                font-size: 16px;
                font-weight: bold;
                color: {colors['text_primary']};
                border: 2px solid {colors['border']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: {colors['bg_secondary']};
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
                color: {colors['text_primary']};
            }}
            
            /* Buttons */
            QPushButton {{
                background-color: {colors['accent']};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
            }}
            
            QPushButton:hover {{
                background-color: {colors['accent_hover']};
            }}
            
            QPushButton:pressed {{
                background-color: {colors['accent']};
            }}
            
            QPushButton:disabled {{
                background-color: {colors['border']};
                color: {colors['text_muted']};
            }}
            
            /* Line Edit */
            QLineEdit {{
                background-color: {colors['bg_tertiary']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
                border-radius: 5px;
                padding: 8px 12px;
            }}
            
            QLineEdit:focus {{
                border: 1px solid {colors['accent']};
            }}
            
            /* ComboBox */
            QComboBox {{
                background-color: {colors['bg_tertiary']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
                border-radius: 5px;
                padding: 8px 12px;
            }}
            
            QComboBox:hover {{
                border: 1px solid {colors['accent']};
            }}
            
            QComboBox::drop-down {{
                border: none;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {colors['bg_tertiary']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
                selection-background-color: {colors['accent']};
            }}
            
            /* Slider */
            QSlider::groove:horizontal {{
                background: {colors['border']};
                height: 6px;
                border-radius: 3px;
            }}
            
            QSlider::handle:horizontal {{
                background: {colors['accent']};
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            
            QSlider::handle:horizontal:hover {{
                background: {colors['accent_hover']};
            }}
            
            /* Table Widget */
            QTableWidget {{
                background-color: {colors['bg_tertiary']};
                border: 1px solid {colors['border']};
                color: {colors['text_primary']};
                gridline-color: {colors['border']};
            }}
            
            QTableWidget::item {{
                color: {colors['text_primary']};
            }}
            
            QTableWidget::item:selected {{
                background-color: {colors['accent']};
                color: white;
            }}
            
            QHeaderView::section {{
                background-color: {colors['bg_secondary']};
                color: {colors['text_secondary']};
                padding: 10px;
                border: none;
                font-weight: bold;
            }}
            
            /* ScrollBar */
            QScrollBar:vertical {{
                background: {colors['bg_secondary']};
                width: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:vertical {{
                background: {colors['border']};
                border-radius: 6px;
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background: {colors['accent']};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            /* Tab Widget */
            QTabWidget::pane {{
                border: 1px solid {colors['border']};
                background-color: {colors['bg_secondary']};
            }}
            
            QTabBar::tab {{
                background-color: {colors['bg_tertiary']};
                color: {colors['text_secondary']};
                padding: 10px 20px;
                border: 1px solid {colors['border']};
            }}
            
            QTabBar::tab:selected {{
                background-color: {colors['accent']};
                color: white;
            }}
            
            QTabBar::tab:hover {{
                background-color: {colors['bg_secondary']};
            }}
            
            /* Text Edit */
            QTextEdit, QPlainTextEdit {{
                background-color: {colors['bg_tertiary']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
                border-radius: 5px;
            }}
            
            /* Progress Bar */
            QProgressBar {{
                background-color: {colors['bg_tertiary']};
                border: 1px solid {colors['border']};
                border-radius: 5px;
                text-align: center;
                color: {colors['text_primary']};
            }}
            
            QProgressBar::chunk {{
                background-color: {colors['accent']};
                border-radius: 5px;
            }}
        """


# Global instance
theme_config = ThemeConfig()
