"""
Timetable Generation Tab — UI layer that triggers the scheduler.
Now includes year/semester and lunch/start/end controls, and passes metadata to scheduler.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QSpinBox,
    QComboBox, QTimeEdit, QCheckBox, QGridLayout, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, QTime

from ..scheduler.timetable_scheduler import TimetableScheduler, GenerationSettings


class TimetableGenerationTab(QWidget):
    """Tab for generating timetables."""

    timetable_generated = pyqtSignal(list, dict, list)

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.scheduler = TimetableScheduler(self.db)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Top grid: degree / year / semester / durations
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
        self.lab_spin.setValue(2)  # default 2 hours for labs
        grid.addWidget(self.lab_spin, 1, 3)

        layout.addLayout(grid)

        # Time settings and lunch
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Start Time:"))
        self.start_time = QTimeEdit()
        self.start_time.setTime(QTime.fromString("09:00", "HH:mm"))
        time_layout.addWidget(self.start_time)

        time_layout.addWidget(QLabel("End Time:"))
        self.end_time = QTimeEdit()
        self.end_time.setTime(QTime.fromString("17:00", "HH:mm"))
        time_layout.addWidget(self.end_time)

        time_layout.addWidget(QLabel("Lunch Start:"))
        self.lunch_start = QTimeEdit()
        self.lunch_start.setTime(QTime.fromString("13:00", "HH:mm"))
        time_layout.addWidget(self.lunch_start)

        time_layout.addWidget(QLabel("Lunch End:"))
        self.lunch_end = QTimeEdit()
        self.lunch_end.setTime(QTime.fromString("14:00", "HH:mm"))
        time_layout.addWidget(self.lunch_end)

        layout.addLayout(time_layout)

        # Days (simple checkboxes)
        days_layout = QHBoxLayout()
        self.day_checkboxes = []
        for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]:
            cb = QCheckBox(d)
            cb.setChecked(True if d != "Sat" else False)  # default Mon-Fri
            days_layout.addWidget(cb)
            self.day_checkboxes.append(cb)

        layout.addLayout(days_layout)

        # Generate button
        self.generate_btn = QPushButton("Generate Timetable")
        self.generate_btn.clicked.connect(self.start_generation)
        layout.addWidget(self.generate_btn)

        # Status label
        self.status_label = QLabel("Ready to generate.")
        layout.addWidget(self.status_label)

    def start_generation(self):
        """Trigger timetable generation process."""
        self.status_label.setText("Generating timetable...")
        try:
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

            assignments, info, conflicts = self.scheduler.generate_timetable(settings)
            self.status_label.setText(f"Generated {len(assignments)} classes. Conflicts: {len(conflicts)}")
            # emit for main window to consume
            self.timetable_generated.emit(assignments, info, conflicts)

        except Exception as e:
            self.status_label.setText("Error generating timetable.")
            QMessageBox.critical(self, "Error", str(e))
