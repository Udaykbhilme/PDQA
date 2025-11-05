"""
Timetable Generation Tab — UI layer that triggers the scheduler.
Now cleaned up and simplified to pass GenerationSettings properly.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QSpinBox, QMessageBox
)
from PyQt6.QtCore import pyqtSignal

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

        # Duration settings
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(QLabel("Lecture Duration (hrs):"))
        self.lecture_spin = QSpinBox()
        self.lecture_spin.setRange(1, 4)
        self.lecture_spin.setValue(1)
        settings_layout.addWidget(self.lecture_spin)

        settings_layout.addWidget(QLabel("Lab Duration (hrs):"))
        self.lab_spin = QSpinBox()
        self.lab_spin.setRange(1, 4)
        self.lab_spin.setValue(2)
        settings_layout.addWidget(self.lab_spin)

        layout.addLayout(settings_layout)

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
            settings = GenerationSettings(
                lecture_duration=self.lecture_spin.value(),
                lab_duration=self.lab_spin.value(),
            )

            assignments, info, conflicts = self.scheduler.generate_timetable(settings)
            self.status_label.setText(f"Generated {len(assignments)} classes.")
            self.timetable_generated.emit(assignments, info, conflicts)

        except Exception as e:
            self.status_label.setText("Error generating timetable.")
            QMessageBox.critical(self, "Error", str(e))
