# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Important**: Use context7 for accessing up-to-date library documentation when needed.

## Project Overview

HoistScraper is a web scraping platform designed to collect funding opportunities from various grant and funding websites. It consists of a FastAPI backend, Next.js frontend, PostgreSQL database, and Redis-based job queue system for asynchronous scraping operations.

## System Architecture

### Core Components
- **Backend** (FastAPI + Python 3.11): RESTful API at `backend/` handling data management and scraping orchestration
- **Frontend** (Next.js 14 + TypeScript): User interface at `frontend/` for managing sites and viewing results  
- **Worker** (RQ + Playwright): Background job processor for web scraping tasks
- **Database** (PostgreSQL/SQLite): Stores websites, jobs, and scraping results
- **Queue** (Redis + RQ): Manages asynchronous scraping jobs

### Key Architectural Patterns
1. **API Design**: Router-based organization with automatic OpenAPI docs at `/docs`
   - `/api/sites` - Website CRUD operations
   - `/api/ingest/csv` - Bulk CSV import with validation
   - `/api/scrape/{id}` - Trigger scraping jobs
   - `/api/jobs` - Job status and management
   - `/api/results/{job_id}` - Retrieve scraping results

2. **Database Models** (SQLModel at `backend/hoistscraper/models.py`):
   - `Website`: Scraping targets with URL and metadata
   - `ScrapeJob`: Tracks job status (pending/running/completed/failed)
   - Auto-migration on startup via `init_db()`

3. **Worker Architecture**:
   - Redis-based job queue using RQ
   - Playwright with stealth mode for scraping
   - Results stored as JSON in `/data` directory
   - Configurable proxies and rate limiting

4. **Frontend Data Flow**:
   - SWR hooks for data fetching/caching
   - Real-time job status polling
   - Toast notifications for user feedback

## Development Commands

### Running the Full Stack
```bash
# With Docker (recommended)
docker compose up --build

# Without Docker
# Terminal 1: Backend
cd backend && poetry run uvicorn hoistscraper.main:app --reload

# Terminal 2: Worker  
cd backend && poetry run python -m hoistscraper.worker

# Terminal 3: Frontend
cd frontend && npm run dev
```

### Testing
```bash
# Backend tests
cd backend
poetry run pytest                    # All tests
poetry run pytest -m "not integration"  # Unit tests only
poetry run pytest -m integration     # Integration tests (needs DB)
poetry run pytest tests/test_worker.py -v  # Specific test file

# Frontend tests
cd frontend  
npm test                # Run once
npm run test:watch      # Watch mode
npm run type-check      # TypeScript checking
```

### Code Quality
```bash
# Backend
cd backend
poetry run ruff check .     # Linting
poetry run ruff format .    # Auto-format
poetry run mypy .          # Type checking

# Frontend
cd frontend
npm run lint              # ESLint
npm run type-check        # TypeScript
```

### Database Operations
```bash
# Reset database (Docker)
docker compose down -v
docker compose up --build

# Manual migration (if needed)
cd backend
poetry run python -c "from hoistscraper.db import init_db; init_db()"
```

## Key Implementation Details

### CSV Ingestion (`/api/ingest/csv`)
- Validates URLs with regex pattern
- Sanitizes input strings  
- Chunks processing for memory efficiency
- Detects and skips duplicates
- Returns import statistics

### Web Scraping
- Uses Playwright with stealth plugins
- Configurable proxy support via `PROXY_URL`
- Rate limiting to respect robots.txt
- Stores results as JSON with metadata
- Handles authentication (placeholder for future)

### Error Handling
- Custom exceptions: `CaptchaChallenge`, `AuthFailure`
- Structured error responses with status codes
- Comprehensive logging throughout

### Security Considerations
- URL validation to prevent SSRF
- Input sanitization for XSS prevention
- File size limits on CSV uploads
- Optional auth requirement via `REQUIRE_AUTH_FOR_INGEST`

## Environment Variables

