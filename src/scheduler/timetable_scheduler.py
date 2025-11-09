"""
Constraint-based Timetable Scheduler (CP-SAT)
- Builds schedule using Google OR-Tools CP-SAT solver.
- Supports lecture/lab separation, subsections, faculty load balancing, and lunch skip.
- Respects Subject.preferred_faculty_ids and venue type restrictions.

Notes:
- ClassAssignment objects returned contain plain fields (subject_name, faculty_name, faculties -> list of dicts)
  to remain thread-safe and exporter-friendly. Do not rely on attached ORM objects being alive across threads.
"""

from ortools.sat.python import cp_model
from ..database.db_models import Subject, Faculty, Venue, Section, ClassAssignment, Conflict


class GenerationSettings:
    """Configuration class for timetable generation."""

    def __init__(
        self,
        lecture_duration: int = 1,
        lab_duration: int = 2,
        lunch_start: str = "13:00",
        lunch_end: str = "14:00",
        start_time: str = "09:00",
        end_time: str = "17:00",
        days=None,
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


class CPSATScheduler:
    def __init__(self, db_manager):
        self.db = db_manager
        # model will be created per-run in generate()
        self.model = None
        self.assignments = []
        self.conflicts = []

    # ---------------------------------------------------------------------
    # Main Generation Entry Point
    # ---------------------------------------------------------------------
    def generate(self, settings: GenerationSettings):
        # reset state for each run
        self.model = cp_model.CpModel()
        self.assignments = []
        self.conflicts = []

        faculties = self.db.get_faculties()
        subjects = self.db.get_subjects(settings.year, settings.semester, settings.degree)
        venues = self.db.get_venues()
        sections = self.db.get_sections(settings.year, settings.semester, settings.degree)

        if not faculties or not subjects or not venues or not sections:
            raise ValueError("Database missing required data (faculty, subject, venue, or section).")

        num_days = len(settings.days)
        hours_per_day = self._hours_range(settings)
        slots_per_day = len(hours_per_day)
        num_slots = num_days * slots_per_day
        num_faculties = len(faculties)
        num_venues = len(venues)

        # Decision variables
        X = {}  # (subject, section, subsection) → (slot, room, faculty)
        for subj in subjects:
            for section in sections:
                if getattr(subj, "year", None) != getattr(section, "year", None) or getattr(subj, "semester", None) != getattr(section, "semester", None):
                    continue
                subsections = section.subsections if getattr(subj, "is_lab", False) else [None]
                for sub in subsections:
                    key = (subj.id, section.id, sub)

                    # --- faculty domain: restrict to preferred_faculty_ids if present ---
                    if getattr(subj, "preferred_faculty_ids", None):
                        allowed_faculty_ids = [fid for fid in subj.preferred_faculty_ids or []]
                        allowed_faculty_indices = [i for i, f in enumerate(faculties) if f.id in allowed_faculty_ids]
                        if not allowed_faculty_indices:
                            # no mapped faculties found in DB; record conflict and fallback to all faculties
                            self.conflicts.append(Conflict("qualification", subj.code,
                                                           f"No mapped faculty IDs present for subject {subj.code}. Allowing all faculties as fallback.",
                                                           "high"))
                            allowed_faculty_indices = list(range(num_faculties))
                    else:
                        allowed_faculty_indices = list(range(num_faculties))

                    fac_var = self.model.NewIntVarFromDomain(
                        cp_model.Domain.FromValues(allowed_faculty_indices),
                        f"fac_{key}"
                    )

                    # --- room domain: restrict to correct venue_type (lecture/lab) ---
                    desired_type = "lab" if getattr(subj, "is_lab", False) else "lecture"
                    allowed_room_indices = [i for i, v in enumerate(venues) if getattr(v, "venue_type", None) == desired_type]
                    if not allowed_room_indices:
                        # if no room of that type exists, add conflict and fallback to all rooms
                        self.conflicts.append(Conflict("venue", subj.code,
                                                       f"No venues of type '{desired_type}' found for subject {subj.code}. Allowing all venues as fallback.",
                                                       "high"))
                        allowed_room_indices = list(range(num_venues))

                    room_var = self.model.NewIntVarFromDomain(
                        cp_model.Domain.FromValues(allowed_room_indices),
                        f"room_{key}"
                    )

                    slot_var = self.model.NewIntVar(0, num_slots - 1, f"slot_{key}")

                    X[key] = {
                        "slot": slot_var,
                        "room": room_var,
                        "faculty": fac_var,
                        "subject": subj,
                        "section_obj": section,
                    }

        # ---------------------------------------------------------------------
        # Constraints
        # ---------------------------------------------------------------------
        self._faculty_no_overlap(X, slots_per_day, num_faculties)
        self._section_no_overlap(X)
        self._lab_duration_constraint(X, subjects, settings, slots_per_day)
        self._respect_lunch(X, settings, slots_per_day)
        self._venue_capacity_constraint(X, subjects, venues, sections)
        # Balance faculty load as an objective (connected to X)
        self._balance_faculty_load(X, faculties, num_faculties)

        # ---------------------------------------------------------------------
        # Solve Model
        # ---------------------------------------------------------------------
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 60  # bump while debugging/trying real instances
        solver.parameters.num_search_workers = 8
        status = solver.Solve(self.model)

        # prepare timetable metadata to return to GUI
        timetable_info = {
            "degree": settings.degree,
            "year": settings.year,
            "semester": settings.semester,
            "days": settings.days,
            "start_time": settings.start_time,
            "end_time": settings.end_time,
            "lunch_start": settings.lunch_start,
            "lunch_end": settings.lunch_end,
        }

        if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            self.conflicts.append(Conflict("solver", "none", "No feasible solution found", "critical"))
            return [], timetable_info, self.conflicts

        print("✅ Feasible timetable found")
        self._build_assignments(X, solver, subjects, sections, faculties, venues, settings, slots_per_day)
        return self.assignments, timetable_info, self.conflicts

    # ---------------------------------------------------------------------
    # Constraint Definitions
    # ---------------------------------------------------------------------
    def _faculty_no_overlap(self, X, slots_per_day: int, num_faculties: int):
        """No faculty can teach two classes in the same time slot.

        For every pair of distinct classes A,B:
          If A.faculty == B.faculty then A.slot != B.slot.

        Uses a reified boolean to link equality -> slot-difference.
        """
        keys = list(X.keys())
        n = len(keys)
        # If there are many variables this is O(n^2) constraints; still typical for timetabling.
        for i in range(n):
            for j in range(i + 1, n):
                a = X[keys[i]]
                b = X[keys[j]]

                # Boolean that is true iff the two faculty indices are equal
                same_fac = self.model.NewBoolVar(f"same_fac_{i}_{j}")

                # Link equality with the boolean
                self.model.Add(a["faculty"] == b["faculty"]).OnlyEnforceIf(same_fac)
                self.model.Add(a["faculty"] != b["faculty"]).OnlyEnforceIf(same_fac.Not())

                # If they are same faculty then slots must differ
                self.model.Add(a["slot"] != b["slot"]).OnlyEnforceIf(same_fac)

    def _section_no_overlap(self, X):
        """Each section/subsection can attend only one class at a time."""
        sec_slots = {}
        for key, vars in X.items():
            _, sec_id, _ = key
            sec_slots.setdefault(sec_id, []).append(vars["slot"])
        for sec, slots in sec_slots.items():
            if len(slots) > 1:
                self.model.AddAllDifferent(slots)

    def _lab_duration_constraint(self, X, subjects, settings, slots_per_day):
        """Ensure labs occupy multi-hour continuous slots (lab_duration by default)."""
        lab_dur = settings.lab_duration
        if lab_dur <= 1:
            return

        # Constrain: hour_index = slot % slots_per_day, and hour_index <= max_start
        max_start = slots_per_day - lab_dur
        if max_start < 0:
            # lab duration longer than day length -> impossible; record conflict
            self.conflicts.append(Conflict("timing", "lab_duration",
                                           "Lab duration exceeds slots per day", "critical"))
            return

        for key, vars in X.items():
            subj_id, _, _ = key
            subj = next((s for s in subjects if s.id == subj_id), None)
            if subj and getattr(subj, "is_lab", False):
                hour_index = self.model.NewIntVar(0, slots_per_day - 1, f"hour_idx_{key}")
                # hour_index == slot mod slots_per_day
                self.model.AddModuloEquality(hour_index, vars["slot"], slots_per_day)
                self.model.Add(hour_index <= max_start)

    def _respect_lunch(self, X, settings, slots_per_day):
        """Ensure lunch break has no sessions.

        This computes slot indices that start inside the lunch window and forbids them.
        Works for arbitrary start/end times (assumes hourly slots).
        """
        lunch_start = self._to_minutes(settings.lunch_start)
        lunch_end = self._to_minutes(settings.lunch_end)
        day_start_min = self._to_minutes(settings.start_time)

        # Build list of hour offsets (0..slots_per_day-1) whose start minute falls inside lunch window
        lunch_indices = []
        for hour_offset in range(slots_per_day):
            slot_start_min = day_start_min + hour_offset * 60
            # if slot overlaps lunch start -> forbid (we assume no partial-slot handling; slots are hourly)
            if slot_start_min >= lunch_start and slot_start_min < lunch_end:
                lunch_indices.append(hour_offset)

        if not lunch_indices:
            return

        for key, vars in X.items():
            hour_index = self.model.NewIntVar(0, slots_per_day - 1, f"li_hour_idx_{key}")
            self.model.AddModuloEquality(hour_index, vars["slot"], slots_per_day)
            for idx in lunch_indices:
                self.model.Add(hour_index != idx)

    def _venue_capacity_constraint(self, X, subjects, venues, sections):
        """Ensure sections fit in venues."""
        for key, vars in X.items():
            subj_id, sec_id, _ = key
            subj = next((s for s in subjects if s.id == subj_id), None)
            sec = next((s for s in sections if s.id == sec_id), None)
            if subj and sec:
                for i, v in enumerate(venues):
                    if getattr(v, "capacity", 0) < getattr(sec, "strength", 0):
                        self.model.Add(vars["room"] != i)

    def _balance_faculty_load(self, X, faculties, num_faculties: int):
        """Create load variables tied to X and set an objective to minimize load sum (balance).

        For each faculty f:
          load_f == number of classes assigned to f
        Then minimize sum(load_f).
        """
        # create load vars
        loads = [self.model.NewIntVar(0, 1000, f"load_{i}") for i in range(num_faculties)]

        # Build indicators: for each class and each faculty index, a Bool indicating class uses that faculty.
        indicators_for_fac = {f: [] for f in range(num_faculties)}
        for key, vars in X.items():
            class_indicators = []
            for f in range(num_faculties):
                b = self.model.NewBoolVar(f"ind_{key}_{f}")
                # b -> vars["faculty"] == f ; not(b) -> != f
                self.model.Add(vars["faculty"] == f).OnlyEnforceIf(b)
                self.model.Add(vars["faculty"] != f).OnlyEnforceIf(b.Not())
                indicators_for_fac[f].append(b)

        # link loads to sums
        for f in range(num_faculties):
            self.model.Add(loads[f] == sum(indicators_for_fac[f]))

        # objective: minimize sum(loads) to encourage spreading work a bit
        self.model.Minimize(sum(loads))

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------
    def _build_assignments(self, X, solver, subjects, sections, faculties, venues, settings, slots_per_day):
        """Convert CP-SAT variable results into ClassAssignment objects (thread-safe data)."""
        total_slots_per_day = slots_per_day
        for key, vars in X.items():
            subj_id, sec_id, sub = key
            subj = next((s for s in subjects if s.id == subj_id), None)
            sec = next((s for s in sections if s.id == sec_id), None)
            fac_index = solver.Value(vars["faculty"])
            room_index = solver.Value(vars["room"])
            slot_val = solver.Value(vars["slot"])

            # safe guards: index bounds
            if fac_index < 0 or fac_index >= len(faculties) or room_index < 0 or room_index >= len(venues):
                # This should not happen if domains were set correctly, but guard anyway
                self.conflicts.append(Conflict("index", str(key), "Solver returned out-of-bounds index for faculty/room", "high"))
                continue

            fac = faculties[fac_index]
            ven = venues[room_index]

            day_index = slot_val // total_slots_per_day
            hour_index = slot_val % total_slots_per_day
            day = settings.days[day_index]
            start_hour = (self._to_minutes(settings.start_time) // 60) + hour_index

            # Use subj.duration if present, else use lecture/lab durations
            duration = getattr(subj, "duration", None)
            if duration is None:
                duration = settings.lab_duration if getattr(subj, "is_lab", False) else settings.lecture_duration

            # Build assignment object (keep IDs consistent)
            a = ClassAssignment(
                subj_id,
                fac.id,
                sec_id,
                ven.id,
                sub,
                day,
                f"{start_hour:02}:00",
                duration
            )

            # Thread-safe flattened fields for exporters / UI (strings and simple lists/dicts)
            a.subject_code = getattr(subj, "code", "") if subj else ""
            a.subject_name = getattr(subj, "name", "") if subj else ""
            a.faculty_name = getattr(fac, "name", "") if fac else ""
            a.section_name = getattr(sec, "name", f"Section {sec_id}") if sec else f"Section {sec_id}"
            a.venue_name = getattr(ven, "name", getattr(ven, "code", "")) if ven else ""

            a.day = day
            a.start_time = f"{start_hour:02}:00"
            a.duration = duration
            a.is_lab = getattr(subj, "is_lab", False) if subj else False

            # Provide a serializable faculty list (id + name) for multi-faculty-safe rendering
            a.faculties = [{"id": fac.id, "name": a.faculty_name}] if fac else []

            # Keep original object refs too (but do not rely on them across threads)
            a.subject = subj
            a.section = sec
            a.faculty = fac
            a.venue = ven

            self.assignments.append(a)

    def _hours_range(self, settings):
        """Return list of working-hour indices; assumes hourly slots."""
        s = self._to_minutes(settings.start_time)
        e = self._to_minutes(settings.end_time)
        total_hours = (e - s) // 60
        return list(range(total_hours))

    def _to_minutes(self, time_str):
        h, m = map(int, time_str.split(":"))
        return h * 60 + m
