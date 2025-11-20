from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QHBoxLayout, QSplitter, QMessageBox, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import Qt
import json


class FacultySubjectMappingTab(QWidget):
    """Manages which faculty can teach which subjects (SQLite version, no ORM)."""

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.faculties = []
        self.subjects = []
        self._init_ui()
        self._load_data()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def _init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Faculty–Subject Mapping")
        title.setStyleSheet("font: 700 16px 'Arial'; color: #fff; margin: 8px;")
        layout.addWidget(title)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # LEFT: Faculty List
        self.faculty_list = QListWidget()
        self.faculty_list.itemSelectionChanged.connect(self._on_faculty_selected)
        splitter.addWidget(self.faculty_list)

        # RIGHT PANEL
        right_panel = QVBoxLayout()
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        splitter.addWidget(right_widget)

        self.subject_list = QListWidget()
        self.subject_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        right_panel.addWidget(QLabel("Subjects"))
        right_panel.addWidget(self.subject_list)

        # Buttons
        btn_layout = QHBoxLayout()
        self.assign_btn = QPushButton("Assign →")
        self.assign_btn.clicked.connect(self.assign_subjects)
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self.remove_subjects)

        for btn in (self.assign_btn, self.remove_btn):
            btn.setStyleSheet("""
                QPushButton {
                    background:#007ACC; color:white; padding:6px 12px;
                    border-radius:4px; font-weight:bold;
                }
                QPushButton:hover { background:#3399FF; }
            """)
            btn_layout.addWidget(btn)

        right_panel.addLayout(btn_layout)

        # Mapping tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Faculty", "Subjects"])
        layout.addWidget(QLabel("Current Mappings"))
        layout.addWidget(self.tree)

    # ---------------------------------------------------------
    # LOAD DATA
    # ---------------------------------------------------------
    def _load_data(self):
        self.faculties = self.db.get_faculties()
        self.subjects = self.db.get_subjects()

        self.faculty_list.clear()
        self.subject_list.clear()

        # Faculty list
        for f in self.faculties:
            item = QListWidgetItem(f"{f.name} ({f.faculty_code})")
            item.setData(Qt.ItemDataRole.UserRole, f)
            self.faculty_list.addItem(item)

        # Subject list
        for s in self.subjects:
            item = QListWidgetItem(f"{s.code} - {s.name}")
            item.setData(Qt.ItemDataRole.UserRole, s)
            self.subject_list.addItem(item)

        self._refresh_tree()

    # ---------------------------------------------------------
    def _get_selected_faculty(self):
        items = self.faculty_list.selectedItems()
        return items[0].data(Qt.ItemDataRole.UserRole) if items else None

    # ---------------------------------------------------------
    def _on_faculty_selected(self):
        fac = self._get_selected_faculty()
        if not fac:
            return

        self.subject_list.clearSelection()

        for i in range(self.subject_list.count()):
            item = self.subject_list.item(i)
            subj = item.data(Qt.ItemDataRole.UserRole)

            if fac.id in subj.preferred_faculty_ids:
                item.setSelected(True)

    # ---------------------------------------------------------
    # ASSIGN SUBJECTS
    # ---------------------------------------------------------
    def assign_subjects(self):
        fac = self._get_selected_faculty()
        if not fac:
            QMessageBox.warning(self, "Error", "Select a faculty.")
            return

        selected_subjects = [
            self.subject_list.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self.subject_list.count())
            if self.subject_list.item(i).isSelected()
        ]

        if not selected_subjects:
            QMessageBox.warning(self, "Error", "Select subjects.")
            return

        # Update SQLite directly
        cur = self.db.conn.cursor()

        for subj in selected_subjects:
            ids = set(subj.preferred_faculty_ids or [])
            ids.add(fac.id)

            cur.execute(
                "UPDATE subjects SET preferred_faculty_ids=? WHERE id=?",
                (json.dumps(list(ids)), subj.id)
            )

        self.db.conn.commit()

        self._load_data()
        QMessageBox.information(self, "Updated", "Faculty assigned successfully.")

    # ---------------------------------------------------------
    # REMOVE SUBJECTS
    # ---------------------------------------------------------
    def remove_subjects(self):
        fac = self._get_selected_faculty()
        if not fac:
            QMessageBox.warning(self, "Error", "Select a faculty.")
            return

        selected_subjects = [
            self.subject_list.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self.subject_list.count())
            if self.subject_list.item(i).isSelected()
        ]

        cur = self.db.conn.cursor()

        for subj in selected_subjects:
            ids = set(subj.preferred_faculty_ids or [])
            if fac.id in ids:
                ids.remove(fac.id)

            cur.execute(
                "UPDATE subjects SET preferred_faculty_ids=? WHERE id=?",
                (json.dumps(list(ids)), subj.id)
            )

        self.db.conn.commit()

        self._load_data()
        QMessageBox.information(self, "Updated", "Faculty removed from subjects.")

    # ---------------------------------------------------------
    # TREE VIEW
    # ---------------------------------------------------------
    def _refresh_tree(self):
        self.tree.clear()

        for f in self.faculties:
            parent = QTreeWidgetItem([f.name])
            for s in self.subjects:
                if f.id in s.preferred_faculty_ids:
                    QTreeWidgetItem(parent, [f"• {s.code}", s.name])
            self.tree.addTopLevelItem(parent)

        self.tree.expandAll()
