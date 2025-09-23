import tkinter as tk
from PIL import ImageGrab
import threading
from typing import Callable, Tuple, List


class ScreenCapture:
    def __init__(self, on_capture: Callable[[Tuple[int, int, int, int]], None]):
        self.on_capture = on_capture
        self.start_x = self.start_y = 0
        self.canvas = None         # canvas để vẽ
        self.rect_id = None        # id của hình chữ nhật
        self.capture_window = None
        self.captured_coords: List[Tuple[int, int, int, int]] = []

    def start_capture(self):
        self._capture_loop()
        self.root.mainloop()

    def _capture_loop(self):
        # Nếu root đã tồn tại -> tạo cửa sổ mới bằng Toplevel
        if hasattr(self, "root") and self.root:
            self.capture_window = tk.Toplevel(self.root)
        else:
            self.root = tk.Tk()
            self.root.withdraw()  # ẩn cửa sổ gốc
            self.capture_window = tk.Toplevel(self.root)

        self.capture_window.attributes('-fullscreen', True)
        self.capture_window.attributes('-alpha', 0.3)
        self.capture_window.configure(background='black')

        # canvas để vẽ vùng chọn
        self.canvas = tk.Canvas(self.capture_window, cursor="cross", bg="black")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind('<ButtonPress-1>', self.on_button_press)
        self.canvas.bind('<B1-Motion>', self.on_move_press)
        self.canvas.bind('<ButtonRelease-1>', self.on_button_release)

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        # reset rectangle mới
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="red", width=2
        )

    def on_move_press(self, event):
        curX, curY = (event.x, event.y)
        # chỉ update toạ độ thay vì delete all
        if self.rect_id:
            self.canvas.coords(self.rect_id, self.start_x, self.start_y, curX, curY)

    def on_button_release(self, event):
        end_x, end_y = (event.x, event.y)
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)

        # đóng cửa sổ chọn
        self.capture_window.destroy()

        threading.Thread(target=self._capture_and_callback, args=(x1, y1, x2, y2)).start()

    def _capture_and_callback(self, x1: int, y1: int, x2: int, y2: int):
        screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        filename = f"captured_area_{len(self.captured_coords)}.png"
        screenshot.save(filename)
        self.captured_coords.append((x1, y1, x2, y2))
        if self.on_capture:
            self.on_capture((x1, y1, x2, y2))
        # Hỏi tiếp tục hay không
        if self._ask_continue():
            self._capture_loop()
        else:
            self._process_captures()

    def _ask_continue(self) -> bool:
        import tkinter.messagebox as mb
        return mb.askyesno("Tiếp tục?", "Bạn có muốn chọn vùng tiếp theo không?")

    def _process_captures(self):
        print("Các vùng đã chọn:", self.captured_coords)
        # TODO: So sánh các file captured_area_*.png và chạy OCR nếu có thay đổi


def my_callback(coords):
    print("Vùng đã chọn:", coords)
    # Có thể xử lý file captured_area_x.png ở đây.


if __name__ == "__main__":
    sc = ScreenCapture(on_capture=my_callback)
    sc.start_capture()