### Required
- `DATABASE_URL`: PostgreSQL connection (defaults to SQLite in dev)
- `REDIS_URL`: Redis connection (defaults to localhost)

### Optional
- `OLLAMA_HOST`: AI service URL (currently disabled)
- `PROXY_URL`: HTTP proxy for scraping
- `CSV_MAX_FILE_SIZE`: Max upload size in MB (default: 10)
- `REQUIRE_AUTH_FOR_INGEST`: Enable auth for CSV endpoint
- `DATA_DIR`: Result storage directory (default: /data)

## Current Development State

### Recently Completed (feature/dashboard-mvp)
- API client with retry logic (`frontend/src/lib/apiFetch.ts`)
- SWR data hooks for sites, jobs, results
- Complete UI pages with loading states
- Frontend tests with Vitest and MSW
- CI job separation (test-fe)

### Known Issues
- Import error with `BaseCrawler` (fixed by removing unused import)
- Frontend build requires increased memory: `NODE_OPTIONS="--max-old-space-size=2048"`
- Vitest deprecation warning about CJS

### Upcoming Tasks (from docs/task-breakdown.md)
1. **feature/ci-hardening**: Add strict linting and type checking
2. **feature/render-stack**: Deploy to Render.com
3. **feature/ux-refresh**: UI improvements with shadcn/ui
4. **feature/site-credentials**: Encrypted credential storage

## Testing Strategy

### Backend
- Unit tests mock database and external services
- Integration tests use real PostgreSQL
- Worker tests use fakeredis
- Fixtures in `tests/conftest.py`

### Frontend  
- Component tests with React Testing Library
- API mocking with MSW
- Hook tests for data fetching logic
- Build verification in CI

## Deployment Notes

- Configured for Render.com (see `render.yaml` blueprint)
- Memory-optimized builds for 512MB containers
- Health endpoints at `/health` (backend) 
- Static frontend deployment with API proxy
- Worker runs as background service

## Quick Debugging

### Common Issues
1. **Import errors**: Check PYTHONPATH and `__init__.py` files
2. **Database connection**: Verify DATABASE_URL and PostgreSQL is running
3. **Redis connection**: Ensure Redis is running for job queue
4. **CORS errors**: Backend allows frontend origin in development
5. **Memory issues**: Use NODE_OPTIONS for frontend builds

### Useful Commands
```bash
# Check backend logs
docker compose logs backend -f

# Access database
docker compose exec db psql -U postgres -d hoistscraper

# Monitor Redis queue
docker compose exec redis redis-cli
> KEYS rq:*
> LLEN rq:queue:default

# Restart specific service
docker compose restart worker
```

## Development Workflow

### Branch and PR Strategy
Each feature should be developed in isolation following this workflow:

1. **Create Feature Branch**
   ```bash
   # Create and switch to new feature branch
   git checkout -b feature/your-feature-name
   ```

2. **Local Development & Testing**
   ```bash
   # Run full stack locally with Docker
   docker compose up --build
   
   # Run all tests before committing
   cd backend && poetry run pytest
   cd frontend && npm test && npm run type-check && npm run lint
   ```

3. **Commit Changes**
   ```bash
   # Stage and commit with descriptive message
   git add .
   git commit -m "feat: describe your changes"
   ```

4. **Push and Create PR**
   ```bash
   # Push branch to GitHub
   git push -u origin feature/your-feature-name
   
   # Create PR using GitHub CLI
   gh pr create --title "Feature: Your feature name" --body "Description of changes"
   ```

5. **Review Process**
   - Claude reviews PR for code quality and test coverage
   - Run CI/CD checks (automated via GitHub Actions)
   - Address any feedback before merging

6. **Merge to Main**
   ```bash
   # After approval, merge via GitHub UI or CLI
   gh pr merge --squash
   
   # Clean up local branch
   git checkout main
   git pull
   git branch -d feature/your-feature-name
   ```

### Best Practices
- Always test locally with Docker before pushing
- Create atomic PRs focused on single features
- Include tests for new functionality
- Update documentation as needed
- Never push directly to main branch