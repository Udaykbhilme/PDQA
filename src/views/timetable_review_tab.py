"""
Timetable Review Tab (Supercharged Edition)

This tab allows full review and manual editing of generated timetables.

✅ Edit any cell directly — subject, faculty, venue, subgroup, or time.
✅ Allocate new classes in empty cells.
✅ Displays both faculties for labs (if assigned).
✅ Prevents edits or allocations during lunch hour.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QDialog, QDialogButtonBox,
    QGridLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QFont


class TimetableReviewTab(QWidget):
    timetable_updated = pyqtSignal(list, dict)

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.assignments = []
        self.meta = {}
        self.conflicts = []
        self._ui()

    # ------------------ UI SETUP ------------------ #
    def _ui(self):
        layout = QVBoxLayout(self)
        self.info = QLabel("No timetable loaded")
        self.info.setStyleSheet("font: 600 14px 'Segoe UI'; color: #fff;")
        layout.addWidget(self.info)

        # Timetable Grid
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self._on_cell_double_click)
        self.table.setStyleSheet("""
            QTableWidget { background:#111; color:#ddd; gridline-color:#333; }
            QHeaderView::section { background:#1c1c1c; color:#aaa; font-weight:bold; }
        """)
        layout.addWidget(self.table)

        # Buttons
        btns = QHBoxLayout()
        self.approve = self._btn("Approve", "#2E8B57", self._approve)
        self.regen = self._btn("Regenerate", "#007ACC", self._regen)
        btns.addWidget(self.approve)
        btns.addWidget(self.regen)
        layout.addLayout(btns)

    def _btn(self, text, color, fn):
        b = QPushButton(text)
        b.setStyleSheet(f"""
            QPushButton {{
                background:{color}; color:white; border:none;
                padding:6px 12px; border-radius:4px; font-weight:bold;
            }}
            QPushButton:hover {{ background:#3399FF; }}
            QPushButton:disabled {{ background:#444; color:#777; }}
        """)
        b.clicked.connect(fn)
        b.setEnabled(False)
        return b

    # ------------------ TABLE RENDERING ------------------ #
    def set_timetable(self, assignments, info, conflicts):
        self.assignments, self.meta, self.conflicts = assignments, info, conflicts
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
        start = self._to_min(self.meta.get("start_time", "09:00"))
        end = self._to_min(self.meta.get("end_time", "17:00"))
        lunch_start = self._to_min(self.meta.get("lunch_start", "13:00"))
        lunch_end = self._to_min(self.meta.get("lunch_end", "14:00"))

        # build hourly slots skipping nothing visually (we show lunch as gray)
        slots = [{"start": self._fmt(t), "end": self._fmt(t + 60)} for t in range(start, end, 60)]

        header = f"{self.meta.get('degree','B.Tech')} Year {self.meta.get('year','')} Sem {self.meta.get('semester','')}"
        self.info.setText(header)

        self.table.setRowCount(len(slots))
        self.table.setColumnCount(len(days) + 1)
        self.table.setHorizontalHeaderLabels(["Time"] + days)

        for r, s in enumerate(slots):
            # Time label
            t = QTableWidgetItem(f"{s['start']}\n{s['end']}")
            t.setFlags(Qt.ItemFlag.ItemIsEnabled)
            t.setForeground(QColor("#999"))
            self.table.setItem(r, 0, t)

            # Day cells
            for c, d in enumerate(days):
                start_m = self._to_min(s["start"])
                cell_item = QTableWidgetItem()

                # Check if lunch time
                if lunch_start <= start_m < lunch_end:
                    cell_item.setBackground(QColor(40, 40, 40))
                    cell_item.setText("Lunch Break")
                    cell_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    cell_item.setForeground(QBrush(QColor("#888")))
                    self.table.setItem(r, c + 1, cell_item)
                    continue

                # Otherwise fill with class data
                txt, color = self._cell_text_and_color(d, s["start"])
                cell_item.setText(txt)
                cell_item.setBackground(color)
                self.table.setItem(r, c + 1, cell_item)
                self.table.setRowHeight(r, 80)

    def _cell_text_and_color(self, day, start_time):
        """Return cell text and color based on assignments."""
        a = next((x for x in self.assignments if x.day == day and x.start_time == start_time), None)
        if not a:
            return "", QColor(20, 20, 20)

        s = a.subject
        v = a.venue
        # For labs, show both faculties
        if getattr(a, "faculties", None) and len(a.faculties) > 1:
            faculty_names = ", ".join(f.name for f in a.faculties)
        else:
            faculty_names = a.faculty.name if a.faculty else "N/A"

        text = f"{s.code}\n{s.name}\n{faculty_names}\n{v.name}"
        color = QColor(30, 90, 50) if s.is_lab else QColor(35, 70, 110)
        return text, color

    # ------------------ EDITING ------------------ #
    def _on_cell_double_click(self, row, col):
        """Double-click handler: edit or allocate new class."""
        if col == 0:
            return  # Time column

        day = self.table.horizontalHeaderItem(col).text()
        start_time = self.table.item(row, 0).text().split("\n")[0]
        cell_item = self.table.item(row, col)

        if not cell_item:
            return

        if "Lunch" in cell_item.text():
            QMessageBox.information(self, "Lunch Hour", "Cannot allocate during lunch break.")
            return

        existing = next((x for x in self.assignments if x.day == day and x.start_time == start_time), None)
        dialog = EditClassDialog(self.db, existing, day, start_time)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            result = dialog.get_result()
            if existing:
                # Update existing assignment
                existing.subject = result["subject"]
                existing.faculty = result["faculty"]
                existing.faculties = result["faculties"]
                existing.venue = result["venue"]
                existing.subsection = result["subsection"]
            else:
                # Create new one
                from ..database.db_models import ClassAssignment
                new_a = ClassAssignment(
                    result["subject"].id,
                    result["faculty"].id,
                    result["section"].id if result.get("section") else 1,
                    result["venue"].id,
                    result["subsection"],
                    day,
                    start_time,
                    result["subject"].duration
                )
                new_a.subject = result["subject"]
                new_a.faculty = result["faculty"]
                new_a.faculties = result["faculties"]
                new_a.venue = result["venue"]
                self.assignments.append(new_a)

            self._render()  # refresh display

    # ------------------ APPROVE/REGENERATE ------------------ #
    def _approve(self):
        if not self.assignments:
            QMessageBox.warning(self, "Warning", "No timetable to approve.")
            return
        if QMessageBox.question(self, "Confirm", "Approve timetable?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.meta["status"] = "approved"
            self.timetable_updated.emit(self.assignments, self.meta)
            QMessageBox.information(self, "Approved", "Timetable approved.")

    def _regen(self):
        if QMessageBox.question(self, "Regenerate", "Discard current timetable?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.clear()

    # ------------------ HELPERS ------------------ #
    def _to_min(self, t):
        h, m = map(int, t.split(":"))
        return h * 60 + m

    def _fmt(self, m):
        return f"{m//60:02d}:{m%60:02d}"


# ------------------ EDIT DIALOG ------------------ #
class EditClassDialog(QDialog):
    """Dialog to edit or create a class manually."""

    def __init__(self, db, existing, day, start_time):
        super().__init__()
        self.setWindowTitle("Edit Class")
        self.db = db
        self.existing = existing
        self.day = day
        self.start_time = start_time
        self.result_data = {}
        self._build_ui()

    def _build_ui(self):
        layout = QGridLayout(self)
        row = 0

        layout.addWidget(QLabel(f"Day: {self.day}  |  Start: {self.start_time}"), row, 0, 1, 2)
        row += 1

        layout.addWidget(QLabel("Subject:"), row, 0)
        self.subject_box = QComboBox()
        for s in self.db.get_subjects():
            self.subject_box.addItem(f"{s.code} - {s.name}", s)
        layout.addWidget(self.subject_box, row, 1)
        row += 1

        layout.addWidget(QLabel("Faculty (1):"), row, 0)
        self.faculty_box1 = QComboBox()
        for f in self.db.get_faculties():
            self.faculty_box1.addItem(f.name, f)
        layout.addWidget(self.faculty_box1, row, 1)
        row += 1

        layout.addWidget(QLabel("Faculty (2):"), row, 0)
        self.faculty_box2 = QComboBox()
        self.faculty_box2.addItem("None", None)
        for f in self.db.get_faculties():
            self.faculty_box2.addItem(f.name, f)
        layout.addWidget(self.faculty_box2, row, 1)
        row += 1

        layout.addWidget(QLabel("Venue:"), row, 0)
        self.venue_box = QComboBox()
        for v in self.db.get_venues():
            self.venue_box.addItem(v.name, v)
        layout.addWidget(self.venue_box, row, 1)
        row += 1

        layout.addWidget(QLabel("Subgroup:"), row, 0)
        self.sub_box = QComboBox()
        self.sub_box.addItems(["", "A1", "A2", "A3", "B1", "B2", "B3"])
        layout.addWidget(self.sub_box, row, 1)
        row += 1

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons, row, 0, 1, 2)

        if self.existing:
            self._load_existing()

    def _load_existing(self):
        """Preload existing values into combo boxes."""
        s = self.existing.subject
        f = self.existing.faculty
        v = self.existing.venue
        self._set_combo(self.subject_box, s.name)
        self._set_combo(self.faculty_box1, f.name if f else None)
        self._set_combo(self.venue_box, v.name if v else None)
        if getattr(self.existing, "faculties", None) and len(self.existing.faculties) > 1:
            self._set_combo(self.faculty_box2, self.existing.faculties[1].name)

        if self.existing.subsection:
            self._set_combo(self.sub_box, self.existing.subsection)

    def _set_combo(self, combo, name):
        if not name:
            return
        idx = combo.findText(name)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def get_result(self):
        """Return dictionary of selected values."""
        subject = self.subject_box.currentData()
        faculty1 = self.faculty_box1.currentData()
        faculty2 = self.faculty_box2.currentData()
        venue = self.venue_box.currentData()
        subgroup = self.sub_box.currentText()
        faculties = [f for f in [faculty1, faculty2] if f]

        return {
            "subject": subject,
            "faculty": faculty1,
            "faculties": faculties,
            "venue": venue,
            "subsection": subgroup,
        }
