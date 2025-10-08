# Gunicorn configuration for RFID Gate Web UI
# ============================================

# Server socket
bind = "127.0.0.1:8080"
backlog = 2048

# Worker processes
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Timeout settings
timeout = 30
keepalive = 2

# Logging
accesslog = "/opt/rfid-gate/logs/webui_access.log"
errorlog = "/opt/rfid-gate/logs/webui_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "rfid-gate-webui"

# Daemon mode
daemon = False
pidfile = "/opt/rfid-gate/webui/gunicorn.pid"

# User and group
user = "rfid"
group = "rfid"

# Preload app for better performance
preload_app = True

# Restart workers after this many requests
max_requests = 1000

# Graceful timeout for worker shutdown
graceful_timeout = 30

# Enable SSL if certificates are available
# keyfile = "/path/to/private.key"
# certfile = "/path/to/certificate.crt"