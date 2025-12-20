# Digital Student Attendance System (Lab-Secure) 🎓

A professional Flask-based attendance management system designed for college computer labs. It features **Real-Time Live Monitoring** via WebSockets and **Physical Security** through IP-based workstation tracking.

## 🚀 Key Features

- **Live Lab Monitor:** Teachers see a real-time grid of the lab. Boxes turn green instantly when students mark attendance.
- **IP-Based Security:** - Restricts attendance to specific Lab IP ranges (e.g., PC 1-30).
  - Prevents "Proxy Attendance" by blocking multiple logins from the same PC.
- **Attendance Analytics:** Automatically identifies "At-Risk" students (Attendance < 75%) with visual progress bars.
- **Session Management:** Teachers can start/stop labs, choose lab capacity (30/60/90), and extend live sessions by +10 minutes.
- **Export Reports:** Generate Excel reports filtered by Subject, Date, and Teacher.
- **Multi-Teacher Isolation:** Teachers only see their own subjects, history, and analytics.

## 🛠️ Tech Stack

- **Backend:** Python (Flask)
- **Database:** SQLite (SQLAlchemy ORM)
- **Real-time:** Flask-SocketIO (WebSockets)
- **Frontend:** Bootstrap 5, Jinja2, JavaScript
- **Data Export:** Pandas, OpenPyXL

## 📋 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/vedantjadhav07/Digital-Student-Attendece-System.git](https://github.com/vedantjadhav07/Digital-Student-Attendece-System.git)
   cd Digital-Student-Attendece-System



2.Create and Activate Virtual Environment:
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate


3.Install Requirements:
pip install -r requirements.txt

4.Environment Variables: Create a .env file in the root directory:
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///database.db

5.initialize
flask shell
>>> from app import db
>>> db.create_all()
>>> exit()

6.Run the Application:
python run.py