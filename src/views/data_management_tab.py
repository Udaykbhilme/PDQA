from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem,
    QPushButton, QDialog, QFormLayout, QDialogButtonBox, QLineEdit, QComboBox,
    QSpinBox, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt

from ..database.db_models import Faculty, Subject, Venue, Section


# ============================
# Generic Entity Tab Handler
# ============================
class EntityTab(QWidget):
    """
    Reusable CRUD table for Faculty, Subject, Venue, Section.
    """

    def __init__(self, parent, name, columns, dialog_cls, getter, adder, updater, deleter, field_map=None):
        super().__init__(parent)

        self.name = name
        self.columns = columns
        self.dialog_cls = dialog_cls

        # For Subjects & Sections: fetch ALL without filters
        self.get = (lambda: getter(None, None, None)) if name in ["Subject", "Section"] else getter
        self.add = adder
        self.update = updater
        self.delete = deleter

        self.field_map = field_map or {}
        self.init_ui()
        self.load_data()

    # -------------------------
    def init_ui(self):
        layout = QVBoxLayout(self)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # Buttons
        btns = QHBoxLayout()
        for text, func in [
            (f"Add {self.name}", self.handle_add),
            (f"Edit {self.name}", self.handle_edit),
            (f"Delete {self.name}", self.handle_delete)
        ]:
            b = QPushButton(text)
            b.clicked.connect(func)
            btns.addWidget(b)

        btns.addStretch()
        layout.addLayout(btns)

    # -------------------------
    def load_data(self):
        items = self.get()
        self.table.setRowCount(len(items))

        for r, obj in enumerate(items):
            for c, header in enumerate(self.columns):

                # Find attribute
                attr = self.field_map.get(header, header.lower().replace(" ", "_"))
                value = getattr(obj, attr, None)

                # SUBJECT TYPE
                if header == "Type" and hasattr(obj, "is_lab"):
                    value = "Lab" if obj.is_lab else "Lecture"

                # VENUE TYPE
                elif header == "Type" and hasattr(obj, "venue_type"):
                    value = str(obj.venue_type).capitalize()

                # Subsections formatting
                elif header == "Subsections":
                    if isinstance(value, list):
                        value = ", ".join(value)
                    else:
                        value = str(value)

                if value is None:
                    value = "N/A"

                self.table.setItem(r, c, QTableWidgetItem(str(value)))

    # -------------------------
    def selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select", f"Select a {self.name} first.")
            return None
        return int(self.table.item(row, 0).text())

    def find_instance(self, entity_id):
        return next((x for x in self.get() if x.id == entity_id), None)

    # -------------------------
    def handle_add(self):
        dlg = self.dialog_cls(self, title=f"Add {self.name}", adder=self.add)
        if dlg.exec():
            self.load_data()

    def handle_edit(self):
        entity_id = self.selected_id()
        if not entity_id:
            return
        instance = self.find_instance(entity_id)
        dlg = self.dialog_cls(self, title=f"Edit {self.name}", updater=self.update, entity_id=entity_id, instance=instance)
        if dlg.exec():
            self.load_data()

    def handle_delete(self):
        entity_id = self.selected_id()
        if not entity_id:
            return
        if QMessageBox.question(self, "Confirm", f"Delete this {self.name}?") != QMessageBox.StandardButton.Yes:
            return
        if self.delete(entity_id):
            self.load_data()
        else:
            QMessageBox.critical(self, "Error", f"Deletion failed.")


# ============================
# Main Tab Container
# ============================
class DataManagementTab(QWidget):
    def __init__(self, db):
        super().__init__()
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # FACULTY TAB
        self.add_tab(
            "Faculty",
            ["ID", "Name", "Faculty Code", "Max Hours/Day"],
            FacultyDialog,
            db.get_faculties, db.add_faculty, db.update_faculty, db.delete_faculty,
            field_map={"Faculty Code": "faculty_code", "Max Hours/Day": "max_hours_per_day"}
        )

        # SUBJECT TAB
        self.add_tab(
            "Subject",
            ["ID", "Code", "Name", "Type", "Duration", "Year", "Semester"],
            SubjectDialog,
            db.get_subjects, db.add_subject, db.update_subject, db.delete_subject,
            field_map={"Code": "code", "Type": "is_lab", "Duration": "duration",
                       "Year": "year", "Semester": "semester"}
        )

        # VENUE TAB
        self.add_tab(
            "Venue",
            ["ID", "Name", "Type", "Capacity", "Building", "Floor"],
            VenueDialog,
            db.get_venues, db.add_venue, db.update_venue, db.delete_venue,
            field_map={"Type": "venue_type", "Capacity": "capacity", "Floor": "floor"}
        )

        # SECTION TAB
        self.add_tab(
            "Section",
            ["ID", "Name", "Degree", "Year", "Semester", "Subsections"],
            SectionDialog,
            db.get_sections, db.add_section, db.update_section, db.delete_section,
            field_map={"Degree": "degree", "Year": "year", "Semester": "semester",
                       "Subsections": "subsections"}
        )

    def add_tab(self, title, cols, dialog_cls, getter, adder, updater, deleter, field_map):
        self.tabs.addTab(
            EntityTab(self, title, cols, dialog_cls, getter, adder, updater, deleter, field_map),
            title
        )


