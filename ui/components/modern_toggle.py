"""Modern Toggle - iOS-style toggle switch component"""

from PyQt6.QtWidgets import QCheckBox
from PyQt6.QtCore import Qt


class ModernToggle(QCheckBox):
    """Modern iOS-style toggle switch"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 25)
        self._update_style()
    
    def _update_style(self):
        """Update toggle style based on enabled state"""
        if self.isEnabled():
            self.setStyleSheet("""
                QCheckBox {
                    background: transparent;
                }
                QCheckBox::indicator {
                    width: 50px;
                    height: 25px;
                    border-radius: 12px;
                    background-color: #475569;
                }
                QCheckBox::indicator:checked {
                    background-color: #6366f1;
                }
                QCheckBox::indicator:hover {
                    background-color: #5b5fc7;
                }
            """)
        else:
            # Disabled state - grayed out
            self.setStyleSheet("""
                QCheckBox {
                    background: transparent;
                }
                QCheckBox::indicator {
                    width: 50px;
                    height: 25px;
                    border-radius: 12px;
                    background-color: #334155;
                }
                QCheckBox::indicator:checked {
                    background-color: #475569;
                }
            """)
    
    def setEnabled(self, enabled: bool):
        """Override to update style when enabled state changes"""
        super().setEnabled(enabled)
        self._update_style()


class ModernToggleWithLabel(QCheckBox):
    """Toggle with built-in label styling for mode cards"""
    
    def __init__(self, label_text: str, parent=None):
        super().__init__(parent)
        self.label_text = label_text
        self.setText("")  # No text in checkbox itself
        self.setFixedSize(50, 25)
        self._update_style()
    
    def _update_style(self):
        """Update toggle style"""
        if self.isEnabled():
            self.setStyleSheet("""
                QCheckBox {
                    background: transparent;
                }
                QCheckBox::indicator {
                    width: 50px;
                    height: 25px;
                    border-radius: 12px;
                    background-color: #475569;
                }
                QCheckBox::indicator:checked {
                    background-color: #6366f1;
                }
                QCheckBox::indicator:hover {
                    background-color: #5b5fc7;
                }
            """)
        else:
            self.setStyleSheet("""
                QCheckBox {
                    background: transparent;
                }
                QCheckBox::indicator {
                    width: 50px;
                    height: 25px;
                    border-radius: 12px;
                    background-color: #334155;
                }
            """)
    
    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        self._update_style()
