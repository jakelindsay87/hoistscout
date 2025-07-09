#!/bin/bash
# Start HoistScout with PostgreSQL-based task queue (no Redis required)

set -e

echo "Starting HoistScout with Database Queue..."

# Set environment variable to use database queue
export USE_DB_QUEUE=true

# Check if we're in the backend directory
if [ ! -f "pyproject.toml" ]; then
    cd backend || { echo "Backend directory not found"; exit 1; }
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start the database queue worker in the background
echo "Starting database queue worker..."
python -m app.db_worker --worker-id db-worker-1 &
WORKER_PID=$!

# Give the worker time to start
sleep 2

# Start the FastAPI application
echo "Starting FastAPI application..."
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

# Function to cleanup on exit
cleanup() {
    echo "Shutting down..."
    kill $WORKER_PID $API_PID 2>/dev/null || true
    wait $WORKER_PID $API_PID 2>/dev/null || true
    echo "Shutdown complete"
}

# Set up cleanup on script exit
trap cleanup EXIT INT TERM

# Wait for both processes
echo "HoistScout is running with database queue!"
echo "API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Press Ctrl+C to stop"

# Wait for any process to exit
wait -n $WORKER_PID $API_PID

# If we get here, one of the processes died
echo "One of the processes exited unexpectedly"
cleanup