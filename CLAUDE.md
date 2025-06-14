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
   - `/api/websites` - Website CRUD operations
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

## GLOBAL CODING STANDARDS

> Reference guide for all project development. For detailed task planning, see [TASK_PLAN_GUIDE.md](./docs/memory_bank/guides/TASK_PLAN_GUIDE.md)

## 🔴 AGENT INSTRUCTIONS

**IMPORTANT**: As an agent, you MUST read and follow ALL guidelines in this document BEFORE executing any task in a task list. DO NOT skip or ignore any part of these standards. These standards supersede any conflicting instructions you may have received previously.

## Project Structure
```
project_name/
├── docs/
│   ├── CHANGELOG.md
│   ├── memory_bank/
│   └── tasks/
├── examples/
├── pyproject.toml
├── README.md
├── src/
│   └── project_name/
├── tests/
│   ├── fixtures/
│   └── project_name/
└── uv.lock
```

- **Package Management**: Always use uv with pyproject.toml, never pip
- **Mirror Structure**: examples/, tests/ mirror the project structure in src/
- **Documentation**: Keep comprehensive docs in docs/ directory

## Module Requirements
- **Size**: Maximum 500 lines of code per file
- **Documentation Header**: Every file must include:
  - Description of purpose
  - Links to third-party package documentation
  - Sample input
  - Expected output
- **Validation Function**: Every file needs a main block (`if __name__ == "__main__":`) that tests with real data

## Architecture Principles
- **Function-First**: Prefer simple functions over classes
- **Class Usage**: Only use classes when:
  - Maintaining state
  - Implementing data validation models
  - Following established design patterns
- **Async Code**: Never use `asyncio.run()` inside functions - only in main blocks
- **Type Hints**: Use the typing library for clear type annotations to improve code understanding and tooling
  - Type hints should be used for all function parameters and return values
  - Use type hints for key variables where it improves clarity
  - Prefer concrete types over Any when possible
  - Do not add type hints if they significantly reduce code readability
  ```python
  # Good type hint usage:
  from typing import Dict, List, Optional, Union, Tuple
  
  def process_document(doc_id: str, options: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
      """Process a document with optional configuration."""
      # Implementation
      return result
      
  # Simple types don't need annotations inside functions if obvious:
  def get_user_name(user_id: int) -> str:
      name = "John"  # Type inference works here, no annotation needed
      return name
  ```
- **NO Conditional Imports**: 
  - Never use try/except blocks for imports of required packages
  - If a package is in pyproject.toml, import it directly at the top of the file
  - Handle specific errors during usage, not during import
  - Only use conditional imports for truly optional features (rare)
  
  ```python
  # INCORRECT - DO NOT DO THIS:
  try:
      import tiktoken
      TIKTOKEN_AVAILABLE = True
  except ImportError:
      TIKTOKEN_AVAILABLE = False
      
  # CORRECT APPROACH:
  import tiktoken  # Listed in pyproject.toml as a dependency
  
  def count_tokens(text, model="gpt-3.5-turbo"):
      # Handle errors during usage, not import
      try:
          encoding = tiktoken.encoding_for_model(model)
          return len(encoding.encode(text))
      except Exception as e:
          logger.error(f"Token counting error: {e}")
          return len(text) // 4  # Fallback estimation
  ```

