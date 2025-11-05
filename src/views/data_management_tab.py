from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem,
    QPushButton, QDialog, QFormLayout, QDialogButtonBox, QLineEdit, QComboBox,
    QSpinBox, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt

# import models
from ..database.db_models import Faculty, Subject, Venue, Section


# -----------------------------------------------------
# GENERIC REUSABLE ENTITY TAB FOR CRUD OPERATIONS
# -----------------------------------------------------
class EntityTab(QWidget):
    """Reusable tab component for managing any entity table (Faculty, Subject, etc.)"""
    
    def __init__(self, parent, name, columns, dialog_cls, db_getter, db_adder, db_deleter):
        """
        name: Tab name (string)
        columns: List of column headers
        dialog_cls: Dialog class for add/edit operations
        db_getter: Method reference to fetch all entities
        db_adder: Method reference to add entity
        db_deleter: Method reference to delete entity
        """
        super().__init__(parent)
        self.parent = parent
        self.name = name
        self.columns = columns
        self.dialog_cls = dialog_cls
        self.db_getter = db_getter
        self.db_adder = db_adder
        self.db_deleter = db_deleter
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """Create the table and buttons"""
        layout = QVBoxLayout(self)

        # Table setup
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # Buttons setup
        btn_layout = QHBoxLayout()
        for text, handler in [
            (f"Add {self.name}", self.add_entry),
            (f"Edit {self.name}", self.edit_entry),
            (f"Delete {self.name}", self.delete_entry)
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(handler)
            btn_layout.addWidget(btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def load_data(self):
        """Fetch and populate table data from DB"""
        data = self.db_getter()
        self.table.setRowCount(len(data))
        for row, record in enumerate(data):
            for col, attr in enumerate(self.columns):
                val = getattr(record, attr.lower().replace(" ", "_"), "N/A")
                self.table.setItem(row, col, QTableWidgetItem(str(val)))

    def _selected_row_id(self):
        """Return selected row's entity ID"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Warning", f"Select a {self.name} to continue.")
            return None
        return int(self.table.item(row, 0).text())

    def add_entry(self):
        """Handle 'Add'"""
        dlg = self.dialog_cls(self.parent)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

    def edit_entry(self):
        """Handle 'Edit'"""
        entity_id = self._selected_row_id()
        if not entity_id:
            return
        dlg = self.dialog_cls(self.parent, entity_id)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

    def delete_entry(self):
        """Handle 'Delete'"""
        entity_id = self._selected_row_id()
        if not entity_id:
            return
        name = self.table.item(self.table.currentRow(), 1).text()
        if QMessageBox.question(self, "Confirm Delete",
            f"Delete {self.name} '{name}'?") == QMessageBox.StandardButton.Yes:
            if self.db_deleter(entity_id):
                QMessageBox.information(self, "Success", f"{self.name} deleted.")
                self.load_data()
            else:
                QMessageBox.critical(self, "Error", f"Failed to delete {self.name}.")


# -----------------------------------------------------
# MAIN TAB HOLDER
# -----------------------------------------------------
class DataManagementTab(QWidget):
    """Main container for all entity management tabs"""

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Create all four tabs
        self.tabs.addTab(
            EntityTab(self, "Faculty",
                      ["ID", "Name", "Faculty Code", "Max Hours/Day"],
                      FacultyDialog, self.db.get_faculties,
                      self.db.add_faculty, self.db.delete_faculty),
            "Faculty"
        )

        self.tabs.addTab(
            EntityTab(self, "Subject",
                      ["ID", "Code", "Name", "Type", "Duration", "Year", "Semester"],
                      SubjectDialog, self.db.get_subjects,
                      self.db.add_subject, self.db.delete_subject),
            "Subjects"
        )

        self.tabs.addTab(
            EntityTab(self, "Venue",
                      ["ID", "Name", "Type", "Capacity", "Building", "Floor"],
                      VenueDialog, self.db.get_venues,
                      self.db.add_venue, self.db.delete_venue),
            "Venues"
        )

        self.tabs.addTab(
            EntityTab(self, "Section",
                      ["ID", "Name", "Degree", "Year", "Semester", "Subsections"],
                      SectionDialog, self.db.get_sections,
                      self.db.add_section, self.db.delete_section),
            "Sections"
        )


# -----------------------------------------------------
# GENERIC DIALOG BASE + SPECIFIC ONES
# -----------------------------------------------------
class BaseDialog(QDialog):
    """Reusable base for Add/Edit dialogs"""

    def __init__(self, parent, title):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.layout = QFormLayout(self)
        self.resize(400, 250)
        self.init_fields()
        self.init_buttons()

    def init_buttons(self):
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        self.layout.addRow(btns)

    def warn_if_empty(self, *fields):
        """Quick validator"""
        if any(not f.text().strip() for f in fields):
            QMessageBox.warning(self, "Warning", "Please fill in all required fields")
            return True
        return False


class FacultyDialog(BaseDialog):
    def __init__(self, parent, _id=None):
        self.parent, self.id = parent, _id
        super().__init__(parent, "Add Faculty" if not _id else "Edit Faculty")

    def init_fields(self):
        self.name = QLineEdit()
        self.code = QLineEdit()
        self.max_hours = QSpinBox()
        self.max_hours.setRange(1, 12)
        self.layout.addRow("Name:", self.name)
        self.layout.addRow("Faculty Code:", self.code)
        self.layout.addRow("Max Hours/Day:", self.max_hours)

    def accept(self):
        if self.warn_if_empty(self.name, self.code): return
        self.parent.db.add_faculty(self.name.text(), self.code.text(), self.max_hours.value())
        super().accept()


class SubjectDialog(BaseDialog):
    def __init__(self, parent, _id=None):
        self.parent, self.id = parent, _id
        super().__init__(parent, "Add Subject" if not _id else "Edit Subject")

    def init_fields(self):
        self.code = QLineEdit()
        self.name = QLineEdit()
        self.type = QComboBox()
        self.type.addItems(["Lecture", "Lab"])
        self.duration = QSpinBox(); self.duration.setRange(1, 4)
        self.year = QSpinBox(); self.year.setRange(1, 4)
        self.sem = QSpinBox(); self.sem.setRange(1, 8)
        self.layout.addRow("Code:", self.code)
        self.layout.addRow("Name:", self.name)
        self.layout.addRow("Type:", self.type)
        self.layout.addRow("Duration:", self.duration)
        self.layout.addRow("Year:", self.year)
        self.layout.addRow("Semester:", self.sem)

    def accept(self):
        if self.warn_if_empty(self.code, self.name): return
        self.parent.db.add_subject(
            self.code.text(), self.name.text(),
            self.type.currentText() == "Lab",
            self.duration.value(), self.sem.value(), self.year.value(), "B.Tech"
        )
        super().accept()


class VenueDialog(BaseDialog):
    def __init__(self, parent, _id=None):
        self.parent, self.id = parent, _id
        super().__init__(parent, "Add Venue" if not _id else "Edit Venue")

    def init_fields(self):
        self.name = QLineEdit()
        self.type = QComboBox(); self.type.addItems(["lecture", "lab"])
        self.capacity = QSpinBox(); self.capacity.setRange(1, 500)
        self.building = QLineEdit("Main Building")
        self.floor = QSpinBox(); self.floor.setRange(0, 10)
        self.layout.addRow("Name:", self.name)
        self.layout.addRow("Type:", self.type)
        self.layout.addRow("Capacity:", self.capacity)
        self.layout.addRow("Building:", self.building)
        self.layout.addRow("Floor:", self.floor)

    def accept(self):
        if self.warn_if_empty(self.name): return
        self.parent.db.add_venue(
            self.name.text(), self.type.currentText(), self.capacity.value(),
            self.building.text(), self.floor.value()
        )
        super().accept()


class SectionDialog(BaseDialog):
    def __init__(self, parent, _id=None):
        self.parent, self.id = parent, _id
        super().__init__(parent, "Add Section" if not _id else "Edit Section")

    def init_fields(self):
        self.name = QLineEdit()
        self.degree = QComboBox(); self.degree.addItems(["B.Tech", "M.Tech"])
        self.year = QSpinBox(); self.year.setRange(1, 4)
        self.sem = QSpinBox(); self.sem.setRange(1, 8)
        self.subs = QLineEdit(); self.subs.setPlaceholderText("A1, A2, A3")
        self.layout.addRow("Name:", self.name)
        self.layout.addRow("Degree:", self.degree)
        self.layout.addRow("Year:", self.year)
        self.layout.addRow("Semester:", self.sem)
        self.layout.addRow("Subsections:", self.subs)

    def accept(self):
        if self.warn_if_empty(self.name): return
        subs = [s.strip() for s in self.subs.text().split(",") if s.strip()]
        self.parent.db.add_section(self.name.text(), self.sem.value(),
                                   self.year.value(), self.degree.currentText(),
                                   subs, 60)
        super().accept()
