"""
Data Management Tab for Timetable Generator

This module provides a comprehensive interface for managing all data entities:
- Faculty management (add, edit, delete)
- Subject management (add, edit, delete)
- Venue management (add, edit, delete)
- Section management (add, edit, delete)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget, 
    QTableWidgetItem, QPushButton, QLineEdit, QComboBox, QSpinBox,
    QCheckBox, QLabel, QMessageBox, QHeaderView, QFormLayout,
    QGroupBox, QDialog, QDialogButtonBox, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ..database.db_models import Faculty, Subject, Venue, Section


class DataManagementTab(QWidget):
    """
    Tab for managing all data entities in the timetable system
    
    Provides CRUD operations for:
    - Faculty members
    - Subjects/courses
    - Venues (lecture halls and labs)
    - Sections and subsections
    """
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Create tab widget for different data types
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs for each data type
        self.create_faculty_tab()
        self.create_subject_tab()
        self.create_venue_tab()
        self.create_section_tab()
    
    def create_faculty_tab(self):
        """Create faculty management tab"""
        faculty_widget = QWidget()
        layout = QVBoxLayout(faculty_widget)
        
        # Faculty table
        self.faculty_table = QTableWidget()
        self.faculty_table.setColumnCount(4)
        self.faculty_table.setHorizontalHeaderLabels([
            "ID", "Name", "Faculty Code", "Max Hours/Day"
        ])
        self.faculty_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.faculty_table)
        
        # Faculty buttons
        button_layout = QHBoxLayout()
        
        self.add_faculty_btn = QPushButton("Add Faculty")
        self.add_faculty_btn.clicked.connect(self.add_faculty)
        button_layout.addWidget(self.add_faculty_btn)
        
        self.edit_faculty_btn = QPushButton("Edit Faculty")
        self.edit_faculty_btn.clicked.connect(self.edit_faculty)
        button_layout.addWidget(self.edit_faculty_btn)
        
        self.delete_faculty_btn = QPushButton("Delete Faculty")
        self.delete_faculty_btn.clicked.connect(self.delete_faculty)
        button_layout.addWidget(self.delete_faculty_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.tab_widget.addTab(faculty_widget, "Faculty")
    
    def create_subject_tab(self):
        """Create subject management tab"""
        subject_widget = QWidget()
        layout = QVBoxLayout(subject_widget)
        
        # Subject table
        self.subject_table = QTableWidget()
        self.subject_table.setColumnCount(7)
        self.subject_table.setHorizontalHeaderLabels([
            "ID", "Code", "Name", "Type", "Duration", "Year", "Semester"
        ])
        self.subject_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.subject_table)
        
        # Subject buttons
        button_layout = QHBoxLayout()
        
        self.add_subject_btn = QPushButton("Add Subject")
        self.add_subject_btn.clicked.connect(self.add_subject)
        button_layout.addWidget(self.add_subject_btn)
        
        self.edit_subject_btn = QPushButton("Edit Subject")
        self.edit_subject_btn.clicked.connect(self.edit_subject)
        button_layout.addWidget(self.edit_subject_btn)
        
        self.delete_subject_btn = QPushButton("Delete Subject")
        self.delete_subject_btn.clicked.connect(self.delete_subject)
        button_layout.addWidget(self.delete_subject_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.tab_widget.addTab(subject_widget, "Subjects")
    
    def create_venue_tab(self):
        """Create venue management tab"""
        venue_widget = QWidget()
        layout = QVBoxLayout(venue_widget)
        
        # Venue table
        self.venue_table = QTableWidget()
        self.venue_table.setColumnCount(6)
        self.venue_table.setHorizontalHeaderLabels([
            "ID", "Name", "Type", "Capacity", "Building", "Floor"
        ])
        self.venue_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.venue_table)
        
        # Venue buttons
        button_layout = QHBoxLayout()
        
        self.add_venue_btn = QPushButton("Add Venue")
        self.add_venue_btn.clicked.connect(self.add_venue)
        button_layout.addWidget(self.add_venue_btn)
        
        self.edit_venue_btn = QPushButton("Edit Venue")
        self.edit_venue_btn.clicked.connect(self.edit_venue)
        button_layout.addWidget(self.edit_venue_btn)
        
        self.delete_venue_btn = QPushButton("Delete Venue")
        self.delete_venue_btn.clicked.connect(self.delete_venue)
        button_layout.addWidget(self.delete_venue_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.tab_widget.addTab(venue_widget, "Venues")
    
    def create_section_tab(self):
        """Create section management tab"""
        section_widget = QWidget()
        layout = QVBoxLayout(section_widget)
        
        # Section table
        self.section_table = QTableWidget()
        self.section_table.setColumnCount(6)
        self.section_table.setHorizontalHeaderLabels([
            "ID", "Name", "Degree", "Year", "Semester", "Subsections"
        ])
        self.section_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.section_table)
        
        # Section buttons
        button_layout = QHBoxLayout()
        
        self.add_section_btn = QPushButton("Add Section")
        self.add_section_btn.clicked.connect(self.add_section)
        button_layout.addWidget(self.add_section_btn)
        
        self.edit_section_btn = QPushButton("Edit Section")
        self.edit_section_btn.clicked.connect(self.edit_section)
        button_layout.addWidget(self.edit_section_btn)
        
        self.delete_section_btn = QPushButton("Delete Section")
        self.delete_section_btn.clicked.connect(self.delete_section)
        button_layout.addWidget(self.delete_section_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.tab_widget.addTab(section_widget, "Sections")
    
    def load_data(self):
        """Load all data from database"""
        self.load_faculties()
        self.load_subjects()
        self.load_venues()
        self.load_sections()
    
    def load_faculties(self):
        """Load faculty data into table"""
        faculties = self.db_manager.get_faculties()
        self.faculty_table.setRowCount(len(faculties))
        
        for row, faculty in enumerate(faculties):
            self.faculty_table.setItem(row, 0, QTableWidgetItem(str(faculty.id)))
            self.faculty_table.setItem(row, 1, QTableWidgetItem(faculty.name))
            self.faculty_table.setItem(row, 2, QTableWidgetItem(faculty.faculty_code))
            self.faculty_table.setItem(row, 3, QTableWidgetItem(str(faculty.max_hours_per_day)))
    
    def load_subjects(self):
        """Load subject data into table"""
        subjects = self.db_manager.get_subjects()
        self.subject_table.setRowCount(len(subjects))
        
        for row, subject in enumerate(subjects):
            self.subject_table.setItem(row, 0, QTableWidgetItem(str(subject.id)))
            self.subject_table.setItem(row, 1, QTableWidgetItem(subject.code))
            self.subject_table.setItem(row, 2, QTableWidgetItem(subject.name))
            self.subject_table.setItem(row, 3, QTableWidgetItem("Lab" if subject.is_lab else "Lecture"))
            self.subject_table.setItem(row, 4, QTableWidgetItem(str(subject.duration)))
            self.subject_table.setItem(row, 5, QTableWidgetItem(str(subject.year)))
            self.subject_table.setItem(row, 6, QTableWidgetItem(str(subject.semester)))
    
    def load_venues(self):
        """Load venue data into table"""
        venues = self.db_manager.get_venues()
        self.venue_table.setRowCount(len(venues))
        
        for row, venue in enumerate(venues):
            self.venue_table.setItem(row, 0, QTableWidgetItem(str(venue.id)))
            self.venue_table.setItem(row, 1, QTableWidgetItem(venue.name))
            self.venue_table.setItem(row, 2, QTableWidgetItem(venue.venue_type.title()))
            self.venue_table.setItem(row, 3, QTableWidgetItem(str(venue.capacity)))
            self.venue_table.setItem(row, 4, QTableWidgetItem(venue.building))
            self.venue_table.setItem(row, 5, QTableWidgetItem(str(venue.floor)))
    
    def load_sections(self):
        """Load section data into table"""
        sections = self.db_manager.get_sections()
        self.section_table.setRowCount(len(sections))
        
        for row, section in enumerate(sections):
            self.section_table.setItem(row, 0, QTableWidgetItem(str(section.id)))
            self.section_table.setItem(row, 1, QTableWidgetItem(section.name))
            self.section_table.setItem(row, 2, QTableWidgetItem(section.degree))
            self.section_table.setItem(row, 3, QTableWidgetItem(str(section.year)))
            self.section_table.setItem(row, 4, QTableWidgetItem(str(section.semester)))
            subsections_text = ", ".join(section.subsections) if section.subsections else "None"
            self.section_table.setItem(row, 5, QTableWidgetItem(subsections_text))
    
    def add_faculty(self):
        """Add new faculty member"""
        dialog = FacultyDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_faculties()
    
    def edit_faculty(self):
        """Edit selected faculty member"""
        current_row = self.faculty_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a faculty to edit")
            return
        
        faculty_id = int(self.faculty_table.item(current_row, 0).text())
        dialog = FacultyDialog(self, faculty_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_faculties()
    
    def delete_faculty(self):
        """Delete selected faculty member"""
        current_row = self.faculty_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a faculty to delete")
            return
        
        faculty_id = int(self.faculty_table.item(current_row, 0).text())
        faculty_name = self.faculty_table.item(current_row, 1).text()
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete faculty '{faculty_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_manager.delete_faculty(faculty_id):
                self.load_faculties()
                QMessageBox.information(self, "Success", "Faculty deleted successfully")
            else:
                QMessageBox.critical(self, "Error", "Failed to delete faculty")
    
    def add_subject(self):
        """Add new subject"""
        dialog = SubjectDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_subjects()
    
    def edit_subject(self):
        """Edit selected subject"""
        current_row = self.subject_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a subject to edit")
            return
        
        subject_id = int(self.subject_table.item(current_row, 0).text())
        dialog = SubjectDialog(self, subject_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_subjects()
    
    def delete_subject(self):
        """Delete selected subject"""
        current_row = self.subject_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a subject to delete")
            return
        
        subject_id = int(self.subject_table.item(current_row, 0).text())
        subject_name = self.subject_table.item(current_row, 2).text()
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete subject '{subject_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_manager.delete_subject(subject_id):
                self.load_subjects()
                QMessageBox.information(self, "Success", "Subject deleted successfully")
            else:
                QMessageBox.critical(self, "Error", "Failed to delete subject")
    
    def add_venue(self):
        """Add new venue"""
        dialog = VenueDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_venues()
    
    def edit_venue(self):
        """Edit selected venue"""
        current_row = self.venue_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a venue to edit")
            return
        
        venue_id = int(self.venue_table.item(current_row, 0).text())
        dialog = VenueDialog(self, venue_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_venues()
    
    def delete_venue(self):
        """Delete selected venue"""
        current_row = self.venue_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a venue to delete")
            return
        
        venue_id = int(self.venue_table.item(current_row, 0).text())
        venue_name = self.venue_table.item(current_row, 1).text()
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete venue '{venue_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_manager.delete_venue(venue_id):
                self.load_venues()
                QMessageBox.information(self, "Success", "Venue deleted successfully")
            else:
                QMessageBox.critical(self, "Error", "Failed to delete venue")
    
    def add_section(self):
        """Add new section"""
        dialog = SectionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_sections()
    
    def edit_section(self):
        """Edit selected section"""
        current_row = self.section_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a section to edit")
            return
        
        section_id = int(self.section_table.item(current_row, 0).text())
        dialog = SectionDialog(self, section_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_sections()
    
    def delete_section(self):
        """Delete selected section"""
        current_row = self.section_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a section to delete")
            return
        
        section_id = int(self.section_table.item(current_row, 0).text())
        section_name = self.section_table.item(current_row, 1).text()
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete section '{section_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_manager.delete_section(section_id):
                self.load_sections()
                QMessageBox.information(self, "Success", "Section deleted successfully")
            else:
                QMessageBox.critical(self, "Error", "Failed to delete section")


class FacultyDialog(QDialog):
    """Dialog for adding/editing faculty members"""
    
    def __init__(self, parent, faculty_id=None):
        super().__init__(parent)
        self.parent = parent
        self.faculty_id = faculty_id
        self.init_ui()
        
        if faculty_id:
            self.load_faculty_data()
    
    def init_ui(self):
        """Initialize dialog UI"""
        self.setWindowTitle("Add Faculty" if not self.faculty_id else "Edit Faculty")
        self.setModal(True)
        self.resize(400, 200)
        
        layout = QFormLayout(self)
        
        # Name field
        self.name_edit = QLineEdit()
        layout.addRow("Name:", self.name_edit)
        
        # Faculty code field
        self.code_edit = QLineEdit()
        layout.addRow("Faculty Code:", self.code_edit)
        
        # Max hours per day field
        self.max_hours_spin = QSpinBox()
        self.max_hours_spin.setRange(1, 12)
        self.max_hours_spin.setValue(6)
        layout.addRow("Max Hours/Day:", self.max_hours_spin)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def load_faculty_data(self):
        """Load faculty data for editing"""
        # This would need to be implemented to load existing faculty data
        pass
    
    def accept(self):
        """Handle dialog acceptance"""
        name = self.name_edit.text().strip()
        code = self.code_edit.text().strip()
        max_hours = self.max_hours_spin.value()
        
        if not name or not code:
            QMessageBox.warning(self, "Warning", "Please fill in all required fields")
            return
        
        try:
            if self.faculty_id:
                # Update existing faculty
                # This would need to be implemented
                pass
            else:
                # Add new faculty
                self.parent.db_manager.add_faculty(name, code, max_hours)
            
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save faculty: {e}")


class SubjectDialog(QDialog):
    """Dialog for adding/editing subjects"""
    
    def __init__(self, parent, subject_id=None):
        super().__init__(parent)
        self.parent = parent
        self.subject_id = subject_id
        self.init_ui()
    
    def init_ui(self):
        """Initialize dialog UI"""
        self.setWindowTitle("Add Subject" if not self.subject_id else "Edit Subject")
        self.setModal(True)
        self.resize(500, 300)
        
        layout = QFormLayout(self)
        
        # Code field
        self.code_edit = QLineEdit()
        layout.addRow("Subject Code:", self.code_edit)
        
        # Name field
        self.name_edit = QLineEdit()
        layout.addRow("Subject Name:", self.name_edit)
        
        # Type field
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Lecture", "Lab"])
        layout.addRow("Type:", self.type_combo)
        
        # Duration field
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 4)
        self.duration_spin.setValue(1)
        layout.addRow("Duration (hours):", self.duration_spin)
        
        # Year field
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2, 4)
        self.year_spin.setValue(3)
        layout.addRow("Year:", self.year_spin)
        
        # Semester field
        self.semester_spin = QSpinBox()
        self.semester_spin.setRange(3, 8)
        self.semester_spin.setValue(5)
        layout.addRow("Semester:", self.semester_spin)
        
        # Degree field
        self.degree_combo = QComboBox()
        self.degree_combo.addItems(["B.Tech", "M.Tech"])
        layout.addRow("Degree:", self.degree_combo)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def accept(self):
        """Handle dialog acceptance"""
        code = self.code_edit.text().strip()
        name = self.name_edit.text().strip()
        is_lab = self.type_combo.currentText() == "Lab"
        duration = self.duration_spin.value()
        year = self.year_spin.value()
        semester = self.semester_spin.value()
        degree = self.degree_combo.currentText()
        
        if not code or not name:
            QMessageBox.warning(self, "Warning", "Please fill in all required fields")
            return
        
        try:
            if self.subject_id:
                # Update existing subject
                # This would need to be implemented
                pass
            else:
                # Add new subject
                self.parent.db_manager.add_subject(code, name, is_lab, duration, semester, year, degree)
            
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save subject: {e}")


class VenueDialog(QDialog):
    """Dialog for adding/editing venues"""
    
    def __init__(self, parent, venue_id=None):
        super().__init__(parent)
        self.parent = parent
        self.venue_id = venue_id
        self.init_ui()
    
    def init_ui(self):
        """Initialize dialog UI"""
        self.setWindowTitle("Add Venue" if not self.venue_id else "Edit Venue")
        self.setModal(True)
        self.resize(400, 250)
        
        layout = QFormLayout(self)
        
        # Name field
        self.name_edit = QLineEdit()
        layout.addRow("Venue Name:", self.name_edit)
        
        # Type field
        self.type_combo = QComboBox()
        self.type_combo.addItems(["lecture", "lab"])
        layout.addRow("Type:", self.type_combo)
        
        # Capacity field
        self.capacity_spin = QSpinBox()
        self.capacity_spin.setRange(1, 500)
        self.capacity_spin.setValue(60)
        layout.addRow("Capacity:", self.capacity_spin)
        
        # Building field
        self.building_edit = QLineEdit()
        self.building_edit.setText("Main Building")
        layout.addRow("Building:", self.building_edit)
        
        # Floor field
        self.floor_spin = QSpinBox()
        self.floor_spin.setRange(0, 10)
        self.floor_spin.setValue(1)
        layout.addRow("Floor:", self.floor_spin)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def accept(self):
        """Handle dialog acceptance"""
        name = self.name_edit.text().strip()
        venue_type = self.type_combo.currentText()
        capacity = self.capacity_spin.value()
        building = self.building_edit.text().strip()
        floor = self.floor_spin.value()
        
        if not name:
            QMessageBox.warning(self, "Warning", "Please fill in venue name")
            return
        
        try:
            if self.venue_id:
                # Update existing venue
                # This would need to be implemented
                pass
            else:
                # Add new venue
                self.parent.db_manager.add_venue(name, venue_type, capacity, building, floor)
            
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save venue: {e}")


class SectionDialog(QDialog):
    """Dialog for adding/editing sections"""
    
    def __init__(self, parent, section_id=None):
        super().__init__(parent)
        self.parent = parent
        self.section_id = section_id
        self.init_ui()
    
    def init_ui(self):
        """Initialize dialog UI"""
        self.setWindowTitle("Add Section" if not self.section_id else "Edit Section")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QFormLayout(self)
        
        # Name field
        self.name_edit = QLineEdit()
        layout.addRow("Section Name:", self.name_edit)
        
        # Degree field
        self.degree_combo = QComboBox()
        self.degree_combo.addItems(["B.Tech", "M.Tech"])
        layout.addRow("Degree:", self.degree_combo)
        
        # Year field
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2, 4)
        self.year_spin.setValue(3)
        layout.addRow("Year:", self.year_spin)
        
        # Semester field
        self.semester_spin = QSpinBox()
        self.semester_spin.setRange(3, 8)
        self.semester_spin.setValue(5)
        layout.addRow("Semester:", self.semester_spin)
        
        # Strength field
        self.strength_spin = QSpinBox()
        self.strength_spin.setRange(1, 200)
        self.strength_spin.setValue(60)
        layout.addRow("Strength:", self.strength_spin)
        
        # Subsections field
        self.subsections_edit = QLineEdit()
        self.subsections_edit.setPlaceholderText("A1, A2, A3 (comma separated)")
        layout.addRow("Subsections:", self.subsections_edit)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def accept(self):
        """Handle dialog acceptance"""
        name = self.name_edit.text().strip()
        degree = self.degree_combo.currentText()
        year = self.year_spin.value()
        semester = self.semester_spin.value()
        strength = self.strength_spin.value()
        subsections_text = self.subsections_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Warning", "Please fill in section name")
            return
        
        # Parse subsections
        subsections = []
        if subsections_text:
            subsections = [s.strip() for s in subsections_text.split(',') if s.strip()]
        
        try:
            if self.section_id:
                # Update existing section
                # This would need to be implemented
                pass
            else:
                # Add new section
                self.parent.db_manager.add_section(name, semester, year, degree, subsections, strength)
            
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save section: {e}")
