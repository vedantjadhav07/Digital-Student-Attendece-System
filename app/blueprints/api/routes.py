import io
import pandas as pd
from datetime import datetime, timedelta
from flask import jsonify, request, send_file
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import text, func

from app.blueprints.api import api_bp
from app.extensions import db, limiter
from app.models import (
    User, Department, Subject, Laboratory, Workstation,
    TeacherSubject, StudentEnrollment, AttendanceSession, AttendanceRecord, AuditLog
)
from app.services.auth_service import AuthService
from app.services.session_service import SessionService
from app.services.attendance_service import AttendanceService
from app.services.report_service import ReportService
from app.services.workstation_service import WorkstationService
from app.services.audit_service import AuditService
from app.utils.network import get_real_client_ip
from app.utils.jwt_util import create_access_token, create_refresh_token, get_user_from_jwt


# ---------------- SYSTEM HEALTH & CONTACT ----------------

@api_bp.route('/health')
def health():
    db_ok = False
    try:
        db.session.execute(text("SELECT 1")).scalar()
        db_ok = True
    except Exception:
        db_ok = False

    return jsonify({
        'status': 'healthy' if db_ok else 'degraded',
        'database': 'connected' if db_ok else 'error',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '2.1.0-labora'
    }), 200 if db_ok else 500


@api_bp.route('/api/contact', methods=['POST'])
@limiter.limit("5 per minute")
def contact():
    data = request.get_json() or {}

    # Anti-bot honeypot check (invisible field filled only by spam bots)
    if data.get('website') or data.get('hp_field'):
        return jsonify({'success': True, 'message': 'Thank you! Your message has been received.'}), 200

    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    subject = (data.get('subject') or '').strip()
    message = (data.get('message') or '').strip()

    if not name or not email or not message:
        return jsonify({'success': False, 'message': 'Please provide your name, email, and message.'}), 400

    if len(name) > 100 or len(email) > 120 or len(message) > 3000:
        return jsonify({'success': False, 'message': 'Input length exceeded safety limits.'}), 400

    AuditService.log(
        action="CONTACT_INQUIRY",
        details=f"From: {name} <{email}> | Subj: {subject} | Msg: {message[:100]}",
        ip_address=get_real_client_ip()
    )

    return jsonify({
        'success': True,
        'message': 'Thank you! Your message has been received by the Labora administration team.'
    })


# ---------------- AUTH REST APIS ----------------

@api_bp.route('/api/auth/login', methods=['POST'])
@limiter.limit("15 per minute")
def api_login():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    remember = bool(data.get('remember', False))
    client_ip = get_real_client_ip()

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required.'}), 400

    user, err = AuthService.authenticate_user(username, password, client_ip=client_ip)
    if not user:
        return jsonify({'success': False, 'message': err or 'Invalid username or password.'}), 401

    login_user(user, remember=remember)

    # JWT Authentication: Access token (2 days), Refresh token (7 days)
    access_token = create_access_token(user, expires_days=2)
    refresh_token = create_refresh_token(user, expires_days=7)

    return jsonify({
        'success': True,
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': 2 * 24 * 3600
    })


@api_bp.route('/api/auth/refresh', methods=['POST'])
@limiter.limit("15 per minute")
def api_refresh():
    data = request.get_json() or {}
    refresh_token = data.get('refresh_token')
    if not refresh_token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            refresh_token = auth_header.split(' ', 1)[1].strip()

    if not refresh_token:
        return jsonify({'success': False, 'message': 'Refresh token is required.'}), 400

    user = get_user_from_jwt(refresh_token, expected_type='refresh')
    if not user:
        return jsonify({'success': False, 'message': 'Invalid or expired refresh token.'}), 401

    # Issue new 2-day access token and 7-day refresh token
    new_access_token = create_access_token(user, expires_days=2)
    new_refresh_token = create_refresh_token(user, expires_days=7)

    login_user(user, remember=True)

    return jsonify({
        'success': True,
        'access_token': new_access_token,
        'refresh_token': new_refresh_token,
        'token_type': 'Bearer',
        'expires_in': 2 * 24 * 3600,
        'user': user.to_dict()
    })


@api_bp.route('/api/auth/logout', methods=['POST', 'GET'])
def api_logout():
    if current_user.is_authenticated:
        logout_user()
    return jsonify({'success': True, 'message': 'Logged out successfully.'})