# ============================
# Base Dialog
# ============================
class BaseDialog(QDialog):
    def __init__(self, parent, title, adder=None, updater=None, entity_id=None, instance=None):
        super().__init__(parent)

        self.adder = adder
        self.updater = updater
        self.entity_id = entity_id
        self.instance = instance

        self.fields = {}
        layout = QFormLayout(self)
        self.setLayout(layout)
        self.setWindowTitle(title)

        self.build_fields()
        self.add_buttons()

        if instance:
            self.populate(instance)

    def add_field(self, label, widget):
        self.fields[label] = widget
        self.layout().addRow(label, widget)

    def add_buttons(self):
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.save)
        btns.rejected.connect(self.reject)
        self.layout().addRow(btns)

    def validate(self):
        for w in self.fields.values():
            if isinstance(w, QLineEdit) and not w.text().strip():
                QMessageBox.warning(self, "Missing", "All fields must be filled.")
                return False
        return True

    def populate(self, instance):
        pass

    def build_fields(self):
        pass

    def save(self):
        raise NotImplementedError


# ============================
# Faculty Dialog
# ============================
class FacultyDialog(BaseDialog):
    def build_fields(self):
        self.add_field("Name", QLineEdit())
        self.add_field("Faculty Code", QLineEdit())
        mx = QSpinBox(); mx.setRange(1, 12)
        self.add_field("Max Hours/Day", mx)

    def populate(self, f: Faculty):
        self.fields["Name"].setText(f.name)
        self.fields["Faculty Code"].setText(f.faculty_code)
        self.fields["Max Hours/Day"].setValue(f.max_hours_per_day)

    def save(self):
        if not self.validate():
            return
        f = self.fields
        args = (f["Name"].text(), f["Faculty Code"].text(), f["Max Hours/Day"].value())
        self.updater(self.entity_id, *args) if self.entity_id else self.adder(*args)
        self.accept()


# ============================
# Subject Dialog
# ============================
class SubjectDialog(BaseDialog):
    def build_fields(self):
        self.add_field("Code", QLineEdit())
        self.add_field("Name", QLineEdit())
        type_box = QComboBox(); type_box.addItems(["Lecture", "Lab"])
        self.add_field("Type", type_box)
        dur = QSpinBox(); dur.setRange(1, 4)
        self.add_field("Duration", dur)
        yr = QSpinBox(); yr.setRange(1, 4)
        self.add_field("Year", yr)
        sem = QSpinBox(); sem.setRange(1, 8)
        self.add_field("Semester", sem)

    def populate(self, s: Subject):
        self.fields["Code"].setText(s.code)
        self.fields["Name"].setText(s.name)
        self.fields["Type"].setCurrentText("Lab" if s.is_lab else "Lecture")
        self.fields["Duration"].setValue(s.duration)
        self.fields["Year"].setValue(s.year)
        self.fields["Semester"].setValue(s.semester)

    def save(self):
        if not self.validate():
            return
        f = self.fields
        args = (
            f["Code"].text(),
            f["Name"].text(),
            f["Type"].currentText() == "Lab",
            f["Duration"].value(),
            f["Semester"].value(),
            f["Year"].value(),
            "B.Tech"
        )
        self.updater(self.entity_id, *args) if self.entity_id else self.adder(*args)
        self.accept()


# ============================
# Venue Dialog
# ============================
class VenueDialog(BaseDialog):
    def build_fields(self):
        self.add_field("Name", QLineEdit())
        type_box = QComboBox(); type_box.addItems(["lecture", "lab"])
        self.add_field("Type", type_box)
        cap = QSpinBox(); cap.setRange(1, 500)
        self.add_field("Capacity", cap)
        self.add_field("Building", QLineEdit("Main Building"))
        floor = QSpinBox(); floor.setRange(0, 10)
        self.add_field("Floor", floor)

    def populate(self, v: Venue):
        self.fields["Name"].setText(v.name)
        self.fields["Type"].setCurrentText(v.venue_type)
        self.fields["Capacity"].setValue(v.capacity)
        self.fields["Building"].setText(v.building)
        self.fields["Floor"].setValue(v.floor)

    def save(self):
        if not self.validate():
            return
        f = self.fields
        args = (
            f["Name"].text(),
            f["Type"].currentText(),
            f["Capacity"].value(),
            f["Building"].text(),
            f["Floor"].value()
        )
        self.updater(self.entity_id, *args) if self.entity_id else self.adder(*args)
        self.accept()


# ============================
# Section Dialog
# ============================
class SectionDialog(BaseDialog):
    def build_fields(self):
        self.add_field("Name", QLineEdit())
        deg = QComboBox(); deg.addItems(["B.Tech", "M.Tech"])
        self.add_field("Degree", deg)
        yr = QSpinBox(); yr.setRange(1, 4)
        self.add_field("Year", yr)
        sem = QSpinBox(); sem.setRange(1, 8)
        self.add_field("Semester", sem)
        subs = QLineEdit(); subs.setPlaceholderText("A1, A2, A3")
        self.add_field("Subsections", subs)

    def populate(self, sec: Section):
        self.fields["Name"].setText(sec.name)
        self.fields["Degree"].setCurrentText(sec.degree)
        self.fields["Year"].setValue(sec.year)
        self.fields["Semester"].setValue(sec.semester)
        self.fields["Subsections"].setText(", ".join(sec.subsections or []))

    def save(self):
        if not self.validate():
            return
        f = self.fields
        subsections = [x.strip() for x in f["Subsections"].text().split(",") if x.strip()]
        args = (
            f["Name"].text(),
            f["Semester"].value(),
            f["Year"].value(),
            f["Degree"].currentText(),
            subsections,
            60
        )
        self.updater(self.entity_id, *args) if self.entity_id else self.adder(*args)
        self.accept()
