from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func

from app.blueprints.teacher import teacher_bp
from app.extensions import db
from app.models import (
    User, Subject, Laboratory, AttendanceSession, AttendanceRecord,
    TeacherSubject, Workstation
)
from app.utils.decorators import teacher_required
from app.services.session_service import SessionService
from app.services.report_service import ReportService


@teacher_bp.route('/dashboard')
@login_required
@teacher_required
def dashboard():
    # 1. Assigned subjects
    teacher_subjects = Subject.query.join(TeacherSubject).filter(
        TeacherSubject.teacher_id == current_user.id,
        Subject.is_active == True
    ).all()

    # If no explicitly assigned subjects, fallback to all active subjects for flexibility
    if not teacher_subjects:
        teacher_subjects = Subject.query.filter_by(is_active=True).all()

    # 2. Available laboratories
    labs = Laboratory.query.filter_by(is_active=True).all()

    # 3. Active session for this teacher
    active_session = SessionService.get_active_session_for_teacher(current_user.id)
    session_data = None
    marked_seats = {}

    if active_session:
        summary = SessionService.get_session_roster_summary(active_session.id)
        session_data = summary
        for r in summary['present_records']:
            marked_seats[r.seat_number] = {
                'student_name': r.student.full_name if r.student else 'Unknown',
                'username': r.student.username if r.student else 'N/A',
                'time': r.timestamp.strftime('%H:%M:%S'),
                'ip': r.ip_address
            }

    # 4. Past sessions by this teacher
    past_sessions = db.session.query(
        AttendanceSession,
        func.count(AttendanceRecord.id).label('attended_count')
    ).outerjoin(AttendanceRecord, AttendanceSession.id == AttendanceRecord.session_id)\
     .filter(AttendanceSession.teacher_id == current_user.id)\
     .group_by(AttendanceSession.id)\
     .order_by(AttendanceSession.start_time.desc())\
     .limit(30).all()

    # 5. At-Risk students for this teacher's subjects
    at_risk_students = ReportService.get_at_risk_students(teacher_id=current_user.id, threshold=75.0)

    # 6. All registered students list
    students_list = User.query.filter_by(role='student', is_active=True).order_by(User.username.asc()).all()

    return render_template(
        'teacher/dashboard.html',
        subjects=teacher_subjects,
        labs=labs,
        active_session=active_session,
        session_data=session_data,
        marked_seats=marked_seats,
        past_sessions=past_sessions,
        at_risk_students=at_risk_students,
        students_list=students_list
    )


@teacher_bp.route('/start_session', methods=['POST'])
@login_required
@teacher_required
def start_session():
    subject_id = request.form.get('subject_id', type=int)
    lab_id = request.form.get('lab_id', type=int)
    capacity = request.form.get('capacity', default=30, type=int)
    duration = request.form.get('duration', default=10, type=int)

    # Validate capacity options (30, 60, 90)
    if capacity not in [30, 60, 90]:
        capacity = 30

    if not subject_id or not lab_id:
        flash("Please select both a subject and a computer laboratory.", "danger")
        return redirect(url_for('teacher.dashboard'))

    try:
        session = SessionService.create_and_start_session(
            teacher_id=current_user.id,
            subject_id=subject_id,
            lab_id=lab_id,
            capacity=capacity,
            duration_minutes=duration
        )
        flash(f"Live session {session.session_code} launched in {session.laboratory.name}! Capacity: {capacity} PCs.", "success")
    except Exception as e:
        flash(f"Failed to start session: {str(e)}", "danger")

    return redirect(url_for('teacher.dashboard'))


@teacher_bp.route('/pause_session/<int:session_id>', methods=['POST'])
@login_required
@teacher_required
def pause_session(session_id):
    success, msg = SessionService.pause_or_resume_session(session_id, current_user.id)
    flash(msg, "info" if success else "danger")
    return redirect(url_for('teacher.dashboard'))


@teacher_bp.route('/extend_session/<int:session_id>', methods=['POST'])
@login_required
@teacher_required
def extend_session(session_id):
    minutes = request.form.get('minutes', default=10, type=int)
    success, msg = SessionService.extend_session(session_id, current_user.id, additional_minutes=minutes)
    flash(msg, "success" if success else "danger")
    return redirect(url_for('teacher.dashboard'))


@teacher_bp.route('/stop_session/<int:session_id>', methods=['POST'])
@login_required
@teacher_required
def stop_session(session_id):
    success, msg = SessionService.stop_session(session_id, current_user.id)
    flash(msg, "warning" if success else "danger")
    return redirect(url_for('teacher.dashboard'))


@teacher_bp.route('/delete_sessions', methods=['POST'])
@login_required
@teacher_required
def delete_sessions():
    data = request.get_json() or {}
    session_ids = data.get('session_ids', [])

    if not session_ids:
        return jsonify({'success': False, 'message': 'No sessions selected.'}), 400

    try:
        # Teacher can only delete their own sessions
        AttendanceRecord.query.filter(AttendanceRecord.session_id.in_(session_ids)).delete(synchronize_session=False)
        AttendanceSession.query.filter(
            AttendanceSession.id.in_(session_ids),
            AttendanceSession.teacher_id == current_user.id
        ).delete(synchronize_session=False)
        db.session.commit()
        return jsonify({'success': True, 'message': f'Deleted {len(session_ids)} session(s) successfully.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@teacher_bp.route('/add_subject', methods=['POST'])
@login_required
@teacher_required
def add_subject():
    name = request.form.get('subject_name', '').strip()
    code = request.form.get('subject_code', '').strip().upper()

    if not name or not code:
        flash("Subject name and code are required.", "danger")
        return redirect(url_for('teacher.dashboard'))

    # Check if subject exists
    sub = Subject.query.filter_by(code=code).first()
    if not sub:
        sub = Subject(name=name, code=code, is_active=True)
        db.session.add(sub)
        db.session.commit()

    # Link teacher to subject
    assigned = TeacherSubject.query.filter_by(teacher_id=current_user.id, subject_id=sub.id).first()
    if not assigned:
        link = TeacherSubject(teacher_id=current_user.id, subject_id=sub.id)
        db.session.add(link)
        db.session.commit()
        flash(f"Subject '{name}' ({code}) successfully assigned to your profile.", "success")
    else:
        flash(f"Subject '{name}' ({code}) is already in your profile.", "info")

    return redirect(url_for('teacher.dashboard'))

