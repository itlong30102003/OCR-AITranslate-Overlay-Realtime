"""History Tab - Display translation history"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QTableWidget, QTableWidgetItem,
                             QPushButton, QHeaderView, QMessageBox, QFileDialog,
                             QComboBox)
from PyQt6.QtCore import Qt
from firebase.local_history_service import LocalHistoryService
from PyQt6.QtCore import QTimer
import csv


class HistoryTab(QWidget):
    """Translation history tab"""

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.history_service = LocalHistoryService()
        self.current_history = []
        self.init_ui()
        self.load_history()

        # No auto-refresh timer - only refresh when needed

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Header with search
        header_layout = QHBoxLayout()

        title = QLabel("Lịch sử dịch")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm kiếm...")
        self.search_input.setFixedWidth(300)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #1f2937;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 8px 12px;
                color: #e5e7eb;
            }
        """)
        self.search_input.textChanged.connect(self.search_history)
        header_layout.addWidget(self.search_input)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #374151;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        refresh_btn.clicked.connect(self.load_history)
        header_layout.addWidget(refresh_btn)

        # Sync Now button
        sync_btn = QPushButton("☁️ Sync Now")
        sync_btn.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #047857;
            }
        """)
        sync_btn.clicked.connect(self.sync_now)
        header_layout.addWidget(sync_btn)

        layout.addLayout(header_layout)

        # Statistics
        stats_layout = QHBoxLayout()
        self.total_label = QLabel("Total: 0")
        self.total_label.setStyleSheet("color: #9ca3af; font-size: 13px;")
        stats_layout.addWidget(self.total_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # History table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Time", "Source Text", "Translation", "Lang", "Model", "Actions"
        ])

        # Table styling
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1f2937;
                border: 1px solid #374151;
                border-radius: 6px;
                color: #e5e7eb;
                gridline-color: #374151;
            }
            QHeaderView::section {
                background-color: #111827;
                color: #9ca3af;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #2563eb;
            }
        """)

        # Column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 100)

        # Table settings
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)

        layout.addWidget(self.table)

        # Action buttons
        btn_layout = QHBoxLayout()

        export_btn = QPushButton("📥 Export CSV")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        export_btn.clicked.connect(self.export_csv)
        btn_layout.addWidget(export_btn)

        clear_btn = QPushButton("🗑️ Clear History")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #b91c1c;
            }
        """)
        clear_btn.clicked.connect(self.clear_history)
        btn_layout.addWidget(clear_btn)

        btn_layout.addStretch()

        layout.addLayout(btn_layout)

    def load_history(self):
        """Load translation history from Firebase"""
        try:
            self.current_history = self.history_service.get_user_history(self.user_id, limit=100)

            self.table.setRowCount(len(self.current_history))

            for row, item in enumerate(self.current_history):
                # Time
                time_str = item['timestamp'].strftime('%H:%M:%S')
                time_item = QTableWidgetItem(time_str)
                time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 0, time_item)

                # Source text (truncate if too long)
                source = item.get('sourceText', '')
                if len(source) > 50:
                    source = source[:50] + "..."
                self.table.setItem(row, 1, QTableWidgetItem(source))

                # Translation (truncate if too long)
                translation = item.get('translatedText', '')
                if len(translation) > 50:
                    translation = translation[:50] + "..."
                self.table.setItem(row, 2, QTableWidgetItem(translation))

                # Language pair
                lang_pair = f"{item.get('sourceLang', '')} → {item.get('targetLang', '')}"
                lang_item = QTableWidgetItem(lang_pair)
                lang_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 3, lang_item)

                # Model
                model_str = f"{item.get('modelUsed', '')} ({item.get('confidence', 0):.2f})"
                model_item = QTableWidgetItem(model_str)
                model_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 4, model_item)

                # Action buttons
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(5, 0, 5, 0)
                action_layout.setSpacing(5)

                # Delete button
                del_btn = QPushButton("🗑️")
                del_btn.setFixedSize(30, 30)
                del_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #dc2626;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #b91c1c;
                    }
                """)
                del_btn.clicked.connect(lambda _, id=item['id']: self.delete_item(id))
                action_layout.addWidget(del_btn)

                self.table.setCellWidget(row, 5, action_widget)

            # Update statistics
            self.total_label.setText(f"Total: {len(self.current_history)} translations")

            print(f"[HistoryTab] Loaded {len(self.current_history)} records")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load history: {e}")

    def search_history(self, text):
        """Filter table by search text"""
        if not text:
            # Show all rows
            for row in range(self.table.rowCount()):
                self.table.setRowHidden(row, False)
            return

        # Filter rows
        for row in range(self.table.rowCount()):
            match = False
            for col in [1, 2]:  # Source and translation columns
                item = self.table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def delete_item(self, history_id):
        """Delete history item"""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this translation?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.history_service.delete_record(history_id, self.user_id)
                self.load_history()
                QMessageBox.information(self, "Success", "Translation deleted")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {e}")

    def clear_history(self):
        """Clear all history"""
        reply = QMessageBox.question(
            self,
            "Confirm Clear",
            "Are you sure you want to delete ALL translation history?\nThis cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.history_service.clear_user_history(self.user_id)
                self.load_history()
                QMessageBox.information(self, "Success", "All history cleared")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear: {e}")

    def sync_now(self):
        """Sync history to Firebase immediately"""
        try:
            from firebase.sync_service import SyncService
            sync_service = SyncService(self.user_id)
            sync_service.force_sync_now()
            QMessageBox.information(self, "Success", "History synced to Firebase successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to sync: {e}")

    def export_csv(self):
        """Export history to CSV"""
        if not self.current_history:
            QMessageBox.warning(self, "No Data", "No history to export")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export History",
            "translation_history.csv",
            "CSV Files (*.csv)"
        )

        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Time', 'Source', 'Translation', 'Source Lang', 'Target Lang', 'Model', 'Confidence'])

                    for item in self.current_history:
                        writer.writerow([
                            item['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                            item.get('sourceText', ''),
                            item.get('translatedText', ''),
                            item.get('sourceLang', ''),
                            item.get('targetLang', ''),
                            item.get('modelUsed', ''),
                            item.get('confidence', 0)
                        ])

                QMessageBox.information(self, "Success", f"Exported {len(self.current_history)} records to {filename}")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {e}")
