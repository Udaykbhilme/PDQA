"""
Timetable Generation Tab — Real CP-SAT integration.
Now uses CPSATScheduler for true constraint-based timetable generation.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QSpinBox,
    QComboBox, QTimeEdit, QCheckBox, QGridLayout, QMessageBox, QProgressBar
)
from PyQt6.QtCore import pyqtSignal, QTime, QThread, pyqtSlot
from ..scheduler.timetable_scheduler import CPSATScheduler, GenerationSettings


# -------------------------------
# Worker Thread for CP-SAT Solver
# -------------------------------
class SolverThread(QThread):
    result_ready = pyqtSignal(list, dict, list, str)

    def __init__(self, db, settings):
        super().__init__()
        self.db = db
        self.settings = settings

    def run(self):
        try:
            scheduler = CPSATScheduler(self.db)
            assignments, info, conflicts = scheduler.generate(self.settings)
            msg = f"✅ Generated {len(assignments)} classes. Conflicts: {len(conflicts)}"
        except Exception as e:
            assignments, info, conflicts = [], {}, []
            msg = f"❌ Error: {e}"
        self.result_ready.emit(assignments, info, conflicts, msg)


# -------------------------------
# Main UI Class
# -------------------------------
class TimetableGenerationTab(QWidget):
    """Tab for generating timetables using CP-SAT optimization."""

    timetable_generated = pyqtSignal(list, dict, list)

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # --- Config Grid ---
        grid = QGridLayout()

        grid.addWidget(QLabel("Degree:"), 0, 0)
        self.degree_combo = QComboBox()
        self.degree_combo.addItems(["B.Tech", "M.Tech"])
        grid.addWidget(self.degree_combo, 0, 1)

        grid.addWidget(QLabel("Year:"), 0, 2)
        self.year_combo = QComboBox()
        self.year_combo.addItems(["2", "3", "4"])
        grid.addWidget(self.year_combo, 0, 3)

        grid.addWidget(QLabel("Semester:"), 0, 4)
        self.semester_combo = QComboBox()
        self.semester_combo.addItems([str(i) for i in range(3, 9)])
        grid.addWidget(self.semester_combo, 0, 5)

        grid.addWidget(QLabel("Lecture Duration (hrs):"), 1, 0)
        self.lecture_spin = QSpinBox()
        self.lecture_spin.setRange(1, 4)
        self.lecture_spin.setValue(1)
        grid.addWidget(self.lecture_spin, 1, 1)

        grid.addWidget(QLabel("Lab Duration (hrs):"), 1, 2)
        self.lab_spin = QSpinBox()
        self.lab_spin.setRange(1, 4)
        self.lab_spin.setValue(2)
        grid.addWidget(self.lab_spin, 1, 3)

        layout.addLayout(grid)

        # --- Time and Lunch ---
        time_layout = QHBoxLayout()
        for label, attr, default in [
            ("Start Time", "start_time", "09:00"),
            ("End Time", "end_time", "17:00"),
            ("Lunch Start", "lunch_start", "13:00"),
            ("Lunch End", "lunch_end", "14:00"),
        ]:
            time_layout.addWidget(QLabel(f"{label}:"))
            te = QTimeEdit()
            te.setTime(QTime.fromString(default, "HH:mm"))
            setattr(self, attr, te)
            time_layout.addWidget(te)
        layout.addLayout(time_layout)

        # --- Days selection ---
        days_layout = QHBoxLayout()
        self.day_checkboxes = []
        for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]:
            cb = QCheckBox(d)
            cb.setChecked(d in ["Mon", "Tue", "Wed", "Thu", "Fri"])
            days_layout.addWidget(cb)
            self.day_checkboxes.append(cb)
        layout.addLayout(days_layout)

        # --- Generate + Progress ---
        self.generate_btn = QPushButton("🚀 Generate Timetable")
        self.generate_btn.clicked.connect(self.start_generation)
        layout.addWidget(self.generate_btn)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # --- Status ---
        self.status_label = QLabel("Ready.")
        layout.addWidget(self.status_label)

    # -------------------------------
    # Logic
    # -------------------------------
    @pyqtSlot()
    def start_generation(self):
        """Launch CP-SAT scheduler in background."""
        self.status_label.setText("⏳ Generating timetable...")
        self.progress.setVisible(True)
        self.generate_btn.setEnabled(False)

        days = [cb.text() for cb in self.day_checkboxes if cb.isChecked()]
        settings = GenerationSettings(
            lecture_duration=self.lecture_spin.value(),
            lab_duration=self.lab_spin.value(),
            lunch_start=self.lunch_start.time().toString("HH:mm"),
            lunch_end=self.lunch_end.time().toString("HH:mm"),
            start_time=self.start_time.time().toString("HH:mm"),
            end_time=self.end_time.time().toString("HH:mm"),
            days=days,
            degree=self.degree_combo.currentText(),
            year=int(self.year_combo.currentText()),
            semester=int(self.semester_combo.currentText())
        )

        self.worker = SolverThread(self.db, settings)
        self.worker.result_ready.connect(self._solver_finished)
        self.worker.start()

    @pyqtSlot(list, dict, list, str)
    def _solver_finished(self, assignments, info, conflicts, msg):
        """Handle solver completion."""
        self.progress.setVisible(False)
        self.generate_btn.setEnabled(True)
        self.status_label.setText(msg)
        if conflicts:
            details = "\n".join(f"- {c.subject_code}: {c.details}" for c in conflicts)
            QMessageBox.warning(self, "Conflicts Detected", details)
        if assignments:
            self.timetable_generated.emit(assignments, info, conflicts)
