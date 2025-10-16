"""
Timetable Generation Tab for Timetable Generator

This module provides the interface for generating timetables with various
constraints and settings.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QComboBox, QSpinBox, QCheckBox, QPushButton, QLabel, QTextEdit,
    QProgressBar, QMessageBox, QLineEdit, QTimeEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer, QTime
from PyQt6.QtGui import QFont

from ..scheduler.timetable_scheduler import GenerationSettings


class TimetableGenerationTab(QWidget):
    """
    Tab for generating timetables with configurable constraints
    
    Features:
    - Degree, year, semester selection
    - Section selection
    - Time slot configuration
    - Constraint settings
    - Generation progress tracking
    """
    
    timetable_generated = pyqtSignal(list, dict, list)  # assignments, info, conflicts
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Create form layout for generation settings
        form_layout = QFormLayout()
        
        # Basic Information Group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        # Degree selection
        self.degree_combo = QComboBox()
        self.degree_combo.addItems(["B.Tech", "M.Tech"])
        basic_layout.addRow("Degree:", self.degree_combo)
        
        # Year selection
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2, 4)
        self.year_spin.setValue(3)
        basic_layout.addRow("Year:", self.year_spin)
        
        # Semester selection
        self.semester_spin = QSpinBox()
        self.semester_spin.setRange(3, 8)
        self.semester_spin.setValue(5)
        basic_layout.addRow("Semester:", self.semester_spin)
        
        # Section selection
        self.sections_layout = QVBoxLayout()
        self.section_checkboxes = {}
        basic_layout.addRow("Sections:", self.sections_layout)
        
        layout.addWidget(basic_group)
        
        # Time Configuration Group
        time_group = QGroupBox("Time Configuration")
        time_layout = QFormLayout(time_group)
        
        # Start time
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setTime(QTime.fromString("09:00", "HH:mm"))
        time_layout.addRow("Start Time:", self.start_time_edit)
        
        # End time
        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setTime(QTime.fromString("18:00", "HH:mm"))
        time_layout.addRow("End Time:", self.end_time_edit)
        
        # Lunch start
        self.lunch_start_edit = QTimeEdit()
        self.lunch_start_edit.setTime(QTime.fromString("13:00", "HH:mm"))
        time_layout.addRow("Lunch Start:", self.lunch_start_edit)
        
        # Lunch end
        self.lunch_end_edit = QTimeEdit()
        self.lunch_end_edit.setTime(QTime.fromString("14:00", "HH:mm"))
        time_layout.addRow("Lunch End:", self.lunch_end_edit)
        
        layout.addWidget(time_group)
        
        # Constraints Group
        constraints_group = QGroupBox("Constraints")
        constraints_layout = QFormLayout(constraints_group)
        
        # Max hours per day
        self.max_hours_spin = QSpinBox()
        self.max_hours_spin.setRange(1, 12)
        self.max_hours_spin.setValue(6)
        constraints_layout.addRow("Max Hours per Day:", self.max_hours_spin)
        
        # Lecture duration
        self.lecture_duration_spin = QSpinBox()
        self.lecture_duration_spin.setRange(1, 3)
        self.lecture_duration_spin.setValue(1)
        constraints_layout.addRow("Lecture Duration (hours):", self.lecture_duration_spin)
        
        # Lab duration
        self.lab_duration_spin = QSpinBox()
        self.lab_duration_spin.setRange(1, 4)
        self.lab_duration_spin.setValue(2)
        constraints_layout.addRow("Lab Duration (hours):", self.lab_duration_spin)
        
        layout.addWidget(constraints_group)
        
        # Days selection
        days_group = QGroupBox("Working Days")
        days_layout = QHBoxLayout(days_group)
        
        self.days_checkboxes = {}
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for day in days:
            checkbox = QCheckBox(day)
            checkbox.setChecked(True)
            self.days_checkboxes[day] = checkbox
            days_layout.addWidget(checkbox)
        
        layout.addWidget(days_group)
        
        # Generation controls
        controls_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("Generate Timetable")
        self.generate_btn.clicked.connect(self.generate_timetable)
        self.generate_btn.setStyleSheet("""
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
        controls_layout.addWidget(self.generate_btn)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        controls_layout.addWidget(self.progress_bar)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Generation log
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("Generation log will appear here...")
        layout.addWidget(self.log_text)
    
    def load_data(self):
        """Load data from database"""
        # Load sections based on current settings
        self.update_sections()
        
        # Connect signals for dynamic updates
        self.degree_combo.currentTextChanged.connect(self.update_sections)
        self.year_spin.valueChanged.connect(self.update_sections)
        self.semester_spin.valueChanged.connect(self.update_sections)
    
    def update_sections(self):
        """Update available sections based on current settings"""
        # Clear existing checkboxes
        for checkbox in self.section_checkboxes.values():
            self.sections_layout.removeWidget(checkbox)
            checkbox.deleteLater()
        self.section_checkboxes.clear()
        
        # Get sections from database
        degree = self.degree_combo.currentText()
        year = self.year_spin.value()
        semester = self.semester_spin.value()
        
        sections = self.db_manager.get_sections(year=year, semester=semester, degree=degree)
        
        # Create checkboxes for each section
        for section in sections:
            checkbox = QCheckBox(f"Section {section.name}")
            checkbox.setChecked(True)
            self.section_checkboxes[section.name] = checkbox
            self.sections_layout.addWidget(checkbox)
    
    def start_generation(self):
        """Start timetable generation process"""
        self.generate_timetable()
    
    def generate_timetable(self):
        """Generate timetable with current settings"""
        # Validate inputs
        selected_sections = [name for name, checkbox in self.section_checkboxes.items() if checkbox.isChecked()]
        
        if not selected_sections:
            QMessageBox.warning(self, "Warning", "Please select at least one section")
            return
        
        # Get selected days
        selected_days = [day for day, checkbox in self.days_checkboxes.items() if checkbox.isChecked()]
        
        if not selected_days:
            QMessageBox.warning(self, "Warning", "Please select at least one working day")
            return
        
        # Create generation settings
        settings = GenerationSettings(
            degree=self.degree_combo.currentText(),
            year=self.year_spin.value(),
            semester=self.semester_spin.value(),
            sections=selected_sections,
            start_time=self.start_time_edit.time().toString("HH:mm"),
            end_time=self.end_time_edit.time().toString("HH:mm"),
            lunch_start=self.lunch_start_edit.time().toString("HH:mm"),
            lunch_end=self.lunch_end_edit.time().toString("HH:mm"),
            days=selected_days,
            max_hours_per_day=self.max_hours_spin.value(),
            lab_duration=self.lab_duration_spin.value(),
            lecture_duration=self.lecture_duration_spin.value()
        )
        
        # Start generation
        self.start_generation_process(settings)
    
    def start_generation_process(self, settings: GenerationSettings):
        """Start the generation process in a separate thread"""
        # Disable generate button and show progress
        self.generate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.log_text.clear()
        self.log_text.append("Starting timetable generation...")
        
        # Create and start generation thread
        self.generation_thread = GenerationThread(self.db_manager, settings)
        self.generation_thread.progress_updated.connect(self.update_progress)
        self.generation_thread.generation_completed.connect(self.on_generation_completed)
        self.generation_thread.generation_failed.connect(self.on_generation_failed)
        self.generation_thread.start()
    
    def update_progress(self, message: str):
        """Update generation progress"""
        self.log_text.append(message)
        # Auto-scroll to bottom
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
    
    def on_generation_completed(self, assignments, timetable_info, conflicts):
        """Handle successful generation completion"""
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)
        self.log_text.append("Generation completed successfully!")
        
        # Emit signal to main window
        self.timetable_generated.emit(assignments, timetable_info, conflicts)
    
    def on_generation_failed(self, error_message: str):
        """Handle generation failure"""
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)
        self.log_text.append(f"Generation failed: {error_message}")
        
        QMessageBox.critical(self, "Generation Failed", f"Failed to generate timetable:\n{error_message}")


