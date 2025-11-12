import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QLabel

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("Test")
window.setFixedSize(300, 200)

layout = QVBoxLayout()

label = QLabel("Email:")
layout.addWidget(label)

email_input = QLineEdit()
email_input.setPlaceholderText("your@email.com")
layout.addWidget(email_input)

window.setLayout(layout)
window.show()

sys.exit(app.exec())
