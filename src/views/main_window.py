from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QStatusBar, QLabel, QMessageBox
)
from PyQt6.QtCore import QTimer

from ..database.database_manager import DatabaseManager
from ..scheduler.timetable_scheduler import CPSATScheduler
from ..export.pdf_exporter import PDFExporter
from .data_management_tab import DataManagementTab
from .faculty_subject_mapping_tab import FacultySubjectMappingTab
from .timetable_generation_tab import TimetableGenerationTab
from .timetable_review_tab import TimetableReviewTab
from .export_tab import ExportTab


class MainWindow(QMainWindow):
    """Modern, professional main window for Timetable Generator."""

    def __init__(self):
        super().__init__()

        # Core managers
        self.db = DatabaseManager()
        self.scheduler = CPSATScheduler(self.db)
        self.exporter = PDFExporter()

        # Current session data
        self.current_assignments = []
        self.current_info = {}

        # Main Window setup
        self.setWindowTitle("Timetable Generator — CSE Department")
        self.resize(1400, 900)
        self.setStyleSheet("""
            QMainWindow { background-color: #121212; }
            QLabel, QTabWidget::pane, QWidget {
                color: #ddd; font-family: 'Segoe UI'; font-size: 13px;
            }
            QTabBar::tab {
                background: #1E1E1E; padding: 10px 16px; border: none;
                border-top-left-radius: 6px; border-top-right-radius: 6px;
            }
            QTabBar::tab:selected { background: #2D2D2D; color: #fff; }
            QStatusBar { background: #1E1E1E; color: #aaa; }
        """)
        self._init_ui()

    # -----------------------------------------------------
    # Initialize Tabs
    # -----------------------------------------------------
    def _init_ui(self):
        self.tabs = QTabWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Core tabs
        self.data_tab = DataManagementTab(self.db)
        self.mapping_tab = FacultySubjectMappingTab(self.db)
        self.gen_tab = TimetableGenerationTab(self.db)
        self.review_tab = TimetableReviewTab(self.db)
        self.export_tab = ExportTab(self.exporter)

        for tab, name in [
            (self.data_tab, "Data Management"),
            (self.mapping_tab, "Faculty–Subject Mapping"),
            (self.gen_tab, "Generate Timetable"),
            (self.review_tab, "Review & Edit"),
            (self.export_tab, "Export Timetable"),
        ]:
            self.tabs.addTab(tab, name)

        # Status bar setup
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status_label = QLabel("Ready")
        self.status.addWidget(self.status_label)

        # Connect signals
        self.gen_tab.timetable_generated.connect(self._on_generated)
        self.review_tab.timetable_updated.connect(self._on_updated)

        # Also send generated timetables directly to the export tab
        self.gen_tab.timetable_generated.connect(self.export_tab.set_timetable)

    # -----------------------------------------------------
    # Signal Callbacks
    # -----------------------------------------------------
    def _on_generated(self, assignments, info, conflicts):
        """Triggered after timetable generation completes."""
        self.current_assignments = assignments
        self.current_info = info

        # Update review tab as before
        self.review_tab.set_timetable(assignments, info, conflicts)

        # Also prepare Export tab with same data
        self.export_tab.set_timetable(assignments, info)

        # Optionally switch UI tab to Export immediately:
        # self.tabs.setCurrentWidget(self.export_tab)

        self._update_status(f"Generated {len(assignments)} slots successfully.")

    def _on_updated(self, assignments, info):
        """Triggered when timetable is approved or manually edited in review tab."""
        flattened = []
        for a in assignments:
            subj = getattr(a, "subject", None)
            fac = getattr(a, "faculty", None)
            ven = getattr(a, "venue", None)

            # Flatten ORM-dependent objects into thread-safe strings
            a.subject_code = getattr(subj, "code", getattr(a, "subject_code", ""))
            a.subject_name = getattr(subj, "name", getattr(a, "subject_name", ""))
            a.faculty_name = getattr(fac, "name", getattr(a, "faculty_name", ""))
            a.venue_name = getattr(ven, "name", getattr(a, "venue_name", ""))
            a.faculties = [{"id": getattr(fac, "id", None), "name": a.faculty_name}]

            flattened.append(a)

        self.current_assignments = flattened
        self.current_info = info

        # Update export tab with safe, flattened data
        self.export_tab.set_timetable(flattened, info)

        self._update_status("Timetable approved and ready for export.")

    # -----------------------------------------------------
    # Status Updates & Exit
    # -----------------------------------------------------
    def _update_status(self, msg):
        """Update message bar with timeout."""
        self.status_label.setText(msg)
        QTimer.singleShot(4000, lambda: self.status_label.setText("Ready"))

    def closeEvent(self, event):
        """Confirmation before exiting."""
        if QMessageBox.question(
            self, "Exit", "Exit application?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()
