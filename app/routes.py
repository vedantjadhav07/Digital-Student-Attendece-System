import io
import pandas as pd 
from datetime import datetime, timedelta
from flask import jsonify, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func
from . import login_manager, db, socketio 
from .models import AttendanceRecord, User, AttendanceSession,TeacherSubject
from flask import current_app as app
import pdfkit
from flask import make_response

path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('teacher_dashboard' if user.role == 'teacher' else 'student_dashboard'))
        
        flash('Invalid credentials', 'danger')
    return render_template('login.html')


@app.route('/teacher_dashboard')
@login_required
def teacher_dashboard():
    if current_user.role != 'teacher': 
        return redirect(url_for('login'))

    # 1. Fetch subjects specific to THIS teacher
    my_stored_subjects = TeacherSubject.query.filter_by(teacher_id=current_user.id).all()

    # 2. Fetch active session for THIS teacher only
    active_session = AttendanceSession.query.filter_by(
        is_active=True, 
        teacher_id=current_user.id
    ).first()

    all_students_list = User.query.filter_by(role='student').all()

    marked_pcs = {}
    remaining_seconds = 0
    # FEATURE 4: Dynamic Grid Size (Defaults to 30 if no active session)
    pc_count = active_session.lab_capacity if active_session else 30

    if active_session:
        now = datetime.utcnow()
        if now < active_session.end_time:
            remaining_seconds = int((active_session.end_time - now).total_seconds())
            records = db.session.query(AttendanceRecord, User).join(User).filter(
                AttendanceRecord.session_id == active_session.id
            ).all()
            for record, user in records:
                # Detect PC number from last part of IP
                pc_num = record.ip_address.split('.')[-1] if record.ip_address != '127.0.0.1' else record.student_id
                marked_pcs[str(pc_num)] = user.username
        else:
            active_session.is_active = False
            db.session.commit()
            active_session = None

    # 3. FEATURE 1: At-Risk Student Analysis (Attendance < 75%)
    # Calculate attendance for all students based ONLY on this teacher's labs
    total_labs_by_me = AttendanceSession.query.filter_by(teacher_id=current_user.id).count()
    student_analysis = []
    
    all_students = User.query.filter_by(role='student').all()
    for student in all_students:
        presences = AttendanceRecord.query.join(AttendanceSession).filter(
            AttendanceRecord.student_id == student.id,
            AttendanceSession.teacher_id == current_user.id
        ).count()
        
        perc = (presences / total_labs_by_me * 100) if total_labs_by_me > 0 else 0
        student_analysis.append({
            'name': student.username,
            'percentage': round(perc, 1),
            'status': 'At-Risk' if perc < 75 else 'Safe'
        })

    # 4. Fetch history for the history tab
    history_query = db.session.query(
        AttendanceSession, 
        func.count(AttendanceRecord.id).label('student_count')
    ).outerjoin(AttendanceRecord)\
     .filter(AttendanceSession.teacher_id == current_user.id)\
     .group_by(AttendanceSession.id)\
     .order_by(AttendanceSession.id.desc()).all()

    past_sessions = [{
        'id': sess.id,
        'subject': sess.subject,
        'lab_name': sess.lab_name,
        'start_time': sess.start_time,
        'count': count
    } for sess, count in history_query]

    return render_template('teacher_dash.html', 
                           active_session=active_session, 
                           my_stored_subjects=my_stored_subjects,
                           marked_pcs=marked_pcs,
                           remaining_seconds=remaining_seconds,
                           past_sessions=past_sessions,
                           student_analysis=student_analysis,
                           pc_count=pc_count,
                           all_students_list=all_students_list)


