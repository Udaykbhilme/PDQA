# Timetable Generator – CSE Department

Let’s be honest: creating a college timetable manually is a slow-motion disaster. It’s a mix of Excel frustration, caffeine dependency, and regret.
This project exists to end that particular cycle of pain.

The **Timetable Generator** is a desktop application built using **Python and PyQt6**.
It automates timetable creation, allows full manual editing, detects conflicts in real-time, and exports professional PDF schedules.
In short: it’s Excel, if Excel had a conscience.

---

## What It Actually Does

* Stores your department data — faculties, subjects, venues, sections — in one place.
* Automatically generates timetables using a constraint-based scheduling algorithm.
* Lets you edit the timetable interactively: change subjects, teachers, rooms, or subgroups directly on the grid.
* Detects conflicts instantly (because two classes in one room isn’t “multitasking”).
* Exports clean, color-coded PDF timetables ready for printing or submission.

Basically, it compresses a week’s worth of departmental chaos into a few clicks.

---

## Key Features

| Feature                     | Description                                                                   |
| --------------------------- | ----------------------------------------------------------------------------- |
| **Data Management**         | CRUD operations for faculty, subjects, venues, and sections.                  |
| **Automatic Scheduling**    | Constraint-based, backtracking algorithm that actually respects human limits. |
| **Editable Review Grid**    | Double-click any slot to edit subject, faculty, venue, time, or subgroup.     |
| **Manual Allocation**       | Assign classes manually to empty slots — no regeneration required.            |
| **Lab Subgroup Logic**      | Handles A1/A2/A3 and B1/B2/B3 labs with parallel scheduling.                  |
| **Conflict Detection**      | Prevents double-booking of faculty, sections, or rooms.                       |
| **Full PDF Preview**        | See the complete timetable before exporting — no half-baked thumbnails.       |
| **Professional PDF Export** | A4 landscape, color-coded, and formatted for clean printing.                  |

---

## How It’s Built

* **Frontend:** PyQt6
* **Backend:** SQLAlchemy + SQLite
* **Logic:** Constraint-based scheduler with backtracking
* **Export Engine:** ReportLab (for PDFs)

It’s structured like a real application, not a “final version (real)_new2.xlsx” situation.

---

## File Structure

You don’t need to guess what lives where. Here’s how the codebase is organized:

```
timetable-generator/
├── main.py                          # App entry point
├── requirements.txt                 # Dependencies list
├── README.md                        # This file
├── src/
│   ├── __init__.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db_models.py             # SQLAlchemy models
│   │   └── database_manager.py      # Database setup, seeding, CRUD logic
│   ├── scheduler/
│   │   ├── __init__.py
│   │   └── timetable_scheduler.py   # Scheduling algorithm & constraint logic
│   ├── export/
│   │   ├── __init__.py
│   │   └── pdf_exporter.py          # PDF generation & layout formatting
│   └── views/
│       ├── __init__.py
│       ├── main_window.py           # Main app window, menus, toolbar
│       ├── data_management_tab.py   # CRUD interfaces for all entities
│       ├── timetable_generation_tab.py  # Timetable generation UI
│       ├── timetable_review_tab.py  # Interactive review & editing grid
│       └── export_tab.py            # PDF preview & export interface
└── timetable.db                     # SQLite database (auto-created on first run)
```

---

## Setup

### Requirements

* Python 3.8 or higher
* pip (Python package manager)

### Installation

```bash
git clone <repository-url>
cd timetable-generator
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

If it doesn’t open, check your Python version. If it still doesn’t, congratulations — you’re debugging now.

---

## How to Use

### Step 1: Data Management

Start by feeding the system what it needs to think:

* Add **faculties**, **subjects**, **venues**, and **sections** under the *Data Management* tab.
* You can add, edit, or delete anything — it’s built for real-world chaos.

### Step 2: Generate Timetable

Go to the *Generate Timetable* tab:

* Choose degree, year, semester, and working days.
* Hit **Generate** and let the algorithm do its thing.
  It schedules lectures and labs using constraints, backtracking, and whatever optimism you have left.

### Step 3: Review & Edit

This tab is where you fix what the algorithm “tried its best” to do.

* Double-click any cell to edit the subject, faculty, room, subgroup, or even time slot.
* Click empty cells to add new classes manually.
* All changes are instantly validated — no more double-booked rooms or psychic professors.

### Step 4: Export

Go to *Export*:

* Click **Preview PDF** to view the full timetable.
* Click **Export to PDF** to save.
  It outputs a polished, department-grade timetable that won’t embarrass you in a meeting.

---

## How It Works (Simplified)

The scheduling logic:

1. Schedules labs first (they’re harder to fit).
2. Checks all constraints: faculty availability, venue limits, section overlaps.
3. Uses backtracking to fix conflicts dynamically.
4. Validates the final result before showing it.

If it can’t find a placement, it tells you plainly. No vague “runtime error” nonsense.

---

## Common Problems and Fixes

| Problem              | Cause                                        | Fix                                |
| -------------------- | -------------------------------------------- | ---------------------------------- |
| “No placement found” | Not enough rooms or faculty for the load.    | Add more or remove subjects.       |
| Database errors      | Schema changed since last run.               | Delete `timetable.db` and restart. |
| PDF export fails     | ReportLab not installed.                     | `pip install reportlab`            |
| App freezes          | You scheduled the entire university at once. | Start with fewer sections.         |

---

## Developer Notes

If you’re modifying it:

* Add constraints → `src/scheduler/timetable_scheduler.py`
* Change database structure → `src/database/db_models.py`
* Adjust layout or style → `src/views/`
* Customize PDF design → `src/export/pdf_exporter.py`

Follows a clean **MVC** pattern:

* Models → `src/database/`
* Views → `src/views/`
* Logic → `src/scheduler/`

---

## License

Developed for the **CSE Department**.
Use it, improve it, break it — your call.
If you break it, you get to keep the pieces.

---

## Credits

Built by developers tired of manually dragging cells in Excel and pretending it’s computer science.
Powered by **Python**, **PyQt6**, **SQLAlchemy**, and pure academic exhaustion.

