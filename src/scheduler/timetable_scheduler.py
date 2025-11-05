"""
Timetable Scheduler with subsection-aware lab scheduling and balanced faculty assignment.
Improvements:
- Respects lunch break (skip slots in lunch interval)
- Treats labs with configurable duration (default 2 hours)
- Assigns two faculties to lab sessions if available (primary + secondary)
- Propagates metadata (degree, year, semester) into timetable_info
"""

from typing import Dict, List, Optional
from datetime import datetime

from ..database.db_models import Subject, Faculty, Venue, Section, ClassAssignment, Conflict


class TimeSlot:
    def __init__(self, day, start, end):
        self.day = day      # "Mon", "Tue", ...
        self.start = start  # "09:00"
        self.end = end      # "10:00"


class GenerationSettings:
    """
    Settings controlling generation behavior.

    lecture_duration: default lecture duration in hours (int)
    lab_duration: default lab duration in hours (int)
    lunch_start, lunch_end: "HH:MM" strings defining lunch to skip
    start_time, end_time: "HH:MM" working day bounds
    days: list of day strings e.g. ["Mon","Tue","Wed","Thu","Fri"]
    degree, year, semester: metadata forwarded to timetable_info
    """
    def __init__(
        self,
        lecture_duration: int = 1,
        lab_duration: int = 2,
        lunch_start: str = "13:00",
        lunch_end: str = "14:00",
        start_time: str = "09:00",
        end_time: str = "17:00",
        days: Optional[List[str]] = None,
        degree: str = "B.Tech",
        year: int = None,
        semester: int = None
    ):
        self.lecture_duration = lecture_duration
        self.lab_duration = lab_duration
        self.lunch_start = lunch_start
        self.lunch_end = lunch_end
        self.start_time = start_time
        self.end_time = end_time
        self.days = days or ["Mon", "Tue", "Wed", "Thu", "Fri"]
        self.degree = degree
        self.year = year
        self.semester = semester


