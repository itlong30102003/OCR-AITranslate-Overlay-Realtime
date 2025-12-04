"""Overlay configuration for customizable appearance"""

class OverlayConfig:
    """Singleton config for overlay appearance settings"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Font settings
        self.font_family = "Times New Roman"
        self.font_size = 12
        
        # Color settings
        self.color_scheme = "Black on White"  # Default
        self.bg_opacity = 90  # 0-100
        
        # Color schemes mapping
        self.COLOR_SCHEMES = {
            "White on Black": {
                "bg_color": (0, 0, 0),
                "text_color": (255, 255, 255)
            },
            "Black on White": {
                "bg_color": (255, 255, 255),
                "text_color": (0, 0, 0)
            },
            "Yellow on Purple": {
                "bg_color": (75, 0, 130),  # Indigo
                "text_color": (255, 255, 0)  # Yellow
            },
            "Blue on Dark": {
                "bg_color": (30, 30, 50),  # Dark blue-gray
                "text_color": (100, 200, 255)  # Light blue
            }
        }
        
        self._initialized = True
    
    def get_background_color(self):
        """Get background color with opacity"""
        scheme = self.COLOR_SCHEMES.get(self.color_scheme, self.COLOR_SCHEMES["Black on White"])
        r, g, b = scheme["bg_color"]
        alpha = int(self.bg_opacity * 2.55)  # Convert 0-100 to 0-255
        return (r, g, b, alpha)
    
    def get_text_color(self):
        """Get text color (RGB)"""
        scheme = self.COLOR_SCHEMES.get(self.color_scheme, self.COLOR_SCHEMES["Black on White"])
        return scheme["text_color"]
    
    def update_font(self, family: str, size: int):
        """Update font settings"""
        self.font_family = family
        self.font_size = size
        print(f"[OverlayConfig] Font: {family} {size}pt")
    
    def update_colors(self, scheme: str, opacity: int):
        """Update color settings"""
        self.color_scheme = scheme
        self.bg_opacity = opacity
        print(f"[OverlayConfig] Colors: {scheme}, Opacity: {opacity}%")


# Global instance
overlay_config = OverlayConfig()
