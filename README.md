# 🎓 Digital Student Attendance System (Lab-Secure)

A secure, real-time digital attendance management system built using Flask, designed specifically for college computer labs.  
The system prevents proxy attendance using IP-based workstation validation and provides live monitoring for faculty.

---

## 🚀 Project Overview

Lab-Secure replaces traditional paper-based lab attendance with a modern, secure web-based solution.  
Only students physically present inside the lab can mark attendance, ensuring authenticity and transparency.

---

## ✨ Key Features

### 🔴 Real-Time Live Lab Monitoring
- Teachers view a live grid of lab workstations
- Boxes turn green instantly when attendance is marked
- Powered by Flask-SocketIO (WebSockets)

### 🔐 IP-Based Physical Security
- Attendance restricted to predefined lab IP ranges
- Prevents proxy attendance
- Blocks multiple logins from the same PC

### 📊 Attendance Analytics
- Automatic identification of At-Risk students (Attendance < 75%)
- Visual progress bars for quick analysis
- Student-wise and subject-wise statistics

### ⏱️ Session Management
- Teachers can:
  - Start / stop lab sessions
  - Choose lab capacity (30 / 60 / 90 systems)
  - Extend sessions by +10 minutes

### 📁 Export Reports
- Generate Excel reports
- Filter by:
  - Subject
  - Date
  - Teacher

### 👨‍🏫 Multi-Teacher Isolation
- Teachers can access only their own subjects
- Separate attendance history and analytics per teacher

---

## 🛠️ Tech Stack

Backend      : Python (Flask)  
Database     : SQLite (SQLAlchemy ORM)  
Real-Time    : Flask-SocketIO  
Frontend     : Bootstrap 5, Jinja2, JavaScript  
Data Export  : Pandas, OpenPyXL  

---

## 📂 Project Structure

Digital-Student-Attendance-System/
│
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── sockets.py
│
├── templates/
├── static/
├── database.db
├── requirements.txt
├── run.py
└── .env

---

## 📋 Installation & Setup

### 1️⃣ Clone the Repository
git clone https://github.com/vedantjadhav07/Digital-Student-Attendece-System.git  
cd Digital-Student-Attendece-System

---

### 2️⃣ Create & Activate Virtual Environment
python -m venv venv  

Windows:
.\venv\Scripts\activate  

Linux / Mac:
source venv/bin/activate

---

### 3️⃣ Install Dependencies
pip install -r requirements.txt

---

### 4️⃣ Configure Environment Variables
Create a .env file in the root directory:

SECRET_KEY=your_secret_key_here  
DATABASE_URL=sqlite:///database.db

---

### 5️⃣ Initialize the Database
flask shell  

from app import db  
db.create_all()  
exit()

---

### 6️⃣ Run the Application
python run.py

---

## 🌐 Access the Application

http://127.0.0.1:5000

---

## 🎯 Use Case

- Ideal for college computer labs
- Handles 200–300 students concurrently
- Lightweight, fast, and secure

---

## 📌 Future Enhancements

- QR-based fallback attendance
- Facial recognition integration
- Cloud database support (PostgreSQL)
- Advanced admin analytics dashboard

---

## 👨‍💻 Author

Vedant Jadhav  
B.Tech Computer Science  
Walchand College of Engineering

---

⭐ If you like this project, don’t forget to star the repository!
