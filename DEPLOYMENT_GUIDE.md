# HoistScraper Deployment Guide

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Docker and Docker Compose installed
- 4GB RAM minimum (8GB recommended for Ollama)
- 10GB disk space

### 1. Clone and Deploy
```bash
# Clone the repository
git clone <repository-url> hoistscraper
cd hoistscraper

# Start all services
docker-compose up -d

# Wait for services to be healthy (check status)
watch docker-compose ps

# Once all services show "healthy", access the app
open http://localhost:3000
```

### 2. Test the System
```bash
# Create a test scrape job
curl -X POST http://localhost:8000/api/scrape/2/trigger

# Check the results in the UI
open http://localhost:3000/opportunities
```

## 🏭 Production Deployment

### 1. Using Ollama for Intelligent Extraction
```bash
# Deploy with Ollama included
docker-compose -f docker-compose.prod.yml up -d

# Pull the Mistral model (one-time, takes ~5 minutes)
docker exec hoistscraper-ollama ollama pull mistral:7b-instruct

# Verify Ollama is working
curl http://localhost:11434/api/tags
```

### 2. Environment Configuration
Create `.env.production`:
```env
# Database
DATABASE_URL=postgresql://postgres:strong_password@db:5432/hoistscraper

# Redis
REDIS_URL=redis://redis:6379/0

# Ollama
OLLAMA_HOST=http://ollama:11434

# Security
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-fernet-key-here

# Performance
CRAWL_CONCURRENCY=3
RATE_LIMIT_DELAY=2
```

### 3. Deploy to Cloud

#### Option A: Render.com
```bash
# Use the included render.yaml
# 1. Connect your GitHub repo to Render
# 2. Create a new Blueprint instance
# 3. Select render.yaml
# 4. Deploy
```

#### Option B: AWS ECS
```bash
# Build and push images to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URL
docker-compose build
docker-compose push

# Deploy using ECS CLI
ecs-cli compose up --cluster-config hoistscraper
```

#### Option C: Digital Ocean
```bash
# Use the included docker-compose.prod.yml
doctl apps create --spec docker-compose.prod.yml
```

## 📊 Monitoring

### 1. Check Service Health
```bash
# All services status
docker-compose ps

# Individual service logs
docker-compose logs -f backend
docker-compose logs -f worker
docker-compose logs -f frontend

# System resources
docker stats
```

### 2. Monitor Scraping Jobs
- UI: http://localhost:3000/jobs
- API: `curl http://localhost:8000/api/scrape-jobs`
- Logs: `docker-compose logs -f worker`

### 3. Database Monitoring
```bash
# Connect to PostgreSQL
docker-compose exec db psql -U postgres -d hoistscraper

# Check opportunity count
SELECT COUNT(*) FROM opportunity;

# Check recent jobs
SELECT id, website_id, status, created_at 
FROM scrapejob 
ORDER BY created_at DESC 
LIMIT 10;
```

## 🔧 Common Operations

### Start a Scrape Job
```bash
# Method 1: Via API (gets queued)
curl -X POST http://localhost:8000/api/scrape-jobs \
  -H "Content-Type: application/json" \
  -d '{"website_id": 2}'

# Method 2: Direct trigger (immediate)
curl -X POST http://localhost:8000/api/scrape/2/trigger
```

### Import New Websites
```bash
# Prepare CSV file with columns: name,url,description,category
# Then upload via API
curl -X POST http://localhost:8000/api/ingest/csv \
  -F "file=@websites.csv"
```

### Export Opportunities
1. Navigate to http://localhost:3000/opportunities
2. Apply filters as needed
3. Click "Export CSV"

### Backup Database
```bash
# Create backup
docker-compose exec db pg_dump -U postgres hoistscraper > backup_$(date +%Y%m%d).sql

# Restore backup
docker-compose exec -T db psql -U postgres hoistscraper < backup_20240627.sql
```

## 🚨 Troubleshooting

### Worker Not Processing Jobs
```bash
# Check Redis connection
docker-compose exec redis redis-cli ping

# Check job queue
docker-compose exec redis redis-cli -n 0 llen rq:queue:scraper

# Restart worker
docker-compose restart worker
```

### Ollama Not Working
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Check if model is installed
docker exec hoistscraper-ollama ollama list

# Pull model if missing
docker exec hoistscraper-ollama ollama pull mistral:7b-instruct
```

### No Opportunities Found
1. Check if the website has tender listings
2. View worker logs: `docker-compose logs -f worker`
3. Try manual URL in browser to verify content
4. Check if site requires authentication

## 🔒 Security Hardening

### 1. Enable HTTPS
```nginx
# nginx.conf
server {
    listen 80;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    ssl_certificate /etc/ssl/cert.pem;
    ssl_certificate_key /etc/ssl/key.pem;
    
    location / {
        proxy_pass http://frontend:3000;
    }
    
    location /api {
        proxy_pass http://backend:8000;
    }
}
```

### 2. Add Authentication
```bash
# Set environment variables
REQUIRE_AUTH_FOR_INGEST=true
API_KEY=your-secure-api-key
```

### 3. Network Isolation
```yaml
# docker-compose.prod.yml
networks:
  frontend:
    internal: false
  backend:
    internal: true
  data:
    internal: true
```

## 📈 Scaling

### Horizontal Scaling
```yaml
# docker-compose.scale.yml
services:
  worker:
    deploy:
      replicas: 3
```

### Performance Tuning
```env
# Increase concurrency
CRAWL_CONCURRENCY=10
MAX_WORKERS=5

# Adjust timeouts
REQUEST_TIMEOUT=60
PLAYWRIGHT_TIMEOUT=30000
```

## 🎯 Health Checks

All services include health checks:
- Backend: http://localhost:8000/health
- Frontend: http://localhost:3000/api/health  
- Redis: `redis-cli ping`
- PostgreSQL: `pg_isready`
- Ollama: http://localhost:11434/api/tags

## 📞 Support

1. Check logs: `docker-compose logs [service]`
2. Review documentation in `/docs`
3. Check `TROUBLESHOOTING.md`
4. Enable debug mode: `LOG_LEVEL=DEBUG`

---

For production deployment support, ensure you have:
- [ ] SSL certificates configured
- [ ] Strong passwords set
- [ ] Backup strategy in place
- [ ] Monitoring configured
- [ ] Rate limits adjusted for your needs