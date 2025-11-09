from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QSplitter, QTreeWidget, QTreeWidgetItem, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt
from ..database.db_models import Subject


class FacultySubjectMappingTab(QWidget):
    """Tab to manage which faculty teaches which subjects."""

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.faculties = []
        self.subjects = []
        self._init_ui()
        self._load_data()

    # -----------------------------------------------
    # UI SETUP
    # -----------------------------------------------
    def _init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Faculty–Subject Mapping")
        title.setStyleSheet("font: 700 16px 'Segoe UI'; color: #fff; margin: 8px;")
        layout.addWidget(title)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left: Faculty List
        self.faculty_list = QListWidget()
        self.faculty_list.itemSelectionChanged.connect(self._on_faculty_selected)
        self.faculty_list.setStyleSheet("background:#111; color:#ddd;")
        splitter.addWidget(self.faculty_list)

        # Right: Subject List
        right_panel = QVBoxLayout()
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        splitter.addWidget(right_widget)

        self.subject_list = QListWidget()
        self.subject_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.subject_list.setStyleSheet("background:#111; color:#ddd;")
        right_panel.addWidget(QLabel("Subjects"))
        right_panel.addWidget(self.subject_list)

        # Buttons
        btns = QHBoxLayout()
        self.assign_btn = QPushButton("Assign →")
        self.assign_btn.clicked.connect(self.assign_subjects)
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self.remove_subjects)
        for b in [self.assign_btn, self.remove_btn]:
            b.setStyleSheet("""
                QPushButton {
                    background:#007ACC; color:white; border:none;
                    padding:6px 12px; border-radius:4px; font-weight:bold;
                }
                QPushButton:hover { background:#3399FF; }
            """)
            btns.addWidget(b)
        right_panel.addLayout(btns)

        # Mapping Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Faculty", "Subjects"])
        self.tree.setStyleSheet("background:#151515; color:#ccc; margin-top:6px;")
        layout.addWidget(QLabel("Current Mappings"))
        layout.addWidget(self.tree)

    # -----------------------------------------------
    # DATA LOADERS
    # -----------------------------------------------
    def _load_data(self):
        self.faculties = self.db.get_faculties()
        self.subjects = self.db.get_subjects()

        self.faculty_list.clear()
        for f in self.faculties:
            item = QListWidgetItem(f.name)
            item.setData(Qt.ItemDataRole.UserRole, f)
            self.faculty_list.addItem(item)

        self.subject_list.clear()
        for s in self.subjects:
            item = QListWidgetItem(f"{s.code} - {s.name}")
            item.setData(Qt.ItemDataRole.UserRole, s)
            self.subject_list.addItem(item)

        self._refresh_tree()

    # -----------------------------------------------
    # HANDLERS
    # -----------------------------------------------
    def _on_faculty_selected(self):
        """Highlight subjects already linked to the selected faculty."""
        selected_fac = self._get_selected_faculty()
        if not selected_fac:
            return

        self.subject_list.clearSelection()
        for i in range(self.subject_list.count()):
            item = self.subject_list.item(i)
            subj = item.data(Qt.ItemDataRole.UserRole)
            if selected_fac.id in (subj.preferred_faculty_ids or []):
                item.setSelected(True)

    def assign_subjects(self):
        faculty = self._get_selected_faculty()
        if not faculty:
            QMessageBox.warning(self, "Select Faculty", "Select a faculty first.")
            return

        selected_subjects = [self.subject_list.item(i).data(Qt.ItemDataRole.UserRole)
                             for i in range(self.subject_list.count())
                             if self.subject_list.item(i).isSelected()]

        if not selected_subjects:
            QMessageBox.warning(self, "Select Subjects", "Select at least one subject.")
            return

        session = self.db.get_session()
        for subj in selected_subjects:
            s = session.get(Subject, subj.id)
            if s:
                ids = set(s.preferred_faculty_ids or [])
                ids.add(faculty.id)
                s.preferred_faculty_ids = list(ids)
        session.commit()

        QMessageBox.information(self, "Updated", f"{faculty.name} assigned to {len(selected_subjects)} subjects.")
        self._refresh_tree()

    def remove_subjects(self):
        faculty = self._get_selected_faculty()
        if not faculty:
            QMessageBox.warning(self, "Select Faculty", "Select a faculty first.")
            return

        selected_subjects = [self.subject_list.item(i).data(Qt.ItemDataRole.UserRole)
                             for i in range(self.subject_list.count())
                             if self.subject_list.item(i).isSelected()]

        session = self.db.get_session()
        for subj in selected_subjects:
            s = session.get(Subject, subj.id)
            if s and faculty.id in (s.preferred_faculty_ids or []):
                s.preferred_faculty_ids.remove(faculty.id)
        session.commit()

        QMessageBox.information(self, "Removed", f"{faculty.name} unlinked from selected subjects.")
        self._refresh_tree()

    def _refresh_tree(self):
        """Visual tree of current mappings."""
        self.tree.clear()
        faculties = self.db.get_faculties()
        subjects = self.db.get_subjects()

        for f in faculties:
            parent = QTreeWidgetItem([f.name])
            for subj in subjects:
                if f.id in (subj.preferred_faculty_ids or []):
                    QTreeWidgetItem(parent, [f"• {subj.code}", subj.name])
            self.tree.addTopLevelItem(parent)
            self.tree.expandAll()

    def _get_selected_faculty(self):
        items = self.faculty_list.selectedItems()
        return items[0].data(Qt.ItemDataRole.UserRole) if items else None
