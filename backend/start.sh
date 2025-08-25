#!/bin/bash
# Startup script for Render deployment

echo "Starting application..."
echo "Python version:"
python --version

echo "Installed packages:"
pip freeze | grep -E 'flask|langchain|pinecone|cloudinary|gevent|gunicorn'

# Determine worker class based on what's available
if python -c "import gevent" 2>/dev/null; then
    echo "Using gevent worker class"
    WORKER_CLASS="gevent"
else
    echo "Gevent not available, using sync worker class"
    WORKER_CLASS="sync"
fi

# Start gunicorn
echo "Starting gunicorn with $WORKER_CLASS worker class..."
exec gunicorn --worker-class $WORKER_CLASS -c gunicorn_config.py app:app