@app.route('/add_subject', methods=['POST'])
@login_required
def add_subject():
    if current_user.role != 'teacher': 
        return "Unauthorized", 403
        
    name = request.form.get('subject_name').upper().strip()
    
    if not name:
        flash("Subject name cannot be empty.", "danger")
        return redirect(url_for('teacher_dashboard'))

    # Check if this subject is already in the teacher's list
    exists = TeacherSubject.query.filter_by(subject_name=name, teacher_id=current_user.id).first()
    
    if not exists:
        new_sub = TeacherSubject(subject_name=name, teacher_id=current_user.id)
        db.session.add(new_sub)
        db.session.commit()
        flash(f"Subject '{name}' added successfully!", "success")
    else:
        flash(f"Subject '{name}' is already in your list.", "info")
        
    return redirect(url_for('teacher_dashboard'))

@app.route('/student_dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('teacher_dashboard'))

    # 1. Get the student's current IP address
    user_ip = request.remote_addr
    try:
        # Extract the PC number (e.g., 192.168.1.15 -> 15)
        pc_num = int(user_ip.split('.')[-1]) if user_ip != '127.0.0.1' else current_user.id
    except ValueError:
        pc_num = 0

    # 2. Find the active session
    active_session_obj = AttendanceSession.query.filter_by(is_active=True).first()
    active_session = None

    if active_session_obj:
        # 3. VISIBILITY LOGIC: Check if this PC is inside the teacher's selected lab range
        is_visible = False
        if active_session_obj.lab_name == "Lab 1" and (1 <= pc_num <= 30):
            is_visible = True
        elif active_session_obj.lab_name == "Lab 2" and (31 <= pc_num <= 60):
            is_visible = True
        elif active_session_obj.lab_name == "Lab 3" and (61 <= pc_num <= 90):
            is_visible = True
        
        # Only pass session data to the UI if the student is in the correct lab
        if is_visible:
            teacher = User.query.get(active_session_obj.teacher_id)
            active_session = {
                "subject": active_session_obj.subject,
                "lab_name": active_session_obj.lab_name,
                "teacher_name": teacher.username if teacher else "Faculty"
            }

    # 4. Fetch History and Percentage (same as before)
    my_records = db.session.query(
        AttendanceRecord.timestamp,
        AttendanceSession.subject,
        AttendanceSession.lab_name
    ).join(AttendanceSession).filter(AttendanceRecord.student_id == current_user.id).all()

    total_held = AttendanceSession.query.count()
    attendance_pct = round((len(my_records) / total_held * 100), 1) if total_held > 0 else 0

    return render_template('student_dash.html', 
                           active_session=active_session, 
                           my_records=my_records,
                           attendance_pct=attendance_pct,
                           pc_num=pc_num) # Pass pc_num to show them where they are sitting

@app.route('/student_report_download')
@login_required
def student_report_download():
    # Fetch all records for this specific student
    records = db.session.query(
        AttendanceSession.subject,
        AttendanceSession.lab_name,
        AttendanceRecord.timestamp
    ).join(AttendanceSession, AttendanceRecord.session_id == AttendanceSession.id)\
     .filter(AttendanceRecord.student_id == current_user.id).all()

    data = [{"Subject": r[0], "Lab": r[1], "Date": r[2].strftime("%Y-%m-%d"), "Time": r[2].strftime("%H:%M:%S")} for r in records]
    df = pd.DataFrame(data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, startrow=3, index=False, sheet_name='My_Attendance')
        workbook, worksheet = writer.book, writer.sheets['My_Attendance']
        worksheet.write(0, 0, f"PERSONAL ATTENDANCE REPORT: {current_user.username}", workbook.add_format({'bold': True, 'font_size': 14}))
        worksheet.write(1, 0, f"Generated on: {datetime.now().strftime('%Y-%m-%d')}")
    
    output.seek(0)
    return send_file(output, download_name=f"My_Attendance_{current_user.username}.xlsx", as_attachment=True)

@app.route('/advanced_export', methods=['POST'])
@login_required
def advanced_export():
    if current_user.role != 'teacher': return "Unauthorized", 403

    subject = request.form.get('subject')
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')

    start_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1, seconds=-1)

    # 1. Total sessions by THIS teacher in this range
    total_sess_query = AttendanceSession.query.filter(
        AttendanceSession.teacher_id == current_user.id,
        AttendanceSession.start_time.between(start_dt, end_dt)
    )
    if subject != 'ALL':
        total_sess_query = total_sess_query.filter_by(subject=subject)
    
    total_lectures = total_sess_query.count()

    if total_lectures == 0:
        flash("No sessions were conducted by you in this range.", "warning")
        return redirect(url_for('teacher_dashboard'))

    # 2. Get Student Data - OUTER JOIN ensures every student is listed
    # We use a subquery for attendance to isolate it to THIS teacher before joining
    attendance_subquery = db.session.query(
        AttendanceRecord.student_id,
        func.count(AttendanceRecord.id).label('present_count')
    ).join(AttendanceSession).filter(
        AttendanceSession.teacher_id == current_user.id,
        AttendanceSession.start_time.between(start_dt, end_dt)
    )
    if subject != 'ALL':
        attendance_subquery = attendance_subquery.filter(AttendanceSession.subject == subject)
    
    attendance_subquery = attendance_subquery.group_by(AttendanceRecord.student_id).subquery()

    results = db.session.query(
        User.username,
        func.coalesce(attendance_subquery.c.present_count, 0)
    ).filter(User.role == 'student')\
     .outerjoin(attendance_subquery, User.id == attendance_subquery.c.student_id).all()

    # 3. Build Excel
    report_data = []
    for username, count in results:
        report_data.append({
            "Student Name": username,
            "Date Range": f"{start_date_str} to {end_date_str}",
            "Total Attendance": total_lectures,
            "Actual Present": count,
            "Percentage": f"{round((count / total_lectures) * 100, 2)}%"
        })

    df = pd.DataFrame(report_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, startrow=4, index=False, sheet_name='Report')
        workbook, worksheet = writer.book, writer.sheets['Report']
        title_fmt = workbook.add_format({'bold': True, 'font_size': 14, 'font_color': '#0d6efd'})
        worksheet.write(0, 0, "CUMULATIVE ATTENDANCE REPORT", title_fmt)
        worksheet.write(1, 0, f"Subject: {subject}")
        worksheet.write(2, 0, f"Faculty: {current_user.username}")
    
    output.seek(0)
    return send_file(output, download_name=f"Report_{subject}.xlsx", as_attachment=True)



