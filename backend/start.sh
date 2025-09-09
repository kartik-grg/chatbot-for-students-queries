#!/bin/bash
# Startup script for Render deployment

echo "Starting application..."
echo "Python version:"
python --version

echo "Installed packages:"
pip freeze | grep -E 'flask|langchain|pinecone|cloudinary|uvicorn|gunicorn'

# Set environment variables for better AI processing
export GOOGLE_APPLICATION_CREDENTIALS_JSON="${GOOGLE_APPLICATION_CREDENTIALS:-}"
export LANGCHAIN_TRACING_V2="true"
export PYTHONUNBUFFERED=1

# Determine worker class based on environment variable
WORKER_CLASS=${GUNICORN_WORKER_CLASS:-"sync"}  # Default to sync if not set
export USE_GEVENT=false  # Disable gevent by default

# Set optimized settings for AI processing
export WEB_CONCURRENCY=${WEB_CONCURRENCY:-1}  # Single worker for AI processing
export THREADS=${THREADS:-1}                  # Single thread per worker
export TIMEOUT=${TIMEOUT:-600}                # 10 minute timeout
export GRACEFUL_TIMEOUT=${GRACEFUL_TIMEOUT:-120}  # 2 minute graceful timeout

echo "Environment settings:"
echo "  Worker class: $WORKER_CLASS"
echo "  Workers: ${WEB_CONCURRENCY}"
echo "  Threads: ${THREADS}"
echo "  Timeout: ${TIMEOUT}s"
echo "  Graceful timeout: ${GRACEFUL_TIMEOUT}s"

# For Flask (WSGI) applications, we should use sync or gevent workers
# ASGI workers like uvicorn will cause compatibility issues
if [ "$WORKER_CLASS" = "gevent" ]; then
    if python -c "import gevent" 2>/dev/null; then
        echo "Using gevent worker class"
        export USE_GEVENT=true
    else
        echo "Gevent not available, falling back to sync worker"
        WORKER_CLASS="sync"
    fi
else
    echo "Using $WORKER_CLASS worker class"
fi

# Check for gunicorn config file
if [ -f "gunicorn_config.py" ]; then
    echo "Starting gunicorn with config file..."
    exec gunicorn --worker-class $WORKER_CLASS -c gunicorn_config.py app:app
else
    echo "No gunicorn_config.py found, using default settings..."
    exec gunicorn --worker-class $WORKER_CLASS --bind 0.0.0.0:$PORT app:app
fi
