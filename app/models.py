from . import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(10)) # 'teacher' or 'student'

class LabRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_name = db.Column(db.String(20)) # 'Lab 1', 'Lab 2'
    ip_start = db.Column(db.String(50))  # e.g., '192.168.1.1'
    ip_end = db.Column(db.String(50))    # e.g., '192.168.1.30'

class AttendanceSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(50))   # 'OSY', 'STE', 'JAVA'
    lab_id = db.Column(db.Integer, db.ForeignKey('lab_room.id'))
    lab_name = db.Column(db.String(50))
    lab_capacity = db.Column(db.Integer, default=30)
    is_active = db.Column(db.Boolean, default=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)    # When the 10-min timer ends
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class AttendanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    session_id = db.Column(db.Integer, db.ForeignKey('attendance_session.id'))
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class TeacherSubject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)