@app.route('/start_lab', methods=['POST'])
@login_required
def start_lab():
    if current_user.role != 'teacher': 
        return "Unauthorized", 403
    
    # Close any existing sessions for this teacher
    AttendanceSession.query.filter_by(teacher_id=current_user.id, is_active=True).update({"is_active": False})
    
    lab_room = request.form.get('lab_room')
    subject = request.form.get('subject')
    
    # Logic: Every lab has 30 PCs, but different IP/ID ranges
    capacity = 30 
    if lab_room == "Lab 1":
        start_pc = 1     # Range: 1-30
    elif lab_room == "Lab 2":
        start_pc = 31    # Range: 31-60
    elif lab_room == "Lab 3":
        start_pc = 61    # Range: 61-90
    else:
        start_pc = 1

    new_sess = AttendanceSession(
        subject=subject,
        lab_name=lab_room,
        lab_capacity=capacity, 
        start_pc=start_pc, 
        is_active=True,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(minutes=10),
        teacher_id=current_user.id
    )
    
    db.session.add(new_sess)
    db.session.commit()
    flash(f"Portal opened for {subject} in {lab_room} (Range: PC {start_pc}-{start_pc+29})", "success")
    return redirect(url_for('teacher_dashboard'))

@app.route('/submit_attendance', methods=['POST'])
@login_required
def submit_attendance():
    session = AttendanceSession.query.filter_by(is_active=True).first()
    if not session:
        return jsonify({"success": False, "message": "No active session."})

    # Get student PC number from IP
    user_ip = request.remote_addr
    try:
        # Extract last part of IP (e.g., .45)
        pc_num = int(user_ip.split('.')[-1]) if user_ip != '127.0.0.1' else current_user.id
    except (ValueError, IndexError):
        pc_num = 0

    # --- NEW SECURITY RANGE CHECK ---
    start = session.start_pc
    end = start + session.lab_capacity - 1

    if not (start <= pc_num <= end):
        return jsonify({
            "success": False, 
            "message": f"Wrong Lab! You are at PC-{pc_num}, but this session is for PCs {start} to {end}."
        })
    # --------------------------------

    # 1. Check if student already marked
    already_marked = AttendanceRecord.query.filter_by(
        student_id=current_user.id, 
        session_id=session.id
    ).first()
    if already_marked:
        return jsonify({"success": False, "message": "You have already marked your attendance!"})

    # 2. Check if PC already used in this session
    ip_already_used = AttendanceRecord.query.filter_by(
        session_id=session.id, 
        ip_address=user_ip
    ).first()

    if ip_already_used:
        return jsonify({
            "success": False, 
            "message": "This PC has already been used. Please use your assigned PC."
        })

    # 3. Save the record
    record = AttendanceRecord(student_id=current_user.id, session_id=session.id, ip_address=user_ip)
    db.session.add(record)
    db.session.commit()

    # Emit to teacher dash
    socketio.emit('attendance_update', {
        'pc_number': str(pc_num), 
        'student_name': current_user.username
    })

    return jsonify({"success": True, "message": f"Success! Marked at PC-{pc_num}"})