@api_bp.route('/api/auth/me')
def api_me():
    # If already authenticated by session or Bearer header
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': current_user.to_dict()
        })

    # Fallback to check Authorization Bearer header directly
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1].strip()
        user = get_user_from_jwt(token, expected_type='access')
        if user:
            login_user(user, remember=True)
            return jsonify({
                'authenticated': True,
                'user': user.to_dict()
            })

    return jsonify({
        'authenticated': False,
        'user': None
    })


@api_bp.route('/api/auth/change_password', methods=['POST'])
@login_required
def api_change_password():
    data = request.get_json() or {}
    new_pw = data.get('new_password')
    conf_pw = data.get('confirm_password')

    if not new_pw or len(new_pw) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters long.'}), 400

    if new_pw != conf_pw:
        return jsonify({'success': False, 'message': 'Passwords do not match.'}), 400

    success, msg = AuthService.change_password(current_user, new_pw, client_ip=get_real_client_ip())
    return jsonify({'success': success, 'message': msg}), 200 if success else 400


# ---------------- ADMIN REST APIS ----------------

def require_admin():
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({'error': 'Admin authorization required.'}), 403
    return None


@api_bp.route('/api/admin/overview')
@login_required
def admin_overview():
    err = require_admin()
    if err: return err

    total_students = User.query.filter_by(role='student').count()
    total_faculty = User.query.filter_by(role='teacher').count()
    total_labs = Laboratory.query.count()

    return jsonify({
        'total_students': total_students,
        'total_faculty': total_faculty,
        'total_labs': total_labs
    })


@api_bp.route('/api/admin/users', methods=['GET', 'POST'])
@login_required
def admin_users():
    err = require_admin()
    if err: return err

    if request.method == 'GET':
        role = request.args.get('role', 'all')
        search = (request.args.get('search') or '').strip().lower()

        q = User.query
        if role in ['admin', 'teacher', 'student']:
            q = q.filter_by(role=role)
        if search:
            q = q.filter((func.lower(User.username).contains(search)) | (func.lower(User.full_name).contains(search)))

        users = q.order_by(User.id.desc()).all()
        return jsonify([u.to_dict() for u in users])

    # POST - Create User
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    full_name = (data.get('full_name') or '').strip()
    email = (data.get('email') or '').strip() or None
    role = data.get('role', 'student')
    department_id = data.get('department_id') or None
    semester = data.get('semester') or None
    password = data.get('password') or ''

    if not username or not full_name or not password:
        return jsonify({'success': False, 'message': 'Username, Full Name, and Password are required.'}), 400

    if User.query.filter(func.lower(User.username) == username.lower()).first():
        return jsonify({'success': False, 'message': f"Account '{username}' already exists."}), 400

    new_user = User(
        username=username,
        full_name=full_name,
        email=email,
        role=role,
        department_id=department_id,
        semester=semester,
        password=password
    )
    db.session.add(new_user)
    db.session.commit()

    AuditService.log(
        action="USER_CREATED",
        user_id=current_user.id,
        target_type="User",
        target_id=new_user.id,
        details=f"Created {role} account: {username}"
    )

    return jsonify({'success': True, 'message': f'{role.capitalize()} account created successfully.', 'user': new_user.to_dict()})


@api_bp.route('/api/admin/users/<int:user_id>', methods=['PUT', 'DELETE'])
@login_required
def admin_user_detail(user_id):
    err = require_admin()
    if err: return err

    user = User.query.get_or_404(user_id)

    if request.method == 'PUT':
        data = request.get_json() or {}
        user.full_name = (data.get('full_name') or user.full_name).strip()
        user.email = (data.get('email') or '').strip() or None
        user.department_id = data.get('department_id') or None
        user.semester = data.get('semester') or None

        if 'is_active' in data:
            user.is_active = bool(data['is_active'])

        if data.get('password'):
            user.password = data['password']

        db.session.commit()
        return jsonify({'success': True, 'message': 'User details updated.', 'user': user.to_dict()})

    if request.method == 'DELETE':
        if user.id == current_user.id:
            return jsonify({'success': False, 'message': 'Cannot delete your own admin account.'}), 400

        # Toggle or delete safely
        AttendanceRecord.query.filter_by(student_id=user.id).delete()
        AttendanceSession.query.filter_by(teacher_id=user.id).delete()
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True, 'message': f"Account '{user.username}' deleted."})


