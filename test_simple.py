"""
Simple test to verify overlay shows up
"""

import sys
from PyQt6.QtWidgets import QApplication
from overlay.overlay_table_demo import get_demo_manager

print("=" * 50)
print("Simple Overlay Test")
print("=" * 50)

# Create Qt app
app = QApplication(sys.argv)
print("[1] QApplication created")

# Get overlay manager
manager = get_demo_manager()
print("[2] Overlay manager obtained")

# Initialize
manager.initialize(app)
print("[3] Overlay manager initialized")

# Show overlay
manager.show_overlay()
print("[4] Overlay shown - should be visible on screen now!")

print("\n" + "=" * 50)
print("If you see the overlay window, it's working!")
print("Press Ctrl+C to exit")
print("=" * 50)

# Run
sys.exit(app.exec())
