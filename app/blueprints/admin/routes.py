import os
import shutil
from datetime import datetime
import pandas as pd
from flask import render_template, request, redirect, url_for, flash, jsonify, current_app, send_file
from flask_login import login_required, current_user

from app.blueprints.admin import admin_bp
from app.extensions import db
from app.models import (
    User, Department, Subject, Laboratory, Workstation,
    TeacherSubject, StudentEnrollment, AttendanceSession, AttendanceRecord, AuditLog
)
from app.utils.decorators import admin_required
from app.services.workstation_service import WorkstationService
from app.services.audit_service import AuditService
from app.utils.security import hash_password


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_students = User.query.filter_by(role='student').count()
    total_teachers = User.query.filter_by(role='teacher').count()
    total_labs = Laboratory.query.count()
    total_workstations = Workstation.query.count()
    total_sessions = AttendanceSession.query.count()
    active_sessions = AttendanceSession.query.filter_by(is_active=True).count()
    total_records = AttendanceRecord.query.count()

    recent_sessions = AttendanceSession.query.order_by(AttendanceSession.start_time.desc()).limit(10).all()
    recent_audit = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(15).all()

    departments = Department.query.all()
    subjects = Subject.query.all()
    labs = Laboratory.query.all()
    teachers = User.query.filter_by(role='teacher').all()
    students = User.query.filter_by(role='student').order_by(User.username.asc()).limit(50).all()

    return render_template(
        'admin/dashboard.html',
        total_students=total_students,
        total_teachers=total_teachers,
        total_labs=total_labs,
        total_workstations=total_workstations,
        total_sessions=total_sessions,
        active_sessions=active_sessions,
        total_records=total_records,
        recent_sessions=recent_sessions,
        recent_audit=recent_audit,
        departments=departments,
        subjects=subjects,
        labs=labs,
        teachers=teachers,
        students=students
    )


# ---------------- USER MANAGEMENT ----------------

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    role = request.args.get('role', 'all')
    q = User.query
    if role in ['admin', 'teacher', 'student']:
        q = q.filter_by(role=role)
    all_users = q.order_by(User.id.desc()).all()
    departments = Department.query.all()

    return render_template('admin/users.html', users=all_users, departments=departments, current_role=role)


@admin_bp.route('/user/create', methods=['POST'])
@login_required
@admin_required
def create_user():
    username = request.form.get('username', '').strip()
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip() or None
    role = request.form.get('role', 'student')
    department_id = request.form.get('department_id', type=int) or None
    semester = request.form.get('semester', type=int) or None
    password = request.form.get('password', '')

    if not username or not full_name or not password:
        flash("Username, Full Name, and Password are required.", "danger")
        return redirect(url_for('admin.users'))

    if User.query.filter_by(username=username).first():
        flash(f"User with ID/Username '{username}' already exists.", "danger")
        return redirect(url_for('admin.users'))

    user = User(
        username=username,
        full_name=full_name,
        email=email,
        role=role,
        department_id=department_id,
        semester=semester,
        password=password
    )
    db.session.add(user)
    db.session.commit()

    AuditService.log(
        action="USER_CREATED",
        user_id=current_user.id,
        target_type="User",
        target_id=user.id,
        details=f"Admin created {role}: {username} ({full_name})"
    )

    flash(f"{role.capitalize()} account '{username}' created successfully.", "success")
    return redirect(url_for('admin.users', role=role))


