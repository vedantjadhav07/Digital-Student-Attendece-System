from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def role_required(*allowed_roles):
    """Decorator to restrict access to users with specified roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.role not in allowed_roles:
                flash("Access denied: You do not have permission to view this resource.", "danger")
                if current_user.role == 'admin':
                    return redirect(url_for('admin.dashboard'))
                elif current_user.role == 'teacher':
                    return redirect(url_for('teacher.dashboard'))
                elif current_user.role == 'student':
                    return redirect(url_for('student.dashboard'))
                return abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    return role_required('admin')(f)


def teacher_required(f):
    return role_required('teacher')(f)


def student_required(f):
    return role_required('student')(f)

