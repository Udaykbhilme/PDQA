"""
Timetable Review Tab for Timetable Generator

This module provides the interface for reviewing and editing generated timetables
with a grid-based display and conflict resolution capabilities.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QMessageBox, QHeaderView, QGroupBox,
    QTextEdit, QScrollArea, QFrame, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette


class TimetableReviewTab(QWidget):
    """
    Tab for reviewing and editing generated timetables
    
    Features:
    - Grid-based timetable display
    - Color-coded cells for lectures vs labs
    - Conflict display and resolution
    - Cell editing capabilities
    - Statistics display
    """
    
    timetable_updated = pyqtSignal(list, dict)  # assignments, info
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.current_assignments = []
        self.current_timetable_info = {}
        self.current_conflicts = []
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Create splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left side - Timetable grid
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Timetable info
        self.info_label = QLabel("No timetable loaded")
        self.info_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #1e3a8a;")
        left_layout.addWidget(self.info_label)
        
        # Timetable grid
        self.timetable_table = QTableWidget()
        self.timetable_table.setAlternatingRowColors(True)
        self.timetable_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.timetable_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        left_layout.addWidget(self.timetable_table)
        
        # Timetable controls
        controls_layout = QHBoxLayout()
        
        self.approve_btn = QPushButton("Approve Timetable")
        self.approve_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.approve_btn.clicked.connect(self.approve_timetable)
        self.approve_btn.setEnabled(False)
        controls_layout.addWidget(self.approve_btn)
        
        self.regenerate_btn = QPushButton("Regenerate")
        self.regenerate_btn.clicked.connect(self.regenerate_timetable)
        self.regenerate_btn.setEnabled(False)
        controls_layout.addWidget(self.regenerate_btn)
        
        controls_layout.addStretch()
        left_layout.addLayout(controls_layout)
        
        splitter.addWidget(left_widget)
        
        # Right side - Conflicts and statistics
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Conflicts group
        conflicts_group = QGroupBox("Conflicts")
        conflicts_layout = QVBoxLayout(conflicts_group)
        
        self.conflicts_text = QTextEdit()
        self.conflicts_text.setMaximumHeight(200)
        self.conflicts_text.setReadOnly(True)
        self.conflicts_text.setPlaceholderText("No conflicts detected")
        conflicts_layout.addWidget(self.conflicts_text)
        
        right_layout.addWidget(conflicts_group)
        
        # Statistics group
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_text = QTextEdit()
        self.stats_text.setMaximumHeight(150)
        self.stats_text.setReadOnly(True)
        self.stats_text.setPlaceholderText("No statistics available")
        stats_layout.addWidget(self.stats_text)
        
        right_layout.addWidget(stats_group)
        
        # Instructions
        instructions_group = QGroupBox("Instructions")
        instructions_layout = QVBoxLayout(instructions_group)
        
        instructions_text = QTextEdit()
        instructions_text.setMaximumHeight(100)
        instructions_text.setReadOnly(True)
        instructions_text.setHtml("""
        <b>How to use:</b><br/>
        • Double-click a cell to edit the assignment<br/>
        • Green cells indicate labs, blue cells indicate lectures<br/>
        • Review conflicts in the right panel<br/>
        • Click 'Approve Timetable' when satisfied<br/>
        • Use 'Regenerate' to create a new timetable
        """)
        instructions_layout.addWidget(instructions_text)
        
        right_layout.addWidget(instructions_group)
        
        right_layout.addStretch()
        splitter.addWidget(right_widget)
        
        # Set splitter proportions
        splitter.setSizes([800, 400])
    
    def set_timetable(self, assignments, timetable_info, conflicts):
        """Set the current timetable data"""
        self.current_assignments = assignments
        self.current_timetable_info = timetable_info
        self.current_conflicts = conflicts
        
        # Update UI
        self.update_info_label()
        self.create_timetable_grid()
        self.update_conflicts_display()
        self.update_statistics()
        
        # Enable controls
        self.approve_btn.setEnabled(True)
        self.regenerate_btn.setEnabled(True)
    
    def clear_timetable(self):
        """Clear the current timetable"""
        self.current_assignments = []
        self.current_timetable_info = {}
        self.current_conflicts = []
        
        self.timetable_table.clear()
        self.timetable_table.setRowCount(0)
        self.timetable_table.setColumnCount(0)
        
        self.info_label.setText("No timetable loaded")
        self.conflicts_text.clear()
        self.stats_text.clear()
        
        self.approve_btn.setEnabled(False)
        self.regenerate_btn.setEnabled(False)
    
    def update_info_label(self):
        """Update the timetable info label"""
        if not self.current_timetable_info:
            return
        
        info = self.current_timetable_info
        text = f"{info.get('degree', 'B.Tech')} - Year {info.get('year', '')}, Semester {info.get('semester', '')}"
        sections = info.get('sections', [])
        if sections:
            text += f" | Sections: {', '.join(sections)}"
        
        self.info_label.setText(text)
    
    def create_timetable_grid(self):
        """Create the timetable grid display"""
        if not self.current_timetable_info:
            return
        
        # Generate time slots
        time_slots = self.generate_time_slots()
        days = self.current_timetable_info.get('days', ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'])
        
        # Set up table
        self.timetable_table.setRowCount(len(time_slots))
        self.timetable_table.setColumnCount(len(days) + 1)  # +1 for time column
        
        # Set headers
        headers = ['Time'] + days
        self.timetable_table.setHorizontalHeaderLabels(headers)
        
        # Fill time column
        for row, slot in enumerate(time_slots):
            time_item = QTableWidgetItem(f"{slot['start']}\n{slot['end']}")
            time_item.setFlags(time_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            time_item.setBackground(QColor(240, 240, 240))
            time_item.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            self.timetable_table.setItem(row, 0, time_item)
        
        # Fill assignment cells
        for row, slot in enumerate(time_slots):
            for col, day in enumerate(days):
                cell_content = self.get_cell_content(day, slot['start'])
                cell_item = QTableWidgetItem(cell_content)
                
                # Set cell properties based on content
                if cell_content:
                    # Determine if it's a lab or lecture
                    is_lab = self.is_lab_assignment(day, slot['start'])
                    if is_lab:
                        cell_item.setBackground(QColor(200, 255, 200))  # Light green for labs
                    else:
                        cell_item.setBackground(QColor(200, 220, 255))  # Light blue for lectures
                    
                    cell_item.setFont(QFont("Arial", 8))
                else:
                    cell_item.setBackground(QColor(255, 255, 255))  # White for empty
                
                cell_item.setFlags(cell_item.flags() | Qt.ItemFlag.ItemIsEditable)
                self.timetable_table.setItem(row, col + 1, cell_item)
        
        # Set row heights
        for row in range(len(time_slots)):
            self.timetable_table.setRowHeight(row, 80)
    
    def generate_time_slots(self):
        """Generate time slots for the timetable"""
        if not self.current_timetable_info:
            return []
        
        start_time = self.current_timetable_info.get('start_time', '09:00')
        end_time = self.current_timetable_info.get('end_time', '18:00')
        lunch_start = self.current_timetable_info.get('lunch_start', '13:00')
        lunch_end = self.current_timetable_info.get('lunch_end', '14:00')
        
        slots = []
        start_minutes = self.time_to_minutes(start_time)
        end_minutes = self.time_to_minutes(end_time)
        lunch_start_minutes = self.time_to_minutes(lunch_start)
        lunch_end_minutes = self.time_to_minutes(lunch_end)
        
        for time in range(start_minutes, end_minutes, 60):
            # Skip lunch break
            if time >= lunch_start_minutes and time < lunch_end_minutes:
                continue
            
            slots.append({
                'start': self.minutes_to_time(time),
                'end': self.minutes_to_time(time + 60)
            })
        
        return slots
    
    def get_cell_content(self, day, start_time):
        """Get content for a specific cell"""
        # Find assignments for this day and time
        cell_assignments = [
            a for a in self.current_assignments 
            if a.day == day and a.start_time == start_time
        ]
        
        if not cell_assignments:
            return ""
        
        # For now, handle single assignment per cell
        assignment = cell_assignments[0]
        
        # Get related objects (this would need to be loaded from database)
        subject = getattr(assignment, 'subject', None)
        faculty = getattr(assignment, 'faculty', None)
        venue = getattr(assignment, 'venue', None)
        
        if not all([subject, faculty, venue]):
            return "Data Missing"
        
        # Format cell content
        content_parts = []
        
        if assignment.subsection:
            content_parts.append(f"{assignment.subsection}")
        
        content_parts.append(f"{subject.code}")
        content_parts.append(f"{subject.name}")
        content_parts.append(f"{faculty.name} ({faculty.faculty_code})")
        content_parts.append(f"{venue.name}")
        
        return "\n".join(content_parts)
    
    def is_lab_assignment(self, day, start_time):
        """Check if assignment at given day/time is a lab"""
        cell_assignments = [
            a for a in self.current_assignments 
            if a.day == day and a.start_time == start_time
        ]
        
        if not cell_assignments:
            return False
        
        assignment = cell_assignments[0]
        subject = getattr(assignment, 'subject', None)
        return subject and subject.is_lab
    
    def update_conflicts_display(self):
        """Update the conflicts display"""
        if not self.current_conflicts:
            self.conflicts_text.setPlainText("No conflicts detected")
            return
        
        conflict_text = f"Found {len(self.current_conflicts)} conflicts:\n\n"
        
        for i, conflict in enumerate(self.current_conflicts, 1):
            conflict_text += f"{i}. {conflict.subject_code}: {conflict.details}\n"
            conflict_text += f"   Type: {conflict.type} | Severity: {conflict.severity}\n\n"
        
        self.conflicts_text.setPlainText(conflict_text)
    
    def update_statistics(self):
        """Update the statistics display"""
        if not self.current_assignments:
            self.stats_text.setPlainText("No statistics available")
            return
        
        # Calculate statistics
        total_assignments = len(self.current_assignments)
        lab_count = sum(1 for a in self.current_assignments if getattr(a, 'subject', None) and a.subject.is_lab)
        lecture_count = total_assignments - lab_count
        
        # Count unique faculty
        faculty_ids = set()
        for assignment in self.current_assignments:
            if hasattr(assignment, 'faculty_id'):
                faculty_ids.add(assignment.faculty_id)
        unique_faculty = len(faculty_ids)
        
        # Count unique venues
        venue_ids = set()
        for assignment in self.current_assignments:
            if hasattr(assignment, 'venue_id'):
                venue_ids.add(assignment.venue_id)
        unique_venues = len(venue_ids)
        
        stats_text = f"""Timetable Statistics:

