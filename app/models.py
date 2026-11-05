from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint, Index
from app.extensions import db
from app.utils.security import hash_password, verify_password, needs_rehash


class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    code = db.Column(db.String(20), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    users = db.relationship('User', back_populates='department', lazy='dynamic')
    subjects = db.relationship('Subject', back_populates='department', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)  # Roll / Enrollment / Faculty ID
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student', index=True)  # 'admin', 'teacher', 'student'
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    semester = db.Column(db.Integer, nullable=True)  # Student semester (1-8)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    department = db.relationship('Department', back_populates='users')
    taught_subjects = db.relationship('TeacherSubject', back_populates='teacher', cascade='all, delete-orphan')
    enrollments = db.relationship('StudentEnrollment', back_populates='student', cascade='all, delete-orphan')
    conducted_sessions = db.relationship('AttendanceSession', back_populates='teacher', lazy='dynamic')
    attendance_records = db.relationship('AttendanceRecord', back_populates='student', lazy='dynamic')
    audit_logs = db.relationship('AuditLog', back_populates='user', lazy='dynamic')

    @property
    def password(self):
        raise AttributeError("Password is write-only for security")

    @password.setter
    def password(self, plain_password):
        self.password_hash = hash_password(plain_password)

    def verify_password(self, candidate_password: str) -> bool:
        if not self.password_hash:
            return False
        # If legacy plaintext remains during migration, verify and upgrade
        if not self.password_hash.startswith("$argon2"):
            if self.password_hash == candidate_password:
                self.password = candidate_password
                db.session.commit()
                return True
            return False

        verified = verify_password(self.password_hash, candidate_password)
        if verified and needs_rehash(self.password_hash):
            self.password = candidate_password
            db.session.commit()
        return verified

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'email': self.email,
            'role': self.role,
            'department': self.department.name if self.department else None,
            'semester': self.semester,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Subject(db.Model):
    __tablename__ = 'subjects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(30), nullable=False, unique=True, index=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    semester = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    department = db.relationship('Department', back_populates='subjects')
    assigned_teachers = db.relationship('TeacherSubject', back_populates='subject', cascade='all, delete-orphan')
    enrolled_students = db.relationship('StudentEnrollment', back_populates='subject', cascade='all, delete-orphan')
    sessions = db.relationship('AttendanceSession', back_populates='subject', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'department': self.department.name if self.department else None,
            'semester': self.semester
        }


class TeacherSubject(db.Model):
    __tablename__ = 'teacher_subjects'

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    teacher = db.relationship('User', back_populates='taught_subjects')
    subject = db.relationship('Subject', back_populates='assigned_teachers')

    __table_args__ = (
        UniqueConstraint('teacher_id', 'subject_id', name='uq_teacher_subject'),
    )


class StudentEnrollment(db.Model):
    __tablename__ = 'student_enrollments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship('User', back_populates='enrollments')
    subject = db.relationship('Subject', back_populates='enrolled_students')

    __table_args__ = (
        UniqueConstraint('student_id', 'subject_id', name='uq_student_subject'),
    )


class Laboratory(db.Model):
    __tablename__ = 'laboratories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)  # e.g., 'Lab 1', 'Lab 2'
    code = db.Column(db.String(20), nullable=True, unique=True)
    location = db.Column(db.String(100), nullable=True)  # e.g. 'Room 302, 3rd Floor'
    subnet_cidr = db.Column(db.String(50), nullable=True)  # e.g. '192.168.1.0/24'
    ip_start = db.Column(db.String(50), nullable=True)   # e.g. '192.168.1.1'
    ip_end = db.Column(db.String(50), nullable=True)     # e.g. '192.168.1.30'
    default_capacity = db.Column(db.Integer, default=30)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    workstations = db.relationship('Workstation', back_populates='laboratory', cascade='all, delete-orphan')
    sessions = db.relationship('AttendanceSession', back_populates='laboratory', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'location': self.location,
            'ip_start': self.ip_start,
            'ip_end': self.ip_end,
            'capacity': self.default_capacity,
            'workstation_count': len(self.workstations) if isinstance(self.workstations, list) or hasattr(self.workstations, '__len__') else self.workstations.count(),
            'is_active': self.is_active
        }


class Workstation(db.Model):
    __tablename__ = 'workstations'

    id = db.Column(db.Integer, primary_key=True)
    lab_id = db.Column(db.Integer, db.ForeignKey('laboratories.id'), nullable=False)
    workstation_code = db.Column(db.String(30), nullable=False, unique=True, index=True)  # e.g. 'LAB1-WS01'
    seat_number = db.Column(db.Integer, nullable=False)  # 1 to 90
    ip_address = db.Column(db.String(50), nullable=True, index=True)
    mac_address = db.Column(db.String(50), nullable=True)
    secret_token = db.Column(db.String(64), nullable=True)  # Provisioned workstation credential
    status = db.Column(db.String(20), default='active')  # 'active', 'maintenance', 'inactive'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    laboratory = db.relationship('Laboratory', back_populates='workstations')
    attendance_records = db.relationship('AttendanceRecord', back_populates='workstation', lazy='dynamic')

    __table_args__ = (
        UniqueConstraint('lab_id', 'seat_number', name='uq_lab_seat'),
        Index('idx_workstation_lab_ip', 'lab_id', 'ip_address'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'lab_id': self.lab_id,
            'lab_name': self.laboratory.name if self.laboratory else None,
            'workstation_code': self.workstation_code,
            'seat_number': self.seat_number,
            'ip_address': self.ip_address,
            'status': self.status
        }


class AttendanceSession(db.Model):
    __tablename__ = 'attendance_sessions'

    id = db.Column(db.Integer, primary_key=True)
    session_code = db.Column(db.String(12), unique=True, nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lab_id = db.Column(db.Integer, db.ForeignKey('laboratories.id'), nullable=False)
    lab_capacity = db.Column(db.Integer, default=30)  # 30, 60, 90
    start_pc = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=False, index=True)
    is_paused = db.Column(db.Boolean, default=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    subject = db.relationship('Subject', back_populates='sessions')
    teacher = db.relationship('User', back_populates='conducted_sessions')
    laboratory = db.relationship('Laboratory', back_populates='sessions')
    records = db.relationship('AttendanceRecord', back_populates='session', cascade='all, delete-orphan')

    @property
    def is_expired(self):
        return datetime.utcnow() > self.end_time

    @property
    def remaining_seconds(self):
        if not self.is_active or self.is_expired:
            return 0
        return max(0, int((self.end_time - datetime.utcnow()).total_seconds()))

    def to_dict(self):
        return {
            'id': self.id,
            'session_code': self.session_code,
            'subject_name': self.subject.name if self.subject else 'N/A',
            'subject_code': self.subject.code if self.subject else 'N/A',
            'teacher_name': self.teacher.full_name if self.teacher else 'N/A',
            'lab_name': self.laboratory.name if self.laboratory else 'N/A',
            'lab_capacity': self.lab_capacity,
            'start_pc': self.start_pc,
            'is_active': self.is_active,
            'is_paused': self.is_paused,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'remaining_seconds': self.remaining_seconds
        }


class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('attendance_sessions.id'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    workstation_id = db.Column(db.Integer, db.ForeignKey('workstations.id'), nullable=True, index=True)
    seat_number = db.Column(db.Integer, nullable=True)
    ip_address = db.Column(db.String(50), nullable=False)
    verification_method = db.Column(db.String(30), default='network_workstation')  # 'network_workstation', 'token', 'manual'
    status = db.Column(db.String(20), default='present')  # 'present', 'flagged', 'late'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relationships
    session = db.relationship('AttendanceSession', back_populates='records')
    student = db.relationship('User', back_populates='attendance_records')
    workstation = db.relationship('Workstation', back_populates='attendance_records')

    __table_args__ = (
        UniqueConstraint('session_id', 'student_id', name='uq_session_student'),
        UniqueConstraint('session_id', 'workstation_id', name='uq_session_workstation'),
        Index('idx_session_timestamp', 'session_id', 'timestamp'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else None,
            'student_username': self.student.username if self.student else None,
            'seat_number': self.seat_number,
            'ip_address': self.ip_address,
            'status': self.status,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False, index=True)  # e.g., 'LOGIN', 'SESSION_START', 'ATTENDANCE_MARKED'
    target_type = db.Column(db.String(50), nullable=True)  # e.g., 'AttendanceSession', 'User'
    target_id = db.Column(db.Integer, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = db.relationship('User', back_populates='audit_logs')

    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user.username if self.user else 'System',
            'action': self.action,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'ip_address': self.ip_address,
            'details': self.details,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else None
        }