@app.route('/export_attendance/<int:session_id>')
@login_required
def export_attendance(session_id):
    # 1. Get the session details for the header
    session = AttendanceSession.query.get_or_404(session_id)
    
    # 2. Query ALL students and OUTER JOIN with attendance for this specific session
    # This ensures every student is listed, regardless of presence
    results = db.session.query(
        User.username,
        AttendanceRecord.timestamp
    ).filter(User.role == 'student')\
     .outerjoin(AttendanceRecord, (User.id == AttendanceRecord.student_id) & (AttendanceRecord.session_id == session_id))\
     .all()

    # 3. Process data: Separate Date and Time into different columns
    report_data = []
    for username, ts in results:
        report_data.append({
            "Student Name": username,
            "Status": "Present" if ts else "Absent",
            "Date": ts.strftime("%Y-%m-%d") if ts else "-",
            "Time": ts.strftime("%H:%M:%S") if ts else "-"
        })

    # 4. Create DataFrame
    df = pd.DataFrame(report_data)

    # 5. Generate Excel with Professional Header using XlsxWriter
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Start the table at row 5 (index 4) to leave room for headers
        df.to_excel(writer, startrow=4, index=False, sheet_name='Lab_Attendance')
        
        workbook  = writer.book
        worksheet = writer.sheets['Lab_Attendance']
        
        # Define Formats
        title_fmt = workbook.add_format({'bold': True, 'font_size': 14, 'font_color': '#198754'})
        info_fmt = workbook.add_format({'bold': True})
        
        # Write Header Information
        worksheet.write(0, 0, "SINGLE LAB ATTENDANCE REPORT", title_fmt)
        worksheet.write(1, 0, f"Subject: {session.subject}", info_fmt)
        worksheet.write(2, 0, f"Lab: {session.lab_name} | Faculty: {current_user.username}", info_fmt)
        worksheet.write(3, 0, f"Session Conducted: {session.start_time.strftime('%d-%m-%Y %H:%M')}")

        # Set column widths for better readability
        worksheet.set_column('A:A', 25) # Student Name
        worksheet.set_column('B:B', 12) # Status
        worksheet.set_column('C:D', 15) # Date and Time

    output.seek(0)
    return send_file(output, 
                     download_name=f"Attendance_{session.subject}_Session_{session_id}.xlsx", 
                     as_attachment=True)