Total Assignments: {total_assignments}
• Lectures: {lecture_count}
• Labs: {lab_count}

Unique Faculty: {unique_faculty}
Unique Venues: {unique_venues}

Conflicts: {len(self.current_conflicts)}
Status: {'Approved' if not self.current_conflicts else 'Needs Review'}"""
        
        self.stats_text.setPlainText(stats_text)
    
    def approve_timetable(self):
        """Approve the current timetable"""
        if not self.current_assignments:
            QMessageBox.warning(self, "Warning", "No timetable to approve")
            return
        
        reply = QMessageBox.question(
            self, "Approve Timetable",
            "Are you sure you want to approve this timetable?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Update timetable status
            self.current_timetable_info['status'] = 'approved'
            
            # Emit signal to main window
            self.timetable_updated.emit(self.current_assignments, self.current_timetable_info)
            
            QMessageBox.information(self, "Success", "Timetable approved successfully!")
    
    def regenerate_timetable(self):
        """Request regeneration of the timetable"""
        reply = QMessageBox.question(
            self, "Regenerate Timetable",
            "Are you sure you want to regenerate the timetable? Current changes will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Switch to generation tab
            # This would need to be implemented to communicate with main window
            pass
    
    def time_to_minutes(self, time_string):
        """Convert time string (HH:MM) to minutes"""
        hours, minutes = map(int, time_string.split(':'))
        return hours * 60 + minutes
    
    def minutes_to_time(self, minutes):
        """Convert minutes to time string (HH:MM)"""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
