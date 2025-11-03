"""
Test script for table overlay integration
Demonstrates how the overlay will display translation results
"""

import sys
from PyQt6.QtWidgets import QApplication, QTableWidgetItem
from PyQt6.QtGui import QColor
from PyQt6.QtCore import QTimer
from overlay.overlay_table_demo import get_demo_manager

def test_overlay():
    """Test the overlay with sample translation data"""
    # Initialize Qt application
    app = QApplication(sys.argv)

    # Get overlay manager
    manager = get_demo_manager()
    manager.initialize(app)

    # Show overlay
    manager.show_overlay()

    # Simulate translation results
    sample_results = [
        {
            'original': 'Hello World',
            'translated': 'Xin chào thế giới',
            'model': 'gemini',
            'confidence': 0.95
        },
        {
            'original': 'Good morning',
            'translated': 'Chào buổi sáng',
            'model': 'nllb',
            'confidence': 0.88
        },
        {
            'original': 'Thank you very much',
            'translated': 'Cảm ơn rất nhiều',
            'model': 'gemini',
            'confidence': 0.92
        },
        {
            'original': 'How are you?',
            'translated': 'Bạn khỏe không?',
            'model': 'opus',
            'confidence': 0.85
        }
    ]

    # Convert sample_results to the format expected by _perform_table_update
    translation_results = {}
    for idx, result in enumerate(sample_results):
        translation_results[idx] = result

    # Update table using the same method as main.py
    manager.overlay._perform_table_update(translation_results)

    print("[OK] Overlay table is now displaying!")
    print("[OK] Sample translation results loaded")
    print("[INFO] You can drag the overlay window to move it")
    print("[INFO] Click the X button to hide it")
    print("\nPress Ctrl+C in terminal to exit")

    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    test_overlay()
