# PostgreSQL-Based Task Queue

This is a drop-in replacement for Celery that uses PostgreSQL as the task queue backend, eliminating the need for Redis.

## Features

- **No Redis Required**: Uses PostgreSQL which is already available
- **Celery-Compatible API**: Minimal code changes required
- **Task Persistence**: Tasks are stored in the database
- **Retry Support**: Automatic retry with exponential backoff
- **Priority Queue**: Tasks can have different priorities
- **Worker Scaling**: Multiple workers can process tasks concurrently
- **Task Cancellation**: Cancel pending tasks
- **Status Tracking**: Track task progress (pending, running, completed, failed)

## Quick Start

### Option 1: Use the Database Queue Script

```bash
cd backend
./start_with_db_queue.sh
```

This script will:
- Set `USE_DB_QUEUE=true` environment variable
- Start a database queue worker
- Start the FastAPI application

### Option 2: Manual Setup

1. Set the environment variable:
   ```bash
   export USE_DB_QUEUE=true
   ```

2. Start a worker:
   ```bash
   python -m app.db_worker --worker-id worker-1
   ```

3. Start the API:
   ```bash
   uvicorn app.main:app --reload
   ```

## How It Works

The database queue implementation (`db_queue.py`) provides:

1. **TaskQueueModel**: A PostgreSQL table that stores tasks
2. **DBQueue**: Main class that mimics Celery's interface
3. **Task**: Decorator for defining tasks
4. **Worker**: Process that polls the database and executes tasks
5. **TaskResult**: Object for tracking task results

### Task Flow

1. Task is submitted via `task.delay()` or `task.apply_async()`
2. Task is stored in the `task_queue` table with status `PENDING`
3. Worker polls for pending tasks using `SELECT FOR UPDATE SKIP LOCKED`
4. Worker executes the task and updates status to `STARTED`
5. On completion, status is updated to `SUCCESS` or `FAILURE`
6. Results are stored in the database

## API Compatibility

The database queue maintains compatibility with Celery's API:

```python
# Define a task
@celery_app.task(bind=True, max_retries=3)
def my_task(self, arg1, arg2):
    try:
        # Task logic here
        return result
    except Exception as exc:
        # Retry with exponential backoff
        self.retry(exc=exc, countdown=60)

# Queue a task
result = my_task.delay(arg1, arg2)

# Queue with options
result = my_task.apply_async(
    args=[arg1, arg2],
    priority=10,
    task_id='custom-id'
)

# Check status
print(result.state)  # PENDING, STARTED, SUCCESS, FAILURE

# Get result
answer = result.get(timeout=30)
```

## Configuration

The database queue uses the existing PostgreSQL connection from your app configuration. No additional configuration is required.

## Testing

Run the test suite:

```bash
python test_db_queue.py
```

This will test:
- Basic task execution
- Task retries
- Queue statistics
- Real scraping tasks

## Limitations

- No support for scheduled tasks (use cron or systemd timers instead)
- No support for task routing to specific workers
- No support for task rate limiting
- Results are stored in the database (not Redis)

## Production Considerations

1. **Database Load**: Task polling adds some load to PostgreSQL
2. **Worker Scaling**: Run multiple workers with different IDs for concurrency
3. **Task Cleanup**: Old completed tasks should be periodically cleaned up
4. **Monitoring**: Check the `task_queue` table for stuck tasks

## Troubleshooting

1. **Tasks not processing**: Check that a worker is running
2. **Database connection errors**: Verify PostgreSQL is accessible
3. **Task failures**: Check task error messages in the database
4. **Performance issues**: Consider adding indexes or adjusting polling frequency

## Migration from Celery

To migrate from Celery to the database queue:

1. Set `USE_DB_QUEUE=true` environment variable
2. Stop Celery workers
3. Start database queue workers
4. No code changes required if using standard Celery API