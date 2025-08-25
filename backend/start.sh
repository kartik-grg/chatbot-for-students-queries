#!/bin/bash
# Startup script for Render deployment

echo "Starting application..."
echo "Python version:"
python --version

echo "Installed packages:"
pip freeze | grep -E 'flask|langchain|pinecone|cloudinary|uvicorn|gunicorn'

# Determine worker class based on environment variable or what's available
WORKER_CLASS=${GUNICORN_WORKER_CLASS:-"sync"}  # Default to sync if not set

# Try to use uvicorn if available and not explicitly set
if [ "$WORKER_CLASS" = "sync" ] && python -c "import uvicorn" 2>/dev/null; then
    echo "Uvicorn is available, using uvicorn worker class"
    WORKER_CLASS="uvicorn.workers.UvicornWorker"
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
