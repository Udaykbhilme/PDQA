"""
Timetable Review Tab — MULTI-YEAR VERSION
Stable with:
✔ Multiple years
✔ Multiple semesters
✔ Multiple sections
✔ Flattened assignment objects
✔ Stacked classes in a single cell
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QMessageBox
)
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import Qt, pyqtSignal


class TimetableReviewTab(QWidget):
    timetable_updated = pyqtSignal(list, dict)

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.assignments = []
        self.meta = {}
        self.conflicts = []
        self._setup_ui()

    # ---------------------------------------------------
    # UI SETUP
    # ---------------------------------------------------
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        self.info = QLabel("No timetable loaded")
        self.info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info.setStyleSheet("""
            QLabel {
                font: 700 15px 'Segoe UI';
                color: #E0E0E0;
                padding: 8px;
                background-color: #1E1E1E;
                border-bottom: 1px solid #333;
            }
        """)
        layout.addWidget(self.info)

        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget {
                background: #0F0F0F;
                color: #E6E6E6;
                gridline-color: #2A2A2A;
                font: 600 12px 'Segoe UI';
                selection-background-color: #222;
                border: none;
            }
            QHeaderView::section {
                background: #1C1C1C;
                color: #BBBBBB;
                font-weight: 600;
                border: 1px solid #2A2A2A;
                padding: 6px;
            }
        """)
        layout.addWidget(self.table, stretch=1)

        # Buttons
        btns = QHBoxLayout()
        self.approve_btn = self._btn("Approve", "#007f5f", self._approve)
        self.regen_btn = self._btn("Regenerate", "#007ACC", self._regen)
        btns.addWidget(self.approve_btn)
        btns.addWidget(self.regen_btn)
        layout.addLayout(btns)

    def _btn(self, label, color, callback):
        b = QPushButton(label)
        b.setEnabled(False)
        b.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 6px;
                padding: 8px 18px;
                font-weight: 600;
            }}
            QPushButton:hover {{ opacity: 0.85; }}
        """)
        b.clicked.connect(callback)
        return b

    # ---------------------------------------------------
    # INPUT HANDLING
    # ---------------------------------------------------
    def set_timetable(self, assignments, meta, conflicts):
        self.assignments = assignments
        self.meta = meta
        self.conflicts = conflicts
        self._render()
        self.approve_btn.setEnabled(True)
        self.regen_btn.setEnabled(True)

    def clear_timetable(self):
        self.assignments = []
        self.conflicts = []
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.info.setText("No timetable loaded")
        self.approve_btn.setEnabled(False)
        self.regen_btn.setEnabled(False)

    # ---------------------------------------------------
    # RENDERING
    # ---------------------------------------------------
    def _render(self):
        if not self.assignments:
            return

        days = self.meta.get("days", [])
        start = self._min(self.meta["start_time"])
        end = self._min(self.meta["end_time"])
        lunch_start = self._min(self.meta["lunch_start"])
        lunch_end = self._min(self.meta["lunch_end"])

        # Generate hour slots
        slot_starts = list(range(start, end, 60))

        # Header text
        degree = self.meta.get("degree", "B.Tech")
        years = self.meta.get("year", "Multiple")
        sems = self.meta.get("semester", "Multiple")
        self.info.setText(f"{degree} | Years: {years} | Semesters: {sems}")

        # Table structure
        self.table.setRowCount(len(slot_starts))
        self.table.setColumnCount(len(days) + 1)
        self.table.setHorizontalHeaderLabels(["Time"] + days)

        # Stable ordering
        def sec_year(a):
            sec = getattr(a, "section", None)
            return getattr(sec, "year", 0)

        def sec_name(a):
            sec = getattr(a, "section", None)
            return getattr(sec, "name", "")

        self.assignments.sort(key=lambda a: (a.day, self._min(a.start_time), sec_year(a), sec_name(a)))

        for r, st in enumerate(slot_starts):
            # Time label
            item = QTableWidgetItem(f"{self._fmt(st)}\n{self._fmt(st+60)}")
            item.setForeground(QBrush(QColor("#999")))
            self.table.setItem(r, 0, item)

            for c, day in enumerate(days):
                cell = QTableWidgetItem()
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Lunch break
                if lunch_start <= st < lunch_end:
                    cell.setText("Lunch Break")
                    cell.setBackground(QColor("#333"))
                    self.table.setItem(r, c+1, cell)
                    continue

                # Classes for this slot
                classes = [
                    a for a in self.assignments
                    if a.day == day and self._min(a.start_time) == st
                ]

                if not classes:
                    cell.setBackground(QColor("#111"))
                    self.table.setItem(r, c+1, cell)
                    continue

                parts = []
                for a in classes:
                    sec = getattr(a, "section", None)
                    sec_name = sec.name if sec else getattr(a, "section_name", "")

                    subj = a.subject_code
                    fac = a.faculty_name or "Faculty"
                    ven = a.venue_name or "Venue"

                    parts.append(f"[{sec_name}] {subj}\n{fac}\n{ven}")

                cell.setText("\n\n".join(parts))

                # Lab coloring if ANY class is lab
                is_lab = any(getattr(a, "is_lab", False) for a in classes)
                cell.setBackground(QColor("#1B4332") if is_lab else QColor("#1D3557"))

                self.table.setItem(r, c+1, cell)

            self.table.setRowHeight(r, 115)

        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    # ---------------------------------------------------
    # HELPERS
    # ---------------------------------------------------
    def _min(self, t):
        h, m = map(int, t.split(":"))
        return h * 60 + m

    def _fmt(self, m):
        return f"{m//60:02d}:{m%60:02d}"

    # ---------------------------------------------------
    # BUTTONS
    # ---------------------------------------------------
    def _approve(self):
        if not self.assignments:
            QMessageBox.warning(self, "Warning", "No timetable to approve.")
            return

        if QMessageBox.question(
            self, "Confirm", "Approve this timetable?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.meta["status"] = "approved"
            self.timetable_updated.emit(self.assignments, self.meta)
            QMessageBox.information(self, "Approved", "Timetable approved.")

    def _regen(self):
        if QMessageBox.question(
            self, "Regenerate", "Discard the current timetable?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.clear_timetable()
