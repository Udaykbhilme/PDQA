"""
Timetable Review Tab (Modern Fullscreen Edition)

Now fills the full workspace area dynamically, removes wasted padding,
and adapts to any window size. Dark sleek design for dashboard-like feel.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QMessageBox
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
        self._setup_ui()

    # ------------------ UI SETUP ------------------ #
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

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

        # Timetable grid
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
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
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.horizontalHeader().setMinimumSectionSize(120)

        layout.addWidget(self.table, stretch=1)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(12, 4, 12, 8)
        btn_layout.setSpacing(12)

        self.approve_btn = self._styled_btn("Approve", "#007f5f", self._approve)
        self.regen_btn = self._styled_btn("Regenerate", "#007ACC", self._regen)
        btn_layout.addWidget(self.approve_btn)
        btn_layout.addWidget(self.regen_btn)

        layout.addLayout(btn_layout)
        layout.setStretchFactor(self.table, 1)

    def _styled_btn(self, text, color, callback):
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #0096c7;
            }}
            QPushButton:disabled {{
                background-color: #333;
                color: #888;
            }}
        """)
        btn.clicked.connect(callback)
        btn.setEnabled(False)
        return btn

    # ------------------ RENDERING ------------------ #
    def set_timetable(self, assignments, info, conflicts):
        self.assignments, self.meta, self.conflicts = assignments, info, conflicts
        self._render()
        self.approve_btn.setEnabled(True)
        self.regen_btn.setEnabled(True)

    def clear_timetable(self):
        self.assignments.clear()
        self.conflicts.clear()
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.info.setText("No timetable loaded")
        self.approve_btn.setEnabled(False)
        self.regen_btn.setEnabled(False)

    def _render(self):
        if not self.meta:
            return

        days = self.meta.get("days", ["Mon", "Tue", "Wed", "Thu", "Fri"])
        start = self._to_min(self.meta.get("start_time", "09:00"))
        end = self._to_min(self.meta.get("end_time", "17:00"))
        lunch_start = self._to_min(self.meta.get("lunch_start", "13:00"))
        lunch_end = self._to_min(self.meta.get("lunch_end", "14:00"))

        slots = [{"start": self._fmt(t), "end": self._fmt(t + 60)} for t in range(start, end, 60)]

        header = f"{self.meta.get('degree', 'B.Tech')} Year {self.meta.get('year', '')} Sem {self.meta.get('semester', '')}"
        self.info.setText(header)

        self.table.setRowCount(len(slots))
        self.table.setColumnCount(len(days) + 1)
        self.table.setHorizontalHeaderLabels(["Time"] + days)

        for r, s in enumerate(slots):
            time_item = QTableWidgetItem(f"{s['start']}\n{s['end']}")
            time_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            time_item.setForeground(QBrush(QColor("#999")))
            self.table.setItem(r, 0, time_item)

            for c, d in enumerate(days):
                cell = QTableWidgetItem()
                start_m = self._to_min(s["start"])

                # Lunch shading
                if lunch_start <= start_m < lunch_end:
                    cell.setBackground(QColor("#333333"))
                    cell.setText("Lunch Break")
                    cell.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    cell.setForeground(QBrush(QColor("#888")))
                    self.table.setItem(r, c + 1, cell)
                    continue

                # Normal class slot
                txt, color = self._cell_text_and_color(d, s["start"])
                cell.setText(txt)
                cell.setBackground(color)
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, c + 1, cell)
                self.table.setRowHeight(r, 100)

        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def _cell_text_and_color(self, day, start_time):
        """
        Robust cell renderer:
        - Supports assignments where `faculties` contains ORM objects OR dicts
        - Falls back to flattened fields (subject_code, subject_name, faculty_name, venue_name)
        - Returns readable text and a color.
        """
        a = next((x for x in self.assignments if getattr(x, "day", None) == day and getattr(x, "start_time", None) == start_time), None)
        if not a:
            return "", QColor(20, 20, 20)

        # Subject and venue may be ORM objects or missing; prefer subject fields if provided
        subj = getattr(a, "subject", None)
        venue = getattr(a, "venue", None)

        subj_code = getattr(a, "subject_code", None) or (getattr(subj, "code", None) if subj else "")
        subj_name = getattr(a, "subject_name", None) or (getattr(subj, "name", None) if subj else "")
        venue_name = getattr(a, "venue_name", None) or (getattr(venue, "name", None) if venue else "")

        # faculties can be list of dicts, list of ORM objects, or absent
        faculties_attr = getattr(a, "faculties", None)
        faculty_names = None
        if faculties_attr:
            first = faculties_attr[0]
            if isinstance(first, dict):
                faculty_names = ", ".join([f.get("name", "N/A") for f in faculties_attr])
            else:
                # assume object with .name
                faculty_names = ", ".join([getattr(f, "name", "N/A") for f in faculties_attr])
        # fallback to single faculty object or flattened field
        if not faculty_names:
            single_fac = getattr(a, "faculty", None)
            faculty_names = getattr(a, "faculty_name", None) or (getattr(single_fac, "name", None) if single_fac else "N/A")

        # final safe values
        subj_code = subj_code or ""
        subj_name = subj_name or ""
        faculty_names = faculty_names or "N/A"
        venue_name = venue_name or ""

        text = f"{subj_code}\n{subj_name}\n{faculty_names}\n{venue_name}"
        is_lab = getattr(subj, "is_lab", None)
        if is_lab is None:
            is_lab = getattr(a, "is_lab", False)
        color = QColor("#1B4332") if is_lab else QColor("#1D3557")
        return text, color

    # ------------------ BUTTON ACTIONS ------------------ #
    def _approve(self):
        if not self.assignments:
            QMessageBox.warning(self, "Warning", "No timetable to approve.")
            return
        if QMessageBox.question(
            self, "Confirm", "Approve timetable?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.meta["status"] = "approved"
            self.timetable_updated.emit(self.assignments, self.meta)
            QMessageBox.information(self, "Approved", "Timetable approved.")

    def _regen(self):
        if QMessageBox.question(
            self, "Regenerate", "Discard current timetable?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.clear_timetable()

    # ------------------ HELPERS ------------------ #
    def _to_min(self, t):
        h, m = map(int, t.split(":"))
        return h * 60 + m

    def _fmt(self, m):
        return f"{m // 60:02d}:{m % 60:02d}"
