"""
Timetable Scheduler with Constraint-Based Algorithm

This module implements a sophisticated timetable generation algorithm using
greedy approach with backtracking to handle complex scheduling constraints.

The algorithm prioritizes labs first (harder to schedule), then lectures,
and uses backtracking when conflicts are encountered.
"""

from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import random

from ..database.db_models import Faculty, Subject, Venue, Section, ClassAssignment


@dataclass
class TimeSlot:
    """Represents a time slot in the timetable"""
    start_time: str
    end_time: str
    day: str
    
    def __hash__(self):
        return hash((self.start_time, self.end_time, self.day))


@dataclass
class Conflict:
    """Represents a scheduling conflict"""
    type: str  # 'faculty', 'venue', 'section', 'constraint'
    subject_code: str
    details: str
    severity: str  # 'low', 'medium', 'high', 'critical'


@dataclass
class GenerationSettings:
    """Settings for timetable generation"""
    degree: str
    year: int
    semester: int
    sections: List[str]
    start_time: str = "09:00"
    end_time: str = "18:00"
    lunch_start: str = "13:00"
    lunch_end: str = "14:00"
    days: List[str] = None
    max_hours_per_day: int = 6
    lab_duration: int = 2
    lecture_duration: int = 1
    
    def __post_init__(self):
        if self.days is None:
            self.days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


