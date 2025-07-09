# Redis Health Check Endpoint

## Overview

A comprehensive Redis connectivity test endpoint has been added to help diagnose Redis connection issues in production environments. This endpoint tests Redis connectivity, performs basic operations, and checks Celery queue status.

## Endpoint Details

- **URL**: `/api/health/redis`
- **Method**: `GET`
- **Authentication**: None required (publicly accessible for easy testing)

## Response Structure

```json
{
  "timestamp": "2024-01-20T10:30:00",
  "redis_url": "redis://localhost:6379/0...",
  "connection": {
    "status": "connected|failed|disconnected",
    "error": null | "error message",
    "latency_ms": 5.23
  },
  "operations": {
    "set": {"success": true, "error": null},
    "get": {"success": true, "value": "test_value_...", "error": null},
    "delete": {"success": true, "error": null}
  },
  "celery": {
    "queues": {
      "celery": {
        "length": 5,
        "tasks": [
          {
            "id": "task-id-here",
            "name": "app.worker.scrape_website_task",
            "args": [123]
          }
        ]
      }
    },
    "total_tasks": 5,
    "unacked_tasks": 0,
    "related_keys": ["celery", "celery.priority.high"],
    "error": null
  },
  "redis_info": {
    "redis_version": "7.0.11",
    "connected_clients": 10,
    "used_memory_human": "1.5M",
    "uptime_in_seconds": 3600,
    "uptime_in_days": 0,
    "role": "master"
  },
  "healthy": true
}
```

## Testing

### Local Testing

```bash
# From the backend directory
cd /root/hoistscout-repo/backend

# Test local Redis
./test_redis_endpoint.py

# Or with Python
python test_redis_endpoint.py
```

### Production Testing

```bash
# Test production endpoint
./test_redis_endpoint_prod.py

# Or specify a custom URL
./test_redis_endpoint_prod.py https://your-api-url.com

# Using curl
curl https://hoistscout-backend.onrender.com/api/health/redis | jq
```

## What It Tests

1. **Connection Test**
   - Attempts to connect to Redis using the configured REDIS_URL
   - Measures connection latency
   - Reports any connection errors with full traceback

2. **Basic Operations**
   - **SET**: Creates a test key with expiration
   - **GET**: Retrieves the test key and verifies the value
   - **DELETE**: Removes the test key

3. **Celery Queue Status**
   - Lists all Celery queues and their lengths
   - Shows details of first few tasks in each queue
   - Counts total tasks across all queues
   - Checks for unacknowledged tasks

4. **Redis Server Info**
   - Redis version
   - Connected clients count
   - Memory usage
   - Uptime information
   - Server role (master/slave)

## Troubleshooting Guide

### Connection Failed

If `connection.status` is "failed":

1. Check the REDIS_URL environment variable
2. Verify Redis service is running
3. Check network connectivity (firewall, security groups)
4. Look at the `connection.error` and `connection.traceback` fields

### Operations Failed

If any operation fails but connection succeeds:

1. Check Redis permissions
2. Verify Redis isn't in read-only mode
3. Check available memory

### No Celery Tasks

If `celery.total_tasks` is 0:

1. Verify Celery workers are running
2. Check if tasks are being queued properly
3. Look for tasks in different queue names

### High Latency

If `connection.latency_ms` is high (>100ms):

1. Check network distance between app and Redis
2. Consider using Redis connection pooling
3. Check Redis server load

## Integration with Monitoring

This endpoint can be integrated with monitoring tools:

```bash
# Health check script for monitoring
#!/bin/bash
RESPONSE=$(curl -s https://your-api.com/api/health/redis)
HEALTHY=$(echo $RESPONSE | jq -r '.healthy')

if [ "$HEALTHY" = "true" ]; then
  echo "Redis is healthy"
  exit 0
else
  echo "Redis is unhealthy"
  echo $RESPONSE | jq
  exit 1
fi
```

## Security Notes

- This endpoint is **publicly accessible** by design for easy testing
- The Redis URL is partially masked in the response
- No sensitive data is exposed
- Test keys are automatically expired after 60 seconds