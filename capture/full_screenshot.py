from PIL import ImageGrab

def capture_fullscreen():
    """Chụp toàn màn hình và trả về PIL.Image"""
    screenshot = ImageGrab.grab()
    return screenshot

if __name__ == "__main__":
    img = capture_fullscreen()
    img.show()  # chỉ hiển thị test
