"""
Main Window for Timetable Generator

This module contains the main application window with menu bar, toolbar,
and tabbed interface for different functionalities.
"""

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QStatusBar, QMessageBox, QFileDialog, QToolBar,
    QLabel, QPushButton, QFrame
)
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QPixmap
from PyQt6.QtCore import Qt, QTimer

from .data_management_tab import DataManagementTab
from .timetable_generation_tab import TimetableGenerationTab
from .timetable_review_tab import TimetableReviewTab
from .export_tab import ExportTab
from ..database.database_manager import DatabaseManager
from ..scheduler.timetable_scheduler import TimetableScheduler, GenerationSettings
from ..export.pdf_exporter import PDFExporter


class MainWindow(QMainWindow):
    """
    Main application window with tabbed interface
    
    Features:
    - Menu bar with File, Generate, Export, and Help menus
    - Toolbar with quick access buttons
    - Tabbed interface for different functionalities
    - Status bar for application status
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize components
        self.db_manager = DatabaseManager()
        self.scheduler = TimetableScheduler(self.db_manager)
        self.pdf_exporter = PDFExporter()
        
        # Current timetable data
        self.current_assignments = []
        self.current_timetable_info = {}
        
        # Initialize UI
        self.init_ui()
        self.setup_connections()
        
        # Update status
        self.update_status("Application ready")
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Timetable Generator - CSE Department")
        self.setGeometry(100, 100, 1400, 900)
        
        # Set application icon (if available)
        # self.setWindowIcon(QIcon("icons/app_icon.png"))
        
        # Create central widget with tabbed interface
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(self.central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_tabs()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create status bar
        self.create_status_bar()
    
    def create_tabs(self):
        """Create all application tabs"""
        # Data Management Tab
        self.data_tab = DataManagementTab(self.db_manager)
        self.tab_widget.addTab(self.data_tab, "Data Management")
        
        # Timetable Generation Tab
        self.generation_tab = TimetableGenerationTab(self.db_manager)
        self.tab_widget.addTab(self.generation_tab, "Generate Timetable")
        
        # Timetable Review Tab
        self.review_tab = TimetableReviewTab(self.db_manager)
        self.tab_widget.addTab(self.review_tab, "Review & Edit")
        
        # Export Tab
        self.export_tab = ExportTab(self.pdf_exporter)
        self.tab_widget.addTab(self.export_tab, "Export")
    
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu('&File')
        
        # New Timetable
        new_action = QAction('&New Timetable', self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.setStatusTip('Create a new timetable')
        new_action.triggered.connect(self.new_timetable)
        file_menu.addAction(new_action)
        
        # Open Timetable
        open_action = QAction('&Open Timetable', self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.setStatusTip('Open an existing timetable')
        open_action.triggered.connect(self.open_timetable)
        file_menu.addAction(open_action)
        
        # Save Timetable
        save_action = QAction('&Save Timetable', self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.setStatusTip('Save current timetable')
        save_action.triggered.connect(self.save_timetable)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        # Exit
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Generate Menu
        generate_menu = menubar.addMenu('&Generate')
        
        # Generate Timetable
        generate_action = QAction('&Generate Timetable', self)
        generate_action.setShortcut('Ctrl+G')
        generate_action.setStatusTip('Generate a new timetable')
        generate_action.triggered.connect(self.generate_timetable)
        generate_menu.addAction(generate_action)
        
        # Export Menu
        export_menu = menubar.addMenu('&Export')
        
        # Export to PDF
        export_pdf_action = QAction('Export to &PDF', self)
        export_pdf_action.setShortcut('Ctrl+P')
        export_pdf_action.setStatusTip('Export timetable to PDF')
        export_pdf_action.triggered.connect(self.export_to_pdf)
        export_menu.addAction(export_pdf_action)
        
        # Preview PDF
        preview_pdf_action = QAction('&Preview PDF', self)
        preview_pdf_action.setShortcut('Ctrl+R')
        preview_pdf_action.setStatusTip('Preview timetable as PDF')
        preview_pdf_action.triggered.connect(self.preview_pdf)
        export_menu.addAction(preview_pdf_action)
        
        # Help Menu
        help_menu = menubar.addMenu('&Help')
        
        # About
        about_action = QAction('&About', self)
        about_action.setStatusTip('About Timetable Generator')
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Create application toolbar"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # New Timetable
        new_action = QAction('New', self)
        new_action.setStatusTip('Create new timetable')
        new_action.triggered.connect(self.new_timetable)
        toolbar.addAction(new_action)
        
        # Generate Timetable
        generate_action = QAction('Generate', self)
        generate_action.setStatusTip('Generate timetable')
        generate_action.triggered.connect(self.generate_timetable)
        toolbar.addAction(generate_action)
        
        toolbar.addSeparator()
        
        # Export PDF
        export_action = QAction('Export PDF', self)
        export_action.setStatusTip('Export to PDF')
        export_action.triggered.connect(self.export_to_pdf)
        toolbar.addAction(export_action)
    
    def create_status_bar(self):
        """Create application status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Progress bar (hidden by default)
        self.progress_bar = QLabel("")
        self.status_bar.addPermanentWidget(self.progress_bar)
    
    def setup_connections(self):
        """Setup signal connections between components"""
        # Connect generation tab signals
        self.generation_tab.timetable_generated.connect(self.on_timetable_generated)
        
        # Connect review tab signals
        self.review_tab.timetable_updated.connect(self.on_timetable_updated)
    
    def new_timetable(self):
        """Create a new timetable"""
        self.current_assignments = []
        self.current_timetable_info = {}
        self.review_tab.clear_timetable()
        self.export_tab.clear_timetable()
        self.update_status("New timetable created")
        
        # Switch to generation tab
        self.tab_widget.setCurrentWidget(self.generation_tab)
    
    def open_timetable(self):
        """Open an existing timetable"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Timetable", "", "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                # Load timetable from file
                # This would need to be implemented based on your file format
                self.update_status(f"Opened timetable: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open timetable: {e}")
    
    def save_timetable(self):
        """Save current timetable"""
        if not self.current_assignments:
            QMessageBox.warning(self, "Warning", "No timetable to save")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Timetable", "", "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                # Save timetable to file
                # This would need to be implemented based on your file format
                self.update_status(f"Saved timetable: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save timetable: {e}")
    
    def generate_timetable(self):
        """Generate a new timetable"""
        # Switch to generation tab
        self.tab_widget.setCurrentWidget(self.generation_tab)
        
        # Trigger generation from the generation tab
        self.generation_tab.start_generation()
    
    def export_to_pdf(self):
        """Export current timetable to PDF"""
        if not self.current_assignments:
            QMessageBox.warning(self, "Warning", "No timetable to export")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to PDF", "", "PDF Files (*.pdf);;All Files (*)"
        )
        
        if file_path:
            try:
                success = self.pdf_exporter.export_timetable(
                    self.current_assignments,
                    self.current_timetable_info,
                    file_path
                )
                
                if success:
                    self.update_status(f"Exported to PDF: {file_path}")
                    QMessageBox.information(self, "Success", "Timetable exported successfully!")
                else:
                    QMessageBox.critical(self, "Error", "Failed to export timetable")
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export timetable: {e}")
    
    def preview_pdf(self):
        """Preview timetable as PDF"""
        if not self.current_assignments:
            QMessageBox.warning(self, "Warning", "No timetable to preview")
            return
        
        # Switch to export tab and show preview
        self.tab_widget.setCurrentWidget(self.export_tab)
        self.export_tab.show_preview(self.current_assignments, self.current_timetable_info)
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Timetable Generator",
            """
            <h3>Timetable Generator v1.0.0</h3>
            <p>A comprehensive desktop application for generating timetables for the CSE Department.</p>
            <p><b>Features:</b></p>
            <ul>
            <li>Data management for faculties, subjects, venues, and sections</li>
            <li>Intelligent timetable generation with constraint-based algorithm</li>
            <li>Interactive timetable review and editing</li>
            <li>Professional PDF export with customizable layouts</li>
            </ul>
            <p><b>Developed by:</b> CSE Department</p>
            <p><b>Technology:</b> Python, PyQt6, SQLAlchemy, ReportLab</p>
            """
        )
    
    def on_timetable_generated(self, assignments, timetable_info, conflicts):
        """Handle timetable generation completion"""
        self.current_assignments = assignments
        self.current_timetable_info = timetable_info
        
        # Update review tab
        self.review_tab.set_timetable(assignments, timetable_info, conflicts)
        
        # Update export tab
        self.export_tab.set_timetable(assignments, timetable_info)
        
        # Switch to review tab
        self.tab_widget.setCurrentWidget(self.review_tab)
        
        # Show conflicts if any
        if conflicts:
            self.show_conflicts_dialog(conflicts)
        
        self.update_status(f"Timetable generated with {len(assignments)} assignments")
    
    def on_timetable_updated(self, assignments, timetable_info):
        """Handle timetable updates from review tab"""
        self.current_assignments = assignments
        self.current_timetable_info = timetable_info
        
        # Update export tab
        self.export_tab.set_timetable(assignments, timetable_info)
        
        self.update_status("Timetable updated")
    
    def show_conflicts_dialog(self, conflicts):
        """Show conflicts dialog"""
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Generation Conflicts")
        dialog.setIcon(QMessageBox.Icon.Warning)
        
        if len(conflicts) == 1:
            dialog.setText("1 conflict was detected during generation:")
        else:
            dialog.setText(f"{len(conflicts)} conflicts were detected during generation:")
        
        conflict_details = "\n".join([f"• {c.subject_code}: {c.details}" for c in conflicts])
        dialog.setDetailedText(conflict_details)
        
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        dialog.exec()
    
    def update_status(self, message: str):
        """Update status bar message"""
        self.status_label.setText(message)
        
        # Auto-clear status after 5 seconds
        QTimer.singleShot(5000, lambda: self.status_label.setText("Ready"))
    
    def closeEvent(self, event):
        """Handle application close event"""
        reply = QMessageBox.question(
            self,
            'Exit Application',
            'Are you sure you want to exit?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()
