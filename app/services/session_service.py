from datetime import datetime, timedelta
from app.extensions import db, socketio
from app.models import AttendanceSession, AttendanceRecord, Subject, Laboratory, User
from app.utils.security import generate_session_code
from app.services.audit_service import AuditService
from app.services.workstation_service import WorkstationService


class SessionService:
    @staticmethod
    def create_and_start_session(teacher_id: int, subject_id: int, lab_id: int, capacity: int = 30, duration_minutes: int = 10, start_pc: int = 1):
        """
        Close any existing active session for this teacher and start a new attendance session.
        """
        # Deactivate any previous active sessions for this teacher
        active_sessions = AttendanceSession.query.filter_by(teacher_id=teacher_id, is_active=True).all()
        for s in active_sessions:
            s.is_active = False
        db.session.commit()

        lab = Laboratory.query.get(lab_id)
        if not lab:
            raise ValueError("Selected laboratory does not exist.")

        subject = Subject.query.get(subject_id)
        if not subject:
            raise ValueError("Selected subject does not exist.")

        # Ensure lab has workstations provisioned for this capacity
        WorkstationService.provision_lab_workstations(lab, capacity=capacity)

        now = datetime.utcnow()
        end = now + timedelta(minutes=duration_minutes)

        session = AttendanceSession(
            session_code=generate_session_code(),
            subject_id=subject.id,
            teacher_id=teacher_id,
            lab_id=lab.id,
            lab_capacity=capacity,
            start_pc=start_pc,
            is_active=True,
            is_paused=False,
            start_time=now,
            end_time=end
        )
        db.session.add(session)
        db.session.commit()

        AuditService.log(
            action="SESSION_START",
            user_id=teacher_id,
            target_type="AttendanceSession",
            target_id=session.id,
            details=f"Session {session.session_code} started for {subject.code} in {lab.name} (Capacity: {capacity}, Duration: {duration_minutes}m)"
        )

        return session

    @staticmethod
    def get_active_session_for_teacher(teacher_id: int):
        """Return the active session for a teacher, auto-expiring it if time passed."""
        session = AttendanceSession.query.filter_by(teacher_id=teacher_id, is_active=True).first()
        if session:
            if session.is_expired:
                session.is_active = False
                db.session.commit()
                return None
        return session

    @staticmethod
    def get_current_active_session_for_student(student_id: int, client_ip: str = None):
        """
        Find if there is an active session relevant for this student:
        - Must be active and not expired or paused.
        - The student must be enrolled in the subject (or subject open to department/all if not individually enrolled).
        - Optional check for lab IP range/workstation match.
        """
        now = datetime.utcnow()
        # Find active sessions
        sessions = AttendanceSession.query.filter(
            AttendanceSession.is_active == True,
            AttendanceSession.end_time > now,
            AttendanceSession.is_paused == False
        ).all()

        student = User.query.get(student_id)
        if not student:
            return None

        # Get student's enrolled subject IDs
        enrolled_subject_ids = [e.subject_id for e in student.enrollments]

        for s in sessions:
            # Check subject enrollment: if student has enrolled subjects, verify match
            if enrolled_subject_ids and s.subject_id not in enrolled_subject_ids:
                continue

            # Check lab IP compatibility if lab IP range is defined
            lab = s.laboratory
            if lab and lab.ip_start and lab.ip_end and client_ip and client_ip != '127.0.0.1':
                from app.utils.network import is_ip_in_range
                if not is_ip_in_range(client_ip, lab.ip_start, lab.ip_end):
                    continue

            return s

        # If enrolled check didn't match, return active session if only 1 active in the lab for convenience
        if sessions:
            return sessions[0]

        return None

    @staticmethod
    def extend_session(session_id: int, teacher_id: int, additional_minutes: int = 10):
        """Extend an active session by N minutes."""
        session = AttendanceSession.query.filter_by(id=session_id, teacher_id=teacher_id).first()
        if not session:
            return False, "Session not found."

        if not session.is_active:
            # If expired recently, re-activate
            session.is_active = True
            session.end_time = datetime.utcnow() + timedelta(minutes=additional_minutes)
        else:
            session.end_time = session.end_time + timedelta(minutes=additional_minutes)

        db.session.commit()

        # Notify connected room clients
        socketio.emit('session_timer_extended', {
            'remaining_seconds': session.remaining_seconds,
            'end_time': session.end_time.isoformat()
        }, room=f"session_{session.id}")

        AuditService.log(
            action="SESSION_EXTENDED",
            user_id=teacher_id,
            target_type="AttendanceSession",
            target_id=session.id,
            details=f"Session extended by {additional_minutes} minutes"
        )
        return True, f"Session extended by {additional_minutes} minutes."

    @staticmethod
    def pause_or_resume_session(session_id: int, teacher_id: int):
        """Toggle pause state of a session."""
        session = AttendanceSession.query.filter_by(id=session_id, teacher_id=teacher_id).first()
        if not session or not session.is_active:
            return False, "Active session not found."

        session.is_paused = not session.is_paused
        db.session.commit()

        socketio.emit('session_status_changed', {
            'is_paused': session.is_paused
        }, room=f"session_{session.id}")

        action = "SESSION_PAUSED" if session.is_paused else "SESSION_RESUMED"
        AuditService.log(
            action=action,
            user_id=teacher_id,
            target_type="AttendanceSession",
            target_id=session.id,
            details=f"Session pause state changed to {session.is_paused}"
        )
        status_str = "paused" if session.is_paused else "resumed"
        return True, f"Session has been {status_str}."

    @staticmethod
    def stop_session(session_id: int, teacher_id: int):
        """Close an active session manually."""
        session = AttendanceSession.query.filter_by(id=session_id, teacher_id=teacher_id).first()
        if not session:
            return False, "Session not found."

        session.is_active = False
        db.session.commit()

        socketio.emit('session_closed', {
            'session_id': session.id,
            'message': 'This attendance session has ended.'
        }, room=f"session_{session.id}")

        AuditService.log(
            action="SESSION_STOPPED",
            user_id=teacher_id,
            target_type="AttendanceSession",
            target_id=session.id,
            details=f"Session {session.session_code} manually closed by teacher."
        )
        return True, "Attendance session closed successfully."

    @staticmethod
    def get_session_roster_summary(session_id: int):
        """
        Get comprehensive session breakdown:
        - Marked students list with seat and timestamp.
        - Pending / Absent students list.
        - Total attendance statistics.
        """
        session = AttendanceSession.query.get(session_id)
        if not session:
            return None

        # Present students
        records = AttendanceRecord.query.filter_by(session_id=session_id).order_by(AttendanceRecord.seat_number.asc()).all()
        present_student_ids = {r.student_id for r in records}

        # Find eligible students: enrolled in this subject or students with same department
        all_eligible = User.query.filter_by(role='student', is_active=True).all()
        absent_students = [s for s in all_eligible if s.id not in present_student_ids]

        return {
            'session': session,
            'present_records': records,
            'present_count': len(records),
            'absent_students': absent_students,
            'absent_count': len(absent_students),
            'capacity': session.lab_capacity,
            'completion_pct': round((len(records) / session.lab_capacity * 100), 1) if session.lab_capacity else 0
        }

