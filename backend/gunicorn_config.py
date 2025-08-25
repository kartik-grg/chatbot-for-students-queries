"""Gunicorn configuration for Render deployment"""
import os
import multiprocessing

# Calculate optimal number of workers based on CPU cores
# A good rule of thumb is 2-4 workers per CPU core
cpu_count = multiprocessing.cpu_count()
default_workers = (cpu_count * 2) + 1

# Worker configuration
workers = int(os.environ.get('WEB_CONCURRENCY', default_workers))
threads = int(os.environ.get('THREADS', 2))
worker_class = 'gevent'  # Using gevent for better async performance
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
preload_app = True

# Additional server hardening
forwarded_allow_ips = '*'  # Trust X-Forwarded-* headers from all IPs
secure_scheme_headers = {
    'X-Forwarded-Proto': 'https',
}

# Log configuration
capture_output = True
logger_class = 'gunicorn.glogging.Logger'
logconfig_dict = None  # Use default logging config
