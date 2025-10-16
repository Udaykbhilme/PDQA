#!/usr/bin/env python3
"""
Example Usage Script for Timetable Generator

This script demonstrates how to use the Timetable Generator programmatically
without the GUI interface.
"""

import sys
import os
from datetime import datetime

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database.database_manager import DatabaseManager
from src.scheduler.timetable_scheduler import TimetableScheduler, GenerationSettings
from src.export.pdf_exporter import PDFExporter


def main():
    """Demonstrate timetable generation without GUI"""
    print("Timetable Generator - Example Usage")
    print("=" * 50)
    
    # Initialize database
    print("1. Initializing database...")
    db_manager = DatabaseManager()
    db_manager.initialize_database()
    print("   ✓ Database initialized with sample data")
    
    # Create scheduler
    print("\n2. Creating scheduler...")
    scheduler = TimetableScheduler(db_manager)
    print("   ✓ Scheduler created")
    
    # Define generation settings
    print("\n3. Setting up generation parameters...")
    settings = GenerationSettings(
        degree="B.Tech",
        year=3,
        semester=5,
        sections=["A", "B"],
        start_time="09:00",
        end_time="18:00",
        lunch_start="13:00",
        lunch_end="14:00",
        days=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
        max_hours_per_day=6,
        lab_duration=2,
        lecture_duration=1
    )
    print(f"   ✓ Settings: {settings.degree} Year {settings.year}, Semester {settings.semester}")
    print(f"   ✓ Sections: {', '.join(settings.sections)}")
    print(f"   ✓ Time: {settings.start_time} - {settings.end_time}")
    
    # Generate timetable
    print("\n4. Generating timetable...")
    try:
        assignments, conflicts = scheduler.generate_timetable(settings)
        print(f"   ✓ Generated {len(assignments)} assignments")
        
        if conflicts:
            print(f"   ⚠ Found {len(conflicts)} conflicts:")
            for i, conflict in enumerate(conflicts, 1):
                print(f"      {i}. {conflict.subject_code}: {conflict.details}")
        else:
            print("   ✓ No conflicts detected")
            
    except Exception as e:
        print(f"   ✗ Generation failed: {e}")
        return
    
    # Create timetable info
    timetable_info = {
        'degree': settings.degree,
        'year': settings.year,
        'semester': settings.semester,
        'sections': settings.sections,
        'start_time': settings.start_time,
        'end_time': settings.end_time,
        'lunch_start': settings.lunch_start,
        'lunch_end': settings.lunch_end,
        'days': settings.days,
        'max_hours_per_day': settings.max_hours_per_day,
        'lab_duration': settings.lab_duration,
        'lecture_duration': settings.lecture_duration
    }
    
    # Export to PDF
    print("\n5. Exporting to PDF...")
    try:
        pdf_exporter = PDFExporter()
        output_path = f"example_timetable_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        success = pdf_exporter.export_timetable(assignments, timetable_info, output_path)
        
        if success:
            print(f"   ✓ PDF exported successfully: {output_path}")
        else:
            print("   ✗ PDF export failed")
            
    except Exception as e:
        print(f"   ✗ PDF export failed: {e}")
    
    # Display sample assignments
    print("\n6. Sample assignments:")
    for i, assignment in enumerate(assignments[:5], 1):  # Show first 5
        subject_code = getattr(assignment, 'subject', None)
        if subject_code and hasattr(subject_code, 'code'):
            print(f"   {i}. {assignment.day} {assignment.start_time} - {subject_code.code}")
        else:
            print(f"   {i}. {assignment.day} {assignment.start_time} - Subject ID: {assignment.subject_id}")
    
    if len(assignments) > 5:
        print(f"   ... and {len(assignments) - 5} more assignments")
    
    print("\n" + "=" * 50)
    print("Example completed successfully!")
    print("\nTo run the full GUI application, use:")
    print("  python main.py")


if __name__ == "__main__":
    main()
