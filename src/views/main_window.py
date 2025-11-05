"""
Compact, maintainable Main Window for Timetable Generator.
Uses abstraction to avoid redundant QAction and menu/toolbar logic.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QStatusBar, QLabel, 
    QMessageBox, QFileDialog, QToolBar
)
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtCore import QTimer

from .data_management_tab import DataManagementTab
from .timetable_generation_tab import TimetableGenerationTab
from .timetable_review_tab import TimetableReviewTab
from .export_tab import ExportTab
from ..database.database_manager import DatabaseManager
from ..scheduler.timetable_scheduler import TimetableScheduler
from ..export.pdf_exporter import PDFExporter


class MainWindow(QMainWindow):
    """Main window with unified tab interface, menus, toolbar, and status bar."""

    def __init__(self):
        super().__init__()

        # Core objects
        self.db = DatabaseManager()
        self.scheduler = TimetableScheduler(self.db)
        self.exporter = PDFExporter()

        self.current_assignments, self.current_info = [], {}

        self.setWindowTitle("Timetable Generator - CSE Department")
        self.resize(1400, 900)

        # UI setup
        self.init_ui()
        self.update_status("Application ready")

    # -----------------------------------------------------
    # UI INITIALIZATION
    # -----------------------------------------------------
    def init_ui(self):
        """Initialize main window UI"""
        self.tabs = QTabWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Tabs
        self.data_tab = DataManagementTab(self.db)
        self.gen_tab = TimetableGenerationTab(self.db)
        self.review_tab = TimetableReviewTab(self.db)
        self.export_tab = ExportTab(self.exporter)

        for tab, name in [
            (self.data_tab, "Data Management"),
            (self.gen_tab, "Generate Timetable"),
            (self.review_tab, "Review & Edit"),
            (self.export_tab, "Export"),
        ]:
            self.tabs.addTab(tab, name)

        # Menus, toolbar, and status
        self.create_menu_bar()
        self.create_toolbar()
        self.create_status_bar()

        # Signals
        self.gen_tab.timetable_generated.connect(self.on_generated)
        self.review_tab.timetable_updated.connect(self.on_updated)

    # -----------------------------------------------------
    # GENERIC UTILITIES
    # -----------------------------------------------------
    def make_action(self, text, shortcut=None, tip=None, handler=None):
        """Helper to create QAction with consistent setup"""
        act = QAction(text, self)
        if shortcut:
            act.setShortcut(shortcut)
        if tip:
            act.setStatusTip(tip)
        if handler:
            act.triggered.connect(handler)
        return act

    def add_actions_to_menu(self, menu, *actions):
        """Helper to add multiple actions to a QMenu"""
        for act in actions:
            menu.addAction(act)
        menu.addSeparator()

    # -----------------------------------------------------
    # MENUBAR + TOOLBAR
    # -----------------------------------------------------
    def create_menu_bar(self):
        menubar = self.menuBar()

        # --- File Menu ---
        file_menu = menubar.addMenu("&File")
        self.add_actions_to_menu(
            file_menu,
            self.make_action("New Timetable", QKeySequence.StandardKey.New, "Create new timetable", self.new_timetable),
            self.make_action("Open Timetable", QKeySequence.StandardKey.Open, "Open timetable", self.open_timetable),
            self.make_action("Save Timetable", QKeySequence.StandardKey.Save, "Save timetable", self.save_timetable),
        )
        file_menu.addAction(self.make_action("Exit", QKeySequence.StandardKey.Quit, "Exit app", self.close))

        # --- Generate Menu ---
        gen_menu = menubar.addMenu("&Generate")
        gen_menu.addAction(self.make_action("Generate Timetable", "Ctrl+G", "Generate timetable", self.generate_timetable))

        # --- Export Menu ---
        exp_menu = menubar.addMenu("&Export")
        exp_menu.addAction(self.make_action("Export to PDF", "Ctrl+P", "Export to PDF", self.export_to_pdf))
        exp_menu.addAction(self.make_action("Preview PDF", "Ctrl+R", "Preview timetable", self.preview_pdf))

        # --- Help Menu ---
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction(self.make_action("About", None, "About app", self.show_about))

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        for text, tip, func in [
            ("New", "New timetable", self.new_timetable),
            ("Generate", "Generate timetable", self.generate_timetable),
            ("Export PDF", "Export timetable to PDF", self.export_to_pdf),
        ]:
            act = QAction(text, self)
            act.setStatusTip(tip)
            act.triggered.connect(func)
            toolbar.addAction(act)

    def create_status_bar(self):
        """Create persistent status bar"""
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status_label = QLabel("Ready")
        self.status.addWidget(self.status_label)

    # -----------------------------------------------------
    # CORE ACTIONS
    # -----------------------------------------------------
    def new_timetable(self):
        """Reset state and open generation tab"""
        self.current_assignments, self.current_info = [], {}
        self.review_tab.clear_timetable()
        self.export_tab.clear_timetable()
        self.update_status("New timetable created")
        self.tabs.setCurrentWidget(self.gen_tab)

    def open_timetable(self):
        """Load existing timetable (placeholder)"""
        path, _ = QFileDialog.getOpenFileName(self, "Open Timetable", "", "JSON Files (*.json)")
        if not path:
            return
        try:
            # TODO: Implement file deserialization
            self.update_status(f"Opened: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open: {e}")

    def save_timetable(self):
        """Save current timetable (placeholder)"""
        if not self.current_assignments:
            QMessageBox.warning(self, "Warning", "No timetable to save")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Timetable", "", "JSON Files (*.json)")
        if not path:
            return
        try:
            # TODO: Implement save logic
            self.update_status(f"Saved: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")

    def generate_timetable(self):
        """Trigger timetable generation"""
        self.tabs.setCurrentWidget(self.gen_tab)
        self.gen_tab.start_generation()

    def export_to_pdf(self):
        """Export timetable to PDF"""
        if not self.current_assignments:
            QMessageBox.warning(self, "Warning", "No timetable to export")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Export to PDF", "", "PDF Files (*.pdf)")
        if not path:
            return

        try:
            ok = self.exporter.export_timetable(self.current_assignments, self.current_info, path)
            if ok:
                QMessageBox.information(self, "Success", "Timetable exported successfully!")
                self.update_status(f"Exported PDF: {path}")
            else:
                QMessageBox.critical(self, "Error", "Failed to export timetable")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def preview_pdf(self):
        """Preview PDF export"""
        if not self.current_assignments:
            QMessageBox.warning(self, "Warning", "No timetable to preview")
            return
        self.tabs.setCurrentWidget(self.export_tab)
        self.export_tab.show_preview(self.current_assignments, self.current_info)

    # -----------------------------------------------------
    # CALLBACKS + STATUS
    # -----------------------------------------------------
    def on_generated(self, assignments, info, conflicts):
        """Handle generated timetable"""
        self.current_assignments, self.current_info = assignments, info
        self.review_tab.set_timetable(assignments, info, conflicts)
        self.export_tab.set_timetable(assignments, info)
        self.tabs.setCurrentWidget(self.review_tab)

        if conflicts:
            self._show_conflicts(conflicts)
        self.update_status(f"Generated {len(assignments)} slots")

    def on_updated(self, assignments, info):
        """Handle timetable edits"""
        self.current_assignments, self.current_info = assignments, info
        self.export_tab.set_timetable(assignments, info)
        self.update_status("Timetable updated")

    def _show_conflicts(self, conflicts):
        """Popup listing detected conflicts"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Generation Conflicts")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText(f"{len(conflicts)} conflicts detected during generation.")
        msg.setDetailedText("\n".join(f"• {c.subject_code}: {c.details}" for c in conflicts))
        msg.exec()

    def show_about(self):
        """Show About dialog"""
        QMessageBox.about(
            self,
            "About Timetable Generator",
            """
            <h3>Timetable Generator v1.0.0</h3>
            <p>Desktop tool for generating and managing timetables for the CSE Department.</p>
            <ul>
                <li>Faculty, Subject, Venue, Section management</li>
                <li>Constraint-based generation algorithm</li>
                <li>Interactive editing and PDF export</li>
            </ul>
            <p><b>Tech Stack:</b> Python, PyQt6, SQLAlchemy, ReportLab</p>
            """
        )

    def update_status(self, msg):
        """Set status message and auto-clear"""
        self.status_label.setText(msg)
        QTimer.singleShot(4000, lambda: self.status_label.setText("Ready"))

    def closeEvent(self, event):
        """Prompt before exit"""
        if QMessageBox.question(self, "Exit", "Exit application?",
                                 QMessageBox.StandardButton.Yes |
                                 QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()
