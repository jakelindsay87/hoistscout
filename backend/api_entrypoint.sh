#!/bin/sh

# Handle REDIS_URL in different formats
if [ -n "$REDIS_URL" ]; then
  # Check if it's already a full redis:// URL
  if echo "$REDIS_URL" | grep -q "^redis://"; then
    echo "REDIS_URL already in correct format"
  else
    # Assume it's just host:port format from Render
    echo "Converting REDIS_URL from host:port to redis:// format"
    export REDIS_URL="redis://$REDIS_URL"
  fi
fi

echo "Starting API with REDIS_URL: $REDIS_URL"

# Start the API
exec uvicorn hoistscraper.main:app --host 0.0.0.0 --port $PORT