@app.route('/stop_lab', methods=['POST'])
@login_required
def stop_lab():
    if current_user.role != 'teacher':
        return "Unauthorized", 403

    active_session = AttendanceSession.query.filter_by(is_active=True).first()
    if active_session:
        active_session.is_active = False
        db.session.commit()
        flash("Attendance portal closed manually.", "warning")
    
    return redirect(url_for('teacher_dashboard'))

@app.route('/api/student_stats/<string:username>')
@login_required
def student_stats(username):
    if current_user.role != 'teacher':
        return jsonify({"error": "Unauthorized"}), 403

    user = User.query.filter_by(username=username, role='student').first()
    if not user:
        return jsonify({"error": "Student not found"}), 404

    # 1. Get presence count ONLY for sessions conducted by the LOGGED-IN teacher
    records = db.session.query(AttendanceSession.subject, func.count(AttendanceRecord.id))\
        .join(AttendanceRecord, AttendanceSession.id == AttendanceRecord.session_id)\
        .filter(AttendanceRecord.student_id == user.id)\
        .filter(AttendanceSession.teacher_id == current_user.id)\
        .group_by(AttendanceSession.subject).all()

    # 2. Get total sessions held ONLY by THIS teacher
    total_conducted = db.session.query(AttendanceSession.subject, func.count(AttendanceSession.id))\
        .filter(AttendanceSession.teacher_id == current_user.id)\
        .group_by(AttendanceSession.subject).all()

    conducted_dict = {subj: count for subj, count in total_conducted}
    
    stats = []
    total_present = 0
    for subj, present_count in records:
        total_present += present_count
        total_held = conducted_dict.get(subj, 1)
        percentage = (present_count / total_held) * 100
        stats.append({
            "subject": subj,
            "percentage": f"{round(percentage, 2)}%"
        })

    return jsonify({
        "total_presence": total_present,
        "subject_stats": stats
    })

@app.route('/extend_session', methods=['POST'])
@login_required
def extend_session():
    active_session = AttendanceSession.query.filter_by(is_active=True, teacher_id=current_user.id).first()
    if active_session:
        # Add 10 minutes to the end time
        active_session.end_time += timedelta(minutes=10)
        db.session.commit()
        flash("Session extended by 10 minutes!", "success")
    return redirect(url_for('teacher_dashboard'))

@app.route('/export_pdf/<int:session_id>')
@login_required
def export_pdf(session_id):
    if current_user.role != 'teacher':
        return "Unauthorized", 403

    # 1. Fetch Session and Attendance Data
    session = AttendanceSession.query.get_or_404(session_id)
    results = db.session.query(
        User.username,
        AttendanceRecord.timestamp
    ).filter(User.role == 'student')\
     .outerjoin(AttendanceRecord, (User.id == AttendanceRecord.student_id) & (AttendanceRecord.session_id == session_id))\
     .all()

    # 2. Render HTML Template
    html = render_template('pdf_single_report.html', 
                           session=session, 
                           results=results, 
                           faculty=current_user.username)
    
    # 3. Generate PDF with Config
    try:
        pdf = pdfkit.from_string(html, False, configuration=config)
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=Session_{session.subject}_{session_id}.pdf'
        return response
    except OSError as e:
        flash("PDF Engine not found. Please ensure wkhtmltopdf is installed.", "danger")
        return redirect(url_for('teacher_dashboard'))


