from typing import Optional
from PIL import Image

from capture.screen_capture import ScreenCapture
from translation.config import TranslationConfig
from services import OCRService, TranslationService, OverlayService, UIService, AsyncProcessingService


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

        # Initialize async processing service
        self.async_service = AsyncProcessingService(
            self.ocr_service,
            self.translation_service,
            self.overlay_service
        )

        # Screen capture (will be initialized when monitoring starts)
        self.screen_capture = None

        print("[INFO] OCR Translation App initialized with services")
        print(f"[INFO] Translation available: {self.translation_service.is_available()}")
        print("[INFO] Async processing enabled for better performance")

    def on_region_change(self, idx: int, img: Image.Image, scan_counter: int):
        """
        Callback khi có thay đổi trong vùng - OCR + Translation (Async)

        Args:
            idx: Region index
            img: PIL Image of the region
            scan_counter: Current scan counter
        """
        # Process asynchronously - non-blocking, parallel execution
        self.async_service.process_region_async(idx, img, scan_counter)

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

        # Start async processing service
        print("[INFO] Starting async processing service...")
        self.async_service.start()

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
