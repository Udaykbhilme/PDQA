"""
PDF Exporter (Modernized, SQLite-compatible, Multi-year + Multi-section)
Matches ReviewTab rendering.
"""

from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch


class PDFExporter:
    def __init__(self):
        self.page_width, self.page_height = landscape(A4)
        self.margin = 0.6 * inch
        self.lecture_color = colors.HexColor("#dbeafe")  # blue-ish
        self.lab_color = colors.HexColor("#dcfce7")      # green-ish
        self.lunch_color = colors.HexColor("#f1f5f9")    # gray-ish

    # ----------------------------------------------------------------------
    # PUBLIC
    # ----------------------------------------------------------------------
    def export_timetable(self, assignments, info, output_path):
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
            story += self._header(info)
            story.append(Spacer(1, 0.2 * inch))
            story.append(self._timetable(assignments, info))
            story.append(Spacer(1, 0.3 * inch))
            story += self._footer()
            doc.build(story)
            return True
        except Exception as e:
            print("PDF EXPORT ERROR:", e)
            return False

    def preview_timetable(self, assignments, info):
        """HTML preview with multi-section, multi-year support."""
        time_slots = self._slots(info)
        days = info.get("days", [])

        # Header
        year = info.get("year", "Multiple")
        sem = info.get("semester", "Multiple")
        deg = info.get("degree", "B.Tech")

        html = f"""
        <html>
        <head>
            <style>
                body {{
                    background:#0f172a; color:#e2e8f0; font-family:Arial; padding:20px;
                }}
                table {{
                    width:100%; border-collapse:collapse; margin-top:15px;
                }}
                th {{
                    background:#1e293b; padding:8px; border:1px solid #475569;
                }}
                td {{
                    border:1px solid #475569; padding:6px; text-align:center;
                    vertical-align:middle; font-size:12px;
                }}
                td.time {{
                    background:#334155; color:#f1f5f9; font-weight:bold;
                }}
                td.lunch {{
                    background:#475569; color:#cbd5e1; font-style:italic;
                }}
                td.lab {{ background:#14532d; color:#f1f5f9; }}
                td.lecture {{ background:#1e40af; color:#f1f5f9; }}
                h2 {{ text-align:center; color:#38bdf8; }}
            </style>
        </head>
        <body>
            <h2>CSE Timetable Preview</h2>
            <p style="text-align:center;">
                {deg} — Years: {year} | Semesters: {sem}<br>
                Generated on {datetime.now().strftime("%B %d, %Y %I:%M %p")}
            </p>
            <table>
                <tr><th>Time</th>{"".join(f"<th>{d}</th>" for d in days)}</tr>
        """

        for slot in time_slots:
            s, e, is_lunch = slot["start"], slot["end"], slot["is_lunch"]
            html += f"<tr><td class='time'>{s}<br>{e}</td>"

            for d in days:
                if is_lunch:
                    html += "<td class='lunch'>Lunch Break</td>"
                else:
                    html += self._html_cell(assignments, d, s)

            html += "</tr>"

        html += "</table></body></html>"
        return html

    # ----------------------------------------------------------------------
    # HEADER + FOOTER
    # ----------------------------------------------------------------------
    def _header(self, info):
        styles = getSampleStyleSheet()
        title = ParagraphStyle("T", parent=styles["Heading1"],
                               fontSize=17, alignment=TA_CENTER,
                               textColor=colors.HexColor("#1e3a8a"))
        sub = ParagraphStyle("S", parent=styles["Normal"],
                             alignment=TA_CENTER)

        deg = info.get("degree", "B.Tech")
        year = info.get("year", "Multiple")
        sem = info.get("semester", "Multiple")

        return [
            Paragraph("Computer Science & Engineering Department", title),
            Paragraph(f"{deg} — Years: {year} | Semesters: {sem}", sub),
            Paragraph(datetime.now().strftime("Generated on %B %d, %Y %I:%M %p"), sub)
        ]

    def _footer(self):
        style = ParagraphStyle("F",
                               fontSize=8,
                               alignment=TA_CENTER,
                               textColor=colors.gray)
        return [Paragraph("Generated by Timetable Generator", style)]

    # ----------------------------------------------------------------------
    # BUILD TABLE
    # ----------------------------------------------------------------------
    def _timetable(self, assignments, info):
        slots = self._slots(info)
        days = info.get("days", [])

        data = [["Time"] + days]

        for slot in slots:
            row = [f"{slot['start']} - {slot['end']}"]

            for day in days:
                if slot["is_lunch"]:
                    row.append("Lunch Break")
                else:
                    row.append(self._pdf_cell(assignments, day, slot["start"]))

            data.append(row)

        tbl = Table(data)
        tbl.setStyle(self._style(data))
        return tbl

    def _style(self, data):
        st = TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])

        for r in range(1, len(data)):
            if all(c == "Lunch Break" or i == 0 for i, c in enumerate(data[r])):
                st.add("BACKGROUND", (0, r), (-1, r), self.lunch_color)
                st.add("TEXTCOLOR", (0, r), (-1, r), colors.gray)

        return st

    # ----------------------------------------------------------------------
    # TIME SLOTS
    # ----------------------------------------------------------------------
    def _slots(self, info):
        def to_min(t): h, m = map(int, t.split(":")); return h * 60 + m
        def fmt(m): return f"{m//60:02d}:{m%60:02d}"

        s = to_min(info.get("start_time"))
        e = to_min(info.get("end_time"))
        Ls = to_min(info.get("lunch_start"))
        Le = to_min(info.get("lunch_end"))

        slots = []
        for t in range(s, e, 60):
            slots.append({
                "start": fmt(t),
                "end": fmt(t + 60),
                "is_lunch": Ls <= t < Le
            })
        return slots

    # ----------------------------------------------------------------------
    # CELL RENDERING (PDF & HTML)
    # ----------------------------------------------------------------------
    def _collect_classes(self, assignments, day, start):
        """All sections for a given day+start."""
        return [
            a for a in assignments
            if a.day == day and a.start_time == start
        ]

    def _pdf_cell(self, assignments, day, start):
        cls = self._collect_classes(assignments, day, start)
        if not cls:
            return ""

        lines = []
        for a in cls:
            sec = getattr(a.section, "name", f"S{a.section_id}")
            subj = a.subject_code
            fac = a.faculty_name
            ven = a.venue_name
            lines.append(f"[{sec}] {subj}\n{fac}\n{ven}")

        return "\n\n".join(lines)

    def _html_cell(self, assignments, day, start):
        cls = self._collect_classes(assignments, day, start)
        if not cls:
            return "<td></td>"

        is_lab = any(getattr(a, "is_lab", False) for a in cls)
        color_class = "lab" if is_lab else "lecture"

        parts = []
        for a in cls:
            sec = getattr(a.section, "name", f"S{a.section_id}")
            subj = a.subject_code
            fac = a.faculty_name
            ven = a.venue_name
            parts.append(f"<b>{sec}</b><br>{subj}<br>{fac}<br>{ven}")

        return f"<td class='{color_class}'>{'<br><br>'.join(parts)}</td>"
