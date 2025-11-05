"""
Database models for Timetable Generator
Defines ORM mappings for Faculty, Subject, Venue, Section, and related entities.
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, JSON
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Faculty(Base):
    __tablename__ = "faculties"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    faculty_code = Column(String, nullable=False)
    max_hours_per_day = Column(Integer, default=6)

    def __repr__(self):
        return f"<Faculty {self.name} ({self.faculty_code})>"


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    is_lab = Column(Boolean, default=False)
    duration = Column(Integer, default=1)
    year = Column(Integer, default=1)
    semester = Column(Integer, default=1)
    degree = Column(String, default="B.Tech")

    # NEW: list of faculty IDs who are allowed to teach this subject
    preferred_faculty_ids = Column(JSON, default=list)

    def __repr__(self):
        return f"<Subject {self.code}: {self.name}>"


class Venue(Base):
    __tablename__ = "venues"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    venue_type = Column(String, nullable=False)  # "lecture" or "lab"
    capacity = Column(Integer, default=60)
    building = Column(String, default="Main Building")
    floor = Column(Integer, default=1)

    def __repr__(self):
        return f"<Venue {self.name} ({self.venue_type})>"


class Section(Base):
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    degree = Column(String, default="B.Tech")
    year = Column(Integer, default=1)
    semester = Column(Integer, default=1)
    strength = Column(Integer, default=60)
    subsections = Column(JSON, default=list)  # e.g. ["A1", "A2", "A3"]

    def __repr__(self):
        return f"<Section {self.name} ({self.degree})>"


class ClassAssignment:
    """Simple struct-like container for generated timetable data."""

    def __init__(self, subject_id, faculty_id, section_id, venue_id, subsection, day, start_time, duration):
        self.subject_id = subject_id
        self.faculty_id = faculty_id
        self.section_id = section_id
        self.venue_id = venue_id
        self.subsection = subsection
        self.day = day
        self.start_time = start_time
        self.duration = duration

        # Populated later
        self.subject = None
        self.faculty = None
        self.section = None
        self.venue = None


class Conflict:
    """Represents a scheduling conflict during timetable generation."""

    def __init__(self, conflict_type, subject_code, details, severity):
        self.conflict_type = conflict_type
        self.subject_code = subject_code
        self.details = details
        self.severity = severity

    def __repr__(self):
        return f"<Conflict {self.subject_code}: {self.details}>"
