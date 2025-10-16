# Timetable Generator - CSE Department

A comprehensive desktop application for generating timetables for the Computer Science & Engineering department using Python and PyQt6.

## Features

### Core Functionality
- **Data Management**: Complete CRUD operations for faculties, subjects, venues, and sections
- **Intelligent Scheduling**: Constraint-based algorithm with backtracking for optimal timetable generation
- **Interactive Review**: Grid-based timetable display with editing capabilities
- **Professional Export**: High-quality PDF generation with customizable layouts
- **Conflict Resolution**: Comprehensive conflict detection and resolution suggestions

### Advanced Features
- **Multi-degree Support**: B.Tech and M.Tech programs
- **Flexible Time Slots**: Configurable working hours with lunch breaks
- **Smart Constraints**: Faculty availability, venue capacity, section conflicts
- **Lab Management**: Special handling for laboratory sessions with subsections
- **Real-time Validation**: Live conflict checking during generation

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd timetable-generator
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run the Application
```bash
python main.py
```

## Project Structure

```
timetable-generator/
├── main.py                          # Application entry point
├── requirements.txt                 # Python dependencies
├── README.md                       # This file
├── src/                            # Source code directory
│   ├── __init__.py
│   ├── database/                   # Database layer
│   │   ├── __init__.py
│   │   ├── db_models.py           # SQLAlchemy models
│   │   └── database_manager.py    # Database operations
│   ├── scheduler/                  # Scheduling algorithms
│   │   ├── __init__.py
│   │   └── timetable_scheduler.py # Core scheduling logic
│   ├── export/                     # PDF export functionality
│   │   ├── __init__.py
│   │   └── pdf_exporter.py        # ReportLab PDF generation
│   └── views/                      # PyQt6 GUI components
│       ├── __init__.py
│       ├── main_window.py         # Main application window
│       ├── data_management_tab.py # Data CRUD operations
│       ├── timetable_generation_tab.py # Generation interface
│       ├── timetable_review_tab.py # Review and editing
│       └── export_tab.py          # PDF export interface
└── timetable.db                    # SQLite database (created on first run)
```

## Usage Guide

### 1. Data Management

#### Adding Faculty
1. Go to **Data Management** tab
2. Select **Faculty** sub-tab
3. Click **Add Faculty**
4. Fill in:
   - Name: Full name of the faculty member
   - Faculty Code: Unique identifier (e.g., RK001)
   - Max Hours/Day: Maximum teaching hours per day (default: 6)

#### Adding Subjects
1. Select **Subjects** sub-tab
2. Click **Add Subject**
3. Fill in:
   - Subject Code: Course code (e.g., CS301)
   - Subject Name: Full course name
   - Type: Lecture or Lab
   - Duration: Hours per session (1 for lectures, 2 for labs)
   - Year/Semester: Academic year and semester
   - Degree: B.Tech or M.Tech

#### Adding Venues
1. Select **Venues** sub-tab
2. Click **Add Venue**
3. Fill in:
   - Venue Name: Room identifier (e.g., LT-101)
   - Type: Lecture or Lab
   - Capacity: Maximum seating capacity
   - Building: Building name
   - Floor: Floor number

#### Adding Sections
1. Select **Sections** sub-tab
2. Click **Add Section**
3. Fill in:
   - Section Name: A, B, C, or D
   - Degree: B.Tech or M.Tech
   - Year/Semester: Academic details
   - Strength: Number of students
   - Subsections: Comma-separated list (e.g., A1, A2, A3)

### 2. Timetable Generation

#### Basic Settings
1. Go to **Generate Timetable** tab
2. Configure:
   - **Degree**: B.Tech or M.Tech
   - **Year**: 2nd, 3rd, or 4th year
   - **Semester**: 3rd through 8th semester
   - **Sections**: Select one or more sections

#### Time Configuration
- **Start Time**: Beginning of working day (default: 09:00)
- **End Time**: End of working day (default: 18:00)
- **Lunch Break**: Start and end times (default: 13:00-14:00)

#### Constraints
- **Max Hours per Day**: Faculty workload limit (default: 6)
- **Lecture Duration**: Hours per lecture session (default: 1)
- **Lab Duration**: Hours per lab session (default: 2)

#### Working Days
Select which days of the week are working days (Monday-Saturday).

#### Generate
Click **Generate Timetable** to start the scheduling process. The algorithm will:
1. Prioritize labs (harder to schedule)
2. Apply constraint-based scheduling
3. Use backtracking for conflict resolution
4. Display results with any conflicts

### 3. Review and Edit

