# Local Docker Deployment Guide

## Prerequisites

1. **Enable Docker Desktop WSL Integration:**
   - Open Docker Desktop
   - Go to Settings > Resources > WSL Integration
   - Enable integration with your WSL distro
   - Apply & Restart

2. **Or run from Windows PowerShell/CMD:**
   - Open PowerShell as Administrator
   - Navigate to: `cd C:\Users\jacob\hoistscraper`

## Deployment Steps

### Option 1: Full Deployment (Recommended)

```bash
# Start all services
docker-compose up -d

# Watch the logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### Option 2: Test Deployment with Memory Limits

```bash
# Start services with Render-like constraints
docker-compose -f docker-compose.test.yml up -d

# Monitor memory usage
docker stats

# Check logs
docker-compose -f docker-compose.test.yml logs -f
```

### Option 3: Step-by-Step Deployment

```bash
# 1. Start database first
docker-compose up -d db

# 2. Wait for database to be ready (watch logs)
docker-compose logs -f db

# 3. Start backend
docker-compose up -d backend

# 4. Check backend health
curl http://localhost:8000/health

# 5. Start frontend
docker-compose up -d frontend

# 6. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
```

## Troubleshooting

### If builds fail with memory errors:

```bash
# Build with limited memory
docker build -f frontend/Dockerfile . -t frontend-test --memory="512m"

# Or use BuildKit
DOCKER_BUILDKIT=1 docker-compose build
```

### If services won't start:

```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Restart individual services
docker-compose restart backend
docker-compose restart frontend
```

### Clean up and retry:

```bash
# Stop everything
docker-compose down

# Remove volumes (database data)
docker-compose down -v

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d
```

## Monitoring

```bash
# Watch all logs
docker-compose logs -f

# Check memory/CPU usage
docker stats

# Test API
curl http://localhost:8000/health
curl http://localhost:8000/sites

# Access database
docker-compose exec db psql -U postgres -d hoistscraper
```

## Expected Output

When everything is working:
- Database: Healthy and accepting connections
- Backend: Running on http://localhost:8000
- Frontend: Running on http://localhost:3000
- All health checks passing

## Stop Services

```bash
# Stop but keep data
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove everything including volumes
docker-compose down -v
```