class TimetableScheduler:
    """Core timetable generation engine."""

    def __init__(self, db_manager):
        self.db = db_manager
        self.assignments: List[ClassAssignment] = []
        self.conflicts: List[Conflict] = []

        # schedules (maps to lists of TimeSlot objects)
        self.faculty_schedule: Dict = {}
        self.section_schedule: Dict = {}
        self.venue_schedule: Dict = {}

    # Public API
    def generate_timetable(self, settings: GenerationSettings):
        """Main entry point for timetable generation."""
        self.assignments.clear()
        self.conflicts.clear()
        self.faculty_schedule.clear()
        self.section_schedule.clear()
        self.venue_schedule.clear()

        # load data
        data = {
            "faculties": self.db.get_faculties(),
            "subjects": self.db.get_subjects(),
            "venues": self.db.get_venues(),
            "sections": self.db.get_sections(),
        }

        time_slots = self._generate_time_slots(settings)

        # Place all subjects (simple greedy approach; improvements possible)
        for subject in data["subjects"]:
            self._place_subject(subject, data, time_slots, settings)

        # Build timetable_info metadata for UI/export
        timetable_info = {
            "degree": settings.degree,
            "year": settings.year,
            "semester": settings.semester,
            "start_time": settings.start_time,
            "end_time": settings.end_time,
            "lunch_start": settings.lunch_start,
            "lunch_end": settings.lunch_end,
            "days": settings.days
        }

        return self.assignments, timetable_info, self.conflicts

    # Core logic
    def _generate_time_slots(self, settings: GenerationSettings) -> List[TimeSlot]:
        """Create hourly time slots between start and end time excluding lunch."""
        slots = []
        start_min = self._to_minutes(settings.start_time)
        end_min = self._to_minutes(settings.end_time)
        lunch_start = self._to_minutes(settings.lunch_start)
        lunch_end = self._to_minutes(settings.lunch_end)

        for day in settings.days:
            t = start_min
            while t + 60 <= end_min:
                # skip slots that fall fully or partially inside lunch window
                if not (t >= lunch_start and t < lunch_end):
                    start_str = self._fmt(t)
                    end_str = self._fmt(t + 60)
                    slots.append(TimeSlot(day, start_str, end_str))
                t += 60
        return slots

    def _section_key(self, section, subsection: Optional[str]):
        return f"{section.id}:{subsection if subsection else ''}"

    def _place_subject(self, subject: Subject, data, time_slots, settings) -> bool:
        """
        Place subject across sections/subsections.
        For labs: uses settings.lab_duration and tries to assign two faculties if possible.
        """
        duration = settings.lab_duration if subject.is_lab else settings.lecture_duration
        valid_venues = [v for v in data["venues"] if v.venue_type == ("lab" if subject.is_lab else "lecture")]

        placed_any = False

        # candidate faculties: prefer explicit list on subject if present
        if getattr(subject, "preferred_faculty_ids", None):
            candidate_faculties = [f for f in data["faculties"] if f.id in subject.preferred_faculty_ids]
        else:
            candidate_faculties = data["faculties"][:]

        if not candidate_faculties:
            self.conflicts.append(Conflict("qualification", subject.code, "No qualified faculty", "high"))
            return False

        # basic load balancing: sort faculties by assigned minutes
        def faculty_load(fac):
            sched = self.faculty_schedule.get(fac.id, {})
            total = 0
            for day_slots in sched.values():
                for ts in day_slots:
                    total += (self._to_minutes(ts.end) - self._to_minutes(ts.start))
            return total

        candidate_faculties.sort(key=faculty_load)

        for section in data["sections"]:
            # only schedule subjects for matching year/semester/degree if subject metadata present
            if getattr(subject, "year", None) and subject.year and subject.year != section.year:
                continue
            if getattr(subject, "semester", None) and subject.semester and subject.semester != section.semester:
                continue
            if getattr(subject, "degree", None) and subject.degree and subject.degree != section.degree:
                continue

            subsections = section.subsections if subject.is_lab and section.subsections else [None]
            for subsection in subsections:
                placed = False
                for slot in time_slots:
                    # ensure enough contiguous time for multi-hour sessions (duration hours)
                    if not self._slot_fits(slot, time_slots, slot.day, slot.start, duration):
                        continue

                    # find a venue available for the whole duration
                    venue = self._get_free_venue_for_duration(valid_venues, slot, duration)
                    if not venue:
                        continue

                    # For labs: try to pick two distinct faculties; for lectures pick one
                    primary = None
                    secondary = None
                    for fac in candidate_faculties:
                        if self._is_busy(self.faculty_schedule, fac.id, slot, duration):
                            continue
                        primary = fac
                        break

                    if not primary:
                        continue  # no free primary faculty at this slot

                    if subject.is_lab:
                        # try to pick a second, different faculty if possible (assistant/TA)
                        for fac2 in candidate_faculties:
                            if fac2.id == primary.id:
                                continue
                            if self._is_busy(self.faculty_schedule, fac2.id, slot, duration):
                                continue
                            secondary = fac2
                            break
                        # if no secondary found, it's acceptable (depends on policy) — we still allow single faculty
                        # but prefer two if available
                    # create assignment
                    assignment = ClassAssignment(
                        subject.id,
                        primary.id,
                        section.id,
                        venue.id,
                        subsection,
                        slot.day,
                        slot.start,
                        duration
                    )
                    # attach objects
                    assignment.subject = subject
                    assignment.section = section
                    assignment.venue = venue
                    assignment.faculty = primary
                    assignment.faculty_ids = [primary.id] + ([secondary.id] if secondary else [])
                    assignment.faculties = [primary] + ([secondary] if secondary else [])

                    # block the slot for primary, secondary (if any), section-subsection and venue
                    self._block_slot(primary, section, venue, slot, duration, subsection)
                    if secondary:
                        self._block_slot(secondary, section, venue, slot, duration, subsection)
                    self.assignments.append(assignment)

                    placed = True
                    placed_any = True
                    # re-sort faculties to keep basic balance
                    candidate_faculties.sort(key=faculty_load)
                    break  # move to next subsection
                if not placed:
                    self.conflicts.append(Conflict("constraint", subject.code,
                                                   f"No slot for {section.name}{('/' + subsection) if subsection else ''}",
                                                   "high"))
        return placed_any

    # Helpers
    def _slot_fits(self, start_slot: TimeSlot, all_slots: List[TimeSlot], day: str, start_time: str, duration_hours: int) -> bool:
        """
        Check if duration_hours contiguous hourly slots are free starting at start_time on given day.
        Relies on the hour-based slots produced by _generate_time_slots.
        """
        needed = duration_hours
        # find index of start_slot among all_slots for that day + time
        day_slots = [s for s in all_slots if s.day == day]
        idx = next((i for i, s in enumerate(day_slots) if s.start == start_time), None)
        if idx is None:
            return False
        # ensure there are enough consecutive slots after idx
        if idx + needed > len(day_slots):
            return False
        return True

    def _has_space(self, faculty, section, subsection, venues, slot, duration):
        """Check if slot is free for faculty + subsection."""
        if self._is_busy(self.faculty_schedule, faculty.id, slot, duration):
            return False
        key = self._section_key(section, subsection)
        if self._is_busy(self.section_schedule, key, slot, duration, key_is_str=True):
            return False
        return True

    def _is_busy(self, schedule, entity_id, slot, duration, key_is_str=False):
        """Check if an entity (faculty/venue/section key) is busy over the requested duration."""
        # build list of contiguous slots for requested duration (hourly)
        start_min = self._to_minutes(slot.start)
        end_min = start_min + duration * 60

        if key_is_str:
            key = entity_id
            if key not in schedule:
                return False
            slots = schedule[key].get(slot.day, [])
        else:
            if entity_id not in schedule:
                return False
            slots = schedule[entity_id].get(slot.day, [])

        for s in slots:
            s1, e1 = self._to_minutes(s.start), self._to_minutes(s.end)
            # overlap check
            if not (end_min <= s1 or e1 <= start_min):
                return True
        return False

    def _get_free_venue_for_duration(self, venues, start_slot, duration):
        """Return a venue free for the entire duration starting at start_slot."""
        # naive check: ensure for each candidate venue it's not busy for the whole duration
        for v in venues:
            if not self._is_busy(self.venue_schedule, v.id, start_slot, duration):
                return v
        return None

    def _block_slot(self, faculty, section, venue, start_slot, duration, subsection=None):
        """Reserve slot(s) for faculty, section-subsection, and venue across the duration (hours)."""
        # For each hourly chunk we create a TimeSlot-like object to store in schedule maps
        start_min = self._to_minutes(start_slot.start)
        for h in range(duration):
            s_min = start_min + h * 60
            e_min = s_min + 60
            t = TimeSlot(start_slot.day, self._fmt(s_min), self._fmt(e_min))

            # faculty
            self.faculty_schedule.setdefault(faculty.id, {}).setdefault(start_slot.day, []).append(t)
            # section (string key)
            key = self._section_key(section, subsection)
            self.section_schedule.setdefault(key, {}).setdefault(start_slot.day, []).append(t)
            # venue
            self.venue_schedule.setdefault(venue.id, {}).setdefault(start_slot.day, []).append(t)

    # Time helpers
    def _to_minutes(self, time_str):
        h, m = map(int, time_str.split(":"))
        return h * 60 + m

    def _fmt(self, total_minutes):
        h, m = divmod(total_minutes, 60)
        return f"{h:02}:{m:02}"
