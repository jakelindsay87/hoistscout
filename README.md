# HoistScraper

A mono-repo web scraping platform with FastAPI backend, Next.js frontend, and Ollama AI integration.

## Quick Start

```bash
docker compose up --build
```

- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Ollama API**: http://localhost:11434

## Architecture

- **Backend** (`./backend/`): FastAPI with Playwright crawler, Firecrawl integration, and Ollama AI
- **Frontend** (`./frontend/`): Next.js 14 with shadcn/ui components
- **AI**: Ollama with Mistral 7B model for content extraction and analysis

## Development

### Backend
```bash
cd backend
poetry install
poetry run uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Services

- **Ollama**: AI model server (Mistral 7B)
- **Backend**: FastAPI application with web scraping capabilities
- **Frontend**: Next.js web interface 