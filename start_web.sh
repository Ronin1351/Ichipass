#!/bin/bash

# Ichipass Web Application Startup Script

echo "================================================"
echo "  Ichipass - Ichimoku Cloud Scanner Web UI"
echo "================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Checking dependencies..."
pip install -q -r requirements.txt

# Create cache directory if it doesn't exist
if [ ! -d "cache" ]; then
    echo "Creating cache directory..."
    mkdir -p cache
fi

# Start the web server
echo ""
echo "Starting Ichipass Web Server..."
echo "================================================"
echo "  🌐 Web Interface: http://localhost:8000"
echo "  📚 API Docs:      http://localhost:8000/docs"
echo "================================================"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd web && python app.py
