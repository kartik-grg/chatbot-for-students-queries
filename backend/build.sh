#!/bin/bash
# Custom build script for Render deployment

echo "Starting custom build script..."
echo "Python version:"
python --version

# Upgrade pip first
pip install --upgrade pip

echo "Installing dependencies with preference for binary wheels..."
# Try to install with prefer-binary and no build isolation first
pip install -r requirements.txt --prefer-binary --no-build-isolation || {
    echo "First attempt failed, trying without gevent..."
    # Remove gevent from requirements.txt temporarily
    grep -v "gevent" requirements.txt > requirements_no_gevent.txt
    pip install -r requirements_no_gevent.txt --prefer-binary
    echo "Installing minimal version of gevent if possible..."
    pip install "gevent<22.0.0" --prefer-binary || echo "Skipping gevent installation"
}

# Verify installation of critical packages
echo "Checking installed packages:"
pip freeze | grep -E 'flask|langchain|pinecone|cloudinary'

echo "Build completed"
exit 0