@app.route('/export_overall_pdf', methods=['POST'])
@login_required
def export_overall_pdf():
    if current_user.role != 'teacher': 
        return "Unauthorized", 403

    subject = request.form.get('subject')
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')

    # Convert strings to datetime objects
    start_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1, seconds=-1)

    # 1. Get total sessions conducted
    total_sess_query = AttendanceSession.query.filter(
        AttendanceSession.teacher_id == current_user.id,
        AttendanceSession.start_time.between(start_dt, end_dt)
    )
    if subject != 'ALL':
        total_sess_query = total_sess_query.filter_by(subject=subject)
    
    total_lectures = total_sess_query.count()

    if total_lectures == 0:
        flash("No sessions found to generate PDF.", "warning")
        return redirect(url_for('teacher_dashboard'))

    # 2. Query Student Cumulative Data
    attendance_subquery = db.session.query(
        AttendanceRecord.student_id,
        func.count(AttendanceRecord.id).label('present_count')
    ).join(AttendanceSession).filter(
        AttendanceSession.teacher_id == current_user.id,
        AttendanceSession.start_time.between(start_dt, end_dt)
    )
    if subject != 'ALL':
        attendance_subquery = attendance_subquery.filter(AttendanceSession.subject == subject)
    
    attendance_subquery = attendance_subquery.group_by(AttendanceRecord.student_id).subquery()

    results = db.session.query(
        User.username,
        func.coalesce(attendance_subquery.c.present_count, 0)
    ).filter(User.role == 'student')\
     .outerjoin(attendance_subquery, User.id == attendance_subquery.c.student_id).all()

    # 3. Format data for the PDF Template
    report_list = []
    for username, count in results:
        percentage = round((count / total_lectures) * 100, 2)
        report_list.append({
            "name": username,
            "count": count,
            "total": total_lectures,
            "perc": percentage
        })

    # 4. Render HTML and Convert
    html = render_template('pdf_cumulative_report.html', 
                           data=report_list, 
                           subject=subject, 
                           start=start_date_str, 
                           end=end_date_str,
                           faculty=current_user.username)
    
    try:
        pdf = pdfkit.from_string(html, False, configuration=config)
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=Overall_Report_{subject}.pdf'
        return response
    except OSError:
        flash("PDF Engine error. Check wkhtmltopdf installation.", "danger")
        return redirect(url_for('teacher_dashboard'))

@app.route('/delete_sessions', methods=['POST'])
@login_required
def delete_sessions():
    if current_user.role != 'teacher':
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    data = request.get_json()
    session_ids = data.get('session_ids', [])

    try:
        # Delete related attendance records first
        AttendanceRecord.query.filter(AttendanceRecord.session_id.in_(session_ids)).delete(synchronize_session=False)
        
        # Delete the sessions
        AttendanceSession.query.filter(
            AttendanceSession.id.in_(session_ids),
            AttendanceSession.teacher_id == current_user.id
        ).delete(synchronize_session=False)
        
        db.session.commit()
        return jsonify({"success": True, "message": f"Deleted {len(session_ids)} sessions."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/manage_students', methods=['POST'])
@login_required
def manage_students():
    if current_user.role != 'teacher':
        return jsonify({"success": False, "message": "Unauthorized"}), 403
        
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        flash("Username and password are required.", "danger")
        return redirect(url_for('teacher_dashboard', tab='students'))

    # Check if user already exists
    if User.query.filter_by(username=username).first():
        flash("Username already exists.", "warning")
    else:
        new_student = User(username=username, password=password, role='student')
        db.session.add(new_student)
        db.session.commit()
        flash(f"Student '{username}' added successfully!", "success")
        
    return redirect(url_for('teacher_dashboard', tab='students'))


@app.route('/delete_student/<int:student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    if current_user.role != 'teacher':
        return jsonify({"success": False, "message": "Unauthorized"}), 403
        
    student = User.query.get_or_404(student_id)
    if student.role == 'student':
        # Optional: Delete their attendance records first to avoid foreign key errors
        AttendanceRecord.query.filter_by(student_id=student_id).delete()
        db.session.delete(student)
        db.session.commit()
        flash("Student account deleted.", "info")
    
    return redirect(url_for('teacher_dashboard', tab='students'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))
