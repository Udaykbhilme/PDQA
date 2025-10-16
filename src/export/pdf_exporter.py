"""
PDF Exporter for Timetable Generator

This module handles the generation of professional PDF timetables using ReportLab.
Creates A4 landscape format with proper layout, styling, and content organization.
"""

from typing import List, Dict, Optional
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas

from ..database.db_models import ClassAssignment, Faculty, Subject, Venue, Section


class PDFExporter:
    """
    PDF Exporter for Timetables
    
    Generates professional PDF timetables with:
    - A4 landscape format
    - Proper header with department info
    - Grid layout with time slots and days
    - Color-coded cells for lectures vs labs
    - Detailed cell content with all required information
    """
    
    def __init__(self):
        self.page_width, self.page_height = landscape(A4)
        self.margin = 1 * inch
        self.content_width = self.page_width - (2 * self.margin)
        self.content_height = self.page_height - (2 * self.margin)
        
        # Colors
        self.lecture_color = colors.lightblue
        self.lab_color = colors.lightgreen
        self.header_color = colors.darkblue
        self.border_color = colors.black
        
    def export_timetable(self, assignments: List[ClassAssignment], 
                        timetable_info: Dict, output_path: str) -> bool:
        """
        Export timetable to PDF
        
        Args:
            assignments: List of class assignments
            timetable_info: Dictionary with timetable metadata
            output_path: Path to save the PDF file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=landscape(A4),
                rightMargin=self.margin,
                leftMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin
            )
            
            # Build content
            story = []
            
            # Add header
            story.extend(self._create_header(timetable_info))
            story.append(Spacer(1, 0.2 * inch))
            
            # Add timetable grid
            timetable_table = self._create_timetable_grid(assignments, timetable_info)
            story.append(timetable_table)
            story.append(Spacer(1, 0.2 * inch))
            
            # Add footer info
            story.extend(self._create_footer(timetable_info))
            
            # Build PDF
            doc.build(story)
            
            return True
            
        except Exception as e:
            print(f"Error exporting PDF: {e}")
            return False
    
    def _create_header(self, timetable_info: Dict) -> List:
        """Create PDF header with department and timetable information"""
        styles = getSampleStyleSheet()
        
        # Title style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=self.header_color,
            alignment=TA_CENTER,
            spaceAfter=12
        )
        
        # Subtitle style
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=6
        )
        
        story = []
        
        # Department title
        story.append(Paragraph("Computer Science & Engineering Department", title_style))
        
        # Timetable info
        degree = timetable_info.get('degree', 'B.Tech')
        year = timetable_info.get('year', '')
        semester = timetable_info.get('semester', '')
        sections = timetable_info.get('sections', [])
        
        subtitle_text = f"{degree} - Year {year}, Semester {semester}"
        if sections:
            subtitle_text += f" | Sections: {', '.join(sections)}"
        
        story.append(Paragraph(subtitle_text, subtitle_style))
        
        # Generation date
        date_text = f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        story.append(Paragraph(date_text, subtitle_style))
        
        return story
    
    def _create_timetable_grid(self, assignments: List[ClassAssignment], 
                              timetable_info: Dict) -> Table:
        """Create the main timetable grid"""
        
        # Generate time slots
        time_slots = self._generate_time_slots(timetable_info)
        days = timetable_info.get('days', ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'])
        
        # Create grid data
        grid_data = []
        
        # Header row
        header_row = ['Time'] + days
        grid_data.append(header_row)
        
        # Time slot rows
        for slot in time_slots:
            row = [f"{slot['start']}<br/>{slot['end']}"]
            
            for day in days:
                cell_content = self._get_cell_content(assignments, day, slot['start'])
                row.append(cell_content)
            
            grid_data.append(row)
        
        # Create table
        table = Table(grid_data, colWidths=self._calculate_column_widths(len(days)))
        
        # Apply table style
        table.setStyle(self._get_table_style(len(days), len(time_slots)))
        
        return table
    
    def _generate_time_slots(self, timetable_info: Dict) -> List[Dict]:
        """Generate time slots for the timetable"""
        start_time = timetable_info.get('start_time', '09:00')
        end_time = timetable_info.get('end_time', '18:00')
        lunch_start = timetable_info.get('lunch_start', '13:00')
        lunch_end = timetable_info.get('lunch_end', '14:00')
        
        slots = []
        start_minutes = self._time_to_minutes(start_time)
        end_minutes = self._time_to_minutes(end_time)
        lunch_start_minutes = self._time_to_minutes(lunch_start)
        lunch_end_minutes = self._time_to_minutes(lunch_end)
        
        for time in range(start_minutes, end_minutes, 60):
            # Skip lunch break
            if time >= lunch_start_minutes and time < lunch_end_minutes:
                continue
            
            slots.append({
                'start': self._minutes_to_time(time),
                'end': self._minutes_to_time(time + 60)
            })
        
        return slots
    
    def _get_cell_content(self, assignments: List[ClassAssignment], 
                         day: str, start_time: str) -> str:
        """Get content for a specific cell in the timetable grid"""
        # Find assignments for this day and time
        cell_assignments = [
            a for a in assignments 
            if a.day == day and a.start_time == start_time
        ]
        
        if not cell_assignments:
            return ""
        
        # For now, handle single assignment per cell
        # In a more complex scenario, you might need to handle multiple assignments
        assignment = cell_assignments[0]
        
        # Get related objects (this would need to be loaded from database)
        subject = getattr(assignment, 'subject', None)
        faculty = getattr(assignment, 'faculty', None)
        venue = getattr(assignment, 'venue', None)
        
        if not all([subject, faculty, venue]):
            return "Data Missing"
        
        # Format cell content
        content_parts = []
        
        # Subsection (top-left)
        if assignment.subsection:
            content_parts.append(f"<b>{assignment.subsection}</b>")
        
        # Subject code (center, large)
        content_parts.append(f"<b><font size='12'>{subject.code}</font></b>")
        
        # Subject name (below center)
        content_parts.append(f"<font size='8'>{subject.name}</font>")
        
        # Faculty and venue (bottom)
        faculty_text = f"{faculty.name} ({faculty.faculty_code})"
        content_parts.append(f"<font size='7'>{faculty_text}</font>")
        content_parts.append(f"<font size='7'>{venue.name}</font>")
        
        # Footer with subject code
        content_parts.append(f"<font size='6' color='gray'>{subject.code}</font>")
        
        return "<br/>".join(content_parts)
    
    def _calculate_column_widths(self, num_days: int) -> List[float]:
        """Calculate column widths for the table"""
        time_column_width = 1.2 * inch
        day_column_width = (self.content_width - time_column_width) / num_days
        
        return [time_column_width] + [day_column_width] * num_days
    
    def _get_table_style(self, num_days: int, num_slots: int) -> TableStyle:
        """Get table style for the timetable grid"""
        style_data = [
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Time column styling
            ('BACKGROUND', (0, 1), (0, -1), colors.lightgrey),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (0, -1), 8),
            
            # Grid lines
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Cell padding
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]
        
        return TableStyle(style_data)
    
    def _create_footer(self, timetable_info: Dict) -> List:
        """Create PDF footer with additional information"""
        styles = getSampleStyleSheet()
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER,
            spaceBefore=12
        )
        
        story = []
        
        # Footer text
        footer_text = "This timetable was generated automatically by the CSE Timetable Generator System"
        story.append(Paragraph(footer_text, footer_style))
        
        footer_text2 = "For any queries or corrections, please contact the department administration"
        story.append(Paragraph(footer_text2, footer_style))
        
        return story
    
    def _time_to_minutes(self, time_string: str) -> int:
        """Convert time string (HH:MM) to minutes"""
        hours, minutes = map(int, time_string.split(':'))
        return hours * 60 + minutes
    
    def _minutes_to_time(self, minutes: int) -> str:
        """Convert minutes to time string (HH:MM)"""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    
    def preview_timetable(self, assignments: List[ClassAssignment], 
                         timetable_info: Dict) -> str:
        """
        Generate HTML preview of the timetable
        
        Args:
            assignments: List of class assignments
            timetable_info: Dictionary with timetable metadata
            
        Returns:
            HTML string for preview
        """
        # Generate time slots
        time_slots = self._generate_time_slots(timetable_info)
        days = timetable_info.get('days', ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'])
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Timetable Preview</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ text-align: center; margin-bottom: 20px; }}
                .title {{ font-size: 18px; font-weight: bold; color: #1e3a8a; }}
                .subtitle {{ font-size: 12px; margin: 5px 0; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #000; padding: 8px; text-align: center; }}
                th {{ background-color: #f3f4f6; font-weight: bold; }}
                .time-column {{ background-color: #e5e7eb; font-weight: bold; }}
                .lecture {{ background-color: #dbeafe; }}
                .lab {{ background-color: #dcfce7; }}
                .cell-content {{ font-size: 10px; line-height: 1.2; }}
                .subject-code {{ font-weight: bold; font-size: 12px; }}
                .subject-name {{ font-size: 8px; }}
                .faculty-info {{ font-size: 7px; }}
                .venue-info {{ font-size: 7px; }}
                .subsection {{ font-weight: bold; font-size: 8px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="title">Computer Science & Engineering Department</div>
                <div class="subtitle">{timetable_info.get('degree', 'B.Tech')} - Year {timetable_info.get('year', '')}, Semester {timetable_info.get('semester', '')}</div>
                <div class="subtitle">Sections: {', '.join(timetable_info.get('sections', []))}</div>
                <div class="subtitle">Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Time</th>
        """
        
        for day in days:
            html += f"<th>{day}</th>"
        
        html += """
                    </tr>
                </thead>
                <tbody>
        """
        
        for slot in time_slots:
            html += f"""
                    <tr>
                        <td class="time-column">{slot['start']}<br/>{slot['end']}</td>
            """
            
            for day in days:
                cell_content = self._get_html_cell_content(assignments, day, slot['start'])
                html += f"<td class='cell-content'>{cell_content}</td>"
            
            html += "</tr>"
        
        html += """
                </tbody>
            </table>
            
            <div style="text-align: center; margin-top: 20px; font-size: 8px; color: #666;">
                This timetable was generated automatically by the CSE Timetable Generator System
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _get_html_cell_content(self, assignments: List[ClassAssignment], 
                              day: str, start_time: str) -> str:
        """Get HTML content for a specific cell in the timetable grid"""
        # Find assignments for this day and time
        cell_assignments = [
            a for a in assignments 
            if a.day == day and a.start_time == start_time
        ]
        
        if not cell_assignments:
            return ""
        
        assignment = cell_assignments[0]
        
        # Get related objects
        subject = getattr(assignment, 'subject', None)
        faculty = getattr(assignment, 'faculty', None)
        venue = getattr(assignment, 'venue', None)
        
        if not all([subject, faculty, venue]):
            return "Data Missing"
        
        # Determine cell class based on subject type
        cell_class = "lab" if subject.is_lab else "lecture"
        
        # Format cell content
        content_parts = []
        
        if assignment.subsection:
            content_parts.append(f"<div class='subsection'>{assignment.subsection}</div>")
        
        content_parts.append(f"<div class='subject-code'>{subject.code}</div>")
        content_parts.append(f"<div class='subject-name'>{subject.name}</div>")
        content_parts.append(f"<div class='faculty-info'>{faculty.name} ({faculty.faculty_code})</div>")
        content_parts.append(f"<div class='venue-info'>{venue.name}</div>")
        
        return f"<div class='{cell_class}'>" + "<br/>".join(content_parts) + "</div>"
