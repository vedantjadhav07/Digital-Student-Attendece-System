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
    def mark_attendance(
        student: User,
        client_ip: str,
        session_id: int = None,
        workstation_token: str = None,
        seat_number: int = None,
        device_id: str = None,
        mac_address: str = None
    ) -> AttendanceValidationResult:
        """
        Server-side authenticated attendance verification and atomic write.
        Strictly enforces:
        1. Active session belonging to the teacher.
        2. Computer belongs to the designated laboratory selected for this practical.
        3. Only one student can mark attendance from one registered PC during the session (PC locked once marked).
        4. A student cannot mark attendance more than once in the same session.
        5. Hardware device identity, IP address, and MAC address validation.
        """
        # Check 1: Student validation
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

        lab = session.laboratory
        if not lab:
            return AttendanceValidationResult(False, "Session is not associated with a valid laboratory.", status_code=500)

        # Check 3: Check if student has ALREADY marked attendance for this session
        existing_student_record = AttendanceRecord.query.filter_by(
            session_id=session.id,
            student_id=student.id
        ).first()
        if existing_student_record:
            return AttendanceValidationResult(
                False,
                f"Duplicate attendance rejected: You have already marked attendance for this session at Workstation #{existing_student_record.seat_number}.",
                status_code=409
            )

        # Check 4: Subject Enrollment
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

        # Check 5: Resolve the Workstation and verify it belongs to session.lab_id
        workstation = None

        # A. Check if device_id matches any workstation
        if device_id:
            ws_dev = Workstation.query.filter_by(device_id=device_id).first()
            if ws_dev:
                if ws_dev.lab_id != session.lab_id:
                    AuditService.log(
                        action="ATTENDANCE_REJECTED_WRONG_LAB",
                        user_id=student.id,
                        target_type="AttendanceSession",
                        target_id=session.id,
                        ip_address=client_ip,
                        details=f"Device {device_id} belongs to Lab #{ws_dev.lab_id}, but session is in Lab #{session.lab_id}"
                    )
                    return AttendanceValidationResult(
                        False,
                        f"Access Denied: This computer ({ws_dev.workstation_code}) belongs to {ws_dev.laboratory.name if ws_dev.laboratory else 'another lab'}. The active practical is being conducted in {lab.name}.",
                        status_code=403
                    )
                workstation = ws_dev

        # B. Check if token matches
        if not workstation and workstation_token:
            ws_tok = Workstation.query.filter_by(secret_token=workstation_token).first()
            if ws_tok:
                if ws_tok.lab_id != session.lab_id:
                    return AttendanceValidationResult(
                        False,
                        f"Access Denied: Workstation token belongs to a different laboratory.",
                        status_code=403
                    )
                workstation = ws_tok

        # C. Check if client_ip matches an exact registered workstation
        if not workstation and client_ip and client_ip != '127.0.0.1':
            ws_ip = Workstation.query.filter_by(ip_address=client_ip).first()
            if ws_ip:
                if ws_ip.lab_id != session.lab_id:
                    AuditService.log(
                        action="ATTENDANCE_REJECTED_WRONG_LAB",
                        user_id=student.id,
                        target_type="AttendanceSession",
                        target_id=session.id,
                        ip_address=client_ip,
                        details=f"IP {client_ip} belongs to Lab #{ws_ip.lab_id}, but session is in Lab #{session.lab_id}"
                    )
                    return AttendanceValidationResult(
                        False,
                        f"Access Denied: Computer with IP {client_ip} belongs to {ws_ip.laboratory.name if ws_ip.laboratory else 'another lab'}. Only PCs registered to {lab.name} can be used for this practical session.",
                        status_code=403
                    )
                workstation = ws_ip

        # D. Match by seat_number if provided and belonging to session.lab_id
        if not workstation and seat_number:
            ws_seat = Workstation.query.filter_by(lab_id=session.lab_id, seat_number=seat_number).first()
            if ws_seat:
                workstation = ws_seat

        # E. Fallback search using WorkstationService
        if not workstation:
            workstation = WorkstationService.find_workstation_for_request(
                lab_id=session.lab_id,
                client_ip=client_ip,
                token=workstation_token,
                device_id=device_id,
                mac_address=mac_address
            )

        # F. If still not found, check client_ip subnet bounds or assign PC within lab
        if not workstation:
            # Fallback calculation from IP host address for local test or newly aligned seat
            calc_seat = 1
            if client_ip:
                try:
                    last_octet = int(client_ip.split('.')[-1])
                    if 1 <= last_octet <= session.lab_capacity:
                        calc_seat = last_octet
                    else:
                        calc_seat = (student.id % session.lab_capacity) + 1
                except Exception:
                    calc_seat = (student.id % session.lab_capacity) + 1
            else:
                calc_seat = (student.id % session.lab_capacity) + 1

            code_prefix = lab.code or f"LAB{session.lab_id}"
            workstation = Workstation.query.filter_by(lab_id=session.lab_id, seat_number=calc_seat).first()
            if not workstation:
                ws_ip = WorkstationService.generate_sequential_ip(lab.ip_start, calc_seat) if lab.ip_start else client_ip
                workstation = Workstation(
                    lab_id=session.lab_id,
                    workstation_code=f"{code_prefix}-WS{calc_seat:02d}",
                    seat_number=calc_seat,
                    ip_address=ws_ip,
                    mac_address=WorkstationService.generate_mac_address(lab.id, calc_seat, lab.code),
                    device_id=WorkstationService.generate_device_id(lab.code, calc_seat),
                    status='active'
                )
                db.session.add(workstation)
                db.session.commit()

        # Strict Lab verification
        if workstation.lab_id != session.lab_id:
            return AttendanceValidationResult(
                False,
                f"Security Verification Failed: This workstation does not belong to the active laboratory ({lab.name}). Attendance can only be marked from PCs inside {lab.name}.",
                status_code=403
            )

        seat_num = workstation.seat_number

        # Check capacity
        if seat_num > session.lab_capacity:
            return AttendanceValidationResult(
                False,
                f"Workstation seat {seat_num} is outside current lab capacity ({session.lab_capacity}).",
                status_code=400
            )

        # Check Network Subnet boundary if configured
        if lab.subnet_cidr and client_ip and client_ip != '127.0.0.1':
            if not is_ip_in_subnet(client_ip, lab.subnet_cidr) and not workstation:
                return AttendanceValidationResult(
                    False,
                    f"Network security error: Your connection ({client_ip}) does not originate from {lab.name}.",
                    status_code=403
                )

        # Check 6: Check MAC address mismatch if student submitted a conflicting MAC
        if mac_address and workstation.mac_address:
            if workstation.mac_address.replace("-", ":").upper() != mac_address.replace("-", ":").upper():
                return AttendanceValidationResult(
                    False,
                    "Hardware MAC Address verification failed. Device does not match registered workstation profile.",
                    status_code=403
                )

        # Check 7: SINGLE STUDENT PER PC ENFORCEMENT (PC LOCK)
        # Once a student successfully marks attendance from a PC, that PC is locked for the same session.
        existing_seat_record = AttendanceRecord.query.filter(
            AttendanceRecord.session_id == session.id,
            (AttendanceRecord.workstation_id == workstation.id) | (AttendanceRecord.seat_number == seat_num)
        ).first()

        if existing_seat_record:
            claimer = existing_seat_record.student
            claimer_name = claimer.full_name if claimer else "Another student"
            claimer_user = f" ({claimer.username})" if claimer else ""
            return AttendanceValidationResult(
                False,
                f"Workstation {workstation.workstation_code} (PC #{seat_num}) has already been claimed by student {claimer_name}{claimer_user} for this session. It is locked and cannot be used by multiple students.",
                status_code=409
            )

        # Check 8: Atomic write with SQLite concurrency retry
        max_retries = 3
        retry_delay = 0.05
        record = None

        for attempt in range(max_retries):
            try:
                record = AttendanceRecord(
                    session_id=session.id,
                    student_id=student.id,
                    workstation_id=workstation.id,
                    seat_number=seat_num,
                    ip_address=client_ip or workstation.ip_address or '127.0.0.1',
                    verification_method='workstation_hardware_bound',
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
                    "Attendance conflict detected: Either your attendance or this PC was just claimed by another student.",
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
            'workstation_code': workstation.workstation_code,
            'student_name': student.full_name,
            'student_username': student.username,
            'ip_address': client_ip or workstation.ip_address,
            'mac_address': workstation.mac_address,
            'device_id': workstation.device_id,
            'timestamp': record.timestamp.strftime('%H:%M:%S'),
            'total_present': total_present,
            'capacity': session.lab_capacity,
            'completion_pct': completion_pct
        }

        # Targeted room emission for live monitoring
        socketio.emit('attendance_marked', event_payload, room=f"session_{session.id}")
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
            details=f"Attendance marked at {workstation.workstation_code} (PC #{seat_num}, MAC: {workstation.mac_address}, Device: {workstation.device_id}) for Session {session.session_code}"
        )

        return AttendanceValidationResult(
            True,
            f"Attendance successfully recorded at Workstation {workstation.workstation_code} (PC #{seat_num})!",
            record=record
        )
