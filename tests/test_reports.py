from app.services.session_service import SessionService
from app.services.attendance_service import AttendanceService
from app.services.report_service import ReportService
from app.models import StudentEnrollment
import openpyxl


def test_at_risk_and_overall_stats(db, test_teacher, test_subject, test_lab, test_student, test_student_2):
    # Enroll both students
    db.session.add(StudentEnrollment(student_id=test_student.id, subject_id=test_subject.id))
    db.session.add(StudentEnrollment(student_id=test_student_2.id, subject_id=test_subject.id))
    db.session.commit()

    # Create 4 sessions
    for i in range(4):
        sess = SessionService.create_and_start_session(
            teacher_id=test_teacher.id,
            subject_id=test_subject.id,
            lab_id=test_lab.id,
            capacity=30,
            duration_minutes=10
        )
        # Student 1 attends all 4 sessions (100%)
        AttendanceService.mark_attendance(test_student, "192.168.1.1", session_id=sess.id)

        # Student 2 only attends 1 session (25% -> At-Risk!)
        if i == 0:
            AttendanceService.mark_attendance(test_student_2, "192.168.1.2", session_id=sess.id)

        # Finalize/close each session
        SessionService.stop_session(sess.id, test_teacher.id)

    # Check at-risk
    at_risk = ReportService.get_at_risk_students(teacher_id=test_teacher.id, threshold=75.0)
    assert len(at_risk) == 1
    assert at_risk[0]['username'] == test_student_2.username
    assert at_risk[0]['percentage'] == 25.0

    # Check student overall stats
    stats1 = ReportService.get_student_overall_stats(test_student.id)
    assert stats1['overall_percentage'] == 100.0
    assert stats1['total_attended'] == 4

    stats2 = ReportService.get_student_overall_stats(test_student_2.id)
    assert stats2['overall_percentage'] == 25.0
    assert stats2['total_attended'] == 1
    assert stats2['absent_count'] == 3


def test_excel_export_generation(db, test_teacher, test_subject, test_lab, test_student):
    db.session.add(StudentEnrollment(student_id=test_student.id, subject_id=test_subject.id))
    db.session.commit()

    sess = SessionService.create_and_start_session(
        teacher_id=test_teacher.id,
        subject_id=test_subject.id,
        lab_id=test_lab.id,
        capacity=30,
        duration_minutes=10
    )
    AttendanceService.mark_attendance(test_student, "192.168.1.5", session_id=sess.id)

    # Generate Excel
    excel_stream = ReportService.generate_excel_session_report(sess.id, test_teacher)
    assert excel_stream is not None

    wb = openpyxl.load_workbook(excel_stream)
    assert "Lab Attendance" in wb.sheetnames
    ws = wb["Lab Attendance"]
    assert "LAB-SECURE" in ws["A1"].value


def test_student_personal_export_route(client, test_student):
    client.post('/login', data={'username': test_student.username, 'password': 'StudentTestPassword!123'})
    res = client.get('/student/export_personal')
    assert res.status_code == 200
    assert res.headers['Content-Disposition'].startswith('attachment')
    assert res.data[:2] == b'PK'  # ZIP / xlsx magic header


