from app import create_app, db
from app.models import User, LabRoom 

app = create_app()

with app.app_context():
   
    # db.create_all() 
    admin = User(full_name='System Admin', username='admin', password='admin123', role='admin')
    db.session.add(admin)
    db.session.commit()
    print("Admin user created!")
    print("Success")