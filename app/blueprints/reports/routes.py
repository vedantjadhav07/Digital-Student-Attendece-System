from datetime import datetime, timedelta
from flask import render_template, request, send_file, flash, redirect, url_for
from flask_login import login_required, current_user

from app.blueprints.reports import reports_bp
from app.utils.decorators import role_required
from app.models import AttendanceSession, AttendanceRecord, User, Subject
from app.services.report_service import ReportService
from app.extensions import db


@reports_bp.route('/session/<int:session_id>/excel')
@login_required
@role_required('admin', 'teacher')
def export_session_excel(session_id):
    session = AttendanceSession.query.get_or_404(session_id)
    if current_user.role == 'teacher' and session.teacher_id != current_user.id:
        flash("You are not authorized to export attendance records for another faculty member's session.", "danger")
        return redirect(url_for('teacher.dashboard'))

    try:
        output = ReportService.generate_excel_session_report(session_id, current_user)
        filename = f"Attendance_{session.subject.code}_Session_{session.id}_{session.start_time.strftime('%Y%m%d')}.xlsx"
        return send_file(output, download_name=filename, as_attachment=True)
    except Exception as e:
        flash(f"Error generating Excel report: {str(e)}", "danger")
        return redirect(url_for('teacher.dashboard'))


@reports_bp.route('/session/<int:session_id>/print')
@login_required
@role_required('admin', 'teacher')
def print_session_report(session_id):
    session = AttendanceSession.query.get_or_404(session_id)
    if current_user.role == 'teacher' and session.teacher_id != current_user.id:
        flash("Unauthorized to view this report.", "danger")
        return redirect(url_for('teacher.dashboard'))

    # Query all students with outer join
    students = User.query.filter_by(role='student', is_active=True).order_by(User.username.asc()).all()
    records_map = {r.student_id: r for r in AttendanceRecord.query.filter_by(session_id=session_id).all()}

    roster = []
    for s in students:
        rec = records_map.get(s.id)
        roster.append({
            'full_name': s.full_name,
            'username': s.username,
            'is_present': rec is not None,
            'seat_number': rec.seat_number if rec else None,
            'time': rec.timestamp.strftime('%H:%M:%S') if rec else None
        })

    return render_template(
        'reports/print_single.html',
        session=session,
        roster=roster,
        faculty_name=session.teacher.full_name if session.teacher else "N/A"
    )


@reports_bp.route('/cumulative_excel', methods=['POST'])
@login_required
@role_required('admin', 'teacher')
def export_cumulative_excel():
    subject_id = request.form.get('subject_id', type=int)
    start_str = request.form.get('start_date')
    end_str = request.form.get('end_date')

    if not start_str or not end_str:
        flash("Please select both a start date and an end date.", "warning")
        return redirect(url_for('teacher.dashboard'))

    try:
        start_date = datetime.strptime(start_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_str, '%Y-%m-%d') + timedelta(days=1, seconds=-1)
    except ValueError:
        flash("Invalid date format provided.", "danger")
        return redirect(url_for('teacher.dashboard'))

    teacher_id = current_user.id if current_user.role == 'teacher' else request.form.get('teacher_id', type=int)

    output = ReportService.generate_cumulative_excel_report(
        teacher_id=teacher_id,
        subject_id=subject_id,
        start_date=start_date,
        end_date=end_date
    )

    filename = f"Cumulative_Attendance_{start_str}_to_{end_str}.xlsx"
    return send_file(output, download_name=filename, as_attachment=True)

