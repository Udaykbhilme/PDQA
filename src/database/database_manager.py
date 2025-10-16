"""
Database Manager for Timetable Generator

This module handles database initialization, session management, and provides
utility functions for database operations.
"""

import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from .db_models import Base, Faculty, Subject, Venue, Section, ClassAssignment, Timetable


class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, db_path: str = "timetable.db"):
        """Initialize database manager with SQLite database"""
        self.db_path = db_path
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize SQLAlchemy engine and session factory"""
        try:
            # Create SQLite database engine
            self.engine = create_engine(
                f"sqlite:///{self.db_path}",
                echo=False,  # Set to True for SQL debugging
                connect_args={"check_same_thread": False}
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
        except Exception as e:
            print(f"Error initializing database engine: {e}")
            raise
    
    def initialize_database(self):
        """Create all database tables and seed with sample data"""
        try:
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            
            # Check if database is empty and seed with sample data
            with self.get_session() as session:
                faculty_count = session.query(Faculty).count()
                if faculty_count == 0:
                    self._seed_database(session)
                    
        except SQLAlchemyError as e:
            print(f"Error initializing database: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()
    
    def _seed_database(self, session: Session):
        """Seed database with sample data"""
        try:
            # Create sample faculties
            faculties = [
                Faculty(name="Dr. Rajesh Kumar", faculty_code="RK001", max_hours_per_day=6),
                Faculty(name="Prof. Sunita Sharma", faculty_code="SS002", max_hours_per_day=6),
                Faculty(name="Dr. Amit Patel", faculty_code="AP003", max_hours_per_day=6),
                Faculty(name="Prof. Priya Singh", faculty_code="PS004", max_hours_per_day=6),
                Faculty(name="Dr. Vikram Gupta", faculty_code="VG005", max_hours_per_day=6),
                Faculty(name="Prof. Neha Agarwal", faculty_code="NA006", max_hours_per_day=6),
            ]
            
            for faculty in faculties:
                session.add(faculty)
            
            # Create sample subjects
            subjects = [
                # 3rd Year, 5th Semester
                Subject(code="CS301", name="Data Structures and Algorithms", is_lab=False, duration=1, semester=5, year=3, degree="B.Tech"),
                Subject(code="CS301L", name="Data Structures and Algorithms Lab", is_lab=True, duration=2, semester=5, year=3, degree="B.Tech"),
                Subject(code="CS302", name="Database Management Systems", is_lab=False, duration=1, semester=5, year=3, degree="B.Tech"),
                Subject(code="CS302L", name="Database Management Systems Lab", is_lab=True, duration=2, semester=5, year=3, degree="B.Tech"),
                Subject(code="CS303", name="Computer Networks", is_lab=False, duration=1, semester=5, year=3, degree="B.Tech"),
                Subject(code="CS303L", name="Computer Networks Lab", is_lab=True, duration=2, semester=5, year=3, degree="B.Tech"),
                Subject(code="CS304", name="Software Engineering", is_lab=False, duration=1, semester=5, year=3, degree="B.Tech"),
                Subject(code="CS304L", name="Software Engineering Lab", is_lab=True, duration=2, semester=5, year=3, degree="B.Tech"),
                Subject(code="CS305", name="Operating Systems", is_lab=False, duration=1, semester=5, year=3, degree="B.Tech"),
                Subject(code="CS305L", name="Operating Systems Lab", is_lab=True, duration=2, semester=5, year=3, degree="B.Tech"),
                
                # 4th Year, 7th Semester
                Subject(code="CS401", name="Machine Learning", is_lab=False, duration=1, semester=7, year=4, degree="B.Tech"),
                Subject(code="CS401L", name="Machine Learning Lab", is_lab=True, duration=2, semester=7, year=4, degree="B.Tech"),
                Subject(code="CS402", name="Artificial Intelligence", is_lab=False, duration=1, semester=7, year=4, degree="B.Tech"),
                Subject(code="CS402L", name="Artificial Intelligence Lab", is_lab=True, duration=2, semester=7, year=4, degree="B.Tech"),
            ]
            
            for subject in subjects:
                session.add(subject)
            
            # Create sample venues
            venues = [
                Venue(name="LT-101", venue_type="lecture", capacity=120, building="Main Building", floor=1),
                Venue(name="LT-102", venue_type="lecture", capacity=100, building="Main Building", floor=1),
                Venue(name="LT-201", venue_type="lecture", capacity=80, building="Main Building", floor=2),
                Venue(name="LAB-101", venue_type="lab", capacity=30, building="Computer Center", floor=1),
                Venue(name="LAB-102", venue_type="lab", capacity=30, building="Computer Center", floor=1),
                Venue(name="LAB-201", venue_type="lab", capacity=25, building="Computer Center", floor=2),
            ]
            
            for venue in venues:
                session.add(venue)
            
            # Create sample sections
            sections = [
                Section(name="A", semester=5, year=3, degree="B.Tech", subsections=["A1", "A2", "A3"], strength=60),
                Section(name="B", semester=5, year=3, degree="B.Tech", subsections=["B1", "B2", "B3"], strength=60),
                Section(name="A", semester=7, year=4, degree="B.Tech", subsections=["A1", "A2", "A3"], strength=60),
                Section(name="B", semester=7, year=4, degree="B.Tech", subsections=["B1", "B2", "B3"], strength=60),
            ]
            
            for section in sections:
                session.add(section)
            
            # Commit all changes
            session.commit()
            print("Database seeded successfully with sample data")
            
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error seeding database: {e}")
            raise
    
    def get_faculties(self) -> list[Faculty]:
        """Get all faculties"""
        with self.get_session() as session:
            return session.query(Faculty).all()
    
    def get_subjects(self, year: int = None, semester: int = None, degree: str = None) -> list[Subject]:
        """Get subjects with optional filters"""
        with self.get_session() as session:
            query = session.query(Subject)
            if year:
                query = query.filter(Subject.year == year)
            if semester:
                query = query.filter(Subject.semester == semester)
            if degree:
                query = query.filter(Subject.degree == degree)
            return query.all()
    
    def get_venues(self, venue_type: str = None) -> list[Venue]:
        """Get venues with optional type filter"""
        with self.get_session() as session:
            query = session.query(Venue)
            if venue_type:
                query = query.filter(Venue.venue_type == venue_type)
            return query.all()
    
    def get_sections(self, year: int = None, semester: int = None, degree: str = None) -> list[Section]:
        """Get sections with optional filters"""
        with self.get_session() as session:
            query = session.query(Section)
            if year:
                query = query.filter(Section.year == year)
            if semester:
                query = query.filter(Section.semester == semester)
            if degree:
                query = query.filter(Section.degree == degree)
            return query.all()
    
    def get_assignments(self, timetable_id: int = None) -> list[ClassAssignment]:
        """Get class assignments with optional timetable filter"""
        with self.get_session() as session:
            query = session.query(ClassAssignment)
            if timetable_id:
                # This would need to be implemented based on how assignments are linked to timetables
                pass
            return query.all()
    
    def add_faculty(self, name: str, faculty_code: str, max_hours_per_day: int = 6) -> Faculty:
        """Add a new faculty member"""
        with self.get_session() as session:
            faculty = Faculty(name=name, faculty_code=faculty_code, max_hours_per_day=max_hours_per_day)
            session.add(faculty)
            session.commit()
            session.refresh(faculty)
            return faculty
    
    def add_subject(self, code: str, name: str, is_lab: bool, duration: int, 
                   semester: int, year: int, degree: str = "B.Tech") -> Subject:
        """Add a new subject"""
        with self.get_session() as session:
            subject = Subject(code=code, name=name, is_lab=is_lab, duration=duration,
                            semester=semester, year=year, degree=degree)
            session.add(subject)
            session.commit()
            session.refresh(subject)
            return subject
    
    def add_venue(self, name: str, venue_type: str, capacity: int = 60, 
                 building: str = "Main Building", floor: int = 1) -> Venue:
        """Add a new venue"""
        with self.get_session() as session:
            venue = Venue(name=name, venue_type=venue_type, capacity=capacity,
                         building=building, floor=floor)
            session.add(venue)
            session.commit()
            session.refresh(venue)
            return venue
    
    def add_section(self, name: str, semester: int, year: int, degree: str = "B.Tech",
                   subsections: list = None, strength: int = 60) -> Section:
        """Add a new section"""
        if subsections is None:
            subsections = []
            
        with self.get_session() as session:
            section = Section(name=name, semester=semester, year=year, degree=degree,
                            subsections=subsections, strength=strength)
            session.add(section)
            session.commit()
            session.refresh(section)
            return section
    
    def delete_faculty(self, faculty_id: int) -> bool:
        """Delete a faculty member"""
        try:
            with self.get_session() as session:
                faculty = session.query(Faculty).filter(Faculty.id == faculty_id).first()
                if faculty:
                    session.delete(faculty)
                    session.commit()
                    return True
                return False
        except SQLAlchemyError:
            return False
    
    def delete_subject(self, subject_id: int) -> bool:
        """Delete a subject"""
        try:
            with self.get_session() as session:
                subject = session.query(Subject).filter(Subject.id == subject_id).first()
                if subject:
                    session.delete(subject)
                    session.commit()
                    return True
                return False
        except SQLAlchemyError:
            return False
    
    def delete_venue(self, venue_id: int) -> bool:
        """Delete a venue"""
        try:
            with self.get_session() as session:
                venue = session.query(Venue).filter(Venue.id == venue_id).first()
                if venue:
                    session.delete(venue)
                    session.commit()
                    return True
                return False
        except SQLAlchemyError:
            return False
    
    def delete_section(self, section_id: int) -> bool:
        """Delete a section"""
        try:
            with self.get_session() as session:
                section = session.query(Section).filter(Section.id == section_id).first()
                if section:
                    session.delete(section)
                    session.commit()
                    return True
                return False
        except SQLAlchemyError:
            return False
