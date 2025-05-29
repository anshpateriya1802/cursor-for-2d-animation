#!/bin/bash

# Check if virtual environment exists, if not create it
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Function to check if a port is in use
check_port() {
    lsof -i :$1 >/dev/null 2>&1
    return $?
}

# Function to kill process on a port
kill_port() {
    local port=$1
    if check_port $port; then
        echo "Killing process on port $port"
        lsof -ti :$port | xargs kill -9 2>/dev/null || true
    fi
}

# Kill any existing processes
echo "Cleaning up existing processes..."
kill_port 8000
kill_port 8501

# Give the system a moment to free up the ports
sleep 2

# Start FastAPI server in the background
echo "Starting FastAPI server..."
uvicorn src.main:app --host 0.0.0.0 --port 8000 &
FASTAPI_PID=$!

# Wait for FastAPI server to start
echo "Waiting for FastAPI server to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/docs >/dev/null; then
        echo "FastAPI server is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Error: FastAPI server failed to start"
        kill $FASTAPI_PID
        exit 1
    fi
    echo "Waiting... ($i/30)"
    sleep 1
done

# Start Streamlit
echo "Starting Streamlit app..."
streamlit run src/app.py

# Cleanup on exit
trap "kill $FASTAPI_PID 2>/dev/null || true" EXIT 