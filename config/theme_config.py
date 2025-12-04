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
            QWidget {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {colors['bg_primary']},
                    stop:1 {colors['bg_secondary']}
                );
                color: {colors['text_primary']};
            }}
            
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
            }}
            
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
            
            QLineEdit, QComboBox {{
                background-color: {colors['bg_tertiary']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
                border-radius: 5px;
                padding: 8px 12px;
            }}
            
            QLabel {{
                color: {colors['text_primary']};
            }}
            
            QTableWidget {{
                background-color: {colors['bg_tertiary']};
                border: 1px solid {colors['border']};
                color: {colors['text_primary']};
                gridline-color: {colors['border']};
            }}
            
            QHeaderView::section {{
                background-color: {colors['bg_primary']};
                color: {colors['text_muted']};
                padding: 10px;
                border: none;
                font-weight: bold;
            }}
        """


# Global instance
theme_config = ThemeConfig()
