# Testing Deployment Locally

This guide helps you test the deployment before pushing to Render.

## Prerequisites

- Docker and Docker Compose installed
- Node.js 20+ installed
- Python 3.11+ installed

## Testing Steps

### 1. Test Docker Builds

Test that both frontend and backend can build successfully:

```bash
# Test backend build
docker build -f backend/Dockerfile . -t hoistscraper-backend

# Test frontend build  
docker build -f frontend/Dockerfile . -t hoistscraper-frontend
```

### 2. Test with Memory Constraints

Run the test deployment with Render-like memory limits:

```bash
# Start all services with memory limits
docker-compose -f docker-compose.test.yml up -d

# Check if services are healthy
docker-compose -f docker-compose.test.yml ps

# Check memory usage
docker stats --no-stream

# View logs for any errors
docker-compose -f docker-compose.test.yml logs
```

### 3. Manual Memory Test

Test frontend build memory usage:

```bash
cd frontend
npm ci
NODE_OPTIONS="--max-old-space-size=384" npm run build
```

### 4. Automated Test Script

Run the comprehensive test:

```bash
./test-deployment.sh
```

This script will:
- Build all services
- Check health endpoints
- Monitor memory usage
- Validate API functionality

## Common Issues and Fixes

### Frontend Memory Issues
- The frontend Dockerfile sets `NODE_OPTIONS="--max-old-space-size=384"`
- next.config.js disables worker threads to reduce memory usage
- Build uses standalone output mode

### Backend Poetry Issues
- Dockerfile includes fallback to regenerate poetry.lock if needed
- Uses specific Poetry version (1.7.1) for consistency
- Includes `--no-interaction --no-ansi` flags

### Port Configuration
- Frontend uses `PORT` environment variable with fallback to 3000
- Backend always uses port 8000
- Test deployment uses different ports (3001, 8001) to avoid conflicts

## Deployment Checklist

Before deploying to Render:

- [ ] All Docker builds complete successfully
- [ ] Services start without errors in docker-compose.test.yml
- [ ] Memory usage stays under 512MB
- [ ] Health checks pass
- [ ] No errors in logs
- [ ] API endpoints respond correctly

## Cleanup

After testing:

```bash
# Stop test deployment
docker-compose -f docker-compose.test.yml down

# Remove test images
docker rmi hoistscraper-backend hoistscraper-frontend
```