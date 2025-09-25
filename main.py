from typing import Tuple
from PIL import Image

from capture.screen_capture import ScreenCapture
from ocr.ocr import run_ocr_on_image


def on_region_change(idx: int, img: Image.Image, scan_counter: int):
    """Nhận ảnh vùng khi có thay đổi và gọi OCR cho vùng đó."""
    try:
        lines = run_ocr_on_image(img)
        if not lines:
            return
        print(f"[OCR] Region {idx} @ scan {scan_counter}:")
        for line in lines.values():
            txt = " ".join(line["text"]).strip()
            if not txt:
                continue
            bbox = (line["x1"], line["y1"], line["x2"], line["y2"])
            print(f"  {txt} -> bbox={bbox}")
    except Exception as e:
        print(f"[OCR] Error on region {idx}: {e}")


def main():
    sc = ScreenCapture(on_capture=None, on_region_change=on_region_change)
    sc.start_capture()


if __name__ == "__main__":
    main()
