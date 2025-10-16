"""
Database Models for Timetable Generator

This module defines all the SQLAlchemy models for the timetable generator application.
Includes Faculty, Subject, Venue, Section, and ClassAssignment models with proper
relationships and constraints.
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Faculty(Base):
    """Faculty model representing teaching staff"""
    __tablename__ = 'faculties'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    faculty_code = Column(String(20), unique=True, nullable=False)
    max_hours_per_day = Column(Integer, default=6, nullable=False)
    
    # Relationships
    assignments = relationship("ClassAssignment", back_populates="faculty")
    
    def __repr__(self):
        return f"<Faculty(id={self.id}, name='{self.name}', code='{self.faculty_code}')>"


class Subject(Base):
    """Subject model representing courses/subjects"""
    __tablename__ = 'subjects'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    is_lab = Column(Boolean, default=False, nullable=False)
    duration = Column(Integer, default=1, nullable=False)  # 1 for lecture, 2 for lab
    semester = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    degree = Column(String(10), default="B.Tech", nullable=False)  # B.Tech or M.Tech
    
    # Relationships
    assignments = relationship("ClassAssignment", back_populates="subject")
    
    def __repr__(self):
        return f"<Subject(id={self.id}, code='{self.code}', name='{self.name}')>"


class Venue(Base):
    """Venue model representing lecture halls and laboratories"""
    __tablename__ = 'venues'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    venue_type = Column(String(20), nullable=False)  # 'lecture' or 'lab'
    capacity = Column(Integer, default=60, nullable=False)
    building = Column(String(50), default="Main Building")
    floor = Column(Integer, default=1)
    
    # Relationships
    assignments = relationship("ClassAssignment", back_populates="venue")
    
    def __repr__(self):
        return f"<Venue(id={self.id}, name='{self.name}', type='{self.venue_type}')>"


class Section(Base):
    """Section model representing student sections"""
    __tablename__ = 'sections'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(10), nullable=False)  # A, B, C, D
    semester = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    degree = Column(String(10), default="B.Tech", nullable=False)
    subsections = Column(JSON, default=list)  # ["A1", "A2", "A3"] for section A
    strength = Column(Integer, default=60, nullable=False)
    
    # Relationships
    assignments = relationship("ClassAssignment", back_populates="section")
    
    def __repr__(self):
        return f"<Section(id={self.id}, name='{self.name}', semester={self.semester}, year={self.year})>"


class ClassAssignment(Base):
    """ClassAssignment model representing scheduled classes"""
    __tablename__ = 'class_assignments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=False)
    faculty_id = Column(Integer, ForeignKey('faculties.id'), nullable=False)
    section_id = Column(Integer, ForeignKey('sections.id'), nullable=False)
    subsection = Column(String(10), nullable=True)  # A1, A2, etc.
    venue_id = Column(Integer, ForeignKey('venues.id'), nullable=False)
    day = Column(String(10), nullable=False)  # Mon, Tue, Wed, Thu, Fri, Sat
    start_time = Column(String(10), nullable=False)  # HH:MM format
    duration = Column(Integer, default=1, nullable=False)  # hours
    
    # Relationships
    subject = relationship("Subject", back_populates="assignments")
    faculty = relationship("Faculty", back_populates="assignments")
    section = relationship("Section", back_populates="assignments")
    venue = relationship("Venue", back_populates="assignments")
    
    def __repr__(self):
        return f"<ClassAssignment(id={self.id}, subject='{self.subject.code if self.subject else 'N/A'}', day='{self.day}', time='{self.start_time}')>"


class Timetable(Base):
    """Timetable model representing a complete timetable"""
    __tablename__ = 'timetables'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    degree = Column(String(10), nullable=False)
    year = Column(Integer, nullable=False)
    semester = Column(Integer, nullable=False)
    sections = Column(JSON, nullable=False)  # List of section names
    generation_settings = Column(JSON, nullable=True)  # Store generation parameters
    status = Column(String(20), default="draft", nullable=False)  # draft, generated, approved
    created_at = Column(String(50), nullable=False)
    approved_at = Column(String(50), nullable=True)
    
    def __repr__(self):
        return f"<Timetable(id={self.id}, name='{self.name}', status='{self.status}')>"
