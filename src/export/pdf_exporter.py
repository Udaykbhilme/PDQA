"""
PDF Exporter for Timetable Generator
Generates professional PDFs and HTML previews of timetables.
Now supports:
- Visible lunch slots
- Always shows faculty names (no ORM dependency)
"""

from datetime import datetime
from typing import List, Dict
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch

from ..database.db_models import ClassAssignment


class PDFExporter:
    """Handles timetable export to PDF and HTML preview."""

    def __init__(self):
        self.page_width, self.page_height = landscape(A4)
        self.margin = 1 * inch
        self.lecture_color = colors.HexColor("#dbeafe")  # light blue
        self.lab_color = colors.HexColor("#dcfce7")      # light green
        self.lunch_color = colors.HexColor("#f1f5f9")    # light gray

    # ---------------------------------------------------------
    # PUBLIC METHODS
    # ---------------------------------------------------------
    def export_timetable(self, assignments: List[ClassAssignment],
                         timetable_info: Dict, output_path: str) -> bool:
        """Export timetable as a PDF file."""
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=landscape(A4),
                leftMargin=self.margin,
                rightMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin,
            )
            story = []
            story += self._create_header(timetable_info)
            story.append(Spacer(1, 0.2 * inch))
            story.append(self._create_timetable(assignments, timetable_info))
            story.append(Spacer(1, 0.3 * inch))
            story += self._create_footer()
            doc.build(story)
            return True
        except Exception as e:
            print(f"PDF export failed: {e}")
            return False

    def preview_timetable(self, assignments: List[ClassAssignment],
                          timetable_info: Dict) -> str:
        """Generate simple HTML preview of the timetable."""
        time_slots = self._generate_time_slots(timetable_info, include_lunch=True)
        days = timetable_info.get('days', ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'])

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Timetable Preview</title>
            <style>
                body {{
                    background-color: #0f172a;
                    color: #e2e8f0;
                    font-family: Arial, sans-serif;
                    padding: 20px;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin-top: 10px;
                }}
                th, td {{
                    border: 1px solid #475569;
                    padding: 6px;
                    text-align: center;
                }}
                th {{
                    background-color: #1e293b;
                    color: #f8fafc;
                }}
                td.lecture {{ background-color: #1d4ed8; color: #f1f5f9; }}
                td.lab {{ background-color: #15803d; color: #f1f5f9; }}
                td.time {{ background-color: #334155; font-weight: bold; }}
                td.lunch {{ background-color: #475569; color: #cbd5e1; font-style: italic; }}
                h2 {{ color: #38bdf8; text-align: center; }}
            </style>
        </head>
        <body>
            <h2>Computer Science & Engineering Department</h2>
            <p style="text-align:center;">
                {timetable_info.get('degree', 'B.Tech')} - Year {timetable_info.get('year', '')},
                Semester {timetable_info.get('semester', '')}
            </p>
            <p style="text-align:center; font-size:12px;">
                Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </p>
            <table>
                <thead>
                    <tr><th>Time</th>{"".join(f"<th>{d}</th>" for d in days)}</tr>
                </thead>
                <tbody>
        """
        for slot in time_slots:
            html += f"<tr><td class='time'>{slot['start']}<br>{slot['end']}</td>"
            for day in days:
                if slot.get("is_lunch", False):
                    html += "<td class='lunch'>Lunch Break</td>"
                else:
                    html += self._html_cell(assignments, day, slot['start'])
            html += "</tr>"
        html += """
                </tbody>
            </table>
        </body>
        </html>
        """
        return html

    # ---------------------------------------------------------
    # INTERNAL UTILITIES
    # ---------------------------------------------------------
    def _create_header(self, info: Dict):
        styles = getSampleStyleSheet()
        title = ParagraphStyle(
            "Title", parent=styles["Heading1"],
            fontSize=18, textColor=colors.HexColor("#1e3a8a"), alignment=TA_CENTER
        )
        subtitle = ParagraphStyle(
            "Sub", parent=styles["Normal"],
            fontSize=11, alignment=TA_CENTER, spaceAfter=6
        )
        degree = info.get("degree", "B.Tech")
        year, sem = info.get("year", ""), info.get("semester", "")
        text = f"{degree} - Year {year}, Semester {sem}"
        return [
            Paragraph("Computer Science & Engineering Department", title),
            Paragraph(text, subtitle),
            Paragraph(datetime.now().strftime("Generated on %B %d, %Y, %I:%M %p"), subtitle),
        ]

    def _create_footer(self):
        styles = getSampleStyleSheet()
        style = ParagraphStyle(
            "Footer", parent=styles["Normal"],
            fontSize=8, textColor=colors.gray, alignment=TA_CENTER
        )
        return [Paragraph("Generated by CSE Timetable Generator", style)]

    def _create_timetable(self, assignments, info):
        time_slots = self._generate_time_slots(info, include_lunch=True)
        days = info.get('days', ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'])
        data = [["Time"] + days]

        for slot in time_slots:
            row = [f"{slot['start']} - {slot['end']}"]
            for day in days:
                if slot.get("is_lunch", False):
                    row.append("Lunch Break")
                else:
                    content = self._pdf_cell(assignments, day, slot['start'])
                    row.append(content)
            data.append(row)

        table = Table(data)
        table.setStyle(self._table_style(data))
        return table

    def _table_style(self, data):
        style = TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ])

        # Highlight Lunch Break rows
        for r, row in enumerate(data[1:], start=1):
            if all(c == "Lunch Break" or c == row[0] for c in row):
                style.add('BACKGROUND', (0, r), (-1, r), self.lunch_color)
                style.add('TEXTCOLOR', (0, r), (-1, r), colors.gray)
        return style

    def _generate_time_slots(self, info: Dict, include_lunch=False):
        def to_min(t): h, m = map(int, t.split(":")); return h * 60 + m
        def to_time(m): return f"{m//60:02d}:{m%60:02d}"

        start, end = to_min(info.get('start_time', '09:00')), to_min(info.get('end_time', '18:00'))
        lunch_start, lunch_end = to_min(info.get('lunch_start', '13:00')), to_min(info.get('lunch_end', '14:00'))
        slots = []

        for t in range(start, end, 60):
            if include_lunch and lunch_start <= t < lunch_end:
                slots.append({'start': to_time(t), 'end': to_time(t + 60), 'is_lunch': True})
            else:
                slots.append({'start': to_time(t), 'end': to_time(t + 60)})
        return slots

    # ---------------------------------------------------------
    # FIXED CELLS — FACULTY ALWAYS SHOWN
    # ---------------------------------------------------------
    def _pdf_cell(self, assignments, day, start_time):
        """Return plain text for cell in PDF table (always shows faculty names)."""
        match = [a for a in assignments if a.day == day and a.start_time == start_time]
        if not match:
            return ""

        a = match[0]
        subj_code = getattr(a, "subject_code", getattr(a.subject, "code", ""))
        subj_name = getattr(a, "subject_name", getattr(a.subject, "name", ""))
        faculty_name = getattr(a, "faculty_name", "")
        if not faculty_name and getattr(a, "faculty", None):
            faculty_name = getattr(a.faculty, "name", "Unknown Faculty")

        venue_name = getattr(a, "venue_name", getattr(a.venue, "name", ""))
        if not subj_name and not subj_code:
            return "Data Missing"

        return f"{subj_code}\n{subj_name}\n{faculty_name}\n{venue_name}"

    def _html_cell(self, assignments, day, start_time):
        """Return HTML cell with proper color class and faculty names."""
        match = [a for a in assignments if a.day == day and a.start_time == start_time]
        if not match:
            return "<td></td>"

        a = match[0]
        subj_code = getattr(a, "subject_code", getattr(a.subject, "code", ""))
        subj_name = getattr(a, "subject_name", getattr(a.subject, "name", ""))
        faculty_name = getattr(a, "faculty_name", "")
        if not faculty_name and getattr(a, "faculty", None):
            faculty_name = getattr(a.faculty, "name", "Unknown Faculty")

        venue_name = getattr(a, "venue_name", getattr(a.venue, "name", ""))
        cell_class = "lab" if getattr(a, "is_lab", getattr(a.subject, "is_lab", False)) else "lecture"

        return (
            f"<td class='{cell_class}'>"
            f"{subj_code}<br>{subj_name}<br>"
            f"{faculty_name}<br>{venue_name}</td>"
        )
