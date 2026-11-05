import io
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from sqlalchemy import func
from app.extensions import db
from app.models import User, Subject, Laboratory, AttendanceSession, AttendanceRecord, Department


class ReportService:
    @staticmethod
    def get_at_risk_students(teacher_id: int = None, threshold: float = 75.0):
        """
        Identify students whose attendance is below threshold percentage.
        If teacher_id is provided, calculate based only on that teacher's sessions.
        """
        # 1. Total sessions query
        total_sess_q = db.session.query(AttendanceSession.subject_id, func.count(AttendanceSession.id).label('total_sessions'))
        if teacher_id:
            total_sess_q = total_sess_q.filter(AttendanceSession.teacher_id == teacher_id)
        subject_totals = dict(total_sess_q.group_by(AttendanceSession.subject_id).all())

        if not subject_totals:
            return []

        # 2. Student attendance by subject
        q = db.session.query(
            User.id.label('student_id'),
            User.full_name,
            User.username,
            Subject.name.label('subject_name'),
            Subject.code.label('subject_code'),
            AttendanceSession.subject_id,
            func.count(AttendanceRecord.id).label('attended_count')
        ).join(AttendanceRecord, AttendanceRecord.student_id == User.id)\
         .join(AttendanceSession, AttendanceRecord.session_id == AttendanceSession.id)\
         .join(Subject, AttendanceSession.subject_id == Subject.id)\
         .filter(User.role == 'student', User.is_active == True)

        if teacher_id:
            q = q.filter(AttendanceSession.teacher_id == teacher_id)

        records = q.group_by(User.id, AttendanceSession.subject_id).all()

        at_risk_list = []
        for r in records:
            total = subject_totals.get(r.subject_id, 0)
            if total > 0:
                pct = round((r.attended_count / total * 100), 1)
                if pct < threshold:
                    at_risk_list.append({
                        'student_id': r.student_id,
                        'name': r.full_name,
                        'username': r.username,
                        'subject': f"{r.subject_name} ({r.subject_code})",
                        'attended': r.attended_count,
                        'total': total,
                        'percentage': pct,
                        'status': 'At-Risk'
                    })

        return at_risk_list

    @staticmethod
    def get_student_overall_stats(student_id: int):
        """Calculate detailed statistics for a specific student dashboard."""
        student = User.query.get(student_id)
        if not student:
            return None

        # Total sessions conducted
        total_conducted = AttendanceSession.query.filter_by(is_active=False).count()
        # Total attended by this student
        attended_count = AttendanceRecord.query.filter_by(student_id=student_id).count()

        overall_pct = round((attended_count / total_conducted * 100), 1) if total_conducted > 0 else 0.0

        # Subject-wise breakdown
        all_subjects = Subject.query.filter_by(is_active=True).all()
        subject_stats = []

        for sub in all_subjects:
            total_sub_sessions = AttendanceSession.query.filter_by(subject_id=sub.id).count()
            sub_attended = AttendanceRecord.query.join(AttendanceSession).filter(
                AttendanceRecord.student_id == student_id,
                AttendanceSession.subject_id == sub.id
            ).count()

            pct = round((sub_attended / total_sub_sessions * 100), 1) if total_sub_sessions > 0 else 0.0
            subject_stats.append({
                'subject_id': sub.id,
                'name': sub.name,
                'code': sub.code,
                'attended': sub_attended,
                'total': total_sub_sessions,
                'percentage': pct,
                'is_at_risk': pct < 75.0 if total_sub_sessions > 0 else False
            })

        # Recent logs
        recent_logs = db.session.query(
            AttendanceRecord.timestamp,
            AttendanceRecord.seat_number,
            Subject.name.label('subject_name'),
            Laboratory.name.label('lab_name'),
            User.full_name.label('teacher_name')
        ).join(AttendanceSession, AttendanceRecord.session_id == AttendanceSession.id)\
         .join(Subject, AttendanceSession.subject_id == Subject.id)\
         .join(Laboratory, AttendanceSession.lab_id == Laboratory.id)\
         .join(User, AttendanceSession.teacher_id == User.id)\
         .filter(AttendanceRecord.student_id == student_id)\
         .order_by(AttendanceRecord.timestamp.desc())\
         .limit(20).all()

        return {
            'student': student,
            'overall_percentage': overall_pct,
            'total_conducted': total_conducted,
            'total_attended': attended_count,
            'absent_count': max(0, total_conducted - attended_count),
            'subject_stats': subject_stats,
            'recent_logs': recent_logs
        }

    @staticmethod
    def generate_excel_session_report(session_id: int, user: User) -> io.BytesIO:
        """Generate a professional styled Excel report for a single session using OpenPyXL."""
        session = AttendanceSession.query.get_or_404(session_id)
        if user.role == 'teacher' and session.teacher_id != user.id:
            raise PermissionError("Unauthorized to export this session.")

        # Query all students with outer join
        students = User.query.filter_by(role='student', is_active=True).order_by(User.username.asc()).all()
        records_map = {r.student_id: r for r in AttendanceRecord.query.filter_by(session_id=session_id).all()}

        wb = Workbook()
        ws = wb.active
        ws.title = "Lab Attendance"

        # Theme Colors
        NAVY_FILL = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        PURPLE_FILL = PatternFill(start_color="6366F1", end_color="6366F1", fill_type="solid")
        LIGHT_GRAY = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
        PRESENT_FILL = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
        ABSENT_FILL = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")

        FONT_TITLE = Font(name="Calibri", size=16, bold=True, color="FFFFFF")
        FONT_HEADER = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        FONT_BOLD = Font(name="Calibri", size=10, bold=True)
        FONT_REGULAR = Font(name="Calibri", size=10)

        THIN_BORDER = Border(
            left=Side(style='thin', color='E2E8F0'),
            right=Side(style='thin', color='E2E8F0'),
            top=Side(style='thin', color='E2E8F0'),
            bottom=Side(style='thin', color='E2E8F0')
        )

        # Title Block
        ws.merge_cells("A1:G1")
        title_cell = ws["A1"]
        title_cell.value = f"LAB-SECURE DIGITAL ATTENDANCE REPORT"
        title_cell.font = FONT_TITLE
        title_cell.fill = NAVY_FILL
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 40

        # Session Metadata
        metadata = [
            ("Subject:", f"{session.subject.name} ({session.subject.code})", "Date:", session.start_time.strftime("%d-%b-%Y")),
            ("Laboratory:", session.laboratory.name, "Faculty:", session.teacher.full_name),
            ("Capacity:", f"{session.lab_capacity} Workstations", "Session Code:", session.session_code)
        ]

        for row_idx, data in enumerate(metadata, start=2):
            ws[f"A{row_idx}"] = data[0]
            ws[f"A{row_idx}"].font = FONT_BOLD
            ws[f"B{row_idx}"] = data[1]
            ws[f"B{row_idx}"].font = FONT_REGULAR

            ws[f"D{row_idx}"] = data[2]
            ws[f"D{row_idx}"].font = FONT_BOLD
            ws[f"E{row_idx}"] = data[3]
            ws[f"E{row_idx}"].font = FONT_REGULAR
            ws.row_dimensions[row_idx].height = 20

        # Table Headers
        headers = ["#", "Enrollment No", "Student Full Name", "Status", "Seat / Workstation", "IP Address", "Time In"]
        header_row = 6
        ws.row_dimensions[header_row].height = 28

        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=header_row, column=col_idx, value=header)
            cell.font = FONT_HEADER
            cell.fill = PURPLE_FILL
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Rows
        row_num = 7
        present_count = 0
        for idx, student in enumerate(students, start=1):
            record = records_map.get(student.id)
            is_present = record is not None
            if is_present:
                present_count += 1

            ws.cell(row=row_num, column=1, value=idx).alignment = Alignment(horizontal="center")
            ws.cell(row=row_num, column=2, value=student.username).alignment = Alignment(horizontal="center")
            ws.cell(row=row_num, column=3, value=student.full_name)

            status_cell = ws.cell(row=row_num, column=4, value="PRESENT" if is_present else "ABSENT")
            status_cell.alignment = Alignment(horizontal="center")
            status_cell.font = Font(bold=True, color="166534" if is_present else "991B1B")
            status_cell.fill = PRESENT_FILL if is_present else ABSENT_FILL

            ws.cell(row=row_num, column=5, value=f"Seat #{record.seat_number}" if is_present else "-").alignment = Alignment(horizontal="center")
            ws.cell(row=row_num, column=6, value=record.ip_address if is_present else "-").alignment = Alignment(horizontal="center")
            ws.cell(row=row_num, column=7, value=record.timestamp.strftime("%H:%M:%S") if is_present else "-").alignment = Alignment(horizontal="center")

            for col_idx in range(1, 8):
                ws.cell(row=row_num, column=col_idx).border = THIN_BORDER

            ws.row_dimensions[row_num].height = 22
            row_num += 1

        # Summary footer
        summary_row = row_num + 1
        ws.cell(row=summary_row, column=2, value="Total Registered:").font = FONT_BOLD
        ws.cell(row=summary_row, column=3, value=len(students)).font = FONT_BOLD
        ws.cell(row=summary_row + 1, column=2, value="Total Present:").font = FONT_BOLD
        ws.cell(row=summary_row + 1, column=3, value=present_count).font = FONT_BOLD
        ws.cell(row=summary_row + 2, column=2, value="Attendance Rate:").font = FONT_BOLD
        rate = round((present_count / len(students) * 100), 2) if students else 0
        ws.cell(row=summary_row + 2, column=3, value=f"{rate}%").font = FONT_BOLD

        # Auto-adjust column widths
        for col_idx, col in enumerate(ws.columns, start=1):
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col_idx)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    @staticmethod
    def generate_cumulative_excel_report(teacher_id: int, subject_id: int, start_date: datetime, end_date: datetime) -> io.BytesIO:
        """Generate cumulative attendance report for date range."""
        q = AttendanceSession.query.filter(
            AttendanceSession.teacher_id == teacher_id,
            AttendanceSession.start_time >= start_date,
            AttendanceSession.start_time <= end_date
        )
        if subject_id:
            q = q.filter(AttendanceSession.subject_id == subject_id)

        sessions = q.all()
        session_ids = [s.id for s in sessions]
        total_sessions = len(sessions)

        students = User.query.filter_by(role='student', is_active=True).order_by(User.username.asc()).all()

        # Count per student
        presence_counts = dict(
            db.session.query(
                AttendanceRecord.student_id,
                func.count(AttendanceRecord.id)
            ).filter(AttendanceRecord.session_id.in_(session_ids))
             .group_by(AttendanceRecord.student_id).all()
        ) if session_ids else {}

        wb = Workbook()
        ws = wb.active
        ws.title = "Cumulative Report"

        # Theme Colors
        NAVY_FILL = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        PURPLE_FILL = PatternFill(start_color="6366F1", end_color="6366F1", fill_type="solid")
        FONT_TITLE = Font(name="Calibri", size=16, bold=True, color="FFFFFF")
        FONT_HEADER = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        FONT_BOLD = Font(name="Calibri", size=10, bold=True)
        THIN_BORDER = Border(
            left=Side(style='thin', color='E2E8F0'),
            right=Side(style='thin', color='E2E8F0'),
            top=Side(style='thin', color='E2E8F0'),
            bottom=Side(style='thin', color='E2E8F0')
        )

        ws.merge_cells("A1:F1")
        ws["A1"].value = "CUMULATIVE ATTENDANCE REPORT"
        ws["A1"].font = FONT_TITLE
        ws["A1"].fill = NAVY_FILL
        ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 40

        ws["A2"] = "Date Range:"
        ws["B2"] = f"{start_date.strftime('%d-%b-%Y')} to {end_date.strftime('%d-%b-%Y')}"
        ws["A3"] = "Total Sessions Conducted:"
        ws["B3"] = total_sessions

        headers = ["#", "Enrollment No", "Student Full Name", "Conducted", "Attended", "Percentage", "Status"]
        header_row = 5
        ws.row_dimensions[header_row].height = 26

        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=header_row, column=col_idx, value=header)
            cell.font = FONT_HEADER
            cell.fill = PURPLE_FILL
            cell.alignment = Alignment(horizontal="center", vertical="center")

        row_num = 6
        for idx, student in enumerate(students, start=1):
            attended = presence_counts.get(student.id, 0)
            pct = round((attended / total_sessions * 100), 2) if total_sessions > 0 else 0.0
            is_at_risk = pct < 75.0 if total_sessions > 0 else False

            ws.cell(row=row_num, column=1, value=idx).alignment = Alignment(horizontal="center")
            ws.cell(row=row_num, column=2, value=student.username).alignment = Alignment(horizontal="center")
            ws.cell(row=row_num, column=3, value=student.full_name)
            ws.cell(row=row_num, column=4, value=total_sessions).alignment = Alignment(horizontal="center")
            ws.cell(row=row_num, column=5, value=attended).alignment = Alignment(horizontal="center")
            ws.cell(row=row_num, column=6, value=f"{pct}%").alignment = Alignment(horizontal="center")

            status_cell = ws.cell(row=row_num, column=7, value="AT-RISK (<75%)" if is_at_risk else "SAFE")
            status_cell.alignment = Alignment(horizontal="center")
            status_cell.font = Font(bold=True, color="991B1B" if is_at_risk else "166534")

            for c in range(1, 8):
                ws.cell(row=row_num, column=c).border = THIN_BORDER

            ws.row_dimensions[row_num].height = 20
            row_num += 1

        for col_idx, col in enumerate(ws.columns, start=1):
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col_idx)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output
