from flask import request, jsonify
from flask_login import login_required, current_user
from flask_socketio import join_room, leave_room

from app.blueprints.attendance import attendance_bp
from app.extensions import socketio, limiter
from app.services.attendance_service import AttendanceService
from app.utils.network import get_real_client_ip


@attendance_bp.route('/submit', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def submit():
    """
    Primary endpoint for students marking attendance from lab workstations.
    Performs server-side validation against all 9 security checks.
    """
    if current_user.role != 'student':
        return jsonify({'success': False, 'message': 'Only registered students can mark attendance.'}), 403

    client_ip = get_real_client_ip()
    session_id = request.form.get('session_id', type=int)
    workstation_token = request.headers.get('X-Workstation-Token') or request.form.get('workstation_token')

    result = AttendanceService.mark_attendance(
        student=current_user,
        client_ip=client_ip,
        session_id=session_id,
        workstation_token=workstation_token
    )

    return jsonify({
        'success': result.success,
        'message': result.message,
        'seat_number': result.record.seat_number if result.record else None,
        'timestamp': result.record.timestamp.strftime('%H:%M:%S') if result.record else None
    }), result.status_code


# ---------------- Socket.IO Room Handlers ----------------

@socketio.on('join_session')
def handle_join_session(data):
    """Client joins the isolated room for their active lab session."""
    session_id = data.get('session_id') if isinstance(data, dict) else None
    if session_id:
        room = f"session_{session_id}"
        join_room(room)
        socketio.emit('room_joined', {'room': room, 'message': 'Connected to live lab monitor.'}, to=request.sid)


@socketio.on('leave_session')
def handle_leave_session(data):
    """Client leaves the active lab session room."""
    session_id = data.get('session_id') if isinstance(data, dict) else None
    if session_id:
        room = f"session_{session_id}"
        leave_room(room)

