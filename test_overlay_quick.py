"""Quick test for overlay display"""

import tkinter as tk
from overlay.tkinter_overlay import get_overlay

# Create main window (required for Tkinter)
root = tk.Tk()
root.withdraw()

# Get overlay
overlay = get_overlay()

# Test data
test_results = {
    0: {'translated': 'Hello World translated', 'model': 'gemini', 'confidence': 0.95},
    1: {'translated': 'Good Morning translated', 'model': 'nllb', 'confidence': 0.88},
    2: {'translated': 'Thank you very much', 'model': 'opus', 'confidence': 0.82}
}

# Update overlay
overlay.update_translations(test_results)

print("Overlay displayed! Close overlay to exit.")
root.mainloop()
