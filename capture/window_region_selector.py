"""
Interactive Window Region Selector
Allows user to select a region within a target window using mouse
"""

import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from typing import Optional, Tuple
import win32gui


class WindowRegionSelector:
    """Interactive region selector for a target window"""

    def __init__(self, window_capture):
        """
        Initialize region selector

        Args:
            window_capture: WindowCapture instance
        """
        self.window_capture = window_capture
        self.selected_region = None
        self.start_x = None
        self.start_y = None
        self.rect_id = None

    def select_region(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Show interactive region selector

        Returns:
            (x, y, width, height) or None if cancelled
        """
        # Capture current window
        image = self.window_capture.capture_window()

        if image is None:
            messagebox.showerror("Error", "Failed to capture window")
            return None

        # Create Tkinter window for selection
        root = tk.Tk()
        root.title("Select Region - Click and drag to select area")

        # Get window info
        hwnd = self.window_capture.hwnd
        window_title = win32gui.GetWindowText(hwnd)
        root.title(f"Select Region - {window_title}")

        # Calculate display size (scale down if too large)
        img_width, img_height = image.size
        max_display_width = 1200
        max_display_height = 800

        scale = 1.0
        if img_width > max_display_width or img_height > max_display_height:
            scale_w = max_display_width / img_width
            scale_h = max_display_height / img_height
            scale = min(scale_w, scale_h)

        display_width = int(img_width * scale)
        display_height = int(img_height * scale)

        # Resize image for display
        display_image = image.resize((display_width, display_height), Image.LANCZOS)
        photo = ImageTk.PhotoImage(display_image)

        # Create canvas
        canvas = tk.Canvas(root, width=display_width, height=display_height)
        canvas.pack()

        # Display image
        canvas.create_image(0, 0, anchor=tk.NW, image=photo)

        # Instructions label
        instruction = tk.Label(
            root,
            text="Click and drag to select region | ESC: Full window | Enter: Confirm",
            font=("Arial", 10),
            bg="yellow",
            fg="black"
        )
        instruction.pack(fill=tk.X)

        # Variables for selection
        selection = {
            'start_x': None,
            'start_y': None,
            'rect_id': None,
            'confirmed': False,
            'cancelled': False
        }

        def on_mouse_down(event):
            """Mouse down - start selection"""
            selection['start_x'] = event.x
            selection['start_y'] = event.y

            # Remove previous rectangle
            if selection['rect_id']:
                canvas.delete(selection['rect_id'])

        def on_mouse_drag(event):
            """Mouse drag - update selection"""
            if selection['start_x'] is None:
                return

            # Remove previous rectangle
            if selection['rect_id']:
                canvas.delete(selection['rect_id'])

            # Draw new rectangle
            x1 = min(selection['start_x'], event.x)
            y1 = min(selection['start_y'], event.y)
            x2 = max(selection['start_x'], event.x)
            y2 = max(selection['start_y'], event.y)

            selection['rect_id'] = canvas.create_rectangle(
                x1, y1, x2, y2,
                outline='red',
                width=2
            )

        def on_key_press(event):
            """Key press handler"""
            if event.keysym == 'Return':  # Enter
                selection['confirmed'] = True
                root.quit()
            elif event.keysym == 'Escape':  # ESC - full window
                selection['cancelled'] = True
                root.quit()

        # Bind events
        canvas.bind('<ButtonPress-1>', on_mouse_down)
        canvas.bind('<B1-Motion>', on_mouse_drag)
        root.bind('<Key>', on_key_press)

        # Focus for keyboard events
        root.focus_set()

        # Run event loop
        root.mainloop()

        # Process result
        if selection['cancelled']:
            root.destroy()
            return None  # Full window

        if not selection['confirmed'] or selection['rect_id'] is None:
            root.destroy()
            return None

        # Get rectangle coordinates
        coords = canvas.coords(selection['rect_id'])
        root.destroy()

        if not coords or len(coords) != 4:
            return None

        # Convert display coordinates back to original image coordinates
        x1 = int(coords[0] / scale)
        y1 = int(coords[1] / scale)
        x2 = int(coords[2] / scale)
        y2 = int(coords[3] / scale)

        # Calculate region (x, y, width, height)
        region_x = x1
        region_y = y1
        region_width = x2 - x1
        region_height = y2 - y1

        # Validate region size
        if region_width < 10 or region_height < 10:
            messagebox.showwarning("Warning", "Selected region too small. Using full window.")
            return None

        print(f"\n[Region Selector] Selected region:")
        print(f"  Position: ({region_x}, {region_y})")
        print(f"  Size: {region_width} x {region_height}")

        return (region_x, region_y, region_width, region_height)


def select_window_region_interactive(window_capture) -> Optional[Tuple[int, int, int, int]]:
    """
    Interactive region selection for a window

    Args:
        window_capture: WindowCapture instance

    Returns:
        (x, y, width, height) or None for full window
    """
    print("\n" + "="*80)
    print("Interactive Region Selection")
    print("="*80)
    print("Instructions:")
    print("  1. Click and drag to select a region")
    print("  2. Press ENTER to confirm selection")
    print("  3. Press ESC to use full window")
    print("="*80 + "\n")

    selector = WindowRegionSelector(window_capture)
    region = selector.select_region()

    if region:
        x, y, w, h = region
        print(f"✓ Region selected: ({x}, {y}) - {w}x{h}")
    else:
        print("✓ Using full window")

    return region
