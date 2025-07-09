# Redis Queue Checker for HoistScout

This script helps diagnose issues with Celery tasks not being processed by directly inspecting the Redis queue contents.

## What it does

The script connects to your Redis instance and:
- Lists all Celery-related keys
- Checks all standard Celery queues (celery, default, high_priority, low_priority)
- Shows pending tasks in each queue with details
- Checks for unacknowledged tasks
- Displays recent task results and their status
- Shows Redis server information

## Usage

### Method 1: Using Environment Variable (Recommended for Production)

```bash
# Set your production Redis URL
export REDIS_URL="redis://:your-password@your-redis-host:port/0"

# Run the script
cd /root/hoistscout-repo/backend
python check_prod_redis.py
```

### Method 2: Using Command Line Argument

```bash
cd /root/hoistscout-repo/backend
python check_prod_redis.py "redis://:your-password@your-redis-host:port/0"
```

### Method 3: For Local Testing

```bash
# If Redis is running locally without password
python check_prod_redis.py "redis://localhost:6379/0"
```

## Getting Your Production Redis URL

Your production Redis URL should be available in your deployment environment variables. It typically looks like:

- **Render.com**: Check your Redis service dashboard
- **Railway**: Available in your service variables
- **Heroku**: Check Redis add-on settings
- **AWS ElastiCache**: Use the endpoint from your ElastiCache console

The URL format is: `redis://[:password]@host:port/database_number`

## What to Look For

1. **Pending Tasks**: If you see tasks in the queues, it means they're queued but not being processed
2. **Unacknowledged Tasks**: These are tasks that were picked up by workers but not completed
3. **Task Results**: Check if tasks are failing with errors
4. **Connected Clients**: Should show at least 1 client (your Celery worker)

## Example Output

```
🔍 Connecting to Redis...
   URL: redis-server.example.com:6379
✅ Successfully connected to Redis

📦 Queue: celery
   Found 5 tasks in key: celery
   Task 1: {'task': 'scrape_equipment_task', 'id': '123...', 'args': ['CAT-12345']}
   ...

🔍 Checking for unacknowledged tasks...
   ✅ No unacknowledged task keys found

📊 Checking Celery task results...
   Found 10 task result(s)
   - Task abc123:
     Status: SUCCESS
     Task: scrape_equipment_task
```

## Troubleshooting

If you see tasks in the queue but they're not being processed:
1. Check if Celery workers are running: `celery -A app.celery_app status`
2. Check worker logs for errors
3. Ensure workers are listening to the correct queues
4. Verify Redis connection settings match between Django and Celery

## Security Note

⚠️ **Never commit Redis URLs with passwords to version control!**

Always use environment variables for sensitive configuration.