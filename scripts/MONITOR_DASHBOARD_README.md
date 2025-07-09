# HoistScout Job Monitoring Dashboard

A comprehensive real-time monitoring tool for tracking job processing, Redis queue health, and worker status.

## Available Versions

1. **Full Version** (`monitor_jobs.py`) - Feature-rich dashboard with CLI and web interfaces
2. **Simple Version** (`monitor_jobs_simple.py`) - Lightweight dashboard with no external dependencies

## Features

- **Real-time Statistics**: Monitor pending, running, completed, and failed jobs
- **Redis Queue Monitoring**: Track queue lengths and connection health
- **Worker Health Status**: Check if workers are active and processing jobs
- **Job Processing Rate**: Calculate jobs processed per hour
- **Alerts**: Get notified when jobs are stuck or systems are down
- **Recent Jobs View**: See the last 10 jobs with their status and duration
- **Dual Mode**: Available as both CLI and web dashboard

## Installation

### Full Version

The full dashboard requires Python 3.8+ and the following dependencies:

```bash
pip install redis rich requests

# For web mode (optional)
pip install flask
```

### Simple Version

The simple version requires only Python 3.8+ with no external dependencies. It uses only standard library modules.

## Usage

### Simple Version (No Dependencies)

```bash
# Basic usage
python scripts/monitor_jobs_simple.py

# Custom update interval (3 seconds)
python scripts/monitor_jobs_simple.py --interval 3

# Connect to production
python scripts/monitor_jobs_simple.py --api-url https://hoistscout-api.onrender.com
```

### Full Version

#### CLI Mode (Default)

```bash
# Basic usage
python scripts/monitor_jobs.py

# Custom update interval (3 seconds)
python scripts/monitor_jobs.py --interval 3

# Connect to production
python scripts/monitor_jobs.py --api-url https://hoistscout-api.onrender.com

# Custom Redis URL
python scripts/monitor_jobs.py --redis-url redis://username:password@host:port
```

#### Web Dashboard Mode

```bash
# Start web dashboard on default port (5555)
python scripts/monitor_jobs.py --mode web

# Custom port
python scripts/monitor_jobs.py --mode web --port 8080

# Production web dashboard
python scripts/monitor_jobs.py --mode web --api-url https://hoistscout-api.onrender.com
```

Access the web dashboard at `http://localhost:5555`

## Command Line Options

- `--mode {cli,web}`: Dashboard mode (default: cli)
- `--interval SECONDS`: Update interval in seconds (default: 5)
- `--api-url URL`: API URL (default: http://localhost:8000)
- `--redis-url URL`: Redis URL (default: from environment or config)
- `--port PORT`: Web dashboard port (default: 5555)
- `--username USER`: API username (default: demo)
- `--password PASS`: API password (default: demo123)

## Dashboard Sections

### CLI Dashboard

1. **System Health**
   - Redis connection status and latency
   - API health check
   - Worker availability
   - Memory usage and uptime

2. **Queue Status**
   - Individual queue lengths
   - Total tasks in all queues
   - Unacknowledged tasks

3. **Job Statistics**
   - Count by status (pending, running, completed, failed, cancelled)
   - Visual progress bars
   - Processing rate (jobs/hour)

4. **Recent Jobs**
   - Last 10 jobs with details
   - Job duration tracking
   - Real-time status updates

5. **Alerts**
   - Jobs stuck in pending > 10 minutes
   - System connectivity issues
   - Worker health problems

### Web Dashboard

The web dashboard provides the same information in a browser-friendly format with:
- Auto-refreshing every 5 seconds
- Real-time charts showing job processing trends
- Responsive design for mobile and desktop
- Dark theme for comfortable viewing

## Monitoring Production

To monitor the production deployment:

```bash
# CLI mode
python scripts/monitor_jobs.py \
  --api-url https://hoistscout-api.onrender.com \
  --redis-url $REDIS_URL

# Web mode
python scripts/monitor_jobs.py \
  --mode web \
  --api-url https://hoistscout-api.onrender.com \
  --port 5555
```

## Interpreting Metrics

### Healthy System Indicators
- ✅ Redis connected with < 100ms latency
- ✅ API responding to health checks
- ✅ Workers available and active
- ✅ Jobs moving from pending → running → completed
- ✅ Processing rate > 0 jobs/hour

### Warning Signs
- ⚠️ Jobs stuck in pending for > 10 minutes
- ⚠️ High number of failed jobs
- ⚠️ Redis disconnected or high latency
- ⚠️ No workers available
- ⚠️ Processing rate = 0 with pending jobs

## Troubleshooting

### "Authentication failed"
- Check API is running and accessible
- Verify username/password are correct
- For production, ensure API URL is correct

### "Redis connection failed"
- Check Redis is running
- Verify Redis URL is correct
- Check network connectivity

### "No workers available"
- Ensure Celery workers are running
- Check worker logs for errors
- Verify Redis connectivity from workers

## Development

The monitor uses:
- `rich` for the CLI interface
- `redis` for direct queue inspection
- `requests` for API communication
- `flask` for the web dashboard (optional)
- `asyncio` for concurrent operations

## Security Notes

- API tokens are stored in memory only
- Redis passwords are masked in display
- Web dashboard should be secured in production
- Use environment variables for sensitive data