"""
Database Manager for Timetable Generator

Handles:
- Database initialization (SQLite)
- Session management
- CRUD utilities for Faculty, Subject, Venue, Section
- Seeding with sample data for first run
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from .db_models import Base, Faculty, Subject, Venue, Section


class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(self, db_path: str = "timetable.db"):
        """Initialize database manager with SQLite database."""
        self.db_path = db_path
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()

    # ---------------------------------------------------------------------
    # INITIALIZATION
    # ---------------------------------------------------------------------
    def _initialize_engine(self):
        """Initialize SQLAlchemy engine and session factory."""
        try:
            self.engine = create_engine(
                f"sqlite:///{self.db_path}",
                echo=False,
                connect_args={"check_same_thread": False},
            )
            self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        except Exception as e:
            raise RuntimeError(f"Error initializing database engine: {e}")

    def initialize_database(self):
        """Create tables and seed if empty."""
        try:
            Base.metadata.create_all(bind=self.engine)
            with self.get_session() as session:
                if session.query(Faculty).count() == 0:
                    self._seed_database(session)
        except SQLAlchemyError as e:
            raise RuntimeError(f"Error initializing database: {e}")

    def get_session(self) -> Session:
        """Get new session."""
        return self.SessionLocal()

    # ---------------------------------------------------------------------
    # SEEDING
    # ---------------------------------------------------------------------
    def _seed_database(self, session: Session):
        """Seed initial data for first run."""
        try:
            # Faculties
            faculties = [
                Faculty(name="Dr. Rajesh Kumar", faculty_code="RK001"),
                Faculty(name="Prof. Sunita Sharma", faculty_code="SS002"),
                Faculty(name="Dr. Amit Patel", faculty_code="AP003"),
                Faculty(name="Prof. Priya Singh", faculty_code="PS004"),
                Faculty(name="Dr. Vikram Gupta", faculty_code="VG005"),
                Faculty(name="Prof. Neha Agarwal", faculty_code="NA006"),
            ]
            session.add_all(faculties)

            # Subjects
            subjects = [
                # 3rd Year
                Subject(code="CS301", name="Data Structures and Algorithms", is_lab=False, year=3, semester=5),
                Subject(code="CS301L", name="Data Structures and Algorithms Lab", is_lab=True, year=3, semester=5),
                Subject(code="CS302", name="Database Management Systems", is_lab=False, year=3, semester=5),
                Subject(code="CS302L", name="Database Management Systems Lab", is_lab=True, year=3, semester=5),
                Subject(code="CS303", name="Computer Networks", is_lab=False, year=3, semester=5),
                Subject(code="CS303L", name="Computer Networks Lab", is_lab=True, year=3, semester=5),
                Subject(code="CS304", name="Software Engineering", is_lab=False, year=3, semester=5),
                Subject(code="CS304L", name="Software Engineering Lab", is_lab=True, year=3, semester=5),
                Subject(code="CS305", name="Operating Systems", is_lab=False, year=3, semester=5),
                Subject(code="CS305L", name="Operating Systems Lab", is_lab=True, year=3, semester=5),

                # 4th Year
                Subject(code="CS401", name="Machine Learning", is_lab=False, year=4, semester=7),
                Subject(code="CS401L", name="Machine Learning Lab", is_lab=True, year=4, semester=7),
                Subject(code="CS402", name="Artificial Intelligence", is_lab=False, year=4, semester=7),
                Subject(code="CS402L", name="Artificial Intelligence Lab", is_lab=True, year=4, semester=7),
            ]
            session.add_all(subjects)

            # Venues
            venues = [
                Venue(name="LT-101", venue_type="lecture", capacity=120, building="Main Building", floor=1),
                Venue(name="LT-102", venue_type="lecture", capacity=100, building="Main Building", floor=1),
                Venue(name="LT-201", venue_type="lecture", capacity=80, building="Main Building", floor=2),
                Venue(name="LAB-101", venue_type="lab", capacity=30, building="Computer Center", floor=1),
                Venue(name="LAB-102", venue_type="lab", capacity=30, building="Computer Center", floor=1),
                Venue(name="LAB-201", venue_type="lab", capacity=25, building="Computer Center", floor=2),
            ]
            session.add_all(venues)

            # Sections
            sections = [
                Section(name="A", degree="B.Tech", year=3, semester=5, subsections=["A1", "A2", "A3"]),
                Section(name="B", degree="B.Tech", year=3, semester=5, subsections=["B1", "B2", "B3"]),
                Section(name="A", degree="B.Tech", year=4, semester=7, subsections=["A1", "A2", "A3"]),
                Section(name="B", degree="B.Tech", year=4, semester=7, subsections=["B1", "B2", "B3"]),
            ]
            session.add_all(sections)

            session.commit()
            print("✅ Database seeded successfully with sample data.")

        except SQLAlchemyError as e:
            session.rollback()
            raise RuntimeError(f"Error seeding database: {e}")

    # ---------------------------------------------------------------------
    # GETTERS
    # ---------------------------------------------------------------------
    def get_faculties(self) -> list[Faculty]:
        with self.get_session() as session:
            return session.query(Faculty).all()

    def get_subjects(self, year: int = None, semester: int = None, degree: str = None) -> list[Subject]:
        with self.get_session() as session:
            q = session.query(Subject)
            if year:
                q = q.filter(Subject.year == year)
            if semester:
                q = q.filter(Subject.semester == semester)
            if degree:
                q = q.filter(Subject.degree == degree)
            return q.all()

    def get_venues(self, venue_type: str = None) -> list[Venue]:
        with self.get_session() as session:
            q = session.query(Venue)
            if venue_type:
                q = q.filter(Venue.venue_type == venue_type)
            return q.all()

    def get_sections(self, year: int = None, semester: int = None, degree: str = None) -> list[Section]:
        with self.get_session() as session:
            q = session.query(Section)
            if year:
                q = q.filter(Section.year == year)
            if semester:
                q = q.filter(Section.semester == semester)
            if degree:
                q = q.filter(Section.degree == degree)
            return q.all()

    # ---------------------------------------------------------------------
    # CREATE / ADD
    # ---------------------------------------------------------------------
    def add_faculty(self, name: str, faculty_code: str, max_hours_per_day: int = 6) -> Faculty:
        with self.get_session() as session:
            fac = Faculty(name=name, faculty_code=faculty_code, max_hours_per_day=max_hours_per_day)
            session.add(fac)
            session.commit()
            session.refresh(fac)
            return fac

    def add_subject(self, code: str, name: str, is_lab: bool, duration: int,
                    semester: int, year: int, degree: str = "B.Tech") -> Subject:
        with self.get_session() as session:
            sub = Subject(code=code, name=name, is_lab=is_lab, duration=duration,
                          semester=semester, year=year, degree=degree)
            session.add(sub)
            session.commit()
            session.refresh(sub)
            return sub

    def add_venue(self, name: str, venue_type: str, capacity: int = 60,
                  building: str = "Main Building", floor: int = 1) -> Venue:
        with self.get_session() as session:
            v = Venue(name=name, venue_type=venue_type, capacity=capacity,
                      building=building, floor=floor)
            session.add(v)
            session.commit()
            session.refresh(v)
            return v

    def add_section(self, name: str, semester: int, year: int,
                    degree: str = "B.Tech", subsections: list = None, strength: int = 60) -> Section:
        if subsections is None:
            subsections = []
        with self.get_session() as session:
            sec = Section(name=name, semester=semester, year=year,
                          degree=degree, subsections=subsections, strength=strength)
            session.add(sec)
            session.commit()
            session.refresh(sec)
            return sec

    # ---------------------------------------------------------------------
    # DELETE
    # ---------------------------------------------------------------------
    def delete_faculty(self, faculty_id: int) -> bool:
        return self._delete_entity(Faculty, faculty_id)

    def delete_subject(self, subject_id: int) -> bool:
        return self._delete_entity(Subject, subject_id)

    def delete_venue(self, venue_id: int) -> bool:
        return self._delete_entity(Venue, venue_id)

    def delete_section(self, section_id: int) -> bool:
        return self._delete_entity(Section, section_id)

    def _delete_entity(self, model, entity_id: int) -> bool:
        """Generic delete helper."""
        try:
            with self.get_session() as session:
                obj = session.query(model).filter(model.id == entity_id).first()
                if obj:
                    session.delete(obj)
                    session.commit()
                    return True
                return False
        except SQLAlchemyError:
            return False

    # ---------------------------------------------------------------------
    # UPDATE (NEWLY ADDED)
    # ---------------------------------------------------------------------
    def update_faculty(self, faculty_id, name, code, max_hours):
        """Update faculty details."""
        try:
            with self.get_session() as session:
                fac = session.get(Faculty, faculty_id)
                if fac:
                    fac.name = name
                    fac.faculty_code = code
                    fac.max_hours_per_day = max_hours
                    session.commit()
                    return True
                return False
        except SQLAlchemyError:
            return False

    def update_subject(self, subject_id, code, name, is_lab, duration, semester, year, degree):
        """Update subject details."""
        try:
            with self.get_session() as session:
                sub = session.get(Subject, subject_id)
                if sub:
                    sub.code = code
                    sub.name = name
                    sub.is_lab = is_lab
                    sub.duration = duration
                    sub.semester = semester
                    sub.year = year
                    sub.degree = degree
                    session.commit()
                    return True
                return False
        except SQLAlchemyError:
            return False

    def update_venue(self, venue_id, name, vtype, capacity, building, floor):
        """Update venue details."""
        try:
            with self.get_session() as session:
                v = session.get(Venue, venue_id)
                if v:
                    v.name = name
                    v.venue_type = vtype
                    v.capacity = capacity
                    v.building = building
                    v.floor = floor
                    session.commit()
                    return True
                return False
        except SQLAlchemyError:
            return False

    def update_section(self, section_id, name, semester, year, degree, subsections, strength):
        """Update section details."""
        try:
            with self.get_session() as session:
                s = session.get(Section, section_id)
                if s:
                    s.name = name
                    s.semester = semester
                    s.year = year
                    s.degree = degree
                    s.subsections = subsections
                    s.strength = strength
                    session.commit()
                    return True
                return False
        except SQLAlchemyError:
            return False
