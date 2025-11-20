import sqlite3
import json
import threading
from pathlib import Path

from .db_models import Faculty, Subject, Venue, Section

class DatabaseManager:
    """
    SQLite manager with safe multi-thread reads and serialized writes.
    - check_same_thread=False (allows worker thread access)
    - WAL mode for simultaneous read/write
    - threading.Lock() for all writes
    """

    def __init__(self, db_path="timetable.db"):
        self.db_path = db_path
        Path(db_path).touch(exist_ok=True)

        # main DB connection
        self.conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=30
        )
        self.conn.row_factory = sqlite3.Row

        # enable WAL mode for thread-safe reads
        self.conn.execute("PRAGMA journal_mode = WAL;")
        self.conn.execute("PRAGMA synchronous = NORMAL;")
        self.conn.execute("PRAGMA foreign_keys = ON;")

        # serialize write operations
        self._lock = threading.Lock()

        self._create_tables()

    # ---------------------------------------------------------
    # THREAD-SAFE READ CONNECTION
    # ---------------------------------------------------------
    def get_read_only_connection(self):
        """Safe connection for worker threads (scheduler)."""
        conn = sqlite3.connect(
            f"file:{self.db_path}?mode=ro",
            uri=True,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        return conn

    # ---------------------------------------------------------
    # TABLE CREATION
    # ---------------------------------------------------------
    def _create_tables(self):
        cur = self.conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS faculties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            faculty_code TEXT NOT NULL,
            max_hours_per_day INTEGER DEFAULT 6
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            name TEXT NOT NULL,
            is_lab INTEGER DEFAULT 0,
            duration INTEGER DEFAULT 1,
            year INTEGER NOT NULL,
            semester INTEGER NOT NULL,
            degree TEXT DEFAULT 'B.Tech',
            preferred_faculty_ids TEXT DEFAULT '[]'
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS venues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            venue_type TEXT NOT NULL,
            capacity INTEGER DEFAULT 60,
            building TEXT DEFAULT 'Main Building',
            floor INTEGER DEFAULT 1
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            degree TEXT DEFAULT 'B.Tech',
            year INTEGER NOT NULL,
            semester INTEGER NOT NULL,
            strength INTEGER DEFAULT 60,
            subsections TEXT DEFAULT '[]'
        );
        """)

        self.conn.commit()

    # ---------------------------------------------------------
    # PARSERS -> Dataclasses
    # ---------------------------------------------------------
    def _faculty_from_row(self, r):
        return Faculty(
            id=r["id"],
            name=r["name"],
            faculty_code=r["faculty_code"],
            max_hours_per_day=r["max_hours_per_day"]
        )

    def _subject_from_row(self, r):
        return Subject(
            id=r["id"],
            code=r["code"],
            name=r["name"],
            is_lab=bool(r["is_lab"]),
            duration=r["duration"],
            year=r["year"],
            semester=r["semester"],
            degree=r["degree"],
            preferred_faculty_ids=json.loads(r["preferred_faculty_ids"] or "[]")
        )

    def _venue_from_row(self, r):
        return Venue(
            id=r["id"],
            name=r["name"],
            venue_type=r["venue_type"],
            capacity=r["capacity"],
            building=r["building"],
            floor=r["floor"]
        )

    def _section_from_row(self, r):
        return Section(
            id=r["id"],
            name=r["name"],
            degree=r["degree"],
            year=r["year"],
            semester=r["semester"],
            strength=r["strength"],
            subsections=json.loads(r["subsections"] or "[]")
        )

    # ---------------------------------------------------------
    # GENERIC FETCH
    # ---------------------------------------------------------
    def _fetch_rows(self, query, params=()):
        try:
            cur = self.conn.cursor()
            cur.execute(query, params)
            return cur.fetchall()
        except sqlite3.OperationalError as e:
            print("READ ERROR:", e)
            return []

    # ---------------------------------------------------------
    # FACULTY CRUD
    # ---------------------------------------------------------
    def get_faculties(self):
        rows = self._fetch_rows("SELECT * FROM faculties")
        return [self._faculty_from_row(r) for r in rows]

    def add_faculty(self, name, code, max_hours=6):
        with self._lock:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO faculties (name, faculty_code, max_hours_per_day) VALUES (?, ?, ?)",
                (name, code, max_hours)
            )
            self.conn.commit()
            return cur.lastrowid

    def update_faculty(self, faculty_id, name, code, max_hours):
        with self._lock:
            cur = self.conn.cursor()
            cur.execute(
                "UPDATE faculties SET name=?, faculty_code=?, max_hours_per_day=? WHERE id=?",
                (name, code, max_hours, faculty_id)
            )
            self.conn.commit()
            return cur.rowcount > 0

    def delete_faculty(self, faculty_id):
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM faculties WHERE id=?", (faculty_id,))
            self.conn.commit()
            return cur.rowcount > 0

    # ---------------------------------------------------------
    # SUBJECT CRUD
    # ---------------------------------------------------------
    def _parse_num_list(self, x):
        """Handles: [2,3], (2,3), '2,3', '2', int."""
        if isinstance(x, (list, tuple)):
            return list(x)
        if isinstance(x, int):
            return [x]
        if isinstance(x, str):
            return [int(i.strip()) for i in x.split(",") if i.strip().isdigit()]
        return []

    def get_subjects(self, year=None, semester=None, degree=None):
        q = "SELECT * FROM subjects WHERE 1=1"
        params = []

        if year is not None:
            years = self._parse_num_list(year)
            placeholders = ",".join("?" for _ in years)
            q += f" AND year IN ({placeholders})"
            params.extend(years)

        if semester is not None:
            sems = self._parse_num_list(semester)
            placeholders = ",".join("?" for _ in sems)
            q += f" AND semester IN ({placeholders})"
            params.extend(sems)

        if degree:
            q += " AND degree=?"
            params.append(degree)

        rows = self._fetch_rows(q, tuple(params))
        return [self._subject_from_row(r) for r in rows]

    def add_subject(self, code, name, is_lab, duration, semester, year, degree="B.Tech"):
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO subjects (code, name, is_lab, duration, semester, year, degree)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (code, name, int(is_lab), duration, semester, year, degree))
            self.conn.commit()
            return cur.lastrowid

    def update_subject(self, subject_id, code, name, is_lab, duration, semester, year, degree, preferred=None):
        if preferred is None:
            preferred = []
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("""
                UPDATE subjects SET 
                    code=?, name=?, is_lab=?, duration=?, semester=?, year=?, degree=?, 
                    preferred_faculty_ids=?
                WHERE id=?
            """, (code, name, int(is_lab), duration, semester, year, degree,
                  json.dumps(preferred), subject_id))
            self.conn.commit()
            return cur.rowcount > 0

    def delete_subject(self, subject_id):
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM subjects WHERE id=?", (subject_id,))
            self.conn.commit()
            return cur.rowcount > 0

    # ---------------------------------------------------------
    # VENUE CRUD
    # ---------------------------------------------------------
    def get_venues(self):
        rows = self._fetch_rows("SELECT * FROM venues")
        return [self._venue_from_row(r) for r in rows]

    def add_venue(self, name, venue_type, capacity=60, building="Main Building", floor=1):
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO venues (name, venue_type, capacity, building, floor)
                VALUES (?, ?, ?, ?, ?)
            """, (name, venue_type, capacity, building, floor))
            self.conn.commit()
            return cur.lastrowid

    def update_venue(self, venue_id, name, venue_type, capacity, building, floor):
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("""
                UPDATE venues SET name=?, venue_type=?, capacity=?, building=?, floor=?
                WHERE id=?
            """, (name, venue_type, capacity, building, floor, venue_id))
            self.conn.commit()
            return cur.rowcount > 0

    def delete_venue(self, venue_id):
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM venues WHERE id=?", (venue_id,))
            self.conn.commit()
            return cur.rowcount > 0

    # ---------------------------------------------------------
    # SECTIONS CRUD
    # ---------------------------------------------------------
    def get_sections(self, year=None, semester=None, degree=None):
        q = "SELECT * FROM sections WHERE 1=1"
        params = []

        if year is not None:
            years = self._parse_num_list(year)
            placeholders = ",".join("?" for _ in years)
            q += f" AND year IN ({placeholders})"
            params.extend(years)

        if semester is not None:
            sems = self._parse_num_list(semester)
            placeholders = ",".join("?" for _ in sems)
            q += f" AND semester IN ({placeholders})"
            params.extend(sems)

        if degree:
            q += " AND degree=?"
            params.append(degree)

        rows = self._fetch_rows(q, tuple(params))
        return [self._section_from_row(r) for r in rows]

    def add_section(self, name, semester, year, degree="B.Tech", subsections=None, strength=60):
        if subsections is None:
            subsections = []
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO sections (name, semester, year, degree, subsections, strength)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, semester, year, degree, json.dumps(subsections), strength))
            self.conn.commit()
            return cur.lastrowid

    def update_section(self, section_id, name, semester, year, degree, subsections, strength):
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("""
                UPDATE sections SET name=?, semester=?, year=?, degree=?, subsections=?, strength=?
                WHERE id=?
            """, (name, semester, year, degree, json.dumps(subsections), strength, section_id))
            self.conn.commit()
            return cur.rowcount > 0

    def delete_section(self, section_id):
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM sections WHERE id=?", (section_id,))
            self.conn.commit()
            return cur.rowcount > 0

    # ---------------------------------------------------------
    # Utility
    # ---------------------------------------------------------
    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass
