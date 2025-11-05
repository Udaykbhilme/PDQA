"""
Timetable Scheduler with subsection-aware lab scheduling and balanced faculty assignment.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta

from ..database.db_models import Subject, Faculty, Venue, Section, ClassAssignment, Conflict


class TimeSlot:
    def __init__(self, day, start, end):
        self.day = day
        self.start = start
        self.end = end


class GenerationSettings:
    def __init__(self, lecture_duration=1, lab_duration=2):
        self.lecture_duration = lecture_duration
        self.lab_duration = lab_duration


class TimetableScheduler:
    """Core timetable generation engine."""

    def __init__(self, db_manager):
        self.db = db_manager
        self.assignments: List[ClassAssignment] = []
        self.conflicts: List[Conflict] = []

        self.faculty_schedule: Dict = {}
        self.section_schedule: Dict = {}
        self.venue_schedule: Dict = {}

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------
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

        time_slots = self._generate_time_slots()

        for subject in data["subjects"]:
            self._place_subject(subject, data, time_slots, settings)

        return self.assignments, {"status": "ok"}, self.conflicts

    # -------------------------------------------------------------------------
    # Core placement logic
    # -------------------------------------------------------------------------
    def _generate_time_slots(self):
        """Generate fixed daily time slots (09:00–17:00) for 5 days."""
        slots = []
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri"]:
            start = 9
            while start < 17:
                end = start + 1
                slots.append(TimeSlot(day, f"{start:02}:00", f"{end:02}:00"))
                start = end
        return slots

    def _section_key(self, section, subsection: Optional[str]):
        """Return subsection-level key, e.g. '3:A1'."""
        sub_part = subsection if subsection else ""
        return f"{section.id}:{sub_part}"

    def _place_subject(self, subject: Subject, data, time_slots, settings) -> bool:
        """
        Place subject across sections and (for labs) across subsections.
        Returns True if at least one assignment was placed for the subject.
        """
        duration = settings.lab_duration if subject.is_lab else settings.lecture_duration
        valid_venues = [
            v for v in data["venues"]
            if v.venue_type == ("lab" if subject.is_lab else "lecture")
        ]

        placed_any = False

        # candidate faculties
        if getattr(subject, "preferred_faculty_ids", None):
            candidates = [f for f in data["faculties"] if f.id in subject.preferred_faculty_ids]
        else:
            candidates = data["faculties"][:]

        if not candidates:
            self.conflicts.append(Conflict("qualification", subject.code, "No qualified faculty", "high"))
            return False

        def faculty_load(fac: Faculty):
            sched = self.faculty_schedule.get(fac.id, {})
            total = 0
            for day_slots in sched.values():
                for ts in day_slots:
                    s1, e1 = self._to_minutes(ts.start), self._to_minutes(ts.end)
                    total += (e1 - s1)
            return total

        candidates.sort(key=faculty_load)

        for section in data["sections"]:
            subsections = section.subsections if subject.is_lab and section.subsections else [None]
            for subsection in subsections:
                placed = False
                for slot in time_slots:
                    for fac in candidates:
                        if not self._has_space(fac, section, subsection, valid_venues, slot, duration):
                            continue
                        venue = self._get_free_venue(valid_venues, slot, duration)
                        if not venue:
                            continue

                        assignment = ClassAssignment(
                            subject.id, fac.id, section.id, venue.id, subsection, slot.day, slot.start, duration
                        )
                        assignment.subject, assignment.faculty, assignment.section, assignment.venue = (
                            subject, fac, section, venue
                        )
                        self._block_slot(fac, section, venue, slot, duration, subsection)
                        self.assignments.append(assignment)
                        placed = True
                        placed_any = True
                        candidates.sort(key=faculty_load)
                        break
                    if placed:
                        break
                if not placed:
                    self.conflicts.append(Conflict("constraint", subject.code,
                                                   f"No slot for {section.name}{'/' + subsection if subsection else ''}",
                                                   "high"))
        return placed_any

    # -------------------------------------------------------------------------
    # Utility helpers
    # -------------------------------------------------------------------------
    def _has_space(self, faculty, section, subsection, venues, slot, duration):
        """Check if slot free for faculty + subsection."""
        if self._is_busy(self.faculty_schedule, faculty.id, slot, duration):
            return False
        key = self._section_key(section, subsection)
        if self._is_busy(self.section_schedule, key, slot, duration, key_is_str=True):
            return False
        return True

    def _is_busy(self, schedule, entity_id, slot, duration, key_is_str=False):
        """Check if a given entity (faculty/venue/section) is busy."""
        if key_is_str:
            key = entity_id
            if key not in schedule:
                return False
            slots = schedule[key].get(slot.day, [])
        else:
            if entity_id not in schedule:
                return False
            slots = schedule[entity_id].get(slot.day, [])

        start = self._to_minutes(slot.start)
        end = start + duration * 60
        for s in slots:
            s1, e1 = self._to_minutes(s.start), self._to_minutes(s.end)
            if not (end <= s1 or e1 <= start):
                return True
        return False

    def _get_free_venue(self, venues, slot, duration):
        for v in venues:
            if not self._is_busy(self.venue_schedule, v.id, slot, duration):
                return v
        return None

    def _block_slot(self, faculty, section, venue, slot, duration, subsection=None):
        """Reserve slot for faculty, section-subsection, and venue."""
        s_end = self._fmt(self._to_minutes(slot.start) + duration * 60)
        t = TimeSlot(slot.day, slot.start, s_end)

        # faculty
        self.faculty_schedule.setdefault(faculty.id, {}).setdefault(slot.day, []).append(t)
        # section key
        key = self._section_key(section, subsection)
        self.section_schedule.setdefault(key, {}).setdefault(slot.day, []).append(t)
        # venue
        self.venue_schedule.setdefault(venue.id, {}).setdefault(slot.day, []).append(t)

    # -------------------------------------------------------------------------
    # Time helpers
    # -------------------------------------------------------------------------
    def _to_minutes(self, time_str):
        h, m = map(int, time_str.split(":"))
        return h * 60 + m

    def _fmt(self, total_minutes):
        h, m = divmod(total_minutes, 60)
        return f"{h:02}:{m:02}"
