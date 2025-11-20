"""
Export Tab (SQLite + Non-ORM Compatible Version)
Cleans up:
✔ Uses flat assignment dictionaries
✔ Safer HTML preview handling
✔ Works with rewritten Database + Scheduler
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QGroupBox, QFileDialog, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QTextDocument


try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEB_ENGINE_AVAILABLE = True
except ImportError:
    from PyQt6.QtWidgets import QTextEdit
    WEB_ENGINE_AVAILABLE = False


class ExportTab(QWidget):
    def __init__(self, pdf_exporter):
        super().__init__()
        self.pdf_exporter = pdf_exporter
        self.current_assignments = []
        self.current_timetable_info = {}
        self.init_ui()

    # ----------------------------------------------------------------------
    # UI LAYOUT
    # ----------------------------------------------------------------------
    def init_ui(self):
        layout = QVBoxLayout(self)

        # Buttons
        btn_layout = QHBoxLayout()

        self.preview_btn = QPushButton("Preview PDF")
        self.preview_btn.setEnabled(False)
        self.preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white; border: none;
                padding: 10px 20px; font-size: 14px;
                font-weight: bold; border-radius: 5px;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled { background-color: #444; color: #777; }
        """)
        self.preview_btn.clicked.connect(self.preview_pdf)
        btn_layout.addWidget(self.preview_btn)

        self.export_btn = QPushButton("Export to PDF")
        self.export_btn.setEnabled(False)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white; border: none;
                padding: 10px 20px; font-size: 14px;
                font-weight: bold; border-radius: 5px;
            }
            QPushButton:hover { background-color: #388E3C; }
            QPushButton:disabled { background-color: #444; color: #777; }
        """)
        self.export_btn.clicked.connect(self.export_to_pdf)
        btn_layout.addWidget(self.export_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Preview area
        preview_group = QGroupBox("PDF Preview")
        preview_group.setStyleSheet("""
            QGroupBox {
                color: #fff;
                font-weight: 600;
                border: 1px solid #333;
                border-radius: 6px;
                margin-top: 10px;
            }
        """)
        preview_layout = QVBoxLayout(preview_group)

        if WEB_ENGINE_AVAILABLE:
            self.preview_widget = QWebEngineView()
            self.use_web_engine = True
        else:
            self.preview_widget = QTextEdit()
            self.preview_widget.setReadOnly(True)
            self.use_web_engine = False

        preview_layout.addWidget(self.preview_widget)
        layout.addWidget(preview_group)

    # ----------------------------------------------------------------------
    # DATA INPUT
    # ----------------------------------------------------------------------
    def set_timetable(self, assignments, timetable_info):
        """Populate export tab data."""
        self.current_assignments = assignments
        self.current_timetable_info = timetable_info

        enabled = bool(assignments and timetable_info)
        self.preview_btn.setEnabled(enabled)
        self.export_btn.setEnabled(enabled)

        if enabled:
            self.preview_pdf()

    def clear_timetable(self):
        self.current_assignments = []
        self.current_timetable_info = {}

        self.preview_btn.setEnabled(False)
        self.export_btn.setEnabled(False)

        if self.use_web_engine:
            self.preview_widget.setHtml("<p>No timetable loaded</p>")
        else:
            self.preview_widget.setPlainText("No timetable loaded")

    # ----------------------------------------------------------------------
    # PREVIEW
    # ----------------------------------------------------------------------
    def preview_pdf(self):
        if not self.current_assignments:
            QMessageBox.warning(self, "Warning", "No timetable to preview.")
            return

        try:
            html = self.pdf_exporter.preview_timetable(
                self.current_assignments,
                self.current_timetable_info
            )

            if self.use_web_engine:
                self.preview_widget.setHtml(html)
            else:
                # QTextEdit does not support HTML fully, so fallback to plain
                doc = QTextDocument()
                doc.setHtml(html)
                self.preview_widget.setDocument(doc)

        except Exception as e:
            QMessageBox.critical(self, "Preview Error", str(e))

    # ----------------------------------------------------------------------
    # EXPORT
    # ----------------------------------------------------------------------
    def export_to_pdf(self):
        if not self.current_assignments:
            QMessageBox.warning(self, "Warning", "No timetable to export.")
            return

        default_name = (
            f"timetable_"
            f"{self.current_timetable_info.get('degree','')}_"
            f"{self.current_timetable_info.get('year','')}_"
            f"{self.current_timetable_info.get('semester','')}.pdf"
        )

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Timetable to PDF",
            default_name,
            "PDF Files (*.pdf);;All Files (*)"
        )

        if not file_path:
            return

        self._start_export(file_path)

    # ----------------------------------------------------------------------
    # EXPORT THREAD
    # ----------------------------------------------------------------------
    def _start_export(self, path):
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        self.preview_btn.setEnabled(False)
        self.export_btn.setEnabled(False)

        self.export_thread = ExportThread(
            self.pdf_exporter,
            self.current_assignments,
            self.current_timetable_info,
            path
        )
        self.export_thread.export_completed.connect(self._export_done)
        self.export_thread.export_failed.connect(self._export_fail)
        self.export_thread.start()

    def _export_done(self, file_path):
        self.progress_bar.setVisible(False)
        self.preview_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        QMessageBox.information(self, "Success", f"Exported to:\n{file_path}")

    def _export_fail(self, err):
        self.progress_bar.setVisible(False)
        self.preview_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        QMessageBox.critical(self, "Export Failed", err)


class ExportThread(QThread):
    export_completed = pyqtSignal(str)
    export_failed = pyqtSignal(str)

    def __init__(self, exporter, assignments, info, path):
        super().__init__()
        self.exporter = exporter
        self.assignments = assignments
        self.info = info
        self.path = path

    def run(self):
        try:
            ok = self.exporter.export_timetable(self.assignments, self.info, self.path)
            if ok:
                self.export_completed.emit(self.path)
            else:
                self.export_failed.emit("Exporter returned failure.")
        except Exception as e:
            self.export_failed.emit(str(e))
