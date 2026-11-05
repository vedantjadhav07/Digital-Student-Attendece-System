from datetime import datetime, timedelta
from app.services.session_service import SessionService
from app.services.attendance_service import AttendanceService
from app.models import StudentEnrollment, AttendanceRecord


def test_attendance_lifecycle(db, test_teacher, test_subject, test_lab, test_student, test_student_2):
    # 1. Enroll students in test_subject
    db.session.add(StudentEnrollment(student_id=test_student.id, subject_id=test_subject.id))
    db.session.add(StudentEnrollment(student_id=test_student_2.id, subject_id=test_subject.id))
    db.session.commit()

    # 2. Start session
    session = SessionService.create_and_start_session(
        teacher_id=test_teacher.id,
        subject_id=test_subject.id,
        lab_id=test_lab.id,
        capacity=30,
        duration_minutes=15
    )
    assert session.is_active is True
    assert session.remaining_seconds > 0

    # 3. Mark attendance successfully for student 1 from Seat #5
    res1 = AttendanceService.mark_attendance(
        student=test_student,
        client_ip="192.168.1.5",
        session_id=session.id
    )
    assert res1.success is True
    assert res1.record is not None
    assert res1.record.seat_number == 5

    # 4. Duplicate attendance prevention: Student 1 tries to mark again
    res_dup_student = AttendanceService.mark_attendance(
        student=test_student,
        client_ip="192.168.1.6",
        session_id=session.id
    )
    assert res_dup_student.success is False
    assert res_dup_student.status_code == 409
    assert "already marked" in res_dup_student.message.lower()

    # 5. Workstation collision prevention: Student 2 tries to claim Seat #5
    res_dup_seat = AttendanceService.mark_attendance(
        student=test_student_2,
        client_ip="192.168.1.5",
        session_id=session.id
    )
    assert res_dup_seat.success is False
    assert res_dup_seat.status_code == 409
    assert "already been claimed" in res_dup_seat.message.lower()

    # 6. Student 2 marks at unoccupied Seat #6 successfully
    res2 = AttendanceService.mark_attendance(
        student=test_student_2,
        client_ip="192.168.1.6",
        session_id=session.id
    )
    assert res2.success is True
    assert res2.record.seat_number == 6


def test_paused_session_rejection(db, test_teacher, test_subject, test_lab, test_student):
    db.session.add(StudentEnrollment(student_id=test_student.id, subject_id=test_subject.id))
    db.session.commit()

    session = SessionService.create_and_start_session(
        teacher_id=test_teacher.id,
        subject_id=test_subject.id,
        lab_id=test_lab.id,
        capacity=30,
        duration_minutes=15
    )

    # Pause session
    SessionService.pause_or_resume_session(session.id, test_teacher.id)

    res = AttendanceService.mark_attendance(
        student=test_student,
        client_ip="192.168.1.10",
        session_id=session.id
    )
    assert res.success is False
    assert res.status_code == 403
    assert "paused" in res.message.lower()


def test_expired_session_rejection(db, test_teacher, test_subject, test_lab, test_student):
    db.session.add(StudentEnrollment(student_id=test_student.id, subject_id=test_subject.id))
    db.session.commit()

    session = SessionService.create_and_start_session(
        teacher_id=test_teacher.id,
        subject_id=test_subject.id,
        lab_id=test_lab.id,
        capacity=30,
        duration_minutes=15
    )

    # Expire session manually
    session.end_time = datetime.utcnow() - timedelta(minutes=1)
    db.session.commit()

    res = AttendanceService.mark_attendance(
        student=test_student,
        client_ip="192.168.1.10",
        session_id=session.id
    )
    assert res.success is False
    assert res.status_code == 400


def test_not_enrolled_student_rejection(db, test_teacher, test_subject, test_lab, test_student, test_department):
    from app.models import Subject
    # Create another subject where student is enrolled
    other_sub = Subject(name="Physics Lab", code="PH101", department_id=test_department.id, is_active=True)
    db.session.add(other_sub)
    db.session.commit()
    # Student enrolled in PH101, NOT in test_subject
    db.session.add(StudentEnrollment(student_id=test_student.id, subject_id=other_sub.id))
    db.session.commit()

    session = SessionService.create_and_start_session(
        teacher_id=test_teacher.id,
        subject_id=test_subject.id,
        lab_id=test_lab.id,
        capacity=30,
        duration_minutes=15
    )

    res = AttendanceService.mark_attendance(
        student=test_student,
        client_ip="192.168.1.10",
        session_id=session.id
    )
    assert res.success is False
    assert res.status_code == 403
    assert "not enrolled" in res.message.lower()

