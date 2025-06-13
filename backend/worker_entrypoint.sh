#!/bin/bash
set -e

# Wait for Redis to be ready
echo "Waiting for Redis..."
while ! nc -z ${REDIS_HOST:-redis} ${REDIS_PORT:-6379}; do
  sleep 1
done
echo "Redis is ready!"

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z ${DB_HOST:-postgres} ${DB_PORT:-5432}; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Start the RQ worker
echo "Starting RQ worker..."
exec rq worker \
  --url ${REDIS_URL:-redis://redis:6379/0} \
  --path /app \
  --name worker-$(hostname) \
  scraper