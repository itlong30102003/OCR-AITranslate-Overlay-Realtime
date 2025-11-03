from typing import Tuple, Dict, Optional
from PIL import Image
import tkinter as tk
from tkinter import ttk, messagebox
import sys

from capture.screen_capture import ScreenCapture
from ocr.ocr import run_ocr_on_image
from translation import TranslationManager
from translation.config import TranslationConfig
from overlay.tkinter_overlay import get_overlay


class OCRTranslationApp:
    """Ứng dụng chính kết hợp OCR và Translation"""
    
    def __init__(self):
        self.config = TranslationConfig('config.env')
        self.translation_manager = None
        self.screen_capture = None
        self.translation_window = None
        self.translation_results = {}  # Lưu kết quả translation cho mỗi region
        self._last_text_by_region: Dict[int, str] = {}
        self._last_translated_by_region: Dict[int, str] = {}
        self._scan_last_time: Dict[int, int] = {}
        self._debounce_scans = 0  # yêu cầu ổn định 0 scan trước khi dịch
        self._min_interval = 0.3  # thời gian tối thiểu giữa các lần dịch (giây)
        self._last_translate_time: Dict[int, float] = {}

        # Cài đặt mặc định
        self.source_lang = 'auto'
        self.target_lang = self.config.get('default_target_lang', 'vi')
        self.preferred_model = None  # 'gemini' | 'nllb' | 'm2m' | 'opus' | None
        self.show_overlay = True  # Enable Tkinter overlay

        # Initialize Tkinter overlay (thread-safe)
        self.overlay = get_overlay()

        print("[INFO] OCR Translation App with Tkinter Overlay")

        self._initialize_translation()
    
    def _initialize_translation(self):
        """Khởi tạo translation manager"""
        try:
            self.translation_manager = TranslationManager({
                'gemini_api_key': self.config.get_api_key('gemini')
            })
            print("[OK] Translation system initialized")
            print(f"Available models: {self.translation_manager.get_available_models()}")
        except Exception as e:
            print(f"[ERROR] Failed to initialize translation: {e}")
            self.translation_manager = None
    
    def on_region_change(self, idx: int, img: Image.Image, scan_counter: int):
        """Xử lý khi có thay đổi trong vùng - OCR + Translation"""
        try:
            # Chạy OCR
            lines = run_ocr_on_image(img)
            if not lines:
                return
            
            print(f"[OCR] Region {idx} @ scan {scan_counter}:")
            all_text = []
            
            for line in lines.values():
                txt = " ".join(line["text"]).strip()
                if not txt:
                    continue
                bbox = (line["x1"], line["y1"], line["x2"], line["y2"])
                print(f"  {txt} -> bbox={bbox}")
                all_text.append(txt)
            
            # Ghép tất cả text lại
            combined_text = " ".join(all_text).strip()
            if not combined_text:
                return
            
            # Dịch ngay sau khi có kết quả OCR
            if self.translation_manager:
                self._translate_text(idx, combined_text, scan_counter)
            
        except Exception as e:
            print(f"[OCR] Error on region {idx}: {e}")
    
    def _translate_text(self, region_idx: int, text: str, scan_counter: int):
        """Dịch text và hiển thị kết quả"""
        try:
            # Nếu người dùng chọn model cụ thể, ưu tiên dùng model đó trước
            result = None
            if self.preferred_model:
                res_specific = self.translation_manager.translate_with_model(
                    text, self.source_lang, self.target_lang, self.preferred_model
                )
                if res_specific:
                    result = res_specific
                else:
                    print(f"[TRANSLATION] Preferred model '{self.preferred_model}' failed or unavailable. Falling back...")
            if result is None:
                result = self.translation_manager.translate(text, self.source_lang, self.target_lang)
            if result:
                translated_text = result['text']
                model_used = result.get('model_used', 'unknown')
                confidence = result.get('confidence', 0)
                
                print(f"[TRANSLATION] Region {region_idx}:")
                print(f"  Original: {text}")
                print(f"  Translated: {translated_text}")
                print(f"  Model: {model_used}, Confidence: {confidence:.2f}")
                
                # Lưu kết quả để hiển thị trong UI
                self.translation_results[region_idx] = {
                    'original': text,
                    'translated': translated_text,
                    'model': model_used,
                    'confidence': confidence,
                    'scan': scan_counter
                }

                # Update overlay with new results
                if self.show_overlay:
                    try:
                        self.overlay.update_translations(self.translation_results)
                        print(f"[OVERLAY] Updated with {len(self.translation_results)} translations")
                    except Exception as e:
                        print(f"[OVERLAY] Error updating: {e}")
            else:
                print(f"[TRANSLATION] Failed to translate region {region_idx}")
                
        except Exception as e:
            print(f"[TRANSLATION] Error translating region {region_idx}: {e}")
    
    def _update_table_overlay(self):
        """Cập nhật bảng overlay với tất cả kết quả dịch (DEPRECATED - use _schedule_overlay_update)"""
        try:
            if not self.overlay_manager or not self.overlay_manager.overlay:
                return

            # Lấy overlay table widget
            table = self.overlay_manager.overlay.table

            # Clear existing rows
            table.setRowCount(0)

            # Add all translation results to table
            from PyQt6.QtWidgets import QTableWidgetItem
            from PyQt6.QtGui import QColor

            row = 0
            for region_idx in sorted(self.translation_results.keys()):
                result = self.translation_results[region_idx]

                table.insertRow(row)

                # Original text
                original_item = QTableWidgetItem(result['original'])
                original_item.setForeground(QColor("#FFFFFF"))
                table.setItem(row, 0, original_item)

                # Translated text with model info
                translated_with_info = f"{result['translated']}\n[{result['model']} - {result['confidence']:.2f}]"
                translated_item = QTableWidgetItem(translated_with_info)
                translated_item.setForeground(QColor("#4CAF50"))
                table.setItem(row, 1, translated_item)

                row += 1

            # Resize columns
            table.resizeColumnsToContents()
            table.setColumnWidth(0, 200)
            table.setColumnWidth(1, 250)

            # Show overlay if hidden
            if not self.overlay_manager.visible:
                self.overlay_manager.show_overlay()

        except Exception as e:
            print(f"[OVERLAY] Error updating table overlay: {e}")
    
    def _update_translation_ui(self, region_idx: int):
        """Cập nhật UI hiển thị kết quả translation"""
        if region_idx not in self.translation_results:
            return
        
        result = self.translation_results[region_idx]
        # TODO: Implement UI update
        pass
    
    def show_language_settings(self):
        """Hiển thị cửa sổ cài đặt ngôn ngữ"""
        if not self.translation_manager:
            messagebox.showerror("Error", "Translation system not available")
            return
        
        settings_window = tk.Toplevel()
        settings_window.title("Language Settings")
        settings_window.geometry("420x380")
        
        # Source language
        tk.Label(settings_window, text="Source Language:").pack(pady=5)
        source_var = tk.StringVar(value=self.source_lang)
        source_combo = ttk.Combobox(settings_window, textvariable=source_var, 
                                  values=['auto', 'en', 'ja', 'zh', 'vi', 'fr'])
        source_combo.pack(pady=5)
        
        # Target language
        tk.Label(settings_window, text="Target Language:").pack(pady=5)
        target_var = tk.StringVar(value=self.target_lang)
        target_combo = ttk.Combobox(settings_window, textvariable=target_var,
                                  values=['vi', 'en', 'ja', 'zh', 'fr'])
        target_combo.pack(pady=5)

        # Preferred model (optional)
        tk.Label(settings_window, text="Preferred Model (optional):").pack(pady=5)
        available_models = ['auto'] + (self.translation_manager.get_available_models() or [])
        model_var = tk.StringVar(value=(self.preferred_model or 'auto'))
        model_combo = ttk.Combobox(settings_window, textvariable=model_var, values=available_models)
        model_combo.pack(pady=5)
        
        # Available models info
        tk.Label(settings_window, text="Available Models:", font=('Arial', 10, 'bold')).pack(pady=10)
        models_text = tk.Text(settings_window, height=6, width=50)
        models_text.pack(pady=5)
        
        models = self.translation_manager.get_available_models()
        models_info = ""
        for model in models:
            info = self.translation_manager.get_model_info(model)
            models_info += f"• {model}: {info.get('provider', 'Unknown')}\n"
        
        models_text.insert('1.0', models_info)
        models_text.config(state='disabled')
        
        def save_settings():
            self.source_lang = source_var.get()
            self.target_lang = target_var.get()
            chosen = model_var.get().strip().lower()
            self.preferred_model = None if chosen in ('', 'auto') else chosen
            settings_window.destroy()
            messagebox.showinfo("Settings", f"Language settings updated:\nSource: {self.source_lang}\nTarget: {self.target_lang}\nModel: {self.preferred_model or 'auto'}")
        
        tk.Button(settings_window, text="Save", command=save_settings).pack(pady=10)
    
    def show_translation_results(self):
        """Hiển thị overlay với kết quả translation"""
        if not self.translation_results:
            messagebox.showinfo("No Results", "No translation results yet")
            return

        # Show the overlay window
        self.overlay.show()

        # Update with current results
        self.overlay.update_translations(self.translation_results)
    
    def show_main_menu(self):
        """Hiển thị menu chính"""
        menu_window = tk.Tk()
        menu_window.title("OCR Translation App")
        menu_window.geometry("500x400")
        menu_window.resizable(False, False)
        
        # Title
        title_frame = tk.Frame(menu_window)
        title_frame.pack(pady=20)
        tk.Label(title_frame, text="OCR Translation Overlay", 
                font=('Arial', 16, 'bold')).pack()
        tk.Label(title_frame, text="Real-time OCR and Translation", 
                font=('Arial', 10)).pack()
        
        # Status info
        status_frame = tk.Frame(menu_window)
        status_frame.pack(pady=10)
        
        if self.translation_manager:
            status_text = f"Translation: {self.source_lang} -> {self.target_lang}"
            status_color = "green"
        else:
            status_text = "Translation: Not available (OCR only)"
            status_color = "orange"
        
        tk.Label(status_frame, text=status_text, fg=status_color, 
                font=('Arial', 10, 'bold')).pack()
        
        # Available models info
        if self.translation_manager:
            models_text = f"Models: {', '.join(self.translation_manager.get_available_models())}"
            tk.Label(status_frame, text=models_text, font=('Arial', 9)).pack()
        
        # Buttons
        button_frame = tk.Frame(menu_window)
        button_frame.pack(pady=20)
        
        # Start monitoring button
        start_btn = tk.Button(button_frame, text="Start Monitoring", 
                            command=lambda: self._start_monitoring(menu_window),
                            font=('Arial', 12), bg='#4CAF50', fg='white',
                            width=20, height=2)
        start_btn.pack(pady=10)
        
        # Language settings button
        if self.translation_manager:
            settings_btn = tk.Button(button_frame, text="Language Settings", 
                                   command=self.show_language_settings,
                                   font=('Arial', 12), bg='#2196F3', fg='white',
                                   width=20, height=2)
            settings_btn.pack(pady=5)
        
        # View results button
        results_btn = tk.Button(button_frame, text="View Translation Results", 
                              command=self.show_translation_results,
                              font=('Arial', 12), bg='#FF9800', fg='white',
                              width=20, height=2)
        results_btn.pack(pady=5)
        
        # Overlay toggle button (ẩn để chỉ hiển thị terminal output)
        
        # Instructions
        instructions_frame = tk.Frame(menu_window)
        instructions_frame.pack(pady=20, padx=20, fill='x')
        
        tk.Label(instructions_frame, text="Instructions:", 
                font=('Arial', 10, 'bold')).pack(anchor='w')
        
        instructions = [
            "1. Click 'Start Monitoring' to select screen regions",
            "2. Drag to select areas you want to monitor",
            "3. OCR will detect text changes automatically",
            "4. Translation will be performed in real-time",
            "5. View results in the 'Translation Results' window"
        ]
        
        for instruction in instructions:
            tk.Label(instructions_frame, text=instruction, 
                    font=('Arial', 9), anchor='w').pack(anchor='w', padx=10)
        
        # Exit button
        exit_btn = tk.Button(menu_window, text="Exit", 
                           command=menu_window.destroy,
                           font=('Arial', 10), bg='#f44336', fg='white',
                           width=10)
        exit_btn.pack(pady=10)
        
        menu_window.mainloop()
    
    def _toggle_overlay(self, button):
        """Bật/tắt overlay"""
        self.show_overlay = not self.show_overlay
        button.config(text="Disable Overlay" if self.show_overlay else "Enable Overlay")
        
        # Đóng tất cả overlay hiện tại nếu tắt
        if not self.show_overlay:
            for region_idx in list(self.overlay_windows.keys()):
                self._close_overlay(region_idx)
    
    def _start_monitoring(self, menu_window):
        """Bắt đầu monitoring và đóng menu"""
        menu_window.destroy()
        self.start_capture()
    
    def start_capture(self):
        """Bắt đầu chụp màn hình và theo dõi"""
        if not self.translation_manager:
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
