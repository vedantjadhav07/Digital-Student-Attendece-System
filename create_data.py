from app import create_app, db
from app.models import User, LabRoom 

app = create_app()

with app.app_context():
    db.create_all() 

    t1 = User(username='teacher1', password='t123', role='teacher')
    s1 = User(username='student1', password='s123', role='student')
    
    db.session.add_all([t1, s1])
    db.session.commit()

    lab1 = LabRoom(room_name='Lab 1', ip_start='192.168.1.1', ip_end='192.168.1.30')
    lab2 = LabRoom(room_name='Lab 2', ip_start='192.168.1.31', ip_end='192.168.1.60')
    lab3 = LabRoom(room_name='Lab 3', ip_start='192.168.1.61', ip_end='192.168.1.90')
    
    db.session.add_all([lab1, lab2, lab3])
    db.session.commit()

    print("Success")