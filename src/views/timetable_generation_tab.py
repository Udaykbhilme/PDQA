from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QSpinBox,
    QComboBox, QTimeEdit, QCheckBox, QGridLayout, QMessageBox, QProgressBar
)
from PyQt6.QtCore import pyqtSignal, QTime, QThread, pyqtSlot
from ..scheduler.timetable_scheduler import CPSATScheduler, GenerationSettings


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


class TimetableGenerationTab(QWidget):
    timetable_generated = pyqtSignal(list, dict, list)

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # --------------------------------------
        # GRID: Degree, Years, Semesters, Durations
        # --------------------------------------
        grid = QGridLayout()

        # Degree
        grid.addWidget(QLabel("Degree:"), 0, 0)
        self.degree_combo = QComboBox()
        self.degree_combo.addItems(["B.Tech", "M.Tech"])
        grid.addWidget(self.degree_combo, 0, 1)

        # YEAR MULTI-SELECTION
        grid.addWidget(QLabel("Years:"), 0, 2)
        self.year_box = QComboBox()
        self.year_box.addItems([
            "Select",
            "2",
            "3",
            "4",
            "2,3",
            "3,4",
            "2,3,4"
        ])
        grid.addWidget(self.year_box, 0, 3)

        # SEMESTER MULTI-SELECTION
        grid.addWidget(QLabel("Semesters:"), 0, 4)
        self.sem_box = QComboBox()
        self.sem_box.addItems([
            "Auto (recommended)",
            "3", "4",
            "5", "6",
            "7", "8",
            "3,4",
            "5,6",
            "7,8",
            "3,4,5,6,7,8"
        ])
        grid.addWidget(self.sem_box, 0, 5)

        # Durations
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

        # --------------------------------------
        # TIME INPUTS
        # --------------------------------------
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

        # --------------------------------------
        # DAYS
        # --------------------------------------
        days_layout = QHBoxLayout()
        self.day_checkboxes = []
        for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]:
            cb = QCheckBox(d)
            cb.setChecked(d in ["Mon", "Tue", "Wed", "Thu", "Fri"])
            self.day_checkboxes.append(cb)
            days_layout.addWidget(cb)
        layout.addLayout(days_layout)

        # Generate button
        self.generate_btn = QPushButton("Generate Timetable")
        self.generate_btn.clicked.connect(self.start_generation)
        layout.addWidget(self.generate_btn)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setRange(0, 0)
        layout.addWidget(self.progress)

        self.status_label = QLabel("Ready.")
        layout.addWidget(self.status_label)

    # ----------------------------------------------------
    # LAUNCH SOLVER
    # ----------------------------------------------------
    @pyqtSlot()
    def start_generation(self):
        self.status_label.setText("⏳ Generating timetable...")
        self.progress.setVisible(True)
        self.generate_btn.setEnabled(False)

        # --------------------------------------
        # YEARS
        # --------------------------------------
        year_text = self.year_box.currentText()
        if year_text == "Select":
            QMessageBox.warning(self, "Invalid Input", "Please select years.")
            return

        try:
            years = [int(x.strip()) for x in year_text.split(",")]
        except:
            years = []

        # --------------------------------------
        # SEMESTERS
        # --------------------------------------
        sem_text = self.sem_box.currentText()

        if sem_text.startswith("Auto"):
            sems = []
            for y in years:
                if y == 2:
                    sems.extend([3, 4])
                elif y == 3:
                    sems.extend([5, 6])
                elif y == 4:
                    sems.extend([7, 8])
        else:
            sems = [int(x.strip()) for x in sem_text.split(",")]

        # --------------------------------------
        # DAYS SELECTED
        # --------------------------------------
        days = [cb.text() for cb in self.day_checkboxes if cb.isChecked()]

        # --------------------------------------
        # PACK INTO SETTINGS CLASS
        # --------------------------------------
        settings = GenerationSettings(
            lecture_duration=self.lecture_spin.value(),
            lab_duration=self.lab_spin.value(),
            lunch_start=self.lunch_start.time().toString("HH:mm"),
            lunch_end=self.lunch_end.time().toString("HH:mm"),
            start_time=self.start_time.time().toString("HH:mm"),
            end_time=self.end_time.time().toString("HH:mm"),
            days=days,
            degree=self.degree_combo.currentText(),
            year=years,
            semester=sems
        )

        self.worker = SolverThread(self.db, settings)
        self.worker.result_ready.connect(self._solver_finished)
        self.worker.start()

    # ----------------------------------------------------
    # AFTER SOLVER FINISHES
    # ----------------------------------------------------
    @pyqtSlot(list, dict, list, str)
    def _solver_finished(self, assignments, info, conflicts, msg):
        self.progress.setVisible(False)
        self.generate_btn.setEnabled(True)
        self.status_label.setText(msg)

        if conflicts:
            details = "\n".join(f"- {c.subject_code}: {c.details}" for c in conflicts)
            QMessageBox.warning(self, "Conflicts Detected", details)

        if assignments:
            self.timetable_generated.emit(assignments, info, conflicts)
