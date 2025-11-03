"""
Simple Tkinter overlay for real-time translation display
Thread-safe and lightweight
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict


class TranslationOverlay:
    """Simple overlay window using Tkinter"""

    def __init__(self):
        self.window = None
        self.text_widgets = {}  # region_idx -> Text widget
        self.is_visible = False
        self._resize_edge = None  # Track which edge is being resized
        self._resize_start_x = 0
        self._resize_start_y = 0
        self._resize_start_width = 0
        self._resize_start_height = 0

    def create_window(self):
        """Create the overlay window"""
        if self.window is not None:
            return

        self.window = tk.Toplevel()
        self.window.overrideredirect(True)  # Remove title bar/borders
        self.window.attributes('-topmost', True)
        self.window.attributes('-alpha', 0.9)

        # Position at bottom-right
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        window_width = 500
        window_height = 300
        x = screen_width - window_width - 20
        y = screen_height - window_height - 80
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Make draggable and resizable
        self.window.bind('<Button-1>', self._on_mouse_press)
        self.window.bind('<B1-Motion>', self._on_mouse_drag)
        self.window.bind('<Motion>', self._on_mouse_move)
        self.window.bind('<ButtonRelease-1>', self._on_mouse_release)

        # Header
        header = tk.Frame(self.window, bg='#2E2E2E', height=40)
        header.pack(fill='x')

        title = tk.Label(header, text="Translation Results",
                        bg='#2E2E2E', fg='white',
                        font=('Arial', 12, 'bold'))
        title.pack(side='left', padx=10, pady=5)

        close_btn = tk.Button(header, text="×",
                             command=self.hide,
                             bg='#f44336', fg='white',
                             font=('Arial', 14, 'bold'),
                             width=3, relief='flat')
        close_btn.pack(side='right', padx=5, pady=5)

        # Scrollable content
        canvas = tk.Canvas(self.window, bg='#1E1E1E', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.window, orient="vertical", command=canvas.yview)
        self.content_frame = tk.Frame(canvas, bg='#1E1E1E')

        self.content_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.is_visible = True

    def _get_resize_edge(self, x, y):
        """Determine which edge is near the cursor for resizing"""
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()
        edge_size = 10  # pixels from edge to trigger resize

        edges = []
        if x <= edge_size:
            edges.append('left')
        elif x >= window_width - edge_size:
            edges.append('right')

        if y <= edge_size:
            edges.append('top')
        elif y >= window_height - edge_size:
            edges.append('bottom')

        return '-'.join(edges) if edges else None

    def _on_mouse_move(self, event):
        """Update cursor based on position for resize"""
        edge = self._get_resize_edge(event.x, event.y)

        if edge:
            # Set cursor for resizing
            if edge in ['left', 'right']:
                self.window.config(cursor='sb_h_double_arrow')
            elif edge in ['top', 'bottom']:
                self.window.config(cursor='sb_v_double_arrow')
            elif edge in ['top-left', 'bottom-right']:
                self.window.config(cursor='size_nw_se')
            elif edge in ['top-right', 'bottom-left']:
                self.window.config(cursor='size_ne_sw')
        else:
            self.window.config(cursor='arrow')

    def _on_mouse_press(self, event):
        """Handle mouse press for drag or resize"""
        self._resize_edge = self._get_resize_edge(event.x, event.y)

        if self._resize_edge:
            # Start resizing
            self._resize_start_x = event.x_root
            self._resize_start_y = event.y_root
            self._resize_start_width = self.window.winfo_width()
            self._resize_start_height = self.window.winfo_height()
            self._resize_start_window_x = self.window.winfo_x()
            self._resize_start_window_y = self.window.winfo_y()
        else:
            # Start dragging
            self._drag_start_x = event.x
            self._drag_start_y = event.y

    def _on_mouse_drag(self, event):
        """Handle mouse drag for move or resize"""
        if self._resize_edge:
            # Resizing
            dx = event.x_root - self._resize_start_x
            dy = event.y_root - self._resize_start_y

            new_width = self._resize_start_width
            new_height = self._resize_start_height
            new_x = self._resize_start_window_x
            new_y = self._resize_start_window_y

            if 'right' in self._resize_edge:
                new_width = max(300, self._resize_start_width + dx)
            elif 'left' in self._resize_edge:
                new_width = max(300, self._resize_start_width - dx)
                new_x = self._resize_start_window_x + dx
                if new_width == 300:
                    new_x = self._resize_start_window_x + (self._resize_start_width - 300)

            if 'bottom' in self._resize_edge:
                new_height = max(200, self._resize_start_height + dy)
            elif 'top' in self._resize_edge:
                new_height = max(200, self._resize_start_height - dy)
                new_y = self._resize_start_window_y + dy
                if new_height == 200:
                    new_y = self._resize_start_window_y + (self._resize_start_height - 200)

            self.window.geometry(f"{new_width}x{new_height}+{new_x}+{new_y}")
        else:
            # Dragging
            if hasattr(self, '_drag_start_x'):
                x = self.window.winfo_x() + event.x - self._drag_start_x
                y = self.window.winfo_y() + event.y - self._drag_start_y
                self.window.geometry(f"+{x}+{y}")

    def _on_mouse_release(self, event):
        """Handle mouse release"""
        self._resize_edge = None

    def update_translations(self, translation_results: Dict[int, dict]):
        """
        Update overlay with translation results
        Args:
            translation_results: Dict[region_idx, {original, translated, model, confidence}]
        """
        if self.window is None:
            self.create_window()

        # Clear old widgets
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.text_widgets.clear()

        # Add translation results
        for region_idx in sorted(translation_results.keys()):
            result = translation_results[region_idx]

            # Create frame for this region
            frame = tk.Frame(self.content_frame, bg='#2E2E2E', relief='raised', bd=1)
            frame.pack(fill='x', padx=5, pady=5)

            # Display: Region X: Translation
            text = f"Region {region_idx}: {result['translated']}"

            label = tk.Label(frame, text=text,
                           bg='#2E2E2E', fg='#4CAF50',
                           font=('Arial', 11),
                           wraplength=450, justify='left',
                           anchor='w')
            label.pack(fill='x', padx=10, pady=5)

            # Model info
            info = tk.Label(frame,
                          text=f"[{result['model']} - {result['confidence']:.2f}]",
                          bg='#2E2E2E', fg='#FFC107',
                          font=('Arial', 8))
            info.pack(anchor='w', padx=10, pady=(0, 5))

        # Show window if hidden
        if not self.is_visible:
            self.show()

    def show(self):
        """Show the overlay window"""
        if self.window is None:
            self.create_window()
        self.window.deiconify()
        self.window.lift()
        self.is_visible = True

    def hide(self):
        """Hide the overlay window"""
        if self.window:
            self.window.withdraw()
            self.is_visible = False

    def destroy(self):
        """Destroy the overlay window"""
        if self.window:
            self.window.destroy()
            self.window = None
            self.is_visible = False


# Global instance
_overlay_instance = None


def get_overlay() -> TranslationOverlay:
    """Get the global overlay instance"""
    global _overlay_instance
    if _overlay_instance is None:
        _overlay_instance = TranslationOverlay()
    return _overlay_instance


if __name__ == "__main__":
    # Test
    root = tk.Tk()
    root.withdraw()  # Hide main window

    overlay = get_overlay()

    # Test data
    test_results = {
        0: {'translated': 'Xin chào thế giới', 'model': 'gemini', 'confidence': 0.95},
        1: {'translated': 'Chào buổi sáng', 'model': 'nllb', 'confidence': 0.88},
        2: {'translated': 'Cảm ơn rất nhiều', 'model': 'opus', 'confidence': 0.82}
    }

    overlay.update_translations(test_results)

    print("Overlay displayed! Close window to exit.")
    root.mainloop()
