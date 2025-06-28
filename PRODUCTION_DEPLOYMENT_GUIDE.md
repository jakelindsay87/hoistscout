# HoistScraper Production Deployment Guide

**Version**: 1.0.0  
**Last Updated**: 2025-06-27  
**Status**: Production-Ready with Minor Configuration Required

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Quick Start](#quick-start)
3. [Detailed Deployment Steps](#detailed-deployment-steps)
4. [Security Configuration](#security-configuration)
5. [SSL/HTTPS Setup](#sslhttps-setup)
6. [Database Backup](#database-backup)
7. [Monitoring Setup](#monitoring-setup)
8. [Troubleshooting](#troubleshooting)
9. [Maintenance](#maintenance)

## Pre-Deployment Checklist

Before deploying to production, ensure you have:

- [ ] A server with Docker and Docker Compose installed
- [ ] A domain name pointing to your server
- [ ] Ports 80 and 443 open in your firewall
- [ ] At least 4GB RAM and 20GB disk space
- [ ] Generated secure passwords and API keys
- [ ] Reviewed the security configuration

## Quick Start

For experienced users who want to deploy quickly:

```bash
# 1. Clone the repository
git clone <repository-url> hoistscraper
cd hoistscraper

# 2. Copy and configure environment
cp .env.example .env
# Edit .env with your production values

# 3. Deploy without Redis (recommended)
docker-compose -f docker-compose-no-redis.yml up -d

# 4. Pull Ollama model
docker exec hoistscraper-ollama ollama pull mistral:7b-instruct

# 5. Test the deployment
curl http://localhost:3000
```

## Detailed Deployment Steps

### 1. Server Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add current user to docker group
sudo usermod -aG docker $USER
# Log out and back in for this to take effect
```

### 2. Environment Configuration

Create a secure `.env` file:

```bash
# Copy the example file
cp .env.example .env

# Generate secure values
echo "CREDENTIAL_SALT=$(openssl rand -hex 32)"
echo "CREDENTIAL_PASSPHRASE=$(openssl rand -hex 32)"
echo "API_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
echo "DB_PASSWORD=$(openssl rand -base64 32 | tr -d '=')"
```

Edit `.env` with your values:

```env
# Database Configuration
DB_USER=postgres
DB_PASSWORD=<your-secure-password>
DB_NAME=hoistscraper
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@hoistscraper-db:5432/${DB_NAME}

# Security (REQUIRED - use generated values)
CREDENTIAL_SALT=<your-generated-salt>
CREDENTIAL_PASSPHRASE=<your-generated-passphrase>
API_KEY=<your-generated-api-key>
REQUIRE_AUTH=true

# Domain Configuration
DOMAIN=yourdomain.com
FRONTEND_API_URL=https://yourdomain.com/api

# Performance
CRAWL_CONCURRENCY=3
RATE_LIMIT_DELAY=2
WORKER_THREADS=4

# Monitoring (optional)
SENTRY_DSN=your-sentry-dsn-here
```

### 3. Initial Deployment

#### Option A: Without Redis (Recommended)

```bash
# Deploy using simple queue (no Redis required)
docker-compose -f docker-compose-no-redis.yml up -d

# Check service health
docker-compose -f docker-compose-no-redis.yml ps

# View logs
docker-compose -f docker-compose-no-redis.yml logs -f
```

#### Option B: With SSL/HTTPS (Production)

```bash
# First, set up SSL certificates
sudo ./scripts/setup_letsencrypt.sh

# Deploy with SSL
docker-compose -f docker-compose-secure.yml up -d
```

### 4. Post-Deployment Setup

```bash
# 1. Pull the Ollama model (required for extraction)
docker exec hoistscraper-ollama ollama pull mistral:7b-instruct

# 2. Verify the model is loaded
docker exec hoistscraper-ollama ollama list

# 3. Import initial websites (optional)
docker exec hoistscraper-backend python -m cli.import_csv /path/to/websites.csv

# 4. Test the API
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/websites

# 5. Test scraping
curl -X POST -H "X-API-Key: your-api-key" \
  http://localhost:8000/api/scrape/1/trigger
```

## Security Configuration

### 1. API Authentication

The API uses key-based authentication. Include the API key in requests:

```bash
# In headers
curl -H "X-API-Key: your-api-key" https://yourdomain.com/api/websites

# Or as a query parameter
curl https://yourdomain.com/api/websites?api_key=your-api-key
```

### 2. Firewall Configuration

```bash
# Allow SSH (if needed)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

### 3. Secure Headers

The nginx configuration includes security headers:
- X-Frame-Options: SAMEORIGIN
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security (HSTS)
- Content-Security-Policy

## SSL/HTTPS Setup

### Automated Setup

```bash
# Run the SSL setup script
sudo ./scripts/setup_letsencrypt.sh

# Follow the prompts:
# - Enter your domain name
# - Enter your email for notifications
```

### Manual Setup

```bash
# 1. Install certbot
sudo apt install certbot

# 2. Obtain certificate
sudo certbot certonly --standalone \
  --email your-email@example.com \
  --agree-tos \
  -d yourdomain.com \
  -d www.yourdomain.com

# 3. Update docker-compose-secure.yml with paths
# 4. Deploy with SSL configuration
docker-compose -f docker-compose-secure.yml up -d
```

## Database Backup

### Automated Backup Setup

```bash
# Create backup script
cat > /root/backup_hoistscraper.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/hoistscraper"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
docker exec hoistscraper-db pg_dump -U postgres hoistscraper | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Keep only last 7 days of backups
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete
EOF

chmod +x /root/backup_hoistscraper.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /root/backup_hoistscraper.sh") | crontab -
```

### Manual Backup

```bash
# Backup database
docker exec hoistscraper-db pg_dump -U postgres hoistscraper > backup.sql

# Restore database
docker exec -i hoistscraper-db psql -U postgres hoistscraper < backup.sql
```

## Monitoring Setup

### 1. Health Checks

```bash
# Check all services
curl https://yourdomain.com/health
curl https://yourdomain.com/api/health

# Monitor with a script
while true; do
  if ! curl -sf https://yourdomain.com/health > /dev/null; then
    echo "Health check failed at $(date)"
    # Send alert (email, Slack, etc.)
  fi
  sleep 60
done
```

### 2. Logs Monitoring

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f worker

# Export logs
docker-compose logs > hoistscraper_logs_$(date +%Y%m%d).txt
```

### 3. Resource Monitoring

```bash
# Monitor Docker resource usage
docker stats

# Check disk space
df -h

# Monitor memory
free -h
```

## Troubleshooting

### Common Issues

#### 1. Worker Not Processing Jobs

```bash
# Check worker logs
docker logs hoistscraper-worker

# Restart worker
docker-compose restart worker

# Check for pending jobs
docker exec hoistscraper-backend python -c "
from hoistscraper.models import ScrapeJob
from sqlmodel import Session, select
from hoistscraper.db import engine
jobs = Session(engine).exec(select(ScrapeJob).where(ScrapeJob.status == 'pending')).all()
print(f'{len(jobs)} pending jobs')
"
```

#### 2. Ollama Not Working

```bash
# Check if Ollama is running
docker logs hoistscraper-ollama

# Test Ollama directly
curl http://localhost:11434/api/tags

# Re-pull model
docker exec hoistscraper-ollama ollama pull mistral:7b-instruct
```

#### 3. Database Connection Issues

```bash
# Check PostgreSQL logs
docker logs hoistscraper-db

# Test connection
docker exec hoistscraper-backend python -c "
from hoistscraper.db import engine
print('Database connected successfully')
"
```

#### 4. Memory Issues

```bash
# Check memory usage
docker stats --no-stream

# Reduce concurrent operations
# Edit .env:
CRAWL_CONCURRENCY=1
WORKER_THREADS=2

# Restart services
docker-compose restart
```

## Maintenance

### Regular Tasks

1. **Daily**
   - Check health endpoints
   - Monitor disk space
   - Review error logs

2. **Weekly**
   - Review scraping success rates
   - Check for failed jobs
   - Update opportunity data

3. **Monthly**
   - Update Docker images
   - Review and rotate logs
   - Test backup restoration
   - Security updates

### Updating the Application

```bash
# 1. Pull latest code
git pull origin main

# 2. Rebuild images
docker-compose -f docker-compose-no-redis.yml build

# 3. Deploy with zero downtime
docker-compose -f docker-compose-no-redis.yml up -d --no-deps --scale backend=2 backend
docker-compose -f docker-compose-no-redis.yml up -d --no-deps frontend
docker-compose -f docker-compose-no-redis.yml up -d --no-deps worker
```

### Log Rotation

```bash
# Configure Docker log rotation in /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}

# Restart Docker
sudo systemctl restart docker
```

## Performance Tuning

### 1. PostgreSQL Optimization

```bash
# Edit postgresql.conf via Docker
docker exec -it hoistscraper-db bash
echo "
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
" >> /var/lib/postgresql/data/postgresql.conf

# Restart database
docker-compose restart db
```

### 2. Nginx Caching

Add to nginx configuration for static assets:

```nginx
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 3. Application Tuning

```env
# Adjust in .env based on your server resources
CRAWL_CONCURRENCY=5      # Increase for more parallel scraping
WORKER_THREADS=6         # Increase for more concurrent jobs
RATE_LIMIT_DELAY=1       # Decrease for faster scraping (be careful)
```

## Support and Resources

- **Documentation**: Check `/docs` directory
- **API Reference**: https://yourdomain.com/docs
- **Logs Location**: `docker-compose logs [service-name]`
- **Data Location**: Docker volumes in `/var/lib/docker/volumes/`

## Final Checklist

Before considering your deployment complete:

- [ ] All services are running and healthy
- [ ] SSL certificate is installed and working
- [ ] API authentication is enabled
- [ ] Automated backups are configured
- [ ] Monitoring is in place
- [ ] You can successfully scrape a test website
- [ ] Opportunities are visible in the UI

---

**Congratulations!** Your HoistScraper instance is now running in production. Remember to monitor the logs regularly and keep the system updated.