from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem,
    QPushButton, QDialog, QFormLayout, QDialogButtonBox, QLineEdit, QComboBox,
    QSpinBox, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt
from ..database.db_models import Faculty, Subject, Venue, Section


# -------------------------
# Generic Entity Tab
# -------------------------
class EntityTab(QWidget):
    """Reusable CRUD Tab for Faculty, Subject, Venue, Section"""

    def __init__(self, parent, name, columns, dialog_cls, getter, adder, updater, deleter, field_map=None):
        super().__init__(parent)
        self.name = name
        self.columns = columns
        self.dialog_cls = dialog_cls
        self.get, self.add, self.update, self.delete = getter, adder, updater, deleter
        self.field_map = field_map or {}
        self._ui()
        self.load_data()

    def _ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        for text, func in [(f"Add {self.name}", self._on_add),
                           (f"Edit {self.name}", self._on_edit),
                           (f"Delete {self.name}", self._on_delete)]:
            b = QPushButton(text)
            b.clicked.connect(func)
            btn_layout.addWidget(b)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def load_data(self):
        data = self.get()
        self.table.setRowCount(len(data))
        for r, obj in enumerate(data):
            for c, header in enumerate(self.columns):
                attr = self.field_map.get(header, header.lower().replace(" ", "_"))
                val = getattr(obj, attr, "N/A")
                if attr == "is_lab":
                    val = "Lab" if getattr(obj, "is_lab", False) else "Lecture"
                self.table.setItem(r, c, QTableWidgetItem(str(val)))

    def _selected_id(self):
        r = self.table.currentRow()
        if r < 0:
            QMessageBox.warning(self, "Select", f"Select a {self.name} first.")
            return None
        try:
            return int(self.table.item(r, 0).text())
        except Exception:
            QMessageBox.warning(self, "Error", "Invalid row selection.")
            return None

    def _find_instance(self, _id):
        return next((x for x in self.get() if getattr(x, "id", None) == _id), None)

    def _on_add(self):
        dlg = self.dialog_cls(self, title=f"Add {self.name}", adder=self.add)
        if dlg.exec():
            self.load_data()

    def _on_edit(self):
        _id = self._selected_id()
        if not _id:
            return
        instance = self._find_instance(_id)
        dlg = self.dialog_cls(self, title=f"Edit {self.name}", entity_id=_id, updater=self.update, instance=instance)
        if dlg.exec():
            self.load_data()

    def _on_delete(self):
        _id = self._selected_id()
        if not _id:
            return
        if QMessageBox.question(self, "Confirm", f"Delete this {self.name}?") != QMessageBox.StandardButton.Yes:
            return
        if self.delete(_id):
            self.load_data()
        else:
            QMessageBox.critical(self, "Error", f"Failed to delete {self.name}.")


# -------------------------
# Data Management Tab
# -------------------------
class DataManagementTab(QWidget):
    def __init__(self, db):
        super().__init__()
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Faculty
        self._add_tab("Faculty", ["ID", "Name", "Faculty Code", "Max Hours/Day"],
                      FacultyDialog, db.get_faculties, db.add_faculty, db.update_faculty, db.delete_faculty)

        # Subject
        self._add_tab("Subject", ["ID", "Code", "Name", "Type", "Duration", "Year", "Semester"],
                      SubjectDialog, db.get_subjects, db.add_subject, db.update_subject, db.delete_subject,
                      field_map={"Type": "is_lab"})

        # Venue
        self._add_tab("Venue", ["ID", "Name", "Type", "Capacity", "Building", "Floor"],
                      VenueDialog, db.get_venues, db.add_venue, db.update_venue, db.delete_venue,
                      field_map={"Type": "venue_type"})

        # Section
        self._add_tab("Section", ["ID", "Name", "Degree", "Year", "Semester", "Subsections"],
                      SectionDialog, db.get_sections, db.add_section, db.update_section, db.delete_section,
                      field_map={"Subsections": "subsections"})

    def _add_tab(self, title, cols, dialog_cls, getter, adder, updater, deleter, field_map=None):
        self.tabs.addTab(EntityTab(self, title, cols, dialog_cls, getter, adder, updater, deleter, field_map), title)


# -------------------------
# Generic Dialog Base
# -------------------------
class BaseDialog(QDialog):
    def __init__(self, parent, title, adder=None, updater=None, entity_id=None, instance=None):
        super().__init__(parent)
        self.adder, self.updater, self.entity_id, self.instance = adder, updater, entity_id, instance
        self.layout = QFormLayout(self)
        self.fields = {}
        self.setWindowTitle(title)
        self.resize(400, 250)
        self._build_fields()
        self._add_buttons()
        if self.instance:
            self._populate(self.instance)

    def _add_field(self, label, widget):
        self.fields[label] = widget
        self.layout.addRow(label, widget)

    def _add_buttons(self):
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.save)
        btns.rejected.connect(self.reject)
        self.layout.addRow(btns)

    def _validate(self):
        for w in self.fields.values():
            if isinstance(w, QLineEdit) and not w.text().strip():
                QMessageBox.warning(self, "Missing", "All fields must be filled.")
                return False
        return True

    def _populate(self, instance): pass
    def _build_fields(self): pass
    def save(self): raise NotImplementedError


