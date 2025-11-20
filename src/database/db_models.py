from dataclasses import dataclass, field
from typing import List, Optional


# -----------------------------------------------------
# FACULTY
# -----------------------------------------------------
@dataclass
class Faculty:
    id: int
    name: str
    faculty_code: str
    max_hours_per_day: int

    def __repr__(self):
        return f"<Faculty {self.id}: {self.name}>"


# -----------------------------------------------------
# SUBJECT
# -----------------------------------------------------
@dataclass
class Subject:
    id: int
    code: str
    name: str
    is_lab: bool
    duration: int
    year: int
    semester: int
    degree: str
    preferred_faculty_ids: List[int] = field(default_factory=list)

    def __repr__(self):
        return f"<Subject {self.code} ({self.name})>"


# -----------------------------------------------------
# VENUE
# -----------------------------------------------------
@dataclass
class Venue:
    id: int
    name: str
    venue_type: str
    capacity: int
    building: str
    floor: int

    def __repr__(self):
        return f"<Venue {self.name} ({self.venue_type})>"


# -----------------------------------------------------
# SECTION
# -----------------------------------------------------
@dataclass
class Section:
    id: int
    name: str
    degree: str
    year: int
    semester: int
    strength: int
    subsections: List[str] = field(default_factory=list)

    def __repr__(self):
        return f"<Section {self.name} (Y{self.year} S{self.semester})>"


# -----------------------------------------------------
# CLASS ASSIGNMENT (CORE)
# -----------------------------------------------------
@dataclass
class ClassAssignment:
    subject_id: int
    faculty_id: int
    section_id: int
    venue_id: int
    subsection: Optional[str]
    day: str
    start_time: str
    duration: int

    # ----- Derived fields filled by scheduler -----
    end_time: str = ""
    subject_code: str = ""
    subject_name: str = ""
    faculty_name: str = ""
    section_name: str = ""
    venue_name: str = ""
    is_lab: bool = False

    # multiple faculty choices (for UI editing)
    faculties: List[dict] = field(default_factory=list)

    # actual object refs (optional, not required!)
    subject: Optional[Subject] = None
    faculty: Optional[Faculty] = None
    section: Optional[Section] = None
    venue: Optional[Venue] = None

    def __repr__(self):
        return (
            f"<ClassAssignment {self.day} {self.start_time} "
            f"{self.subject_code} ({self.section_name})>"
        )


# -----------------------------------------------------
# CONFLICT
# -----------------------------------------------------
@dataclass
class Conflict:
    type: str         # venue, faculty clash, solver issue
    subject_code: str
    details: str
    severity: str     # low / high / critical

    def __repr__(self):
        return f"<Conflict {self.type}: {self.subject_code} ({self.severity})>"
