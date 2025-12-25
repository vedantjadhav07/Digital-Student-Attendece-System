from app import create_app, db
from app.models import User,LabRoom

app = create_app()
with app.app_context():
   # Adding a Teacher
    t1 = User(username='teacher1', password='t123', role='teacher')
    # Adding a Student
    s1 = User(username='student1', password='s123', role='student')
    
    db.session.add(t1)
    db.session.add(s1)
    db.session.commit()
    lab1 = LabRoom(room_name='Lab 1', ip_start='192.168.1.1', ip_end='192.168.1.30')
    db.session.add(lab1)
    db.session.commit()

    # t1 = User(username='teacher2', password='t123', role='teacher')
    # db.session.add(t1)
    # db.session.commit()

    # s1 = User(username='student2', password='s123', role='student')
    # db.session.add(s1)
    # db.session.commit()

    # lab2 = LabRoom(room_name='Lab 2', ip_start='192.168.1.31', ip_end='192.168.1.60')
    # db.session.add(lab2)
    # db.session.commit()
    # lab3 = LabRoom(room_name='Lab 3', ip_start='192.168.1.61', ip_end='192.168.1.90')
    # db.session.add(lab3)
    # db.session.commit()
    print("Users Created Successfully!")