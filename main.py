from typing import Optional
from PIL import Image

from capture.screen_capture import ScreenCapture
from translation.config import TranslationConfig
from services import OCRService, TranslationService, OverlayService, UIService


class OCRTranslationApp:
    """Ứng dụng chính kết hợp OCR và Translation - Refactored with Services"""

    def __init__(self):
        # Load configuration
        self.config = TranslationConfig('config.env')

        # Initialize services
        self.ocr_service = OCRService()
        self.translation_service = TranslationService(self.config)
        self.overlay_service = OverlayService(enabled=True)
        self.ui_service = UIService()

        # Screen capture (will be initialized when monitoring starts)
        self.screen_capture = None

        print("[INFO] OCR Translation App initialized with services")
        print(f"[INFO] Translation available: {self.translation_service.is_available()}")

    def on_region_change(self, idx: int, img: Image.Image, scan_counter: int):
        """
        Callback khi có thay đổi trong vùng - OCR + Translation

        Args:
            idx: Region index
            img: PIL Image of the region
            scan_counter: Current scan counter
        """
        try:
            # Step 1: OCR processing
            text = self.ocr_service.process_image(img, idx, scan_counter)
            if not text:
                return

            # Step 2: Translation (if available)
            if self.translation_service.is_available():
                result = self.translation_service.translate(text, idx, scan_counter)

                if result:
                    # Step 3: Update overlay
                    self.overlay_service.update_translation(idx, result)

        except Exception as e:
            print(f"[App] Error processing region {idx}: {e}")

    def show_language_settings(self):
        """Hiển thị cửa sổ cài đặt ngôn ngữ"""
        if not self.translation_service.is_available():
            self.ui_service.show_translation_not_available()
            return

        settings = self.translation_service.get_settings()

        def on_save(source: str, target: str, model: Optional[str]):
            self.translation_service.set_languages(source, target)
            self.translation_service.set_preferred_model(model)

        self.ui_service.show_language_settings(
            current_source=settings['source_lang'],
            current_target=settings['target_lang'],
            current_model=settings['preferred_model'],
            available_models=self.translation_service.get_available_models(),
            get_model_info_callback=self.translation_service.get_model_info,
            on_save=on_save
        )

    def show_translation_results(self):
        """Hiển thị overlay với kết quả translation"""
        if self.overlay_service.get_result_count() == 0:
            self.ui_service.show_no_results_message()
            return

        self.overlay_service.show_results()

    def show_main_menu(self):
        """Hiển thị menu chính"""
        settings = self.translation_service.get_settings()

        self.ui_service.show_main_menu(
            on_start_monitoring=self.start_capture,
            on_show_settings=self.show_language_settings,
            on_show_results=self.show_translation_results,
            translation_available=settings['available'],
            source_lang=settings['source_lang'],
            target_lang=settings['target_lang'],
            available_models=self.translation_service.get_available_models()
        )

    def start_capture(self):
        """Bắt đầu chụp màn hình và theo dõi"""
        if not self.translation_service.is_available():
            print("[WARNING] Translation system not available, running OCR only")

        self.screen_capture = ScreenCapture(
            on_capture=None,
            on_region_change=self.on_region_change
        )

        self.screen_capture.start_capture()

    def run(self):
        """Chạy ứng dụng chính"""
        print("=== OCR Translation Overlay ===")
        print("Starting main menu...")
        self.show_main_menu()


def main():
    app = OCRTranslationApp()
    app.run()


if __name__ == "__main__":
    main()
