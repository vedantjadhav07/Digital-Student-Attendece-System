from flask import render_template, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
import io
from datetime import datetime

from app.blueprints.student import student_bp
from app.utils.decorators import student_required
from app.utils.network import get_real_client_ip
from app.services.session_service import SessionService
from app.services.report_service import ReportService
from app.services.workstation_service import WorkstationService
from app.models import AttendanceRecord, AttendanceSession, Subject, Laboratory


@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    client_ip = get_real_client_ip()

    # Detect active session
    active_session = SessionService.get_current_active_session_for_student(
        student_id=current_user.id,
        client_ip=client_ip
    )

    already_marked = False
    assigned_seat = None
    if active_session:
        rec = AttendanceRecord.query.filter_by(
            session_id=active_session.id,
            student_id=current_user.id
        ).first()
        if rec:
            already_marked = True
            assigned_seat = rec.seat_number
        else:
            # Check workstation matching client IP
            ws = WorkstationService.find_workstation_for_request(
                lab_id=active_session.lab_id,
                client_ip=client_ip
            )
            if ws:
                assigned_seat = ws.seat_number

    stats = ReportService.get_student_overall_stats(current_user.id)

    return render_template(
        'student/dashboard.html',
        active_session=active_session,
        already_marked=already_marked,
        assigned_seat=assigned_seat,
        client_ip=client_ip,
        stats=stats
    )


@student_bp.route('/export_personal')
@login_required
@student_required
def export_personal():
    records = AttendanceRecord.query.filter_by(student_id=current_user.id)\
        .order_by(AttendanceRecord.timestamp.desc()).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "My Attendance History"

    # Header style
    NAVY_FILL = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    FONT_TITLE = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    FONT_HEADER = Font(name="Calibri", size=11, bold=True, color="FFFFFF")

    ws.merge_cells("A1:E1")
    ws["A1"].value = f"ATTENDANCE HISTORY: {current_user.full_name} ({current_user.username})"
    ws["A1"].font = FONT_TITLE
    ws["A1"].fill = NAVY_FILL
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 35

    headers = ["#", "Subject", "Laboratory", "Seat Number", "Timestamp"]
    ws.row_dimensions[3].height = 24
    for idx, h in enumerate(headers, start=1):
        c = ws.cell(row=3, column=idx, value=h)
        c.font = FONT_HEADER
        c.fill = PatternFill(start_color="6366F1", end_color="6366F1", fill_type="solid")
        c.alignment = Alignment(horizontal="center", vertical="center")

    row_num = 4
    for idx, r in enumerate(records, start=1):
        ws.cell(row=row_num, column=1, value=idx).alignment = Alignment(horizontal="center")
        ws.cell(row=row_num, column=2, value=r.session.subject.name if r.session and r.session.subject else "N/A")
        ws.cell(row=row_num, column=3, value=r.session.laboratory.name if r.session and r.session.laboratory else "N/A")
        ws.cell(row=row_num, column=4, value=f"Seat #{r.seat_number}").alignment = Alignment(horizontal="center")
        ws.cell(row=row_num, column=5, value=r.timestamp.strftime("%Y-%m-%d %H:%M:%S")).alignment = Alignment(horizontal="center")
        row_num += 1

    for col_idx, col in enumerate(ws.columns, start=1):
        max_len = max(len(str(c.value or '')) for c in col)
        col_letter = get_column_letter(col_idx)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"Attendance_{current_user.username}_{datetime.utcnow().strftime('%Y%m%d')}.xlsx"
    return send_file(output, download_name=filename, as_attachment=True)

