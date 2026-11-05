import time
import logging
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError
from app.extensions import db, socketio
from app.models import User, AttendanceSession, AttendanceRecord, Workstation, StudentEnrollment
from app.services.workstation_service import WorkstationService
from app.services.audit_service import AuditService
from app.utils.network import is_ip_in_range, is_ip_in_subnet

logger = logging.getLogger(__name__)


class AttendanceValidationResult:
    def __init__(self, success: bool, message: str, record: AttendanceRecord = None, status_code: int = 200):
        self.success = success
        self.message = message
        self.record = record
        self.status_code = status_code

    def to_dict(self):
        return {
            'success': self.success,
            'message': self.message,
            'seat_number': self.record.seat_number if self.record else None,
            'timestamp': self.record.timestamp.strftime('%H:%M:%S') if self.record else None
        }


class AttendanceService:
    @staticmethod
    def mark_attendance(student: User, client_ip: str, session_id: int = None, workstation_token: str = None) -> AttendanceValidationResult:
        """
        Server-side authenticated attendance verification and atomic write.
        Executes strict checks 1 through 9.
        """
        # Check 1: Student verification
        if not student or not student.is_active or student.role != 'student':
            return AttendanceValidationResult(False, "Unauthorized: Valid active student account required.", status_code=403)

        # Check 2: Active session resolution
        session = None
        if session_id:
            session = AttendanceSession.query.get(session_id)
        else:
            now = datetime.utcnow()
            session = AttendanceSession.query.filter(
                AttendanceSession.is_active == True,
                AttendanceSession.end_time > now,
                AttendanceSession.is_paused == False
            ).first()

        if not session or not session.is_active or session.is_expired:
            return AttendanceValidationResult(False, "No active attendance session currently open.", status_code=400)

        if session.is_paused:
            return AttendanceValidationResult(False, "Attendance submission is currently paused by faculty.", status_code=403)

        # Check 3 & 4: Workstation & Network verification
        lab = session.laboratory
        workstation = WorkstationService.find_workstation_for_request(
            lab_id=session.lab_id,
            client_ip=client_ip,
            token=workstation_token
        )

        # Check network IP boundary if lab configured
        if lab and client_ip and client_ip != '127.0.0.1':
            in_range = True
            if lab.ip_start and lab.ip_end:
                in_range = is_ip_in_range(client_ip, lab.ip_start, lab.ip_end)
            elif lab.subnet_cidr:
                in_range = is_ip_in_subnet(client_ip, lab.subnet_cidr)

            # In development/local, allow if loopback or workstation registered
            if not in_range and not workstation and not workstation_token:
                AuditService.log(
                    action="ATTENDANCE_REJECTED_NETWORK",
                    user_id=student.id,
                    target_type="AttendanceSession",
                    target_id=session.id,
                    ip_address=client_ip,
                    details=f"IP {client_ip} outside permitted range for {lab.name}"
                )
                return AttendanceValidationResult(
                    False,
                    f"Network security error: Your connection ({client_ip}) does not originate from {lab.name}.",
                    status_code=403
                )

        # Calculate or assign seat number
        seat_num = None
        if workstation:
            seat_num = workstation.seat_number
        else:
            # Fallback calculation from IP host address
            try:
                last_octet = int(client_ip.split('.')[-1])
                seat_num = last_octet if (1 <= last_octet <= session.lab_capacity) else (student.id % session.lab_capacity) + 1
            except Exception:
                seat_num = (student.id % session.lab_capacity) + 1

            # Ensure or create a workstation record for this seat
            code_prefix = lab.code if lab and lab.code else f"LAB{session.lab_id}"
            workstation = Workstation.query.filter_by(lab_id=session.lab_id, seat_number=seat_num).first()
            if not workstation:
                workstation = Workstation(
                    lab_id=session.lab_id,
                    workstation_code=f"{code_prefix}-WS{seat_num:02d}",
                    seat_number=seat_num,
                    ip_address=client_ip,
                    status='active'
                )
                db.session.add(workstation)
                db.session.commit()

        # Check 5: Workstation within session capacity
        if seat_num > session.lab_capacity:
            return AttendanceValidationResult(
                False,
                f"Workstation seat {seat_num} is outside current lab capacity ({session.lab_capacity}).",
                status_code=400
            )

        # Check 6: Subject Enrollment
        has_enrollments = StudentEnrollment.query.filter_by(student_id=student.id).count() > 0
        if has_enrollments:
            is_enrolled = StudentEnrollment.query.filter_by(student_id=student.id, subject_id=session.subject_id).first()
            if not is_enrolled:
                AuditService.log(
                    action="ATTENDANCE_REJECTED_NOT_ENROLLED",
                    user_id=student.id,
                    target_type="AttendanceSession",
                    target_id=session.id,
                    details=f"Student not enrolled in {session.subject.code}"
                )
                return AttendanceValidationResult(
                    False,
                    f"You are not enrolled in the subject '{session.subject.name}'.",
                    status_code=403
                )

        # Check 7: Duplicate student check
        existing_student_record = AttendanceRecord.query.filter_by(
            session_id=session.id,
            student_id=student.id
        ).first()
        if existing_student_record:
            return AttendanceValidationResult(
                False,
                f"You have already marked attendance for this session at Workstation #{existing_student_record.seat_number}.",
                status_code=409
            )

        # Check 8: Seat / Workstation collision check
        existing_seat_record = AttendanceRecord.query.filter_by(
            session_id=session.id,
            seat_number=seat_num
        ).first()
        if existing_seat_record:
            return AttendanceValidationResult(
                False,
                f"Workstation #{seat_num} has already been claimed by another student. Please use your assigned workstation.",
                status_code=409
            )

        # Check 9: Atomic write with SQLite concurrency retry
        max_retries = 3
        retry_delay = 0.05

        for attempt in range(max_retries):
            try:
                record = AttendanceRecord(
                    session_id=session.id,
                    student_id=student.id,
                    workstation_id=workstation.id if workstation else None,
                    seat_number=seat_num,
                    ip_address=client_ip,
                    verification_method='workstation_ip',
                    status='present',
                    timestamp=datetime.utcnow()
                )
                db.session.add(record)
                db.session.commit()
                break
            except IntegrityError:
                db.session.rollback()
                return AttendanceValidationResult(
                    False,
                    "Attendance conflict detected: Either your attendance or this workstation was just recorded.",
                    status_code=409
                )
            except OperationalError as oe:
                db.session.rollback()
                if "locked" in str(oe).lower() and attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                logger.error(f"Database operational error during attendance: {oe}")
                return AttendanceValidationResult(False, "Database is busy, please retry in a moment.", status_code=503)
            except Exception as ex:
                db.session.rollback()
                logger.error(f"Unexpected error in attendance write: {ex}")
                return AttendanceValidationResult(False, "Internal error processing attendance.", status_code=500)

        # Success: Broadcast real-time event to the specific session room
        total_present = AttendanceRecord.query.filter_by(session_id=session.id).count()
        completion_pct = round((total_present / session.lab_capacity * 100), 1) if session.lab_capacity else 0

        event_payload = {
            'seat_number': seat_num,
            'workstation_code': workstation.workstation_code if workstation else f"WS-{seat_num:02d}",
            'student_name': student.full_name,
            'student_username': student.username,
            'ip_address': client_ip,
            'timestamp': record.timestamp.strftime('%H:%M:%S'),
            'total_present': total_present,
            'capacity': session.lab_capacity,
            'completion_pct': completion_pct
        }

        # Targeted room emission
        socketio.emit('attendance_marked', event_payload, room=f"session_{session.id}")
        # Global fallback emission for backwards compatibility if needed
        socketio.emit('attendance_update', {
            'pc_number': str(seat_num),
            'student_name': student.username
        })

        AuditService.log(
            action="ATTENDANCE_MARKED",
            user_id=student.id,
            target_type="AttendanceRecord",
            target_id=record.id,
            ip_address=client_ip,
            details=f"Attendance marked at Seat #{seat_num} for Session {session.session_code}"
        )

        return AttendanceValidationResult(
            True,
            f"Attendance successfully recorded at Workstation #{seat_num}!",
            record=record
        )

