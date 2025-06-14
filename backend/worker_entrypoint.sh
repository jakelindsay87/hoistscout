#!/bin/sh

# Handle REDIS_URL in different formats
if [ -n "$REDIS_URL" ]; then
  # Check if it's already a full redis:// URL
  if echo "$REDIS_URL" | grep -q "^redis://"; then
    # Extract host from redis://host:port format
    REDIS_HOST=$(echo $REDIS_URL | sed -E 's|redis://([^:]+):.*|\1|')
    REDIS_PORT=$(echo $REDIS_URL | sed -E 's|redis://[^:]+:([0-9]+).*|\1|')
  else
    # Assume it's just host:port format from Render
    REDIS_HOST=$(echo $REDIS_URL | cut -d: -f1)
    REDIS_PORT=$(echo $REDIS_URL | cut -d: -f2)
    # Update REDIS_URL to full format for the Python app
    export REDIS_URL="redis://$REDIS_URL"
  fi
fi

REDIS_HOST=${REDIS_HOST:-localhost}
REDIS_PORT=${REDIS_PORT:-6379}

# Wait for Redis to be ready
echo "Waiting for Redis at $REDIS_HOST:$REDIS_PORT..."
while ! nc -z $REDIS_HOST $REDIS_PORT; do
  echo "Redis not ready yet, waiting..."
  sleep 2
done
echo "Redis is ready!"

# Start the worker
exec python -m hoistscraper.worker