class GenerationThread(QThread):
    """Thread for running timetable generation"""
    
    progress_updated = pyqtSignal(str)
    generation_completed = pyqtSignal(list, dict, list)
    generation_failed = pyqtSignal(str)
    
    def __init__(self, db_manager, settings):
        super().__init__()
        self.db_manager = db_manager
        self.settings = settings
    
    def run(self):
        """Run the generation process"""
        try:
            from ..scheduler.timetable_scheduler import TimetableScheduler
            
            self.progress_updated.emit("Initializing scheduler...")
            scheduler = TimetableScheduler(self.db_manager)
            
            self.progress_updated.emit("Loading data...")
            # Data loading is handled by the scheduler
            
            self.progress_updated.emit("Generating timetable...")
            assignments, conflicts = scheduler.generate_timetable(self.settings)
            
            self.progress_updated.emit(f"Generated {len(assignments)} assignments")
            if conflicts:
                self.progress_updated.emit(f"Found {len(conflicts)} conflicts")
            
            # Create timetable info
            timetable_info = {
                'degree': self.settings.degree,
                'year': self.settings.year,
                'semester': self.settings.semester,
                'sections': self.settings.sections,
                'start_time': self.settings.start_time,
                'end_time': self.settings.end_time,
                'lunch_start': self.settings.lunch_start,
                'lunch_end': self.settings.lunch_end,
                'days': self.settings.days,
                'max_hours_per_day': self.settings.max_hours_per_day,
                'lab_duration': self.settings.lab_duration,
                'lecture_duration': self.settings.lecture_duration
            }
            
            self.generation_completed.emit(assignments, timetable_info, conflicts)
            
        except Exception as e:
            self.generation_failed.emit(str(e))
