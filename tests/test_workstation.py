from app.models import Laboratory, Workstation, StudentEnrollment
from app.services.workstation_service import WorkstationService
from app.services.session_service import SessionService
from app.services.attendance_service import AttendanceService
from app.utils.network import is_ip_in_range, is_ip_in_subnet


def test_ip_range_validation():
    assert is_ip_in_range("192.168.1.15", "192.168.1.1", "192.168.1.30") is True
    assert is_ip_in_range("192.168.1.1", "192.168.1.1", "192.168.1.30") is True
    assert is_ip_in_range("192.168.1.30", "192.168.1.1", "192.168.1.30") is True
    assert is_ip_in_range("192.168.1.31", "192.168.1.1", "192.168.1.30") is False
    assert is_ip_in_range("10.0.0.5", "192.168.1.1", "192.168.1.30") is False


def test_subnet_validation():
    assert is_ip_in_subnet("192.168.1.55", "192.168.1.0/24") is True
    assert is_ip_in_subnet("192.168.2.55", "192.168.1.0/24") is False


def test_workstation_provisioning(db):
    lab = Laboratory(name="Test Lab A", code="TLA", ip_start="10.0.1.1", default_capacity=30)
    db.session.add(lab)
    db.session.commit()

    created = WorkstationService.provision_lab_workstations(lab, capacity=30)
    assert created == 30

    workstations = Workstation.query.filter_by(lab_id=lab.id).order_by(Workstation.seat_number.asc()).all()
    assert len(workstations) == 30
    assert workstations[0].workstation_code == "TLA-WS01"
    assert workstations[0].ip_address == "10.0.1.1"
    assert workstations[29].workstation_code == "TLA-WS30"
    assert workstations[29].ip_address == "10.0.1.30"
    assert workstations[0].secret_token is not None
    assert workstations[0].mac_address is not None
    assert workstations[0].device_id is not None
    assert workstations[0].mac_address.startswith("02:")
    assert "DEV-TLA-PC01" in workstations[0].device_id


def test_sequential_ip_generation_127_0_0_1(db):
    """Admin enters 127.0.0.1 and capacity 30 -> generates 30 sequential IPs changing last octet."""
    lab = Laboratory(
        name="Local Virtual Lab",
        code="LVL",
        location="Computer Center",
        room_number="Room 101",
        ip_start="127.0.0.1",
        default_capacity=30
    )
    db.session.add(lab)
    db.session.commit()

    created = WorkstationService.provision_lab_workstations(lab, capacity=30)
    assert created == 30
    assert lab.ip_end == "127.0.0.30"

    pcs = Workstation.query.filter_by(lab_id=lab.id).order_by(Workstation.seat_number.asc()).all()
    for i, pc in enumerate(pcs):
        expected_ip = f"127.0.0.{i + 1}"
        assert pc.ip_address == expected_ip
        assert pc.mac_address is not None
        assert pc.device_id.startswith("DEV-LVL-PC")


def test_find_workstation(db, test_lab):
    # Find by exact IP
    ws = WorkstationService.find_workstation_for_request(lab_id=test_lab.id, client_ip="192.168.1.5")
    assert ws is not None
    assert ws.seat_number == 5

    # Find by token
    token = ws.secret_token
    ws_by_token = WorkstationService.find_workstation_for_request(lab_id=test_lab.id, client_ip="10.0.0.1", token=token)
    assert ws_by_token is not None
    assert ws_by_token.id == ws.id


def test_cross_laboratory_isolation_and_pc_lock(db, test_teacher, test_subject, test_student, test_student_2):
    """
    Verifies:
    1. Only PCs registered to the teacher's selected laboratory can mark attendance.
    2. PCs from other laboratories are rejected.
    3. Once marked, that PC is locked for that session; second student cannot mark from it.
    """
    # Create Lab A and Lab B
    lab_a = Laboratory(name="Lab Alpha", code="LA", ip_start="192.168.10.1", default_capacity=10)
    lab_b = Laboratory(name="Lab Beta", code="LB", ip_start="192.168.20.1", default_capacity=10)
    db.session.add_all([lab_a, lab_b])
    db.session.commit()

    WorkstationService.provision_lab_workstations(lab_a, capacity=10)
    WorkstationService.provision_lab_workstations(lab_b, capacity=10)

    # Enroll students
    db.session.add(StudentEnrollment(student_id=test_student.id, subject_id=test_subject.id))
    db.session.add(StudentEnrollment(student_id=test_student_2.id, subject_id=test_subject.id))
    db.session.commit()

    # Teacher starts session in Lab Alpha
    session = SessionService.create_and_start_session(
        teacher_id=test_teacher.id,
        subject_id=test_subject.id,
        lab_id=lab_a.id,
        capacity=10,
        duration_minutes=10
    )

    pc_lab_b = Workstation.query.filter_by(lab_id=lab_b.id, seat_number=1).first()

    # Attempt to mark attendance using PC from Lab Beta in Lab Alpha session -> MUST BE REJECTED
    res_wrong_lab = AttendanceService.mark_attendance(
        student=test_student,
        client_ip=pc_lab_b.ip_address,
        session_id=session.id,
        device_id=pc_lab_b.device_id
    )
    assert res_wrong_lab.success is False
    assert res_wrong_lab.status_code == 403
    assert "belongs to" in res_wrong_lab.message.lower() or "different laboratory" in res_wrong_lab.message.lower()

    # Student 1 marks attendance at Lab Alpha PC #1 -> SUCCESS
    pc_lab_a = Workstation.query.filter_by(lab_id=lab_a.id, seat_number=1).first()
    res_correct_lab = AttendanceService.mark_attendance(
        student=test_student,
        client_ip=pc_lab_a.ip_address,
        session_id=session.id,
        device_id=pc_lab_a.device_id
    )
    assert res_correct_lab.success is True
    assert res_correct_lab.record.seat_number == 1

    # Student 2 tries to use PC #1 in Lab Alpha -> MUST BE REJECTED (PC LOCKED)
    res_locked_pc = AttendanceService.mark_attendance(
        student=test_student_2,
        client_ip=pc_lab_a.ip_address,
        session_id=session.id,
        device_id=pc_lab_a.device_id
    )
    assert res_locked_pc.success is False
    assert res_locked_pc.status_code == 409
    assert "locked" in res_locked_pc.message.lower() or "already been claimed" in res_locked_pc.message.lower()


def test_teacher_can_fetch_laboratories(client, test_teacher, db):
    # Create a laboratory
    lab = Laboratory(name="Test Lab", code="TL01", ip_start="10.0.0.1", default_capacity=30)
    db.session.add(lab)
    db.session.commit()

    # Log in as teacher
    client.post('/login', data={'username': test_teacher.username, 'password': 'TeacherTestPassword!123'})

    # 1. Fetch via /api/teacher/laboratories
    res = client.get('/api/teacher/laboratories')
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1

    # 2. Fetch via /api/teacher/overview
    res_overview = client.get('/api/teacher/overview')
    assert res_overview.status_code == 200
    overview_data = res_overview.get_json()
    assert 'laboratories' in overview_data
    assert len(overview_data['laboratories']) >= 1

    # 3. GET /api/admin/laboratories also permits teachers
    res_admin_lab = client.get('/api/admin/laboratories')
    assert res_admin_lab.status_code == 200
    assert len(res_admin_lab.get_json()) >= 1