@api_bp.route('/api/admin/users/bulk_import', methods=['POST'])
@login_required
def admin_bulk_import():
    err = require_admin()
    if err: return err

    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify({'success': False, 'message': 'Please provide a CSV or Excel file.'}), 400

    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            return jsonify({'success': False, 'message': 'Supported formats are .csv, .xlsx, .xls'}), 400

        df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]

        created_count = 0
        skipped_count = 0
        errors = []

        for row_idx, row in df.iterrows():
            username = str(row.get('username') or row.get('enrollment_no') or row.get('roll_no') or '').strip()
            full_name = str(row.get('full_name') or row.get('name') or username).strip()
            password = str(row.get('password') or 'student123').strip()
            email = str(row.get('email') or '').strip() or None
            semester = int(row.get('semester')) if pd.notna(row.get('semester')) else None

            if not username or username == 'nan':
                continue

            if User.query.filter(func.lower(User.username) == username.lower()).first():
                skipped_count += 1
                continue

            new_student = User(
                username=username,
                full_name=full_name,
                email=email,
                role='student',
                semester=semester,
                password=password
            )
            db.session.add(new_student)
            created_count += 1

        db.session.commit()
        return jsonify({
            'success': True,
            'message': f"Bulk import finished. Created {created_count} students. Skipped {skipped_count} existing accounts.",
            'created_count': created_count,
            'skipped_count': skipped_count,
            'errors': errors
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f"Import processing error: {str(e)}"}), 500


@api_bp.route('/api/admin/departments', methods=['GET', 'POST'])
@login_required
def admin_departments():
    err = require_admin()
    if err: return err

    if request.method == 'GET':
        depts = Department.query.order_by(Department.name.asc()).all()
        return jsonify([d.to_dict() for d in depts])

    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    code = (data.get('code') or '').strip().upper()

    if not name or not code:
        return jsonify({'success': False, 'message': 'Department name and code are required.'}), 400

    if Department.query.filter((func.lower(Department.name) == name.lower()) | (func.lower(Department.code) == code.lower())).first():
        return jsonify({'success': False, 'message': 'Department with this name or code already exists.'}), 400

    dept = Department(name=name, code=code)
    db.session.add(dept)
    db.session.commit()
    return jsonify({'success': True, 'department': dept.to_dict()})


@api_bp.route('/api/admin/departments/<int:dept_id>', methods=['PUT', 'DELETE'])
@login_required
def admin_department_detail(dept_id):
    err = require_admin()
    if err: return err

    dept = Department.query.get_or_404(dept_id)

    if request.method == 'PUT':
        data = request.get_json() or {}
        dept.name = (data.get('name') or dept.name).strip()
        dept.code = (data.get('code') or dept.code).strip().upper()
        db.session.commit()
        return jsonify({'success': True, 'department': dept.to_dict()})

    if request.method == 'DELETE':
        db.session.delete(dept)
        db.session.commit()
        return jsonify({'success': True, 'message': f"Department '{dept.name}' deleted."})


@api_bp.route('/api/admin/subjects', methods=['GET', 'POST'])
@login_required
def admin_subjects():
    err = require_admin()
    if err: return err

    if request.method == 'GET':
        subs = Subject.query.order_by(Subject.name.asc()).all()
        result = []
        for s in subs:
            assigned = [{'id': t.teacher.id, 'name': t.teacher.full_name, 'username': t.teacher.username} for t in s.assigned_teachers]
            result.append({
                'id': s.id,
                'name': s.name,
                'code': s.code,
                'department_id': s.department_id,
                'department_name': s.department.name if s.department else None,
                'semester': s.semester,
                'is_active': s.is_active,
                'assigned_teachers': assigned
            })
        return jsonify(result)

    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    code = (data.get('code') or '').strip().upper()
    department_id = data.get('department_id') or None
    semester = data.get('semester') or None
    teacher_id = data.get('teacher_id') or None

    if not name or not code:
        return jsonify({'success': False, 'message': 'Subject name and code are required.'}), 400

    if Subject.query.filter(func.lower(Subject.code) == code.lower()).first():
        return jsonify({'success': False, 'message': f"Subject with code '{code}' already exists."}), 400

    sub = Subject(name=name, code=code, department_id=department_id, semester=semester, is_active=True)
    db.session.add(sub)
    db.session.commit()

    if teacher_id:
        link = TeacherSubject(teacher_id=teacher_id, subject_id=sub.id)
        db.session.add(link)
        db.session.commit()

    return jsonify({'success': True, 'subject': sub.to_dict()})


