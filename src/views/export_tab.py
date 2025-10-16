"""
Export Tab for Timetable Generator

This module provides the interface for exporting timetables to PDF format
with preview capabilities and export options.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QGroupBox, QFileDialog, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont
import tempfile
import os

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEB_ENGINE_AVAILABLE = True
except ImportError:
    WEB_ENGINE_AVAILABLE = False


class ExportTab(QWidget):
    """
    Tab for exporting timetables to PDF format
    
    Features:
    - PDF preview using HTML rendering
    - Export options and settings
    - Progress tracking for export operations
    - Export history and management
    """
    
    def __init__(self, pdf_exporter):
        super().__init__()
        self.pdf_exporter = pdf_exporter
        self.current_assignments = []
        self.current_timetable_info = {}
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Export controls
        controls_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("Preview PDF")
        self.preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.preview_btn.clicked.connect(self.preview_pdf)
        self.preview_btn.setEnabled(False)
        controls_layout.addWidget(self.preview_btn)
        
        self.export_btn = QPushButton("Export to PDF")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.export_btn.clicked.connect(self.export_to_pdf)
        self.export_btn.setEnabled(False)
        controls_layout.addWidget(self.export_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Preview area
        preview_group = QGroupBox("PDF Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        # Use QTextEdit for HTML preview (fallback if QWebEngineView not available)
        if WEB_ENGINE_AVAILABLE:
            self.preview_widget = QWebEngineView()
            self.use_web_engine = True
        else:
            self.preview_widget = QTextEdit()
            self.preview_widget.setReadOnly(True)
            self.use_web_engine = False
        
        preview_layout.addWidget(self.preview_widget)
        layout.addWidget(preview_group)
        
        # Export options
        options_group = QGroupBox("Export Options")
        options_layout = QVBoxLayout(options_group)
        
        self.options_text = QTextEdit()
        self.options_text.setMaximumHeight(100)
        self.options_text.setReadOnly(True)
        self.options_text.setHtml("""
        <b>Export Options:</b><br/>
        • A4 Landscape format<br/>
        • Professional layout with department header<br/>
        • Color-coded cells for lectures and labs<br/>
        • Detailed cell content with all information<br/>
        • Print-ready PDF output
        """)
        options_layout.addWidget(self.options_text)
        
        layout.addWidget(options_group)
    
    def set_timetable(self, assignments, timetable_info):
        """Set the current timetable data"""
        self.current_assignments = assignments
        self.current_timetable_info = timetable_info
        
        # Enable buttons if we have data
        has_data = bool(assignments and timetable_info)
        self.preview_btn.setEnabled(has_data)
        self.export_btn.setEnabled(has_data)
        
        if has_data:
            # Auto-generate preview
            self.preview_pdf()
    
    def clear_timetable(self):
        """Clear the current timetable"""
        self.current_assignments = []
        self.current_timetable_info = {}
        
        self.preview_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        
        if self.use_web_engine:
            self.preview_widget.setHtml("<p>No timetable loaded</p>")
        else:
            self.preview_widget.setPlainText("No timetable loaded")
    
    def preview_pdf(self):
        """Generate and show PDF preview"""
        if not self.current_assignments or not self.current_timetable_info:
            QMessageBox.warning(self, "Warning", "No timetable to preview")
            return
        
        try:
            # Generate HTML preview
            html_content = self.pdf_exporter.preview_timetable(
                self.current_assignments,
                self.current_timetable_info
            )
            
            # Display preview
            if self.use_web_engine:
                self.preview_widget.setHtml(html_content)
            else:
                # For QTextEdit, we need to strip HTML tags for basic display
                self.preview_widget.setHtml(html_content)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate preview: {e}")
    
    def show_preview(self, assignments, timetable_info):
        """Show preview for given timetable data"""
        self.set_timetable(assignments, timetable_info)
        self.preview_pdf()
    
    def export_to_pdf(self):
        """Export timetable to PDF file"""
        if not self.current_assignments or not self.current_timetable_info:
            QMessageBox.warning(self, "Warning", "No timetable to export")
            return
        
        # Get save location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Timetable to PDF",
            f"timetable_{self.current_timetable_info.get('semester', '')}_{self.current_timetable_info.get('year', '')}.pdf",
            "PDF Files (*.pdf);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # Start export process
        self.start_export_process(file_path)
    
    def start_export_process(self, file_path):
        """Start the PDF export process in a separate thread"""
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.export_btn.setEnabled(False)
        self.preview_btn.setEnabled(False)
        
        # Create and start export thread
        self.export_thread = ExportThread(
            self.pdf_exporter,
            self.current_assignments,
            self.current_timetable_info,
            file_path
        )
        self.export_thread.export_completed.connect(self.on_export_completed)
        self.export_thread.export_failed.connect(self.on_export_failed)
        self.export_thread.start()
    
    def on_export_completed(self, file_path):
        """Handle successful export completion"""
        self.progress_bar.setVisible(False)
        self.export_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
        
        QMessageBox.information(
            self,
            "Export Successful",
            f"Timetable exported successfully to:\n{file_path}"
        )
    
    def on_export_failed(self, error_message):
        """Handle export failure"""
        self.progress_bar.setVisible(False)
        self.export_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
        
        QMessageBox.critical(
            self,
            "Export Failed",
            f"Failed to export timetable:\n{error_message}"
        )


class ExportThread(QThread):
    """Thread for running PDF export operations"""
    
    export_completed = pyqtSignal(str)  # file_path
    export_failed = pyqtSignal(str)  # error_message
    
    def __init__(self, pdf_exporter, assignments, timetable_info, file_path):
        super().__init__()
        self.pdf_exporter = pdf_exporter
        self.assignments = assignments
        self.timetable_info = timetable_info
        self.file_path = file_path
    
    def run(self):
        """Run the export process"""
        try:
            success = self.pdf_exporter.export_timetable(
                self.assignments,
                self.timetable_info,
                self.file_path
            )
            
            if success:
                self.export_completed.emit(self.file_path)
            else:
                self.export_failed.emit("Export operation failed")
                
        except Exception as e:
            self.export_failed.emit(str(e))