# -------------------------
# Faculty Dialog
# -------------------------
class FacultyDialog(BaseDialog):
    def _build_fields(self):
        self._add_field("Name", QLineEdit())
        self._add_field("Faculty Code", QLineEdit())
        s = QSpinBox(); s.setRange(1, 12)
        self._add_field("Max Hours/Day", s)

    def _populate(self, f: Faculty):
        self.fields["Name"].setText(f.name)
        self.fields["Faculty Code"].setText(f.faculty_code)
        self.fields["Max Hours/Day"].setValue(getattr(f, "max_hours_per_day", 6))

    def save(self):
        if not self._validate(): return
        f = self.fields
        if self.entity_id:
            self.updater(self.entity_id, f["Name"].text(), f["Faculty Code"].text(), f["Max Hours/Day"].value())
        else:
            self.adder(f["Name"].text(), f["Faculty Code"].text(), f["Max Hours/Day"].value())
        self.accept()


# -------------------------
# Subject Dialog
# -------------------------
class SubjectDialog(BaseDialog):
    def _build_fields(self):
        self._add_field("Code", QLineEdit())
        self._add_field("Name", QLineEdit())
        t = QComboBox(); t.addItems(["Lecture", "Lab"]); self._add_field("Type", t)
        d = QSpinBox(); d.setRange(1, 4); self._add_field("Duration", d)
        y = QSpinBox(); y.setRange(1, 4); self._add_field("Year", y)
        s = QSpinBox(); s.setRange(1, 8); self._add_field("Semester", s)

    def _populate(self, s: Subject):
        self.fields["Code"].setText(s.code)
        self.fields["Name"].setText(s.name)
        self.fields["Type"].setCurrentText("Lab" if s.is_lab else "Lecture")
        self.fields["Duration"].setValue(getattr(s, "duration", 1))
        self.fields["Year"].setValue(getattr(s, "year", 1))
        self.fields["Semester"].setValue(getattr(s, "semester", 1))

    def save(self):
        if not self._validate(): return
        f = self.fields
        args = (f["Code"].text(), f["Name"].text(), f["Type"].currentText() == "Lab",
                f["Duration"].value(), f["Semester"].value(), f["Year"].value(), "B.Tech")
        if self.entity_id: self.updater(self.entity_id, *args)
        else: self.adder(*args)
        self.accept()


# -------------------------
# Venue Dialog
# -------------------------
class VenueDialog(BaseDialog):
    def _build_fields(self):
        self._add_field("Name", QLineEdit())
        t = QComboBox(); t.addItems(["lecture", "lab"]); self._add_field("Type", t)
        c = QSpinBox(); c.setRange(1, 500); self._add_field("Capacity", c)
        b = QLineEdit("Main Building"); self._add_field("Building", b)
        f = QSpinBox(); f.setRange(0, 10); self._add_field("Floor", f)

    def _populate(self, v: Venue):
        self.fields["Name"].setText(v.name)
        self.fields["Type"].setCurrentText(v.venue_type)
        self.fields["Capacity"].setValue(v.capacity)
        self.fields["Building"].setText(v.building)
        self.fields["Floor"].setValue(v.floor)

    def save(self):
        if not self._validate(): return
        f = self.fields
        args = (f["Name"].text(), f["Type"].currentText(), f["Capacity"].value(),
                f["Building"].text(), f["Floor"].value())
        if self.entity_id: self.updater(self.entity_id, *args)
        else: self.adder(*args)
        self.accept()


# -------------------------
# Section Dialog
# -------------------------
class SectionDialog(BaseDialog):
    def _build_fields(self):
        self._add_field("Name", QLineEdit())
        d = QComboBox(); d.addItems(["B.Tech", "M.Tech"]); self._add_field("Degree", d)
        y = QSpinBox(); y.setRange(1, 4); self._add_field("Year", y)
        s = QSpinBox(); s.setRange(1, 8); self._add_field("Semester", s)
        subs = QLineEdit(); subs.setPlaceholderText("A1, A2, A3"); self._add_field("Subsections", subs)

    def _populate(self, sec: Section):
        self.fields["Name"].setText(sec.name)
        self.fields["Degree"].setCurrentText(sec.degree)
        self.fields["Year"].setValue(sec.year)
        self.fields["Semester"].setValue(sec.semester)
        self.fields["Subsections"].setText(", ".join(sec.subsections or []))

    def save(self):
        if not self._validate(): return
        f = self.fields
        subs = [s.strip() for s in f["Subsections"].text().split(",") if s.strip()]
        args = (f["Name"].text(), f["Semester"].value(), f["Year"].value(),
                f["Degree"].currentText(), subs, 60)
        if self.entity_id: self.updater(self.entity_id, *args)
        else: self.adder(*args)
        self.accept()