@api_bp.route('/api/admin/subjects/<int:sub_id>', methods=['PUT', 'DELETE'])
@login_required
def admin_subject_detail(sub_id):
    err = require_admin()
    if err: return err

    sub = Subject.query.get_or_404(sub_id)

    if request.method == 'PUT':
        data = request.get_json() or {}
        sub.name = (data.get('name') or sub.name).strip()
        sub.code = (data.get('code') or sub.code).strip().upper()
        sub.department_id = data.get('department_id') or None
        sub.semester = data.get('semester') or None

        if 'teacher_id' in data:
            TeacherSubject.query.filter_by(subject_id=sub.id).delete()
            if data['teacher_id']:
                db.session.add(TeacherSubject(teacher_id=data['teacher_id'], subject_id=sub.id))

        db.session.commit()
        return jsonify({'success': True, 'subject': sub.to_dict()})

    if request.method == 'DELETE':
        db.session.delete(sub)
        db.session.commit()
        return jsonify({'success': True, 'message': f"Subject '{sub.code}' deleted."})


@api_bp.route('/api/admin/academic_structure')
@login_required
def admin_academic_structure():
    err = require_admin()
    if err: return err

    departments = Department.query.all()
    dept_stats = []
    for d in departments:
        dept_stats.append({
            'id': d.id,
            'name': d.name,
            'code': d.code,
            'students_count': User.query.filter_by(department_id=d.id, role='student').count(),
            'faculty_count': User.query.filter_by(department_id=d.id, role='teacher').count(),
            'subjects_count': len(d.subjects)
        })

    semester_breakdown = {}
    for sem in range(1, 9):
        semester_breakdown[sem] = {
            'students_count': User.query.filter_by(semester=sem, role='student').count(),
            'subjects_count': Subject.query.filter_by(semester=sem).count()
        }

    return jsonify({
        'departments': dept_stats,
        'semester_breakdown': semester_breakdown
    })


@api_bp.route('/api/admin/laboratories', methods=['GET', 'POST'])
@login_required
def admin_laboratories():
    if request.method == 'GET':
        if current_user.role not in ('admin', 'teacher'):
            return jsonify({'success': False, 'message': 'Forbidden'}), 403
        labs = Laboratory.query.order_by(Laboratory.name.asc()).all()
        return jsonify([l.to_dict() for l in labs])

    err = require_admin()
    if err: return err

    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    code = (data.get('code') or '').strip().upper() or f"LAB{name[-1] if name and name[-1].isdigit() else '1'}"
    location = (data.get('location') or '').strip() or None
    room_number = (data.get('room_number') or '').strip() or None
    department_id = data.get('department_id') or None
    ip_start = (data.get('ip_start') or '').strip() or '127.0.0.1'
    ip_end = (data.get('ip_end') or '').strip() or None
    capacity = int(data.get('capacity', 30))

    if not name:
        return jsonify({'success': False, 'message': 'Laboratory name is required.'}), 400

    if Laboratory.query.filter(func.lower(Laboratory.name) == name.lower()).first():
        return jsonify({'success': False, 'message': f"Laboratory with name '{name}' already exists."}), 400

    if Laboratory.query.filter(func.lower(Laboratory.code) == code.lower()).first():
        return jsonify({'success': False, 'message': f"Laboratory with code '{code}' already exists."}), 400

    lab = Laboratory(
        name=name,
        code=code,
        location=location,
        room_number=room_number,
        department_id=department_id,
        ip_start=ip_start,
        ip_end=ip_end,
        default_capacity=capacity
    )
    db.session.add(lab)
    db.session.commit()

    WorkstationService.provision_lab_workstations(lab, capacity=capacity, admin_user_id=current_user.id)
    return jsonify({'success': True, 'laboratory': lab.to_dict()})


