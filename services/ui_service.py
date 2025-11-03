"""UI Service - Handles user interface components"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional


class UIService:
    """Service for managing UI components"""

    def __init__(self):
        """Initialize UI Service"""
        print("[UI Service] Initialized")

    def show_main_menu(
        self,
        on_start_monitoring: Callable,
        on_show_settings: Callable,
        on_show_results: Callable,
        translation_available: bool,
        source_lang: str,
        target_lang: str,
        available_models: list
    ):
        """
        Show main menu window

        Args:
            on_start_monitoring: Callback when start monitoring is clicked
            on_show_settings: Callback when settings is clicked
            on_show_results: Callback when show results is clicked
            translation_available: Whether translation is available
            source_lang: Current source language
            target_lang: Current target language
            available_models: List of available translation models
        """
        menu_window = tk.Tk()
        menu_window.title("OCR Translation App")
        menu_window.geometry("500x400")
        menu_window.resizable(False, False)

        # Title
        title_frame = tk.Frame(menu_window)
        title_frame.pack(pady=20)
        tk.Label(
            title_frame,
            text="OCR Translation Overlay",
            font=('Arial', 16, 'bold')
        ).pack()
        tk.Label(
            title_frame,
            text="Real-time OCR and Translation",
            font=('Arial', 10)
        ).pack()

        # Status info
        status_frame = tk.Frame(menu_window)
        status_frame.pack(pady=10)

        if translation_available:
            status_text = f"Translation: {source_lang} -> {target_lang}"
            status_color = "green"
        else:
            status_text = "Translation: Not available (OCR only)"
            status_color = "orange"

        tk.Label(
            status_frame,
            text=status_text,
            fg=status_color,
            font=('Arial', 10, 'bold')
        ).pack()

        # Available models info
        if translation_available and available_models:
            models_text = f"Models: {', '.join(available_models)}"
            tk.Label(status_frame, text=models_text, font=('Arial', 9)).pack()

        # Buttons
        button_frame = tk.Frame(menu_window)
        button_frame.pack(pady=20)

        # Start monitoring button
        start_btn = tk.Button(
            button_frame,
            text="Start Monitoring",
            command=lambda: self._on_start_click(menu_window, on_start_monitoring),
            font=('Arial', 12),
            bg='#4CAF50',
            fg='white',
            width=20,
            height=2
        )
        start_btn.pack(pady=10)

        # Language settings button
        if translation_available:
            settings_btn = tk.Button(
                button_frame,
                text="Language Settings",
                command=on_show_settings,
                font=('Arial', 12),
                bg='#2196F3',
                fg='white',
                width=20,
                height=2
            )
            settings_btn.pack(pady=5)

        # View results button
        results_btn = tk.Button(
            button_frame,
            text="View Translation Results",
            command=on_show_results,
            font=('Arial', 12),
            bg='#FF9800',
            fg='white',
            width=20,
            height=2
        )
        results_btn.pack(pady=5)

        # Instructions
        instructions_frame = tk.Frame(menu_window)
        instructions_frame.pack(pady=20, padx=20, fill='x')

        tk.Label(
            instructions_frame,
            text="Instructions:",
            font=('Arial', 10, 'bold')
        ).pack(anchor='w')

        instructions = [
            "1. Click 'Start Monitoring' to select screen regions",
            "2. Drag to select areas you want to monitor",
            "3. OCR will detect text changes automatically",
            "4. Translation will be performed in real-time",
            "5. View results in the 'Translation Results' window"
        ]

        for instruction in instructions:
            tk.Label(
                instructions_frame,
                text=instruction,
                font=('Arial', 9),
                anchor='w'
            ).pack(anchor='w', padx=10)

        # Exit button
        exit_btn = tk.Button(
            menu_window,
            text="Exit",
            command=menu_window.destroy,
            font=('Arial', 10),
            bg='#f44336',
            fg='white',
            width=10
        )
        exit_btn.pack(pady=10)

        menu_window.mainloop()

    def _on_start_click(self, window: tk.Tk, callback: Callable):
        """Handle start button click"""
        window.destroy()
        callback()

    def show_language_settings(
        self,
        current_source: str,
        current_target: str,
        current_model: Optional[str],
        available_models: list,
        get_model_info_callback: Callable,
        on_save: Callable
    ):
        """
        Show language settings dialog

        Args:
            current_source: Current source language
            current_target: Current target language
            current_model: Current preferred model
            available_models: List of available models
            get_model_info_callback: Callback to get model info
            on_save: Callback when settings are saved (source, target, model)
        """
        settings_window = tk.Toplevel()
        settings_window.title("Language Settings")
        settings_window.geometry("420x380")

        # Source language
        tk.Label(settings_window, text="Source Language:").pack(pady=5)
        source_var = tk.StringVar(value=current_source)
        source_combo = ttk.Combobox(
            settings_window,
            textvariable=source_var,
            values=['auto', 'en', 'ja', 'zh', 'vi', 'fr']
        )
        source_combo.pack(pady=5)

        # Target language
        tk.Label(settings_window, text="Target Language:").pack(pady=5)
        target_var = tk.StringVar(value=current_target)
        target_combo = ttk.Combobox(
            settings_window,
            textvariable=target_var,
            values=['vi', 'en', 'ja', 'zh', 'fr']
        )
        target_combo.pack(pady=5)

        # Preferred model (optional)
        tk.Label(settings_window, text="Preferred Model (optional):").pack(pady=5)
        models_list = ['auto'] + available_models
        model_var = tk.StringVar(value=(current_model or 'auto'))
        model_combo = ttk.Combobox(
            settings_window,
            textvariable=model_var,
            values=models_list
        )
        model_combo.pack(pady=5)

        # Available models info
        tk.Label(
            settings_window,
            text="Available Models:",
            font=('Arial', 10, 'bold')
        ).pack(pady=10)
        models_text = tk.Text(settings_window, height=6, width=50)
        models_text.pack(pady=5)

        models_info = ""
        for model in available_models:
            info = get_model_info_callback(model)
            models_info += f"• {model}: {info.get('provider', 'Unknown')}\n"

        models_text.insert('1.0', models_info)
        models_text.config(state='disabled')

        def save_settings():
            source = source_var.get()
            target = target_var.get()
            chosen = model_var.get().strip().lower()
            model = None if chosen in ('', 'auto') else chosen

            on_save(source, target, model)
            settings_window.destroy()

            messagebox.showinfo(
                "Settings",
                f"Language settings updated:\nSource: {source}\nTarget: {target}\nModel: {model or 'auto'}"
            )

        tk.Button(settings_window, text="Save", command=save_settings).pack(pady=10)

    def show_no_results_message(self):
        """Show message when no translation results are available"""
        messagebox.showinfo("No Results", "No translation results yet")

    def show_translation_not_available(self):
        """Show message when translation is not available"""
        messagebox.showerror("Error", "Translation system not available")
