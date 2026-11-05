import os
from app import create_app, socketio

# Application Factory
app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() in ('true', '1')

    print(f"Starting Lab-Secure Attendance Server on {host}:{port} (Debug: {debug})...")
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
