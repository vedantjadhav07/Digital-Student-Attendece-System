import pytest
from app import create_app
from app.extensions import db as _db
from app.models import User, Department, Subject, Laboratory, Workstation, TeacherSubject, StudentEnrollment


@pytest.fixture(scope='session')
def app():
    """Create application configured for testing."""
    _app = create_app('testing')
    return _app


@pytest.fixture(scope='function')
def db(app):
    """Create clean database per test function."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app, db):
    """Test client."""
    return app.test_client()


@pytest.fixture
def test_department(db):
    dept = Department(name="Computer Science & Engineering", code="CSE")
    db.session.add(dept)
    db.session.commit()
    return dept


@pytest.fixture
def test_admin(db, test_department):
    admin = User(
        username="admin_test",
        full_name="Admin Test",
        role="admin",
        password="AdminTestPassword!123"
    )
    db.session.add(admin)
    db.session.commit()
    return admin


@pytest.fixture
def test_teacher(db, test_department):
    teacher = User(
        username="faculty_test",
        full_name="Prof. Test Faculty",
        role="teacher",
        department_id=test_department.id,
        password="TeacherTestPassword!123"
    )
    db.session.add(teacher)
    db.session.commit()
    return teacher


@pytest.fixture
def test_student(db, test_department):
    student = User(
        username="21CS001",
        full_name="John Student",
        role="student",
        department_id=test_department.id,
        semester=5,
        password="StudentTestPassword!123"
    )
    db.session.add(student)
    db.session.commit()
    return student


@pytest.fixture
def test_student_2(db, test_department):
    student = User(
        username="21CS002",
        full_name="Jane Student",
        role="student",
        department_id=test_department.id,
        semester=5,
        password="StudentTestPassword!123"
    )
    db.session.add(student)
    db.session.commit()
    return student


@pytest.fixture
def test_subject(db, test_department, test_teacher):
    sub = Subject(
        name="Operating Systems Lab",
        code="CS301",
        department_id=test_department.id,
        semester=5,
        is_active=True
    )
    db.session.add(sub)
    db.session.commit()

    link = TeacherSubject(teacher_id=test_teacher.id, subject_id=sub.id)
    db.session.add(link)
    db.session.commit()
    return sub


@pytest.fixture
def test_lab(db):
    lab = Laboratory(
        name="Systems Lab 1",
        code="LAB1",
        location="Room 301",
        ip_start="192.168.1.1",
        ip_end="192.168.1.30",
        default_capacity=30
    )
    db.session.add(lab)
    db.session.commit()

    # Create workstations
    from app.utils.security import generate_workstation_token
    for seat in range(1, 31):
        ws = Workstation(
            lab_id=lab.id,
            workstation_code=f"LAB1-WS{seat:02d}",
            seat_number=seat,
            ip_address=f"192.168.1.{seat}",
            secret_token=generate_workstation_token(),
            status="active"
        )
        db.session.add(ws)
    db.session.commit()
    return lab
