from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor


class TimetableReviewTab(QWidget):
    """
    Supercharged Timetable Review Tab
    --------------------------------
    - Directly editable timetable grid
    - Allows creating new allocations in empty slots
    - Change subject, faculty, venue, subgroup, and time slot
    - No notes area, just pure control
    - Emits timetable_updated signal on approval
    """

    timetable_updated = pyqtSignal(list, dict)

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.assignments = []
        self.meta = {}
        self.conflicts = []
        self.faculties = []
        self.subjects = []
        self.venues = []
        self._ui()

    def _ui(self):
        layout = QVBoxLayout(self)

        # Header info
        self.info = QLabel("No timetable loaded")
        self.info.setStyleSheet("font: 600 14px 'Segoe UI'; color: #fff;")
        layout.addWidget(self.info)

        # Editable Table
        self.table = QTableWidget()
        self.table.setStyleSheet("""
            QTableWidget { background:#111; color:#ddd; gridline-color:#333; }
            QHeaderView::section { background:#1c1c1c; color:#aaa; font-weight:bold; }
        """)
        self.table.cellDoubleClicked.connect(self._edit_or_allocate_cell)
        layout.addWidget(self.table)

        # Buttons
        btns = QHBoxLayout()
        self.approve = self._btn("Approve Changes", "#2E8B57", self._approve)
        self.regen = self._btn("Discard & Regenerate", "#007ACC", self._regen)
        btns.addWidget(self.approve)
        btns.addWidget(self.regen)
        layout.addLayout(btns)

    def _btn(self, text, color, fn):
        b = QPushButton(text)
        b.setStyleSheet(f"""
            QPushButton {{ background:{color}; color:white; border:none; 
                           padding:6px 12px; border-radius:4px; font-weight:bold; }}
            QPushButton:hover {{ background:#3399FF; }}
            QPushButton:disabled {{ background:#444; color:#777; }}
        """)
        b.clicked.connect(fn)
        b.setEnabled(False)
        return b

    # ---------- CORE ----------
    def set_timetable(self, assignments, info, conflicts):
        self.assignments, self.meta, self.conflicts = assignments, info, conflicts

        # Fetch DB data for options
        self.faculties = self.db.get_faculties()
        self.subjects = self.db.get_subjects()
        self.venues = self.db.get_venues()

        self._render()
        self.approve.setEnabled(True)
        self.regen.setEnabled(True)

    def clear(self):
        self.assignments.clear()
        self.conflicts.clear()
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.info.setText("No timetable loaded")
        self.approve.setEnabled(False)
        self.regen.setEnabled(False)

    def _render(self):
        if not self.meta:
            return

        days = self.meta.get("days", ["Mon", "Tue", "Wed", "Thu", "Fri"])
        slots = self._slots(self.meta)
        self.info.setText(f"{self.meta.get('degree','B.Tech')} {self.meta.get('year','')} Sem {self.meta.get('semester','')}")
        self.table.setRowCount(len(slots))
        self.table.setColumnCount(len(days) + 1)
        self.table.setHorizontalHeaderLabels(["Time"] + days)

        for r, s in enumerate(slots):
            time_item = QTableWidgetItem(f"{s['start']}\n{s['end']}")
            time_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            time_item.setForeground(QColor("#999"))
            self.table.setItem(r, 0, time_item)

            for c, d in enumerate(days):
                txt = self._cell_text(d, s["start"])
                item = QTableWidgetItem(txt)
                if txt:
                    color = QColor(35, 70, 110) if not self._islab(d, s["start"]) else QColor(30, 90, 50)
                    item.setBackground(color)
                    item.setForeground(QColor("#fff"))
                else:
                    item.setBackground(QColor(25, 25, 25))
                    item.setForeground(QColor("#666"))
                    item.setText("Empty Slot")
                self.table.setItem(r, c + 1, item)

            self.table.setRowHeight(r, 75)

    def _slots(self, m):
        s, e = self._min(m.get("start_time", "09:00")), self._min(m.get("end_time", "18:00"))
        l1, l2 = self._min(m.get("lunch_start", "13:00")), self._min(m.get("lunch_end", "14:00"))
        return [{"start": self._time(t), "end": self._time(t + 60)} for t in range(s, e, 60) if not l1 <= t < l2]

    def _cell_text(self, day, start):
        a = next((x for x in self.assignments if x.day == day and x.start_time == start), None)
        if not a:
            return ""
        s, f, v = getattr(a, "subject", None), getattr(a, "faculty", None), getattr(a, "venue", None)
        subgroup = getattr(a, "subsection", "")
        if not all([s, f, v]):
            return "Incomplete"
        sub_str = f" ({subgroup})" if subgroup else ""
        return f"{s.code}{sub_str}\n{s.name}\n{f.name}\n{v.name}"

    def _islab(self, d, s):
        a = next((x for x in self.assignments if x.day == d and x.start_time == s), None)
        return bool(a and getattr(a.subject, "is_lab", False))

    def _min(self, t):
        h, m = map(int, t.split(":"))
        return h * 60 + m

    def _time(self, m):
        return f"{m // 60:02d}:{m % 60:02d}"

    # ---------- EDITING / ALLOCATING ----------
    def _edit_or_allocate_cell(self, row, col):
        """Handle cell double-click for both edit and new allocation."""
        if col == 0:
            return

        time_item = self.table.item(row, 0)
        if not time_item:
            return

        start_time = time_item.text().split("\n")[0]
        day = self.table.horizontalHeaderItem(col).text()

        # Check if there's an existing assignment
        assignment = next((x for x in self.assignments if x.day == day and x.start_time == start_time), None)

        if not assignment:
            # Empty slot -> allocate new class
            self._allocate_new_class(day, start_time)
            return

        # Edit existing allocation
        self._edit_existing_class(assignment)
        self._render()

    def _allocate_new_class(self, day, start_time):
        """Create new class allocation in empty slot."""
        sub_choice, ok = QInputDialog.getItem(
            self, "Allocate Subject", "Select Subject:",
            [f"{s.code} - {s.name}" for s in self.subjects], 0, False
        )
        if not ok or not sub_choice:
            return
        sub_code = sub_choice.split(" - ")[0]
        subject = next((s for s in self.subjects if s.code == sub_code), None)

        fac_choice, ok = QInputDialog.getItem(
            self, "Allocate Faculty", "Select Faculty:",
            [f.name for f in self.faculties], 0, False
        )
        if not ok or not fac_choice:
            return
        faculty = next((f for f in self.faculties if f.name == fac_choice), None)

        ven_choice, ok = QInputDialog.getItem(
            self, "Allocate Venue", "Select Venue:",
            [v.name for v in self.venues], 0, False
        )
        if not ok or not ven_choice:
            return
        venue = next((v for v in self.venues if v.name == ven_choice), None)

        subgroup, ok = QInputDialog.getText(self, "Subgroup (optional)", "Enter Subgroup (A1, B2, etc.):")
        if not ok:
            subgroup = ""

        # Build a new assignment object (simple structure, same as scheduler output)
        new_assignment = type("Assignment", (), {})()
        new_assignment.day = day
        new_assignment.start_time = start_time
        new_assignment.subject = subject
        new_assignment.faculty = faculty
        new_assignment.venue = venue
        new_assignment.subsection = subgroup.strip() if subgroup else ""

        self.assignments.append(new_assignment)
        self._render()
        QMessageBox.information(self, "Success", "Class allocated successfully.")

    def _edit_existing_class(self, a):
        """Edit an existing class allocation."""
        edit_type, ok = QInputDialog.getItem(
            self, "Edit Timetable", "Choose what to edit:",
            ["Subject", "Faculty", "Venue", "Subgroup", "Time Slot"], 0, False
        )
        if not ok:
            return

        if edit_type == "Subject":
            sub_choice, ok = QInputDialog.getItem(
                self, "Change Subject", "Select new subject:",
                [f"{s.code} - {s.name}" for s in self.subjects], 0, False
            )
            if ok and sub_choice:
                sub_code = sub_choice.split(" - ")[0]
                new_sub = next((s for s in self.subjects if s.code == sub_code), None)
                if new_sub:
                    a.subject = new_sub

        elif edit_type == "Faculty":
            fac_choice, ok = QInputDialog.getItem(
                self, "Change Faculty", "Select new faculty:",
                [f.name for f in self.faculties], 0, False
            )
            if ok and fac_choice:
                new_fac = next((f for f in self.faculties if f.name == fac_choice), None)
                if new_fac:
                    a.faculty = new_fac

        elif edit_type == "Venue":
            ven_choice, ok = QInputDialog.getItem(
                self, "Change Venue", "Select new venue:",
                [v.name for v in self.venues], 0, False
            )
            if ok and ven_choice:
                new_v = next((v for v in self.venues if v.name == ven_choice), None)
                if new_v:
                    a.venue = new_v

        elif edit_type == "Subgroup":
            sub, ok = QInputDialog.getText(self, "Change Subgroup", "Enter new subgroup:")
            if ok and sub.strip():
                a.subsection = sub.strip()

        elif edit_type == "Time Slot":
            new_time, ok = QInputDialog.getText(self, "Change Time", "Enter new start time (HH:MM):", text=a.start_time)
            if ok and new_time.strip():
                a.start_time = new_time.strip()

    # ---------- CONTROLS ----------
    def _approve(self):
        if not self.assignments:
            QMessageBox.warning(self, "Warning", "No timetable to approve.")
            return
        if QMessageBox.question(
            self, "Confirm", "Approve and save all timetable changes?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.meta["status"] = "approved"
            self.timetable_updated.emit(self.assignments, self.meta)
            QMessageBox.information(self, "Approved", "All timetable edits and allocations have been saved.")

    def _regen(self):
        if QMessageBox.question(
            self, "Regenerate", "Discard current timetable and regenerate?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.clear()
