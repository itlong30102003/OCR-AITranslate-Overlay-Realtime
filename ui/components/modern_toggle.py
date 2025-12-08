"""Modern Toggle - iOS-style toggle switch component with animated knob"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, pyqtSignal, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush


class ModernToggle(QWidget):
    """Modern iOS-style toggle switch with animated white knob"""
    
    # Signal emitted when checked state changes
    toggled = pyqtSignal(bool)
    stateChanged = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(56, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # State
        self._checked = False
        self._enabled = True
        
        # Animation
        self._knob_position = 4  # Start position (left)
        self._animation = QPropertyAnimation(self, b"knob_position", self)
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        # Colors
        self._bg_on = QColor("#5B53F6")  # Purple/blue when ON
        self._bg_off = QColor("#475569")  # Gray when OFF
        self._bg_disabled = QColor("#334155")  # Darker gray when disabled
        self._knob_color = QColor("#FFFFFF")  # White knob
        self._border_color = QColor("#3D3699")  # Darker border
        
    def isChecked(self) -> bool:
        return self._checked
    
    def setChecked(self, checked: bool):
        if self._checked != checked:
            self._checked = checked
            self._animate_knob()
            self.toggled.emit(checked)
            self.stateChanged.emit(1 if checked else 0)
            self.update()
    
    def isEnabled(self) -> bool:
        return self._enabled
    
    def setEnabled(self, enabled: bool):
        self._enabled = enabled
        self.setCursor(Qt.CursorShape.PointingHandCursor if enabled else Qt.CursorShape.ForbiddenCursor)
        self.update()
    
    def toggle(self):
        if self._enabled:
            self.setChecked(not self._checked)
    
    @pyqtProperty(float)
    def knob_position(self):
        return self._knob_position
    
    @knob_position.setter
    def knob_position(self, pos):
        self._knob_position = pos
        self.update()
    
    def _animate_knob(self):
        """Animate knob from current position to target"""
        knob_size = self.height() - 8
        start = self._knob_position
        end = self.width() - knob_size - 4 if self._checked else 4
        
        self._animation.stop()
        self._animation.setStartValue(start)
        self._animation.setEndValue(end)
        self._animation.start()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._enabled:
            self.toggle()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dimensions
        w = self.width()
        h = self.height()
        radius = h / 2
        
        # Background color based on state
        if not self._enabled:
            bg_color = self._bg_disabled
        elif self._checked:
            bg_color = self._bg_on
        else:
            bg_color = self._bg_off
        
        # Draw border (slightly larger rounded rect)
        border_rect = QRectF(0, 0, w, h)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self._border_color if self._checked else QColor("#374151")))
        painter.drawRoundedRect(border_rect, radius, radius)
        
        # Draw background (inner rounded rect)
        bg_rect = QRectF(2, 2, w - 4, h - 4)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(bg_rect, radius - 2, radius - 2)
        
        # Draw knob (white circle)
        knob_size = h - 8
        knob_y = 4
        knob_rect = QRectF(self._knob_position, knob_y, knob_size, knob_size)
        
        # Knob shadow
        shadow_rect = QRectF(self._knob_position + 1, knob_y + 1, knob_size, knob_size)
        painter.setBrush(QBrush(QColor(0, 0, 0, 30)))
        painter.drawEllipse(shadow_rect)
        
        # Knob
        knob_color = self._knob_color if self._enabled else QColor("#9CA3AF")
        painter.setBrush(QBrush(knob_color))
        painter.drawEllipse(knob_rect)
        
        painter.end()


class ModernToggleWithLabel(ModernToggle):
    """Toggle with built-in label styling for mode cards"""
    
    def __init__(self, label_text: str = "", parent=None):
        super().__init__(parent)
        self.label_text = label_text
