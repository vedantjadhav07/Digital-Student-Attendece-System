"""
Gunicorn Configuration for Lab-Secure Production Deployment
Supports Flask-SocketIO via Eventlet or Gevent worker.
"""
import multiprocessing

# Network Binding
bind = "127.0.0.1:5000"

# Workers & Concurrency
# For Flask-SocketIO, eventlet worker is recommended with 1 or 2 workers per server core
worker_class = "eventlet"
workers = 1  # When using WebSockets without Redis message queue, keep workers=1 to ensure room in-memory state consistency
worker_connections = 1000

# Timeout
timeout = 60
keepalive = 5

# Process Management
daemon = False
pidfile = "/var/run/labsecure.pid"
umask = 0o007

# Logging
accesslog = "/var/log/labsecure/access.log"
errorlog = "/var/log/labsecure/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

