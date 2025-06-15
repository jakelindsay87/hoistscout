# HoistScraper Testing Strategy

## Overview
This document outlines a comprehensive testing strategy to ensure all services are functioning correctly before deployment to Render. Our goal is to achieve "all green" status across all services.

## Testing Levels

### 1. Unit Tests
- **Backend**: Python unit tests with pytest
- **Frontend**: React component tests with Vitest
- **Coverage Target**: 90%+

### 2. Integration Tests
- **API Integration**: Test all endpoints with real database
- **Redis Integration**: Test job queueing and processing
- **Worker Integration**: Test scraping workflow

### 3. End-to-End Tests
- **Full Workflow**: Test complete scraping process from UI to results
- **Docker Compose**: Test all services together locally
- **Deployment Simulation**: Test with production-like environment

## Service-Specific Testing

### Frontend (Next.js)
```bash
# Tests to run:
npm run test           # Unit tests
npm run type-check     # TypeScript validation
npm run lint          # ESLint checks
npm run build         # Build verification
npm run start         # Production server test
```

**Key Areas:**
- API connectivity
- Environment variable handling
- Page rendering
- Error boundaries
- Data fetching with SWR

### Backend API (FastAPI)
```bash
# Tests to run:
poetry run pytest                      # All tests
poetry run pytest -m "not integration" # Unit tests only
poetry run pytest -m integration       # Integration tests
poetry run mypy .                      # Type checking
poetry run ruff check .                # Linting
```

**Key Areas:**
- Database connectivity
- Redis connectivity
- API endpoints (CRUD operations)
- CSV ingestion
- Job creation
- Health endpoint

### Worker (RQ + Playwright)
```bash
# Tests to run:
poetry run pytest tests/test_worker.py -v
poetry run python -m hoistscraper.worker --burst  # Test mode
```

**Key Areas:**
- Redis connection
- Job processing
- Playwright browser launch
- Scraping functionality
- Error handling

### Redis
**Key Areas:**
- Service availability
- Connection from API
- Connection from Worker
- Job persistence

## Testing Scripts

### 1. Local Environment Test (`scripts/test-local.sh`)
Tests all services locally without Docker.

### 2. Docker Compose Test (`scripts/test-docker.sh`)
Tests all services in Docker containers.

### 3. Pre-deployment Test (`scripts/test-predeploy.sh`)
Final verification before pushing to production.

### 4. Post-deployment Test (`scripts/test-postdeploy.sh`)
Verify services after deployment to Render.

## Test Data

### Required Test Data:
1. **Test Websites**: Known URLs that return predictable content
2. **Test CSV**: Sample CSV file with valid website data
3. **Test Credentials**: Mock credentials for authenticated sites

## Success Criteria

### All Green Checklist:
- [ ] All unit tests pass (Frontend + Backend)
- [ ] All integration tests pass
- [ ] Docker Compose runs without errors
- [ ] All health endpoints return 200 OK
- [ ] Frontend can fetch data from API
- [ ] API can queue jobs in Redis
- [ ] Worker can process jobs from Redis
- [ ] End-to-end scraping workflow completes
- [ ] No TypeScript errors
- [ ] No linting errors
- [ ] All builds complete successfully

## Error Tracking

### Common Issues to Check:
1. **Module Not Found**: Missing dependencies or incorrect imports
2. **Connection Refused**: Service discovery or networking issues
3. **Database Errors**: Migration or connection string issues
4. **Redis Errors**: Connection or authentication issues
5. **CORS Errors**: Frontend-backend communication
6. **Memory Errors**: Build memory limits
7. **Permission Errors**: File system or user permissions

## Continuous Testing

### Pre-commit Hooks:
- Run linting
- Run type checking
- Run unit tests

### CI/CD Pipeline:
- Run all tests on every push
- Block deployment if tests fail
- Generate test reports

### Monitoring:
- Health check endpoints
- Error logging
- Performance metrics

## Testing Commands Summary

```bash
# Full test suite
make test-all

# Individual service tests
make test-frontend
make test-backend
make test-worker

# Docker tests
make test-docker

# Pre-deployment verification
make verify-deploy

# Post-deployment health check
make health-check
```

## Implementation Priority

1. **Phase 1**: Get all unit tests passing
2. **Phase 2**: Get Docker Compose working locally
3. **Phase 3**: Fix integration test failures
4. **Phase 4**: Implement pre-deployment verification
5. **Phase 5**: Deploy and verify in production