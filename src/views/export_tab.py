"""
Export Tab for Timetable Generator

Provides full-screen PDF preview and export options.
Streamlined to maximize preview area (removed Export Options box).
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QGroupBox, QFileDialog, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEB_ENGINE_AVAILABLE = True
except ImportError:
    from PyQt6.QtWidgets import QTextEdit
    WEB_ENGINE_AVAILABLE = False


class ExportTab(QWidget):
    """PDF Export tab with full-size preview and cleaner layout."""

    def __init__(self, pdf_exporter):
        super().__init__()
        self.pdf_exporter = pdf_exporter
        self.current_assignments = []
        self.current_timetable_info = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Top Buttons
        btn_layout = QHBoxLayout()

        self.preview_btn = QPushButton("Preview PDF")
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
        self.preview_btn.setEnabled(False)
        btn_layout.addWidget(self.preview_btn)

        self.export_btn = QPushButton("Export to PDF")
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
        self.export_btn.setEnabled(False)
        btn_layout.addWidget(self.export_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Preview Area (Full Height)
        preview_group = QGroupBox("PDF Preview")
        preview_group.setStyleSheet("""
            QGroupBox {
                color: #fff;
                font-weight: 600;
                border: 1px solid #333;
                border-radius: 6px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """)
        preview_layout = QVBoxLayout(preview_group)

        if WEB_ENGINE_AVAILABLE:
            self.preview_widget = QWebEngineView()
            self.use_web_engine = True
        else:
            from PyQt6.QtWidgets import QTextEdit
            self.preview_widget = QTextEdit()
            self.preview_widget.setReadOnly(True)
            self.use_web_engine = False

        preview_layout.addWidget(self.preview_widget)
        layout.addWidget(preview_group)

    # ----------------------------------------------------------------------
    # Core Methods
    # ----------------------------------------------------------------------
    def set_timetable(self, assignments, timetable_info):
        self.current_assignments = assignments
        self.current_timetable_info = timetable_info
        has_data = bool(assignments and timetable_info)
        self.preview_btn.setEnabled(has_data)
        self.export_btn.setEnabled(has_data)
        if has_data:
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

    def preview_pdf(self):
        """Generate HTML preview for the current timetable."""
        if not self.current_assignments or not self.current_timetable_info:
            QMessageBox.warning(self, "Warning", "No timetable to preview.")
            return
        try:
            html_content = self.pdf_exporter.preview_timetable(
                self.current_assignments, self.current_timetable_info
            )
            if self.use_web_engine:
                self.preview_widget.setHtml(html_content)
            else:
                self.preview_widget.setHtml(html_content)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate preview: {e}")

    def show_preview(self, assignments, timetable_info):
        self.set_timetable(assignments, timetable_info)
        self.preview_pdf()

    def export_to_pdf(self):
        """Export timetable as PDF file."""
        if not self.current_assignments or not self.current_timetable_info:
            QMessageBox.warning(self, "Warning", "No timetable to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Timetable to PDF",
            f"timetable_{self.current_timetable_info.get('semester', '')}_{self.current_timetable_info.get('year', '')}.pdf",
            "PDF Files (*.pdf);;All Files (*)",
        )
        if not file_path:
            return

        self._start_export(file_path)

    def _start_export(self, file_path):
        """Run export in a background thread."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.preview_btn.setEnabled(False)
        self.export_btn.setEnabled(False)

        self.export_thread = ExportThread(
            self.pdf_exporter, self.current_assignments,
            self.current_timetable_info, file_path
        )
        self.export_thread.export_completed.connect(self._on_export_completed)
        self.export_thread.export_failed.connect(self._on_export_failed)
        self.export_thread.start()

    def _on_export_completed(self, file_path):
        self.progress_bar.setVisible(False)
        self.preview_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        QMessageBox.information(self, "Export Successful",
                                f"Timetable exported successfully to:\n{file_path}")

    def _on_export_failed(self, error_message):
        self.progress_bar.setVisible(False)
        self.preview_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        QMessageBox.critical(self, "Export Failed",
                             f"Failed to export timetable:\n{error_message}")


class ExportThread(QThread):
    """Worker thread for PDF export."""

    export_completed = pyqtSignal(str)
    export_failed = pyqtSignal(str)

    def __init__(self, pdf_exporter, assignments, timetable_info, file_path):
        super().__init__()
        self.pdf_exporter = pdf_exporter
        self.assignments = assignments
        self.timetable_info = timetable_info
        self.file_path = file_path

    def run(self):
        try:
            success = self.pdf_exporter.export_timetable(
                self.assignments, self.timetable_info, self.file_path
            )
            if success:
                self.export_completed.emit(self.file_path)
            else:
                self.export_failed.emit("Export operation failed.")
        except Exception as e:
            self.export_failed.emit(str(e))
