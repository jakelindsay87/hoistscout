# HoistScout Setup Guide

## Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)
- 16GB+ RAM recommended
- 100GB+ storage for documents

## Quick Start

### 1. Clone and Initialize

```bash
git clone https://github.com/yourusername/hoistscout.git
cd hoistscout
./scripts/init-project.sh
```

### 2. Configure Environment

Edit `backend/.env` with your settings:

```bash
# Required configurations
SECRET_KEY=your-secure-secret-key-here
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/hoistscout

# Optional: 2captcha API key for CAPTCHA solving
CAPTCHA_API_KEY=your-2captcha-api-key
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# Wait for services to be ready (check with)
docker-compose ps

# Apply database migrations
docker-compose exec backend poetry run alembic upgrade head

# Create first admin user
docker-compose exec backend python -m app.scripts.create_admin
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Grafana**: http://localhost:3001 (admin/admin)

## Development Setup

### Backend Development

```bash
cd backend
poetry install
poetry shell

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
poetry run pytest

# Frontend tests
cd frontend
npm test
```

## Production Deployment

### 1. Environment Variables

Create production `.env` file:

```bash
# Production settings
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<strong-random-key>
DATABASE_URL=postgresql+asyncpg://user:pass@db-host:5432/hoistscout
REDIS_URL=redis://redis-host:6379/0

# MinIO production
MINIO_ENDPOINT=minio.yourdomain.com
MINIO_ACCESS_KEY=<secure-access-key>
MINIO_SECRET_KEY=<secure-secret-key>
MINIO_SECURE=true

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
```

### 2. Docker Compose Production

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 3. SSL/TLS Setup

Use a reverse proxy (Nginx/Caddy) for SSL termination:

```nginx
server {
    listen 443 ssl http2;
    server_name hoistscout.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Troubleshooting

### Common Issues

1. **Ollama not starting**: Ensure you have GPU drivers installed or remove GPU requirements
2. **Database connection errors**: Check PostgreSQL is running and credentials are correct
3. **MinIO connection errors**: Ensure MinIO is accessible and bucket exists
4. **Scraping failures**: Check FlareSolverr is running and accessible

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f celery
```

### Reset Database

```bash
# Drop and recreate database
docker-compose exec postgres psql -U postgres -c "DROP DATABASE hoistscout;"
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE hoistscout;"
docker-compose exec backend poetry run alembic upgrade head
```

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Next.js UI    │────▶│  FastAPI Backend │────▶│   PostgreSQL    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ├──────────────────▶ Redis (Queue)
                               │
                               ├──────────────────▶ MinIO (Storage)
                               │
                               └──────────────────▶ Ollama (LLM)
                        
┌─────────────────┐     ┌─────────────────┐
│  Celery Worker  │────▶│  ScrapeGraphAI  │
└─────────────────┘     └─────────────────┘
         │
         └──────────────▶ FlareSolverr (Anti-detection)
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/hoistscout/issues
- Documentation: https://docs.hoistscout.com