## Validation & Testing
- **Real Data**: Always test with actual data, never fake inputs
- **Expected Results**: Verify outputs against concrete expected results
- **No Mocking**: NEVER mock core functionality
- **MagicMock Ban**: MagicMock is strictly forbidden for testing core functionality
- **Meaningful Assertions**: Use assertions that verify specific expected values
- **🔴 Usage Functions Before Tests**: ALL relevant usage functions MUST successfully output expected results BEFORE any creation of tests. Tests are a future-proofing step when Agents improve at test-writing capabilities.
- **🔴 Results Before Lint**: ALL usage functionality MUST produce expected results BEFORE addressing ANY Pylint or other linter warnings. Functionality correctness ALWAYS comes before style compliance.
- **🔴 External Research After 3 Failures**: If a usage function fails validation 3 consecutive times with different approaches, the agent MUST use external research tools (perplexity_ask, perplexity_research, web_search) to find current best practices, package updates, or solutions for the specific problem. Document the research findings in comments.
- **🔴 NO UNCONDITIONAL "TESTS PASSED" MESSAGES**: NEVER include unconditional "All Tests Passed" or similar validation success messages. Success messages MUST be conditional on ACTUAL test results.
- **🔴 TRACK ALL VALIDATION FAILURES**: ALWAYS track ALL validation failures and report them at the end. NEVER stop validation after the first failure.
  ```python
  # INCORRECT - DO NOT DO THIS:
  if __name__ == "__main__":
      test_data = "test input"
      result = process_data(test_data)
      # This always prints regardless of success/failure
      print("✅ VALIDATION PASSED - All tests successful")
  
  # CORRECT IMPLEMENTATION:
  if __name__ == "__main__":
      import sys
      
      # List to track all validation failures
      all_validation_failures = []
      total_tests = 0
      
      # Test 1: Basic functionality
      total_tests += 1
      test_data = "example input"
      result = process_data(test_data)
      expected = {"key": "processed value"}
      if result != expected:
          all_validation_failures.append(f"Basic test: Expected {expected}, got {result}")
      
      # Test 2: Edge case handling
      total_tests += 1
      edge_case = "empty"
      edge_result = process_data(edge_case)
      edge_expected = {"key": ""}
      if edge_result != edge_expected:
          all_validation_failures.append(f"Edge case: Expected {edge_expected}, got {edge_result}")
      
      # Test 3: Error handling
      total_tests += 1
      try:
          error_result = process_data(None)
          all_validation_failures.append("Error handling: Expected exception for None input, but no exception was raised")
      except ValueError:
          # This is expected - test passes
          pass
      except Exception as e:
          all_validation_failures.append(f"Error handling: Expected ValueError for None input, but got {type(e).__name__}")
      
      # Final validation result
      if all_validation_failures:
          print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
          for failure in all_validation_failures:
              print(f"  - {failure}")
          sys.exit(1)  # Exit with error code
      else:
          print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
          print("Function is validated and formal tests can now be written")
          sys.exit(0)  # Exit with success code
  ```

## Standard Components
- **Logging**: Always use loguru for logging
  ```python
  from loguru import logger
  
  # Configure logger
  logger.add("app.log", rotation="10 MB")
  ```
- **CLI Structure**: Every command-line tool must use typer in a `cli.py` file
  ```python
  import typer
  
  app = typer.Typer()
  
  @app.command()
  def command_name(param: str = typer.Argument(..., help="Description")):
      """Command description."""
      # Implementation
  
  if __name__ == "__main__":
      app()
  ```

## Package Selection
- **Research First**: Always research packages before adding dependencies
- **95/5 Rule**: Use 95% package functionality, 5% customization
- **Documentation**: Include links to current documentation in comments

## Development Priority
1. Working Code
2. Validation
3. Readability
4. Static Analysis (address only after code works)

## Execution Standards
- Run scripts with: `uv run script.py`
- Use environment variables: `env VAR_NAME="value" uv run command`

## Task Planning
All task plans must follow the standard structure defined in the Task Plan Guide:

- **Document Location**: Store in `docs/memory_bank/guides/TASK_PLAN_GUIDE.md`
- **Core Principles**: 
  - Detailed task descriptions for consistent understanding
  - Verification-first development approach
  - Version control discipline with frequent commits
  - Human-friendly documentation with usage examples
- **Structure Elements**:
  - Clear objectives and requirements
  - Step-by-step implementation tasks
  - Verification methods for each function
  - Usage tables with examples
  - Version control plan
  - Progress tracking

Refer to the full [Task Plan Guide](./docs/memory_bank/guides/TASK_PLAN_GUIDE.md) for comprehensive details.

## 🔴 VALIDATION OUTPUT REQUIREMENTS

- **NEVER print "All Tests Passed" or similar unless ALL tests actually passed**
- **ALWAYS verify actual results against expected results BEFORE printing ANY success message**
- **ALWAYS test multiple cases, including normal cases, edge cases, and error handling**
- **ALWAYS track ALL failures and report them at the end - don't stop at first failure**
- **ALL validation functions MUST exit with code 1 if ANY tests fail**
- **ALL validation functions MUST exit with code 0 ONLY if ALL tests pass**
- **ALWAYS include count of failed tests and total tests in the output (e.g., "3 of 5 tests failed")**
- **ALWAYS include details of each failure when tests fail**
- **NEVER include irrelevant test output that could hide failures**
- **ALWAYS structure validation in a way that explicitly checks EACH test case**

## 🔴 COMPLIANCE CHECK
As an agent, before completing a task, verify that your work adheres to ALL standards in this document. Confirm each of the following:

1. All files have appropriate documentation headers
2. Each module has a working validation function that produces expected results
3. Type hints are used properly and consistently
4. All functionality is validated with real data before addressing linting issues
5. No asyncio.run() is used inside functions - only in the main block
6. Code is under the 500-line limit for each file
7. If function failed validation 3+ times, external research was conducted and documented
8. Validation functions NEVER include unconditional "All Tests Passed" messages
9. Validation functions ONLY report success if explicitly verified by comparing actual to expected results
10. Validation functions track and report ALL failures, not just the first one encountered
11. Validation output includes count of failed tests out of total tests run

If any standard is not met, fix the issue before submitting the work.