"""History Tab - Display translation history"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QTableWidget, QTableWidgetItem,
                             QPushButton, QHeaderView, QMessageBox, QFileDialog,
                             QComboBox, QDialog, QTextEdit)
from PyQt6.QtCore import Qt, QTimer
from firebase.local_history_service import LocalHistoryService
from firebase.history_service import FirebaseHistoryService
import socket
import csv


class HistoryTab(QWidget):
    """Translation history tab"""

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        # Both services - use Firebase when online, SQLite as fallback
        self.local_history_service = LocalHistoryService()
        self.firebase_history_service = FirebaseHistoryService(user_id)
        self.current_history = []
        self.init_ui()
        self.load_history()

        # No auto-refresh timer - only refresh when needed
    
    def _check_internet(self) -> bool:
        """Quick check if internet is available"""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=1)
            return True
        except (socket.timeout, socket.error):
            return False

    def init_ui(self):
        """Initialize UI"""
        # Set background for the whole tab
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0f172a,
                    stop:1 #1e293b
                );
            }
        """)
        
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
        # Set row height
        self.table.verticalHeader().setDefaultSectionSize(45)
        # Double-click to view full content
        self.table.doubleClicked.connect(self.show_full_content)

        layout.addWidget(self.table)

        # Action buttons
        btn_layout = QHBoxLayout()

        export_btn = QPushButton("📥 Export")
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
        export_btn.clicked.connect(self.export_history)
        btn_layout.addWidget(export_btn)

        clear_btn = QPushButton("Clear History")
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
        """Load translation history - Firebase when online, SQLite as fallback"""
        try:
            is_online = self._check_internet()
            
            if is_online:
                # Online: Read from Firebase
                self.current_history = self.firebase_history_service.get_user_history(self.user_id, limit=100)
                print(f"[HistoryTab] Loaded {len(self.current_history)} records from Firebase")
            else:
                # Offline: Read from SQLite
                self.current_history = self.local_history_service.get_user_history(self.user_id, limit=100)
                print(f"[HistoryTab] Loaded {len(self.current_history)} records from SQLite (offline)")

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
                del_btn = QPushButton("Delete 🗑️")
                del_btn.setFixedSize(80, 32)
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

    def show_full_content(self, index):
        """Show full content of a translation in a dialog"""
        row = index.row()
        if row < 0 or row >= len(self.current_history):
            return
        
        item = self.current_history[row]
        source_text = item.get('sourceText', '')
        translated_text = item.get('translatedText', '')
        lang_pair = f"{item.get('sourceLang', '')} → {item.get('targetLang', '')}"
        model = item.get('modelUsed', '')
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Chi tiết bản dịch")
        dialog.setMinimumSize(600, 400)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1f2937;
            }
            QLabel {
                color: #e5e7eb;
                font-size: 13px;
            }
            QTextEdit {
                background-color: #111827;
                color: #e5e7eb;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Source text section
        source_label = QLabel(f"📝 Văn bản gốc ({lang_pair.split('→')[0].strip()}):")
        source_label.setStyleSheet("font-weight: bold; color: #60a5fa;")
        layout.addWidget(source_label)
        
        source_edit = QTextEdit()
        source_edit.setPlainText(source_text)
        source_edit.setReadOnly(True)
        source_edit.setMinimumHeight(100)
        layout.addWidget(source_edit)
        
        # Translation section
        trans_label = QLabel(f"🌐 Bản dịch ({lang_pair.split('→')[1].strip()}):")
        trans_label.setStyleSheet("font-weight: bold; color: #34d399;")
        layout.addWidget(trans_label)
        
        trans_edit = QTextEdit()
        trans_edit.setPlainText(translated_text)
        trans_edit.setReadOnly(True)
        trans_edit.setMinimumHeight(100)
        layout.addWidget(trans_edit)
        
        # Info label
        info_label = QLabel(f"Model: {model} | {lang_pair}")
        info_label.setStyleSheet("color: #9ca3af; font-size: 11px;")
        layout.addWidget(info_label)
        
        # Close button
        close_btn = QPushButton("Đóng")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #374151;
                color: white;
                border: none;
                padding: 10px 30px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        dialog.exec()

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
                if self._check_internet():
                    self.firebase_history_service.delete_history(self.user_id, history_id)
                else:
                    self.local_history_service.delete_record(history_id, self.user_id)
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
                if self._check_internet():
                    self.firebase_history_service.clear_user_history(self.user_id)
                else:
                    self.local_history_service.clear_user_history(self.user_id)
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

    def export_history(self):
        """Show export format selection and export history"""
        if not self.current_history:
            QMessageBox.warning(self, "No Data", "No history to export")
            return
        
        # Create format selection dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Chọn định dạng xuất")
        dialog.setFixedSize(300, 150)
        dialog.setStyleSheet("""
            QDialog { background-color: #1f2937; }
            QLabel { color: #e5e7eb; font-size: 14px; }
            QPushButton {
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 13px;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        label = QLabel("Chọn định dạng xuất file:")
        layout.addWidget(label)
        
        btn_layout = QHBoxLayout()
        
        csv_btn = QPushButton("📄 CSV")
        csv_btn.setStyleSheet("background-color: #059669;")
        csv_btn.clicked.connect(lambda: self._do_export(dialog, "csv"))
        btn_layout.addWidget(csv_btn)
        
        pdf_btn = QPushButton("📕 PDF")
        pdf_btn.setStyleSheet("background-color: #dc2626;")
        pdf_btn.clicked.connect(lambda: self._do_export(dialog, "pdf"))
        btn_layout.addWidget(pdf_btn)
        
        layout.addLayout(btn_layout)
        dialog.exec()
    
    def _do_export(self, dialog, format_type):
        """Execute export based on format"""
        dialog.close()
        if format_type == "csv":
            self.export_to_csv()
        else:
            self.export_to_pdf()
    
    def export_to_csv(self):
        """Export history to CSV with Excel-compatible format"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export to CSV",
            "translation_history.csv",
            "CSV Files (*.csv)"
        )

        if filename:
            try:
                # Use utf-8-sig for Excel to recognize UTF-8
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    # Use semicolon (;) as delimiter which is standard for Excel in many regions (including VN/EU)
                    # Use quoting=csv.QUOTE_ALL to ensure all fields are properly wrapped
                    writer = csv.writer(f, delimiter=';', quoting=csv.QUOTE_ALL)
                    
                    # Header
                    writer.writerow(['STT', 'Thời gian', 'Văn bản gốc', 'Bản dịch', 'Ngôn ngữ nguồn', 'Ngôn ngữ đích', 'Model', 'Độ tin cậy'])

                    for idx, item in enumerate(self.current_history, 1):
                        timestamp = item['timestamp']
                        if hasattr(timestamp, 'strftime'):
                            time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            time_str = str(timestamp)
                        
                        writer.writerow([
                            idx,
                            time_str,
                            item.get('sourceText', '').replace('\n', ' '),
                            item.get('translatedText', '').replace('\n', ' '),
                            item.get('sourceLang', ''),
                            item.get('targetLang', ''),
                            item.get('modelUsed', ''),
                            f"{item.get('confidence', 0):.2f}"
                        ])

                QMessageBox.information(self, "Success", f"Đã xuất {len(self.current_history)} bản ghi ra {filename}\n(Lưu ý: Dùng dấu chấm phẩy ';' để phân cách cột)")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Lỗi xuất CSV: {e}")
    
    def export_to_pdf(self):
        """Export history to PDF with Unicode font support"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export to PDF",
            "translation_history.pdf",
            "PDF Files (*.pdf)"
        )

        if not filename:
            return
            
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            import os
            
            # Register Arial font from Windows system
            font_path = "C:\\Windows\\Fonts\\arial.ttf"
            font_name = 'Arial'
            
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('Arial', font_path))
                    print("[Export] Loaded Arial font")
                except Exception as e:
                    print(f"[Export] Failed to load Arial: {e}")
                    font_name = 'Helvetica'
            else:
                print("[Export] Arial font not found, using Helvetica")
                font_name = 'Helvetica' # Fallback (no Vietnamese support)
            
            doc = SimpleDocTemplate(filename, pagesize=landscape(A4), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
            elements = []
            
            # Styles
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontName=font_name, fontSize=16, alignment=1)
            elements.append(Paragraph("Lịch sử dịch thuật", title_style))
            elements.append(Spacer(1, 20))
            
            # Prepare data
            # Header
            header = ['STT', 'Thời gian', 'Văn bản gốc', 'Bản dịch', 'Ngôn ngữ', 'Model']
            
            # Create Paragraphs for cells to enable word wrapping
            style_body = ParagraphStyle('Body', parent=styles['Normal'], fontName=font_name, fontSize=9, leading=11)
            style_header = ParagraphStyle('Header', parent=styles['Normal'], fontName=font_name, fontSize=10, textColor=colors.white, alignment=1)
            
            data = [[Paragraph(col, style_header) for col in header]]
            
            for idx, item in enumerate(self.current_history, 1):
                timestamp = item['timestamp']
                if hasattr(timestamp, 'strftime'):
                    time_str = timestamp.strftime('%H:%M:%S\n%d/%m/%Y')
                else:
                    time_str = str(timestamp)
                
                lang = f"{item.get('sourceLang', '')}\n→{item.get('targetLang', '')}"
                
                data.append([
                    str(idx),
                    time_str,
                    Paragraph(item.get('sourceText', ''), style_body),
                    Paragraph(item.get('translatedText', ''), style_body),
                    lang,
                    item.get('modelUsed', '')
                ])
            
            # Create table with autosizing
            # Total width = approx 11 inches for A4 landscape
            col_widths = [0.4*inch, 0.9*inch, 4.0*inch, 4.0*inch, 0.8*inch, 0.8*inch]
            
            table = Table(data, colWidths=col_widths, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f3f4f6')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            
            elements.append(table)
            doc.build(elements)
            
            QMessageBox.information(self, "Success", f"Đã xuất PDF thành công: {filename}")
            
        except ImportError:
            QMessageBox.warning(self, "Missing Library", "Cần cài reportlab: pip install reportlab")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Lỗi xuất PDF: {e}")
            import traceback
            traceback.print_exc()
