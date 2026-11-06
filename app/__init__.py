import os
import click
from datetime import datetime
from flask import Flask, redirect, url_for, render_template, request
from flask_cors import CORS
from app.config import config_by_name
from app.extensions import db, login_manager, socketio, csrf, limiter, migrate
from app.models import User


def create_app(config_name=None):
    """Flask Application Factory."""
    if not config_name:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    config_obj = config_by_name.get(config_name, config_by_name['default'])
    app.config.from_object(config_obj)

    # Initialize Plugins & Extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    socketio.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    migrate.init_app(app, db)

    # Configure CORS: Restrict API access to trusted frontend origins
    allowed_origins = [o.strip() for o in os.getenv(
        'ALLOWED_ORIGINS',
        'http://localhost:5173,http://127.0.0.1:5173,http://localhost:5000,http://127.0.0.1:5000'
    ).split(',') if o.strip()]
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}, r"/attendance/*": {"origins": allowed_origins}}, supports_credentials=True)

    # Setup User Loaders (Session & JWT Bearer token)
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @login_manager.request_loader
    def load_user_from_request(req):
        auth_header = req.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1].strip()
            from app.utils.jwt_util import get_user_from_jwt
            return get_user_from_jwt(token, expected_type='access')
        return None

    # Register Blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.teacher import teacher_bp
    from app.blueprints.student import student_bp
    from app.blueprints.attendance import attendance_bp
    from app.blueprints.reports import reports_bp
    from app.blueprints.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp)

    # Exempt REST API blueprints from CSRF
    csrf.exempt(api_bp)
    csrf.exempt(attendance_bp)

    # Serve built React frontend if available
    dist_dir = os.path.abspath(os.path.join(app.root_path, '..', 'frontend', 'dist'))
    if os.path.exists(dist_dir):
        from flask import send_from_directory

        @app.route('/', defaults={'path': ''})
        @app.route('/<path:path>')
        def serve_react(path):
            if path and os.path.exists(os.path.join(dist_dir, path)):
                return send_from_directory(dist_dir, path)
            return send_from_directory(dist_dir, 'index.html')
    else:
        # Fallback root redirect to login
        @app.route('/')
        def index():
            return redirect(url_for('auth.login'))

    # Security Headers Hook
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'

        # Strict-Transport-Security (HSTS) when running over HTTPS or in production
        if app.config.get('SESSION_COOKIE_SECURE') or request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'

        return response

    # Error Handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    # Register Custom CLI Commands
    register_commands(app)

    return app


def register_commands(app: Flask):
    """Custom CLI commands for clean database initialization, admin creation, and seeding."""

    @app.cli.command("db-init")
    def db_init():
        """Initialize clean database tables without seed data."""
        with app.app_context():
            db.create_all()
            click.echo("Clean database initialized successfully (All tables created).")

    @app.cli.command("create-admin")
    @click.option("--username", prompt="Admin username (ID)", help="Admin username")
    @click.option("--name", prompt="Admin full name", help="Admin real name")
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True, help="Admin password")
    def create_admin(username, name, password):
        """Create a new administrative user securely with Argon2id."""
        with app.app_context():
            existing = User.query.filter_by(username=username).first()
            if existing:
                click.echo(f"Error: User '{username}' already exists.")
                return

            admin = User(
                username=username,
                full_name=name,
                role='admin',
                password=password
            )
            db.session.add(admin)
            db.session.commit()
            click.echo(f"Admin account '{username}' created successfully!")

    @app.cli.command("seed-demo")
    def seed_demo():
        """Optional development seed dataset with labs, subjects, faculty, and test students."""
        from app.models import Department, Subject, Laboratory, TeacherSubject, StudentEnrollment
        from app.services.workstation_service import WorkstationService

        with app.app_context():
            db.create_all()

            # 1. Department
            cse = Department.query.filter_by(code='CSE').first()
            if not cse:
                cse = Department(name='Computer Science & Engineering', code='CSE')
                db.session.add(cse)
                db.session.commit()

            # 2. Admin
            if not User.query.filter_by(username='admin').first():
                admin = User(username='admin', full_name='System Administrator', role='admin', password='AdminSecurePassword!123')
                db.session.add(admin)

            # 3. Faculty
            teacher1 = User.query.filter_by(username='prof.sharma').first()
            if not teacher1:
                teacher1 = User(username='prof.sharma', full_name='Prof. R. K. Sharma', role='teacher', department_id=cse.id, password='TeacherPassword123')
                db.session.add(teacher1)
                db.session.commit()

            # 4. Subjects
            sub1 = Subject.query.filter_by(code='CS301').first()
            if not sub1:
                sub1 = Subject(name='Operating Systems Lab', code='CS301', department_id=cse.id, semester=5, is_active=True)
                db.session.add(sub1)
                db.session.commit()

            sub2 = Subject.query.filter_by(code='CS302').first()
            if not sub2:
                sub2 = Subject(name='Database Management Systems Lab', code='CS302', department_id=cse.id, semester=5, is_active=True)
                db.session.add(sub2)
                db.session.commit()

            # Assign teacher to subjects
            for sub in [sub1, sub2]:
                if not TeacherSubject.query.filter_by(teacher_id=teacher1.id, subject_id=sub.id).first():
                    db.session.add(TeacherSubject(teacher_id=teacher1.id, subject_id=sub.id))

            # 5. Laboratories
            lab1 = Laboratory.query.filter_by(name='Lab 1 - Systems').first()
            if not lab1:
                lab1 = Laboratory(name='Lab 1 - Systems', code='LAB1', location='Room 301, 3rd Floor', ip_start='192.168.1.1', ip_end='192.168.1.30', default_capacity=30)
                db.session.add(lab1)
                db.session.commit()
                WorkstationService.provision_lab_workstations(lab1, capacity=30)

            lab2 = Laboratory.query.filter_by(name='Lab 2 - Advanced Computing').first()
            if not lab2:
                lab2 = Laboratory(name='Lab 2 - Advanced Computing', code='LAB2', location='Room 302, 3rd Floor', ip_start='192.168.2.1', ip_end='192.168.2.60', default_capacity=60)
                db.session.add(lab2)
                db.session.commit()
                WorkstationService.provision_lab_workstations(lab2, capacity=60)

            # 6. Sample Students
            for i in range(1, 11):
                roll = f"21CS{i:03d}"
                if not User.query.filter_by(username=roll).first():
                    student = User(
                        username=roll,
                        full_name=f"Demo Student {i}",
                        role='student',
                        department_id=cse.id,
                        semester=5,
                        password='StudentPassword123'
                    )
                    db.session.add(student)
                    db.session.commit()

                    # Enroll in subjects
                    db.session.add(StudentEnrollment(student_id=student.id, subject_id=sub1.id))
                    db.session.add(StudentEnrollment(student_id=student.id, subject_id=sub2.id))

            db.session.commit()
            click.echo("Development demo dataset seeded successfully!")
            click.echo("  Admin:   username 'admin'       / password 'AdminSecurePassword!123'")
            click.echo("  Teacher: username 'prof.sharma' / password 'TeacherPassword123'")
            click.echo("  Student: username '21CS001'     / password 'StudentPassword123'")