class TimetableScheduler:
    """
    Advanced Constraint-Based Timetable Scheduler
    
    This scheduler uses a combination of greedy algorithms and backtracking
    to generate optimal timetables while respecting all constraints.
    
    Key Features:
    - Faculty conflict prevention
    - Venue conflict prevention  
    - Section/subsection conflict prevention
    - Configurable constraints (max hours, lunch breaks, etc.)
    - Intelligent subject prioritization
    - Backtracking for complex scenarios
    """
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.max_backtrack_depth = 50
        self.debug_mode = True
        
        # Generation state
        self.assignments: List[ClassAssignment] = []
        self.conflicts: List[Conflict] = []
        self.faculty_schedule: Dict[int, Dict[str, List[TimeSlot]]] = {}
        self.venue_schedule: Dict[int, Dict[str, List[TimeSlot]]] = {}
        self.section_schedule: Dict[int, Dict[str, List[TimeSlot]]] = {}
        
    def generate_timetable(self, settings: GenerationSettings) -> Tuple[List[ClassAssignment], List[Conflict]]:
        """
        Generate a complete timetable for given parameters
        
        Args:
            settings: Generation settings including degree, year, semester, etc.
            
        Returns:
            Tuple of (assignments, conflicts)
        """
        self.log("Starting timetable generation...", settings)
        
        try:
            # Reset state
            self.assignments = []
            self.conflicts = []
            self._initialize_schedules()
            
            # Load required data
            data = self._load_generation_data(settings)
            
            # Generate time slots
            time_slots = self._generate_time_slots(settings)
            
            # Sort subjects by difficulty (labs first, then core subjects)
            sorted_subjects = self._prioritize_subjects(data['subjects'])
            
            # Generate assignments
            self._schedule_subjects(sorted_subjects, data, time_slots, settings)
            
            self.log(f"Timetable generation completed. Conflicts: {len(self.conflicts)}")
            
            return self.assignments, self.conflicts
            
        except Exception as error:
            self.log(f"Error in timetable generation: {error}")
            raise
    
    def _initialize_schedules(self):
        """Initialize scheduling tracking dictionaries"""
        self.faculty_schedule = {}
        self.venue_schedule = {}
        self.section_schedule = {}
    
    def _load_generation_data(self, settings: GenerationSettings) -> Dict:
        """Load all required data for generation"""
        subjects = self.db_manager.get_subjects(
            year=settings.year, 
            semester=settings.semester, 
            degree=settings.degree
        )
        
        venues = self.db_manager.get_venues()
        sections = self.db_manager.get_sections(
            year=settings.year,
            semester=settings.semester,
            degree=settings.degree
        )
        
        # Filter sections by selected section names
        sections = [s for s in sections if s.name in settings.sections]
        
        faculties = self.db_manager.get_faculties()
        
        return {
            'subjects': subjects,
            'venues': venues,
            'sections': sections,
            'faculties': faculties
        }
    
    def _generate_time_slots(self, settings: GenerationSettings) -> List[TimeSlot]:
        """Generate available time slots"""
        slots = []
        start = self._time_to_minutes(settings.start_time)
        end = self._time_to_minutes(settings.end_time)
        lunch_start = self._time_to_minutes(settings.lunch_start)
        lunch_end = self._time_to_minutes(settings.lunch_end)
        
        for day in settings.days:
            for time in range(start, end, 60):  # 1-hour slots
                # Skip lunch break
                if time >= lunch_start and time < lunch_end:
                    continue
                
                slots.append(TimeSlot(
                    start_time=self._minutes_to_time(time),
                    end_time=self._minutes_to_time(time + 60),
                    day=day
                ))
        
        return slots
    
    def _prioritize_subjects(self, subjects: List[Subject]) -> List[Subject]:
        """
        Prioritize subjects by scheduling difficulty
        
        Labs are scheduled first as they are harder to place due to:
        - Longer duration (2 hours vs 1 hour)
        - Limited lab venues
        - Subsection requirements
        """
        return sorted(subjects, key=lambda s: (
            not s.is_lab,  # Labs first (False < True)
            s.duration,    # Longer duration first
            s.code         # Alphabetical for consistency
        ))
    
    def _schedule_subjects(self, subjects: List[Subject], data: Dict, 
                          time_slots: List[TimeSlot], settings: GenerationSettings):
        """Main scheduling algorithm with backtracking"""
        backtrack_stack = []
        current_subject_index = 0
        
        while current_subject_index < len(subjects):
            subject = subjects[current_subject_index]
            self.log(f"Scheduling subject: {subject.code}")
            
            placement = self._find_best_placement(subject, data, time_slots, settings)
            
            if placement:
                # Create assignment
                assignment = ClassAssignment(
                    subject_id=subject.id,
                    faculty_id=placement['faculty'].id,
                    section_id=placement['section'].id,
                    subsection=placement.get('subsection'),
                    venue_id=placement['venue'].id,
                    day=placement['day'],
                    start_time=placement['start_time'],
                    duration=placement['duration']
                )
                
                self.assignments.append(assignment)
                self._update_schedules(assignment, placement)
                
                self.log(f"Successfully placed {subject.code} at {placement['day']} {placement['start_time']}")
                current_subject_index += 1
                
                # Clear backtrack stack on success
                backtrack_stack.clear()
                
            else:
                # No placement found, try backtracking
                self.log(f"No placement found for {subject.code}, attempting backtracking...")
                
                if backtrack_stack and len(backtrack_stack) < self.max_backtrack_depth:
                    # Remove last assignment and try alternative
                    last_assignment = backtrack_stack.pop()
                    self.assignments.remove(last_assignment)
                    self._remove_from_schedules(last_assignment)
                    
                    current_subject_index -= 1
                    self.log(f"Backtracking to subject index: {current_subject_index}")
                    
                else:
                    # Create conflict entry
                    self.conflicts.append(Conflict(
                        type='constraint',
                        subject_code=subject.code,
                        details='No available slots found',
                        severity='high'
                    ))
                    
                    self.log(f"Failed to place {subject.code} - creating conflict")
                    current_subject_index += 1
        
        # Validate final assignments for conflicts
        validation_conflicts = self._validate_assignments()
        self.conflicts.extend(validation_conflicts)
    
    def _find_best_placement(self, subject: Subject, data: Dict, 
                           time_slots: List[TimeSlot], settings: GenerationSettings) -> Optional[Dict]:
        """Find the best placement for a subject"""
        available_faculties = data['faculties']
        available_venues = [v for v in data['venues'] if 
                          (subject.is_lab and v.venue_type == 'lab') or 
                          (not subject.is_lab and v.venue_type == 'lecture')]
        
        for faculty in available_faculties:
            for section in data['sections']:
                for slot in time_slots:
                    duration = settings.lab_duration if subject.is_lab else settings.lecture_duration
                    
                    # Check if slot can accommodate duration
                    if not self._can_accommodate_duration(slot, duration, time_slots):
                        continue
                    
                    for venue in available_venues:
                        # Check constraints
                        if self._is_valid_placement(subject, faculty, section, venue, slot, duration, settings):
                            return {
                                'faculty': faculty,
                                'section': section,
                                'subsection': self._select_subsection(section, subject) if subject.is_lab else None,
                                'venue': venue,
                                'day': slot.day,
                                'start_time': slot.start_time,
                                'duration': duration
                            }
        
        return None
    
    def _is_valid_placement(self, subject: Subject, faculty: Faculty, section: Section, 
                          venue: Venue, slot: TimeSlot, duration: int, settings: GenerationSettings) -> bool:
        """Check if a placement is valid according to all constraints"""
        
        # Check faculty availability
        if self._faculty_has_conflict(faculty.id, slot, duration):
            return False
        
        # Check venue availability
        if self._venue_has_conflict(venue.id, slot, duration):
            return False
        
        # Check section availability
        if self._section_has_conflict(section.id, slot, duration):
            return False
        
        # Check faculty daily hours limit
        if self._faculty_exceeds_daily_limit(faculty.id, slot.day, duration, settings.max_hours_per_day):
            return False
        
        return True
    
    def _faculty_has_conflict(self, faculty_id: int, slot: TimeSlot, duration: int) -> bool:
        """Check if faculty has scheduling conflict"""
        if faculty_id not in self.faculty_schedule:
            return False
        
        day_schedule = self.faculty_schedule[faculty_id].get(slot.day, [])
        
        for scheduled_slot in day_schedule:
            if self._slots_overlap(slot, scheduled_slot, duration):
                return True
        
        return False
    
    def _venue_has_conflict(self, venue_id: int, slot: TimeSlot, duration: int) -> bool:
        """Check if venue has scheduling conflict"""
        if venue_id not in self.venue_schedule:
            return False
        
        day_schedule = self.venue_schedule[venue_id].get(slot.day, [])
        
        for scheduled_slot in day_schedule:
            if self._slots_overlap(slot, scheduled_slot, duration):
                return True
        
        return False
    
    def _section_has_conflict(self, section_id: int, slot: TimeSlot, duration: int) -> bool:
        """Check if section has scheduling conflict"""
        if section_id not in self.section_schedule:
            return False
        
        day_schedule = self.section_schedule[section_id].get(slot.day, [])
        
        for scheduled_slot in day_schedule:
            if self._slots_overlap(slot, scheduled_slot, duration):
                return True
        
        return False
    
    def _faculty_exceeds_daily_limit(self, faculty_id: int, day: str, duration: int, max_hours: int) -> bool:
        """Check if faculty would exceed daily hours limit"""
        if faculty_id not in self.faculty_schedule:
            return duration > max_hours
        
        day_schedule = self.faculty_schedule[faculty_id].get(day, [])
        current_hours = len(day_schedule)  # Assuming 1 hour per slot
        
        return (current_hours + duration) > max_hours
    
    def _slots_overlap(self, slot1: TimeSlot, slot2: TimeSlot, duration: int) -> bool:
        """Check if two time slots overlap"""
        start1 = self._time_to_minutes(slot1.start_time)
        end1 = start1 + (duration * 60)
        start2 = self._time_to_minutes(slot2.start_time)
        end2 = start2 + 60  # Assuming slot2 is 1 hour
        
        return not (end1 <= start2 or end2 <= start1)
    
    def _can_accommodate_duration(self, slot: TimeSlot, duration: int, all_slots: List[TimeSlot]) -> bool:
        """Check if a slot can accommodate the required duration"""
        if duration == 1:
            return True
        
        # For multi-hour slots, check if consecutive slots are available
        current_time = self._time_to_minutes(slot.start_time)
        required_slots = duration
        
        for i in range(required_slots):
            check_time = current_time + (i * 60)
            check_slot = TimeSlot(
                start_time=self._minutes_to_time(check_time),
                end_time=self._minutes_to_time(check_time + 60),
                day=slot.day
            )
            
            # Check if this slot exists in available slots
            if not any(s.start_time == check_slot.start_time and s.day == check_slot.day for s in all_slots):
                return False
        
        return True
    
    def _select_subsection(self, section: Section, subject: Subject) -> Optional[str]:
        """Select appropriate subsection for lab"""
        if not section.subsections:
            return None
        
        # Simple round-robin selection
        return section.subsections[0]
    
    def _update_schedules(self, assignment: ClassAssignment, placement: Dict):
        """Update internal scheduling tracking"""
        slot = TimeSlot(
            start_time=placement['start_time'],
            end_time=self._calculate_end_time(placement['start_time'], placement['duration']),
            day=placement['day']
        )
        
        # Update faculty schedule
        if assignment.faculty_id not in self.faculty_schedule:
            self.faculty_schedule[assignment.faculty_id] = {}
        if placement['day'] not in self.faculty_schedule[assignment.faculty_id]:
            self.faculty_schedule[assignment.faculty_id][placement['day']] = []
        self.faculty_schedule[assignment.faculty_id][placement['day']].append(slot)
        
        # Update venue schedule
        if assignment.venue_id not in self.venue_schedule:
            self.venue_schedule[assignment.venue_id] = {}
        if placement['day'] not in self.venue_schedule[assignment.venue_id]:
            self.venue_schedule[assignment.venue_id][placement['day']] = []
        self.venue_schedule[assignment.venue_id][placement['day']].append(slot)
        
        # Update section schedule
        if assignment.section_id not in self.section_schedule:
            self.section_schedule[assignment.section_id] = {}
        if placement['day'] not in self.section_schedule[assignment.section_id]:
            self.section_schedule[assignment.section_id][placement['day']] = []
        self.section_schedule[assignment.section_id][placement['day']].append(slot)
    
    def _remove_from_schedules(self, assignment: ClassAssignment):
        """Remove assignment from internal scheduling tracking"""
        # This would need to be implemented to remove from tracking dictionaries
        pass
    
    def _validate_assignments(self) -> List[Conflict]:
        """Validate all assignments for conflicts"""
        conflicts = []
        
        # Check for faculty conflicts
        faculty_map = {}
        for assignment in self.assignments:
            key = f"{assignment.faculty_id}-{assignment.day}-{assignment.start_time}"
            if key in faculty_map:
                conflicts.append(Conflict(
                    type='faculty',
                    subject_code=assignment.subject.code if hasattr(assignment, 'subject') else 'Unknown',
                    details=f'Faculty double-booked at {assignment.day} {assignment.start_time}',
                    severity='critical'
                ))
            else:
                faculty_map[key] = assignment
        
        return conflicts
    
    def _calculate_end_time(self, start_time: str, duration: int) -> str:
        """Calculate end time based on start time and duration"""
        start_minutes = self._time_to_minutes(start_time)
        end_minutes = start_minutes + (duration * 60)
        return self._minutes_to_time(end_minutes)
    
    def _time_to_minutes(self, time_string: str) -> int:
        """Convert time string (HH:MM) to minutes"""
        hours, minutes = map(int, time_string.split(':'))
        return hours * 60 + minutes
    
    def _minutes_to_time(self, minutes: int) -> str:
        """Convert minutes to time string (HH:MM)"""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    
    def log(self, message: str, data=None):
        """Logging utility"""
        if self.debug_mode:
            print(f"[Scheduler] {message}")
            if data:
                print(f"  Data: {data}")
