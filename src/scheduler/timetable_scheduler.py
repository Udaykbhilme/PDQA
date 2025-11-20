# src/scheduler/timetable_scheduler.py
from ortools.sat.python import cp_model
import time
from collections import defaultdict
from typing import Optional, Union, List

from ..database.db_models import (
    Subject, Faculty, Venue, Section,
    ClassAssignment, Conflict
)


class GenerationSettings:
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
        year: Optional[Union[int, List[int]]] = None,
        semester: Optional[Union[int, List[int]]] = None,
        target_section: Optional[str] = None,  # kept for future UI filter usage
    ):
        self.lecture_duration = lecture_duration
        self.lab_duration = lab_duration
        self.lunch_start = lunch_start
        self.lunch_end = lunch_end
        self.start_time = start_time
        self.end_time = end_time
        self.days = days or ["Mon", "Tue", "Wed", "Thu", "Fri"]
        self.degree = degree
        self.year = year if isinstance(year, list) else ([year] if year else None)
        self.semester = semester if isinstance(semester, list) else ([semester] if semester else None)
        self.target_section = target_section


class CPSATScheduler:
    def __init__(self, db_manager):
        self.db = db_manager
        self.model = None
        self.assignments = []
        self.conflicts = []

        self._faculties_list = []
        self._venues_list = []
        self._sections_list = []

    # ----------------------------
    # PUBLIC: generate timetable
    # ----------------------------
    def generate(self, settings: GenerationSettings):
        self.model = cp_model.CpModel()
        self.assignments = []
        self.conflicts = []

        # Fetch data objects
        faculties = self.db.get_faculties()
        subjects = self.db.get_subjects(settings.year, settings.semester, settings.degree)
        venues = self.db.get_venues()
        sections = self.db.get_sections(settings.year, settings.semester, settings.degree)

        if not faculties or not subjects or not venues or not sections:
            raise ValueError("Missing faculty, subjects, venues, or sections in DB.")

        # time structure
        num_days = len(settings.days)
        hours_per_day = self._hours_range(settings)
        slots_per_day = len(hours_per_day)
        if slots_per_day <= 0:
            raise ValueError("Invalid time range")
        num_slots = num_days * slots_per_day

        # lunch slots (indices per day)
        lunch_start = self._to_minutes(settings.lunch_start)
        lunch_end = self._to_minutes(settings.lunch_end)
        day_start = self._to_minutes(settings.start_time)
        lunch_indices = []
        for offset in range(slots_per_day):
            slot_start = day_start + offset * 60
            if lunch_start <= slot_start < lunch_end:
                lunch_indices.append(offset)

        # sort for deterministic behavior
        faculties = sorted(faculties, key=lambda x: x.id)
        venues = sorted(venues, key=lambda x: x.id)
        sections = sorted(sections, key=lambda x: x.id)

        self._faculties_list = faculties
        self._venues_list = venues
        self._sections_list = sections

        num_faculties = len(faculties)
        num_venues = len(venues)

        # Variables container
        X = {}
        total_classes = 0

        # Build variables for each subject x section x subsection
        for subj in subjects:
            for sec in sections:
                if subj.year != sec.year or subj.semester != sec.semester:
                    continue

                subsections = sec.subsections if subj.is_lab else [None]
                if not subsections:
                    subsections = [None]

                for sub in subsections:
                    total_classes += 1
                    key = (subj.id, sec.id, sub)

                    # faculty domain (preferred or all)
                    pref = subj.preferred_faculty_ids or []
                    if pref:
                        allowed_facs = [i for i, f in enumerate(faculties) if f.id in pref]
                    else:
                        allowed_facs = list(range(num_faculties))
                    if not allowed_facs:
                        allowed_facs = list(range(num_faculties))
                        self.conflicts.append(
                            Conflict("faculty", subj.code, "No preferred faculty found; using all.", "high")
                        )

                    # venue domain (lecture/lab)
                    desired = "lab" if subj.is_lab else "lecture"
                    allowed_rooms = [
                        i for i, v in enumerate(venues)
                        if v.venue_type == desired and v.capacity >= sec.strength
                    ]
                    if not allowed_rooms:
                        allowed_rooms = [i for i, v in enumerate(venues) if v.venue_type == desired]
                    if not allowed_rooms:
                        allowed_rooms = list(range(num_venues))
                        self.conflicts.append(
                            Conflict("venue", subj.code, "No matching venue; using all.", "high")
                        )

                    # duration
                    duration = subj.duration or (settings.lab_duration if subj.is_lab else settings.lecture_duration)
                    # integer variables
                    start = self.model.NewIntVar(0, max(0, num_slots - duration), f"start_{key}")
                    end = self.model.NewIntVar(0, num_slots, f"end_{key}")
                    interval = self.model.NewIntervalVar(start, duration, end, f"iv_{key}")

                    fac_var = self.model.NewIntVarFromDomain(cp_model.Domain.FromValues(allowed_facs), f"fac_{key}")
                    room_var = self.model.NewIntVarFromDomain(cp_model.Domain.FromValues(allowed_rooms), f"room_{key}")

                    # store day booleans for spreading objective
                    day_bools = [self.model.NewBoolVar(f"day_{key}_{d}") for d in range(num_days)]

                    # ensure exactly one day boolean true
                    self.model.Add(sum(day_bools) == 1)

                    # link day booleans with start slot range
                    for d, b in enumerate(day_bools):
                        low = d * slots_per_day
                        high = (d + 1) * slots_per_day - 1
                        # If b true => start in [low, high]
                        self.model.Add(start >= low).OnlyEnforceIf(b)
                        self.model.Add(start <= high).OnlyEnforceIf(b)
                        # If b false => start not in that day interval
                        # (optional but explicit)
                        # Achieved implicitly by the exact-one constraint

                    # disallow starts that would overflow the day (e.g., 2hr class starting in last slot)
                    for d in range(num_days):
                        day_base = d * slots_per_day
                        latest_start = day_base + (slots_per_day - duration)
                        for s in range(latest_start + 1, day_base + slots_per_day):
                            # start cannot equal s (would overflow)
                            self.model.Add(start != s)

                    # lunch exclusion: already done later per-slot below
                    # link end/start
                    self.model.Add(end == start + duration)

                    X[key] = {
                        "start": start,
                        "end": end,
                        "interval": interval,
                        "duration": duration,
                        "faculty": fac_var,
                        "room": room_var,
                        "subject": subj,
                        "section": sec,
                        "day_bools": day_bools,
                    }

                    # Forbid start values that land on lunch slots (for any day)
                    for di in range(num_days):
                        base = di * slots_per_day
                        for li in lunch_indices:
                            # if a class would occupy the lunch slot (any overlap), forbid starting at those starts
                            lo = max(base + li - (duration - 1), 0)
                            hi = min(base + li, num_slots - 1)
                            for s in range(lo, hi + 1):
                                self.model.Add(start != s)

        # -------------------------
        # NO-OVERLAP FOR RESOURCES
        # -------------------------
        faculty_intervals = {i: [] for i in range(num_faculties)}
        venue_intervals = {i: [] for i in range(num_venues)}
        section_intervals = defaultdict(list)

        indicators_for_fac = {i: [] for i in range(num_faculties)}

        # We'll also build day indicator sum for each day
        day_counts = {d: [] for d in range(num_days)}

        for key, vars in X.items():
            start = vars["start"]
            duration = vars["duration"]
            end = vars["end"]
            interval = vars["interval"]
            fac_var = vars["faculty"]
            room_var = vars["room"]
            sec = vars["section"]
            subsection = key[2]

            # section-level separation by subsection: key on (section, subsection)
            sec_key = (sec.id, subsection)
            section_intervals[sec_key].append(interval)

            # faculties: optional intervals per faculty index
            for f_index in range(num_faculties):
                b = self.model.NewBoolVar(f"fac_ind_{key}_{f_index}")
                self.model.Add(fac_var == f_index).OnlyEnforceIf(b)
                self.model.Add(fac_var != f_index).OnlyEnforceIf(b.Not())
                indicators_for_fac[f_index].append(b)
                opt_iv = self.model.NewOptionalIntervalVar(start, duration, end, b, f"optf_{key}_{f_index}")
                faculty_intervals[f_index].append(opt_iv)

            # venues: optional intervals per venue index
            for v_index in range(num_venues):
                b = self.model.NewBoolVar(f"room_ind_{key}_{v_index}")
                self.model.Add(room_var == v_index).OnlyEnforceIf(b)
                self.model.Add(room_var != v_index).OnlyEnforceIf(b.Not())
                opt_iv = self.model.NewOptionalIntervalVar(start, duration, end, b, f"optr_{key}_{v_index}")
                venue_intervals[v_index].append(opt_iv)

            # day counts: each class contributes to exactly one day boolean (already added), collect them
            for d, db in enumerate(vars["day_bools"]):
                day_counts[d].append(db)

        # No overlap constraints
        for ivs in faculty_intervals.values():
            self.model.AddNoOverlap(ivs)
        for ivs in venue_intervals.values():
            self.model.AddNoOverlap(ivs)
        for ivs in section_intervals.values():
            self.model.AddNoOverlap(ivs)

        # -------------------------
        # OBJECTIVE: SPREAD ACROSS DAYS + BALANCE FACULTY LOAD
        # -------------------------
        total_classes = max(1, sum(len(lst) for lst in day_counts.values()))

        # Day load variables: number of classes placed on each day
        day_load_vars = []
        for d in range(num_days):
            dl = self.model.NewIntVar(0, total_classes, f"day_load_{d}")
            self.model.Add(dl == sum(day_counts[d]))
            day_load_vars.append(dl)

        # minimize maximum day load (forces spread)
        max_day_load = self.model.NewIntVar(0, total_classes, "max_day_load")
        self.model.AddMaxEquality(max_day_load, day_load_vars)

        # Faculty load (existing balancing)
        loads = [self.model.NewIntVar(0, total_classes, f"load_{i}") for i in range(num_faculties)]
        for f in range(num_faculties):
            self.model.Add(loads[f] == sum(indicators_for_fac[f]))
        max_fac_load = self.model.NewIntVar(0, total_classes, "max_fac_load")
        self.model.AddMaxEquality(max_fac_load, loads)

        # Combined objective: primarily minimize max_day_load, secondarily balance faculty using small weight
        # weight must be > possible range of second objective; use 1000 as safe multiplier
        self.model.Minimize(max_day_load * 1000 + max_fac_load)

        # -------------------------
        # SOLVE
        # -------------------------
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 60
        solver.parameters.num_search_workers = 8
        solver.parameters.random_seed = int(time.time())

        status = solver.Solve(self.model)

        info = {
            "degree": settings.degree,
            "year": settings.year,
            "semester": settings.semester,
            "days": settings.days,
            "start_time": settings.start_time,
            "end_time": settings.end_time,
            "lunch_start": settings.lunch_start,
            "lunch_end": settings.lunch_end,
        }

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            self.conflicts.append(Conflict("solver", "none", "No feasible timetable found", "critical"))
            return [], info, self.conflicts

        self._build_assignments(X, solver, settings, slots_per_day)
        return self.assignments, info, self.conflicts

    # ----------------------------
    # Build ClassAssignment dataclasses from solver solution
    # ----------------------------
    def _build_assignments(self, X, solver, settings, slots_per_day):
        self.assignments = []

        faculties = self._faculties_list
        venues = self._venues_list
        sections = self._sections_list

        for key, vars in X.items():
            subj_id, sec_id, subsection = key

            start_slot = solver.Value(vars["start"])
            duration = vars["duration"]
            fac_index = solver.Value(vars["faculty"])
            room_index = solver.Value(vars["room"])

            subj = vars["subject"]
            sec = vars["section"]

            if not (0 <= fac_index < len(faculties)):
                continue
            if not (0 <= room_index < len(venues)):
                continue

            faculty = faculties[fac_index]
            venue = venues[room_index]

            day_index = start_slot // slots_per_day
            hour_index = start_slot % slots_per_day

            day = settings.days[day_index]
            base_hour = self._to_minutes(settings.start_time) // 60

            start_hour = base_hour + hour_index
            end_hour = start_hour + duration

            a = ClassAssignment(
                subject_id=subj_id,
                faculty_id=faculty.id,
                section_id=sec_id,
                venue_id=venue.id,
                subsection=subsection,
                day=day,
                start_time=f"{start_hour:02d}:00",
                duration=duration
            )

            a.end_time = f"{end_hour:02d}:00"
            a.subject_code = subj.code
            a.subject_name = subj.name
            a.faculty_name = faculty.name
            a.section_name = sec.name
            a.venue_name = venue.name
            a.is_lab = subj.is_lab
            a.faculties = [{"id": faculty.id, "name": faculty.name}]

            self.assignments.append(a)

    # ----------------------------
    # Utilities
    # ----------------------------
    def _hours_range(self, settings):
        s = self._to_minutes(settings.start_time)
        e = self._to_minutes(settings.end_time)
        if e <= s:
            return []
        total = (e - s) // 60
        return list(range(total))

    def _to_minutes(self, hhmm):
        h, m = map(int, hhmm.split(":"))
        return h * 60 + m
