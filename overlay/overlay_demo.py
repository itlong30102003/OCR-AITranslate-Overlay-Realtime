import sys
import random
import json
from PyQt6.QtWidgets import QApplication, QLabel, QWidget
from PyQt6.QtCore import Qt, QTimer, QRect
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QFontMetrics


class OverlayText(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool  # không hiện trên taskbar
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # Load sample data from JSON
        with open("overlay/sample_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        self.texts = [{"text": item["text"], "bbox": QRect(*item["bbox"])} for item in data]

        # Timer để mô phỏng thay đổi text realtime
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_overlay)
        self.timer.start(int(1000 / 30))  # 30 FPS

        # Timer để sinh dữ liệu OCR mới mỗi vài giây
        self.ocr_timer = QTimer()
        self.ocr_timer.timeout.connect(self.simulate_new_ocr_data)
        self.ocr_timer.start(3000)  # Mỗi 3 giây sinh dữ liệu mới

        self.resize(1920, 1080)

    def update_overlay(self):
        # Giả lập bbox và text thay đổi ngẫu nhiên
        for item in self.texts:
            if random.random() < 0.3:
                dx, dy = random.randint(-3, 3), random.randint(-3, 3)
                item["bbox"].translate(dx, dy)
            if random.random() < 0.1:
                item["text"] = random.choice(["Xin chào", "Chào bạn", "Dịch xong", "Translated!"])
        self.repaint()

    def simulate_new_ocr_data(self):
        # Sinh dữ liệu OCR mới từ sample_data, xoay vòng
        with open("overlay/sample_data.json", "r", encoding="utf-8") as f:
            all_data = json.load(f)
        # Chọn ngẫu nhiên một số item từ all_data
        num_items = random.randint(3, 6)
        selected = random.sample(all_data, num_items)
        self.texts = [{"text": item["text"], "bbox": QRect(*item["bbox"])} for item in selected]
        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        font = QFont("Segoe UI", 12)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        for item in self.texts:
            text = item["text"]
            text_width = metrics.horizontalAdvance(text)
            text_height = metrics.height()
            # Tạo bbox dựa trên kích thước text
            rect = QRect(item["bbox"].x(), item["bbox"].y(), text_width + 10, text_height + 4)  # padding nhỏ

            # Vẽ nền bbox solid black
            painter.fillRect(rect, QColor(0, 0, 0))

            # Vẽ text trắng centered
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = OverlayText()
    overlay.showFullScreen()  # bao phủ toàn màn hình
    sys.exit(app.exec())
