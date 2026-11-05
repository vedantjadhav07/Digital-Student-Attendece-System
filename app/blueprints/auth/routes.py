from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.blueprints.auth import auth_bp
from app.extensions import limiter
from app.services.auth_service import AuthService
from app.utils.network import get_real_client_ip


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("15 per minute", methods=['POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'teacher':
            return redirect(url_for('teacher.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        client_ip = get_real_client_ip()

        user, err = AuthService.authenticate_user(username, password, client_ip=client_ip)
        if user:
            login_user(user, remember=remember)
            flash(f"Welcome back, {user.full_name}!", "success")

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)

            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'teacher':
                return redirect(url_for('teacher.dashboard'))
            else:
                return redirect(url_for('student.dashboard'))
        else:
            flash(err or "Invalid credentials. Please verify your username and password.", "danger")

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    logout_user()
    flash("You have been signed out safely.", "info")
    return redirect(url_for('auth.login'))


@auth_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    client_ip = get_real_client_ip()

    if new_password != confirm_password:
        flash("New passwords do not match.", "danger")
    else:
        success, msg = AuthService.change_password(current_user, new_password, client_ip=client_ip)
        flash(msg, "success" if success else "danger")

    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif current_user.role == 'teacher':
        return redirect(url_for('teacher.dashboard'))
    return redirect(url_for('student.dashboard'))

