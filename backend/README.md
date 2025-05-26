# HoistScraper Backend

FastAPI backend for the HoistScraper project with Playwright crawler and content extractor.

## Features

- FastAPI REST API for managing crawl jobs
- Playwright-based crawler with stealth mode
- Beautiful Soup HTML parsing and extraction
- Docker containerization

## Local Development

```bash
# Install dependencies
poetry install

# Run server
poetry run uvicorn hoistscraper.main:app --reload
```

## API Endpoints

- `/health` - Health check endpoint
- `/api/sites` - Manage site configurations
- `/api/opportunities` - Access scraped opportunities 