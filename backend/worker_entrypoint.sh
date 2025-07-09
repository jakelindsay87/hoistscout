#!/bin/bash
# Worker entrypoint script with better error handling

echo "Starting HoistScout Worker..."
echo "Environment:"
echo "  REDIS_URL: $REDIS_URL"
echo "  DATABASE_URL: ${DATABASE_URL:0:50}..."
echo "  USE_GEMINI: $USE_GEMINI"
echo "  GEMINI_API_KEY: ${GEMINI_API_KEY:+Set}"

# Ensure we're in the right directory
cd /app

# Start Celery worker with explicit configuration
echo "Starting Celery worker..."
exec python -m celery -A app.worker worker \
    --loglevel=info \
    --concurrency=1 \
    --pool=solo \
    -n worker@%h