@api_bp.route('/api/admin/laboratories/<int:lab_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def admin_laboratory_detail(lab_id):
    err = require_admin()
    if err: return err

    lab = Laboratory.query.get_or_404(lab_id)

    if request.method == 'GET':
        return jsonify(lab.to_dict())

    if request.method == 'PUT':
        data = request.get_json() or {}
        lab.name = (data.get('name') or lab.name).strip()
        lab.code = (data.get('code') or lab.code).strip().upper()
        lab.location = (data.get('location') or '').strip() or None
        lab.room_number = (data.get('room_number') or '').strip() or None
        if 'department_id' in data:
            lab.department_id = data.get('department_id') or None
        if 'ip_start' in data:
            lab.ip_start = (data.get('ip_start') or '').strip() or None
        if 'ip_end' in data:
            lab.ip_end = (data.get('ip_end') or '').strip() or None

        if 'capacity' in data:
            cap = int(data['capacity'])
            lab.default_capacity = cap
            WorkstationService.provision_lab_workstations(lab, capacity=cap, admin_user_id=current_user.id)
        else:
            WorkstationService.provision_lab_workstations(lab, capacity=lab.default_capacity, admin_user_id=current_user.id)

        db.session.commit()
        return jsonify({'success': True, 'laboratory': lab.to_dict()})

    if request.method == 'DELETE':
        active = AttendanceSession.query.filter_by(lab_id=lab.id, is_active=True).count()
        if active > 0:
            return jsonify({'success': False, 'message': 'Cannot delete lab with currently active sessions.'}), 400

        db.session.delete(lab)
        db.session.commit()
        return jsonify({'success': True, 'message': f"Laboratory '{lab.name}' deleted."})


@api_bp.route('/api/admin/laboratories/<int:lab_id>/workstations', methods=['GET'])
@login_required
def admin_laboratory_workstations(lab_id):
    err = require_admin()
    if err: return err

    lab = Laboratory.query.get_or_404(lab_id)
    workstations = Workstation.query.filter_by(lab_id=lab.id).order_by(Workstation.seat_number.asc()).all()
    return jsonify({
        'laboratory': lab.to_dict(),
        'workstations': [w.to_dict() for w in workstations]
    })


# ---------------- TEACHER REST APIS ----------------

def require_teacher():
    if not current_user.is_authenticated or current_user.role not in ['teacher', 'admin']:
        return jsonify({'error': 'Teacher authorization required.'}), 403
    return None


@api_bp.route('/api/teacher/overview')
@login_required
def teacher_overview():
    err = require_teacher()
    if err: return err

    assigned_subs = Subject.query.join(TeacherSubject).filter(
        TeacherSubject.teacher_id == current_user.id,
        Subject.is_active == True
    ).all()
    if not assigned_subs:
        assigned_subs = Subject.query.filter_by(is_active=True).all()

    active_sess = SessionService.get_active_session_for_teacher(current_user.id)
    total_students = User.query.filter_by(role='student', is_active=True).count()

    past_sessions = db.session.query(
        AttendanceSession,
        func.count(AttendanceRecord.id).label('attended_count')
    ).outerjoin(AttendanceRecord, AttendanceSession.id == AttendanceRecord.session_id)\
     .filter(AttendanceSession.teacher_id == current_user.id)\
     .group_by(AttendanceSession.id)\
     .order_by(AttendanceSession.start_time.desc())\
     .limit(10).all()

    recent_sessions_data = []
    for sess, count in past_sessions:
        recent_sessions_data.append({
            'id': sess.id,
            'subject_name': sess.subject.name,
            'subject_code': sess.subject.code,
            'lab_name': sess.laboratory.name,
            'start_time': sess.start_time.isoformat() if sess.start_time else None,
            'capacity': sess.lab_capacity,
            'attended_count': count
        })

    labs = Laboratory.query.filter_by(is_active=True).order_by(Laboratory.name.asc()).all()
    if not labs:
        labs = Laboratory.query.order_by(Laboratory.name.asc()).all()

    return jsonify({
        'teacher_name': current_user.full_name,
        'assigned_subjects': [s.to_dict() for s in assigned_subs],
        'laboratories': [l.to_dict() for l in labs],
        'active_session': active_sess.to_dict() if active_sess else None,
        'total_students': total_students,
        'recent_sessions': recent_sessions_data
    })


@api_bp.route('/api/teacher/laboratories')
@login_required
def teacher_laboratories():
    err = require_teacher()
    if err: return err

    labs = Laboratory.query.filter_by(is_active=True).order_by(Laboratory.name.asc()).all()
    if not labs:
        labs = Laboratory.query.order_by(Laboratory.name.asc()).all()
    return jsonify([l.to_dict() for l in labs])


@api_bp.route('/api/teacher/subjects')
@login_required
def teacher_subjects():
    err = require_teacher()
    if err: return err

    assigned = Subject.query.join(TeacherSubject).filter(
        TeacherSubject.teacher_id == current_user.id
    ).all()
    all_subjects = Subject.query.filter_by(is_active=True).all()

    return jsonify({
        'assigned': [s.to_dict() for s in assigned],
        'available': [s.to_dict() for s in all_subjects]
    })


@api_bp.route('/api/teacher/add_subject', methods=['POST'])
@login_required
def teacher_add_subject():
    err = require_teacher()
    if err: return err

    data = request.get_json() or {}
    subject_id = data.get('subject_id')

    if not subject_id:
        return jsonify({'success': False, 'message': 'Please select a subject.'}), 400

    sub = Subject.query.get(subject_id)
    if not sub:
        return jsonify({'success': False, 'message': 'Subject not found.'}), 404

    existing = TeacherSubject.query.filter_by(teacher_id=current_user.id, subject_id=sub.id).first()
    if not existing:
        db.session.add(TeacherSubject(teacher_id=current_user.id, subject_id=sub.id))
        db.session.commit()

    return jsonify({'success': True, 'message': f"Subject '{sub.name}' added to your profile."})


@api_bp.route('/api/teacher/start_session', methods=['POST'])
@login_required
def teacher_start_session():
    err = require_teacher()
    if err: return err

    data = request.get_json() or {}
    subject_id = data.get('subject_id')
    lab_id = data.get('lab_id')
    capacity = int(data.get('capacity', 30))
    duration = int(data.get('duration', 10))

    if not subject_id or not lab_id:
        return jsonify({'success': False, 'message': 'Subject and Laboratory are required.'}), 400

    try:
        session = SessionService.create_and_start_session(
            teacher_id=current_user.id,
            subject_id=subject_id,
            lab_id=lab_id,
            capacity=capacity,
            duration_minutes=duration
        )
        return jsonify({'success': True, 'message': f'Session {session.session_code} launched!', 'session': session.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@api_bp.route('/api/teacher/pause_session/<int:session_id>', methods=['POST'])
@login_required
def teacher_pause_session(session_id):
    err = require_teacher()
    if err: return err

    success, msg = SessionService.pause_or_resume_session(session_id, current_user.id)
    return jsonify({'success': success, 'message': msg}), 200 if success else 400


@api_bp.route('/api/teacher/extend_session/<int:session_id>', methods=['POST'])
@login_required
def teacher_extend_session(session_id):
    err = require_teacher()
    if err: return err

    data = request.get_json() or {}
    minutes = int(data.get('minutes', 10))
    success, msg = SessionService.extend_session(session_id, current_user.id, additional_minutes=minutes)
    return jsonify({'success': success, 'message': msg}), 200 if success else 400


@api_bp.route('/api/teacher/stop_session/<int:session_id>', methods=['POST'])
@login_required
def teacher_stop_session(session_id):
    err = require_teacher()
    if err: return err

    success, msg = SessionService.stop_session(session_id, current_user.id)
    return jsonify({'success': success, 'message': msg}), 200 if success else 400


@api_bp.route('/api/teacher/session/<int:session_id>/live')
@login_required
def teacher_session_live(session_id):
    err = require_teacher()
    if err: return err

    session = AttendanceSession.query.get_or_404(session_id)
    if session.teacher_id != current_user.id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized session view.'}), 403

    summary = SessionService.get_session_roster_summary(session.id)
    marked_seats = {}
    for r in summary['present_records']:
        marked_seats[r.seat_number] = {
            'student_name': r.student.full_name if r.student else 'Unknown',
            'username': r.student.username if r.student else 'N/A',
            'time': r.timestamp.strftime('%H:%M:%S'),
            'ip': r.ip_address
        }

    lab_workstations = Workstation.query.filter_by(lab_id=session.lab_id).order_by(Workstation.seat_number.asc()).all()

    return jsonify({
        'session': session.to_dict(),
        'present_count': summary['present_count'],
        'absent_count': summary['absent_count'],
        'completion_pct': summary['completion_pct'],
        'marked_seats': marked_seats,
        'workstations': [w.to_dict() for w in lab_workstations],
        'present_records': [r.to_dict() for r in summary['present_records']],
        'absent_students': [s.to_dict() for s in summary['absent_students']]
    })


@api_bp.route('/api/teacher/student_analysis')
@login_required
def teacher_student_analysis():
    err = require_teacher()
    if err: return err

    at_risk = ReportService.get_at_risk_students(teacher_id=current_user.id, threshold=75.0)
    all_students = User.query.filter_by(role='student', is_active=True).all()

    total_sessions_by_me = AttendanceSession.query.filter_by(teacher_id=current_user.id).count()

    roster_analysis = []
    for s in all_students:
        presences = AttendanceRecord.query.join(AttendanceSession).filter(
            AttendanceRecord.student_id == s.id,
            AttendanceSession.teacher_id == current_user.id
        ).count()
        pct = round((presences / total_sessions_by_me * 100), 1) if total_sessions_by_me > 0 else 0.0

        roster_analysis.append({
            'id': s.id,
            'name': s.full_name,
            'username': s.username,
            'attended': presences,
            'total_sessions': total_sessions_by_me,
            'percentage': pct,
            'is_at_risk': pct < 75.0 if total_sessions_by_me > 0 else False
        })

    return jsonify({
        'at_risk_students': at_risk,
        'roster_analysis': roster_analysis,
        'total_conducted': total_sessions_by_me
    })


# ---------------- STUDENT REST APIS ----------------

@api_bp.route('/api/student/dashboard')
@login_required
def student_dashboard_api():
    if current_user.role != 'student':
        return jsonify({'error': 'Student authorization required.'}), 403

    client_ip = get_real_client_ip()

    active_session = SessionService.get_current_active_session_for_student(
        student_id=current_user.id,
        client_ip=client_ip
    )

    already_marked = False
    assigned_seat = None
    active_lab_pcs = []
    detected_pc = None

    if active_session:
        rec = AttendanceRecord.query.filter_by(
            session_id=active_session.id,
            student_id=current_user.id
        ).first()
        if rec:
            already_marked = True
            assigned_seat = rec.seat_number

        ws = WorkstationService.find_workstation_for_request(
            lab_id=active_session.lab_id,
            client_ip=client_ip
        )
        if ws:
            detected_pc = ws.to_dict()
            if not assigned_seat:
                assigned_seat = ws.seat_number

        # Build workstation list with locked states for active lab
        marked_records = AttendanceRecord.query.filter_by(session_id=active_session.id).all()
        marked_dict = {r.seat_number: r for r in marked_records}
        all_ws = Workstation.query.filter_by(lab_id=active_session.lab_id).order_by(Workstation.seat_number.asc()).all()
        for w in all_ws:
            is_locked = w.seat_number in marked_dict
            claimer = marked_dict[w.seat_number].student.full_name if is_locked else None
            active_lab_pcs.append({
                'id': w.id,
                'seat_number': w.seat_number,
                'workstation_code': w.workstation_code,
                'ip_address': w.ip_address,
                'mac_address': w.mac_address,
                'device_id': w.device_id,
                'is_locked': is_locked,
                'claimed_by': claimer,
                'is_mine': already_marked and assigned_seat == w.seat_number
            })

    stats = ReportService.get_student_overall_stats(current_user.id)

    recent_logs_data = []
    if stats and stats.get('recent_logs'):
        for ts, seat_num, sub_name, lab_name, teacher_name in stats['recent_logs']:
            recent_logs_data.append({
                'timestamp': ts.strftime('%d-%b-%Y %H:%M'),
                'seat_number': seat_num,
                'subject_name': sub_name,
                'lab_name': lab_name,
                'teacher_name': teacher_name
            })

    return jsonify({
        'student': current_user.to_dict(),
        'client_ip': client_ip,
        'active_session': active_session.to_dict() if active_session else None,
        'already_marked': already_marked,
        'assigned_seat': assigned_seat,
        'detected_pc': detected_pc,
        'active_lab_pcs': active_lab_pcs,
        'stats': {
            'overall_percentage': stats['overall_percentage'] if stats else 0,
            'total_conducted': stats['total_conducted'] if stats else 0,
            'total_attended': stats['total_attended'] if stats else 0,
            'absent_count': stats['absent_count'] if stats else 0,
            'subject_stats': stats['subject_stats'] if stats else [],
            'recent_logs': recent_logs_data
        }
    })