#### Timetable Grid
- **Rows**: Time slots from start to end time
- **Columns**: Working days
- **Cells**: Color-coded assignments
  - Green: Laboratory sessions
  - Blue: Lecture sessions
  - White: Empty slots

#### Cell Content
Each cell displays:
- Subsection (if applicable)
- Subject code (bold)
- Subject name
- Faculty name and code
- Venue name

#### Editing
- Double-click any cell to edit the assignment
- Review conflicts in the right panel
- Check statistics for timetable overview

#### Approval
Click **Approve Timetable** when satisfied with the schedule.

### 4. Export to PDF

#### Preview
1. Go to **Export** tab
2. Click **Preview PDF** to see the formatted output
3. Review layout and content

#### Export
1. Click **Export to PDF**
2. Choose save location
3. Wait for export completion

#### PDF Features
- **A4 Landscape Format**: Optimized for printing
- **Professional Header**: Department name, degree, semester
- **Grid Layout**: Time slots and days clearly organized
- **Detailed Cells**: All assignment information included
- **Color Coding**: Visual distinction between lectures and labs

## Algorithm Details

### Constraint-Based Scheduling

The timetable generator uses a sophisticated algorithm that:

1. **Prioritizes Subjects**: Labs are scheduled first due to their complexity
2. **Applies Constraints**:
   - No faculty double-booking
   - Faculty daily hour limits
   - Venue availability
   - Section/subsection conflicts
3. **Uses Backtracking**: When conflicts occur, the algorithm backtracks to find alternative solutions
4. **Validates Results**: Final validation ensures all constraints are met

### Conflict Types

The system detects and reports:
- **Faculty Conflicts**: Double-booking of faculty members
- **Venue Conflicts**: Multiple classes in the same venue
- **Section Conflicts**: Overlapping classes for the same section
- **Constraint Violations**: Exceeding daily hour limits

## Customization

### Adding New Constraints

To add custom constraints, modify the `TimetableScheduler` class:

```python
def _is_valid_placement(self, subject, faculty, section, venue, slot, duration, settings):
    # Add your custom constraint checks here
    if your_custom_constraint():
        return False
    return True
```

### Modifying PDF Layout

To customize PDF output, edit the `PDFExporter` class:

```python
def _get_table_style(self, num_days, num_slots):
    # Modify table styling
    style_data = [
        # Your custom styles here
    ]
    return TableStyle(style_data)
```

### Database Schema Changes

To modify the database schema:

1. Update models in `src/database/db_models.py`
2. Delete existing `timetable.db` file
3. Restart the application to recreate the database

## Troubleshooting

### Common Issues

#### "No placement found" errors
- **Cause**: Insufficient venues or faculty for the selected subjects
- **Solution**: Add more venues or faculty members, or reduce the number of subjects

#### PDF export fails
- **Cause**: Missing ReportLab dependency or file permissions
- **Solution**: Reinstall requirements: `pip install -r requirements.txt`

#### Database errors
- **Cause**: Corrupted database file
- **Solution**: Delete `timetable.db` and restart the application

#### GUI not responding
- **Cause**: Large dataset or complex scheduling
- **Solution**: Reduce the number of subjects or sections, or increase timeout values

### Performance Optimization

For large datasets:
1. Reduce the number of subjects per generation
2. Limit the number of sections
3. Use fewer working days
4. Increase the backtracking depth limit

## Development

### Adding New Features

1. **Database Changes**: Modify models in `src/database/db_models.py`
2. **Business Logic**: Add methods to `src/scheduler/timetable_scheduler.py`
3. **GUI Components**: Create new widgets in `src/views/`
4. **Export Formats**: Extend `src/export/pdf_exporter.py`

### Testing

Run the application with sample data:
1. The application automatically seeds the database with sample data on first run
2. Use the sample faculties, subjects, venues, and sections for testing
3. Generate timetables with different constraint combinations

### Code Structure

The application follows MVC (Model-View-Controller) pattern:
- **Models**: Database entities in `src/database/`
- **Views**: PyQt6 GUI components in `src/views/`
- **Controllers**: Business logic in `src/scheduler/` and `src/export/`

## License

This project is developed for the CSE Department and is intended for educational and administrative use.

## Support

For technical support or feature requests, please contact the CSE Department administration.

## Version History

### v1.0.0
- Initial release
- Complete timetable generation system
- PDF export functionality
- Comprehensive data management
- Constraint-based scheduling algorithm

---

**Developed by**: CSE Department  
**Technology Stack**: Python, PyQt6, SQLAlchemy, ReportLab  
**Database**: SQLite  
**Platform**: Cross-platform (Windows, macOS, Linux)
# PDQA
