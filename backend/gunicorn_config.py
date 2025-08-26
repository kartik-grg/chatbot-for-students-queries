"""Gunicorn configuration for Render deployment"""
import os
import multiprocessing

# Calculate optimal number of workers based on CPU cores
# For Render's free tier, limit to 1-2 workers to avoid memory issues
# For paid plans, a good rule of thumb is 2-4 workers per CPU core
cpu_count = multiprocessing.cpu_count()
is_free_tier = os.environ.get('RENDER_SERVICE_TYPE', '') == 'free'
default_workers = 1 if is_free_tier else (cpu_count * 2) + 1

# Worker configuration
workers = int(os.environ.get('WEB_CONCURRENCY', default_workers))
threads = int(os.environ.get('THREADS', 2))
# Use sync workers for Flask (WSGI) app to avoid ASGI/WSGI compatibility issues
worker_class = 'sync'  # Standard synchronous workers for WSGI apps

# Check if gevent is available and use it for better performance
use_gevent = os.environ.get('USE_GEVENT', 'false').lower() == 'true'
if use_gevent:
    try:
        import gevent
        worker_class = 'gevent'  # Using gevent for better performance if available
    except ImportError:
        # Gevent not available, staying with sync worker
        pass

worker_connections = 1000

# Timeout configuration
timeout = int(os.environ.get('TIMEOUT', 120))  # Longer timeout for PDF processing
graceful_timeout = int(os.environ.get('GRACEFUL_TIMEOUT', 30))
keepalive = int(os.environ.get('KEEP_ALIVE', 5))

# Server configuration
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"
accesslog = '-'  # Log to stdout for Render
errorlog = '-'   # Log to stderr for Render
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')

# Process naming
proc_name = 'student-chatbot-api'

# Reload on code changes (disabled in production)
reload = os.environ.get('FLASK_ENV', 'production') == 'development'

# Maximum requests per worker before restarting
# This helps prevent memory leaks
max_requests = int(os.environ.get('MAX_REQUESTS', 1000))
max_requests_jitter = int(os.environ.get('MAX_REQUESTS_JITTER', 50))

# Preload application to save memory
# Set to False on Render Free tier to reduce memory usage
is_free_tier = os.environ.get('RENDER_SERVICE_TYPE', '') == 'free'
preload_app = not is_free_tier

# Additional server hardening
forwarded_allow_ips = '*'  # Trust X-Forwarded-* headers from all IPs
secure_scheme_headers = {
    'X-Forwarded-Proto': 'https',
}

# Log configuration
capture_output = True
logger_class = 'gunicorn.glogging.Logger'

# Flask application specific hooks
def on_starting(server):
    """Log when server is starting"""
    server.log.info("Starting student chatbot API server")

def post_fork(server, worker):
    """Log when worker is spawned"""
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def worker_exit(server, worker):
    """Log when worker exits"""
    server.log.info(f"Worker exited (pid: {worker.pid})")

def on_exit(server):
    """Log when server is shutting down"""
    server.log.info("Shutting down student chatbot API server")