@admin_bp.route('/user/edit/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    user.full_name = request.form.get('full_name', '').strip()
    user.email = request.form.get('email', '').strip() or None
    user.department_id = request.form.get('department_id', type=int) or None
    user.semester = request.form.get('semester', type=int) or None

    new_pass = request.form.get('password', '').strip()
    if new_pass:
        user.password = new_pass

    is_active_val = request.form.get('is_active')
    user.is_active = True if is_active_val in ['true', '1', 'on'] else False

    db.session.commit()
    AuditService.log(
        action="USER_UPDATED",
        user_id=current_user.id,
        target_type="User",
        target_id=user.id,
        details=f"Admin updated user {user.username}"
    )

    flash(f"User '{user.username}' details updated successfully.", "success")
    return redirect(url_for('admin.users'))


@admin_bp.route('/user/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot delete your own admin account.", "danger")
        return redirect(url_for('admin.users'))

    # Clean up foreign relations
    AttendanceRecord.query.filter_by(student_id=user.id).delete()
    AttendanceSession.query.filter_by(teacher_id=user.id).delete()

    db.session.delete(user)
    db.session.commit()

    AuditService.log(
        action="USER_DELETED",
        user_id=current_user.id,
        target_type="User",
        target_id=user_id,
        details=f"Admin deleted user {user.username} ({user.role})"
    )

    flash(f"User account '{user.username}' deleted.", "info")
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/import_csv', methods=['POST'])
@login_required
@admin_required
def import_students_csv():
    file = request.files.get('file')
    if not file or file.filename == '':
        flash("Please upload a CSV or Excel file.", "danger")
        return redirect(url_for('admin.users'))

    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            flash("Supported file types are .csv, .xlsx, .xls", "danger")
            return redirect(url_for('admin.users'))

        # Normalize column names
        df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]

        created_count = 0
        skipped_count = 0

        for _, row in df.iterrows():
            username = str(row.get('username') or row.get('enrollment_no') or row.get('roll_no') or '').strip()
            full_name = str(row.get('full_name') or row.get('name') or username).strip()
            password = str(row.get('password') or 'student123').strip()
            email = str(row.get('email') or '').strip() or None
            semester = int(row.get('semester')) if pd.notna(row.get('semester')) else None

            if not username or username == 'nan':
                continue

            if User.query.filter_by(username=username).first():
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
        flash(f"Bulk Import Complete! Created {created_count} students. Skipped {skipped_count} existing.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Import failed: {str(e)}", "danger")

    return redirect(url_for('admin.users', role='student'))


# ---------------- LABORATORY & WORKSTATIONS ----------------

@admin_bp.route('/labs')
@login_required
@admin_required
def labs():
    all_labs = Laboratory.query.all()
    return render_template('admin/labs.html', labs=all_labs)


@admin_bp.route('/lab/create', methods=['POST'])
@login_required
@admin_required
def create_lab():
    name = request.form.get('name', '').strip()
    code = request.form.get('code', '').strip().upper() or None
    location = request.form.get('location', '').strip() or None
    ip_start = request.form.get('ip_start', '').strip() or None
    ip_end = request.form.get('ip_end', '').strip() or None
    capacity = request.form.get('capacity', default=30, type=int)

    if not name:
        flash("Lab name is required.", "danger")
        return redirect(url_for('admin.labs'))

    lab = Laboratory(
        name=name,
        code=code or f"LAB{name[-1] if name[-1].isdigit() else '1'}",
        location=location,
        ip_start=ip_start,
        ip_end=ip_end,
        default_capacity=capacity
    )
    db.session.add(lab)
    db.session.commit()

    # Automatically provision default workstations
    WorkstationService.provision_lab_workstations(lab, capacity=capacity, admin_user_id=current_user.id)

    flash(f"Laboratory '{name}' created and {capacity} workstations provisioned.", "success")
    return redirect(url_for('admin.labs'))


@admin_bp.route('/lab/edit/<int:lab_id>', methods=['POST'])
@login_required
@admin_required
def edit_lab(lab_id):
    lab = Laboratory.query.get_or_404(lab_id)
    lab.name = request.form.get('name', '').strip()
    lab.code = request.form.get('code', '').strip().upper() or lab.code
    lab.location = request.form.get('location', '').strip() or None
    lab.ip_start = request.form.get('ip_start', '').strip() or None
    lab.ip_end = request.form.get('ip_end', '').strip() or None
    new_capacity = request.form.get('capacity', default=30, type=int)

    lab.default_capacity = new_capacity
    db.session.commit()

    # Re-align workstations if capacity expanded
    WorkstationService.provision_lab_workstations(lab, capacity=new_capacity, admin_user_id=current_user.id)

    flash(f"Laboratory '{lab.name}' updated.", "success")
    return redirect(url_for('admin.labs'))


@admin_bp.route('/lab/delete/<int:lab_id>', methods=['POST'])
@login_required
@admin_required
def delete_lab(lab_id):
    lab = Laboratory.query.get_or_404(lab_id)
    # Check if active sessions exist
    active_count = AttendanceSession.query.filter_by(lab_id=lab.id, is_active=True).count()
    if active_count > 0:
        flash("Cannot delete laboratory with currently active sessions.", "danger")
        return redirect(url_for('admin.labs'))

    name = lab.name
    db.session.delete(lab)
    db.session.commit()

    AuditService.log(
        action="LAB_DELETED",
        user_id=current_user.id,
        target_type="Laboratory",
        target_id=lab_id,
        details=f"Admin deleted lab {name}"
    )

    flash(f"Laboratory '{name}' deleted.", "info")
    return redirect(url_for('admin.labs'))


@admin_bp.route('/workstations')
@login_required
@admin_required
def workstations():
    lab_id = request.args.get('lab_id', type=int)
    labs = Laboratory.query.all()
    q = Workstation.query
    if lab_id:
        q = q.filter_by(lab_id=lab_id)
    ws_list = q.order_by(Workstation.lab_id.asc(), Workstation.seat_number.asc()).all()

    return render_template('admin/workstations.html', workstations=ws_list, labs=labs, current_lab_id=lab_id)


@admin_bp.route('/workstation/toggle_status/<int:ws_id>', methods=['POST'])
@login_required
@admin_required
def toggle_workstation_status(ws_id):
    ws = Workstation.query.get_or_404(ws_id)
    new_status = request.form.get('status', 'active')
    ws.status = new_status
    db.session.commit()
    return jsonify({'success': True, 'status': ws.status})


# ---------------- DEPARTMENTS & SUBJECTS ----------------

@admin_bp.route('/academics')
@login_required
@admin_required
def academics():
    departments = Department.query.all()
    subjects = Subject.query.all()
    teachers = User.query.filter_by(role='teacher', is_active=True).all()
    return render_template('admin/academics.html', departments=departments, subjects=subjects, teachers=teachers)


@admin_bp.route('/department/create', methods=['POST'])
@login_required
@admin_required
def create_department():
    name = request.form.get('name', '').strip()
    code = request.form.get('code', '').strip().upper()
    if not name or not code:
        flash("Department name and code are required.", "danger")
    else:
        dept = Department(name=name, code=code)
        db.session.add(dept)
        db.session.commit()
        flash(f"Department '{name}' created.", "success")
    return redirect(url_for('admin.academics'))


@admin_bp.route('/subject/create', methods=['POST'])
@login_required
@admin_required
def create_subject():
    name = request.form.get('name', '').strip()
    code = request.form.get('code', '').strip().upper()
    department_id = request.form.get('department_id', type=int) or None
    semester = request.form.get('semester', type=int) or None
    teacher_id = request.form.get('teacher_id', type=int) or None

    if not name or not code:
        flash("Subject name and code are required.", "danger")
        return redirect(url_for('admin.academics'))

    sub = Subject(name=name, code=code, department_id=department_id, semester=semester, is_active=True)
    db.session.add(sub)
    db.session.commit()

    if teacher_id:
        link = TeacherSubject(teacher_id=teacher_id, subject_id=sub.id)
        db.session.add(link)
        db.session.commit()

    flash(f"Subject '{name}' ({code}) registered successfully.", "success")
    return redirect(url_for('admin.academics'))


# ---------------- AUDIT LOGS & BACKUPS ----------------

@admin_bp.route('/audit_logs')
@login_required
@admin_required
def audit_logs():
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action')

    q = AuditLog.query.order_by(AuditLog.timestamp.desc())
    if action_filter:
        q = q.filter(AuditLog.action == action_filter)

    pagination = q.paginate(page=page, per_page=30, error_out=False)
    actions = [a[0] for a in db.session.query(AuditLog.action).distinct().all()]

    return render_template('admin/audit_logs.html', pagination=pagination, actions=actions, current_action=action_filter)


@admin_bp.route('/backup_database', methods=['POST'])
@login_required
@admin_required
def backup_database():
    instance_dir = current_app.config['INSTANCE_DIR']
    db_file = instance_dir / 'attendance.db'
    backup_dir = instance_dir / 'backups'
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"attendance_backup_{timestamp}.db"
    dest_path = backup_dir / backup_filename

    try:
        shutil.copy2(db_file, dest_path)
        AuditService.log(
            action="DATABASE_BACKUP",
            user_id=current_user.id,
            details=f"Created backup snapshot: {backup_filename}"
        )
        flash(f"Database backup snapshot saved: {backup_filename}", "success")
    except Exception as e:
        flash(f"Backup failed: {str(e)}", "danger")

    return redirect(url_for('admin.dashboard'))

