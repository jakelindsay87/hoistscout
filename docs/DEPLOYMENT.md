# HoistScraper Production Deployment Guide

## Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- Docker and Docker Compose installed
- Domain name pointing to your server
- Root or sudo access

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/hoistscraper.git
cd hoistscraper

# 2. Generate secure configuration
sudo python scripts/generate_secrets.py

# 3. Setup SSL (requires domain)
sudo ./scripts/setup_ssl.sh yourdomain.com your-email@example.com

# 4. Deploy
docker-compose --env-file .env.production -f docker-compose-no-redis.yml up -d

# 5. Initialize Ollama
docker exec hoistscraper-ollama ollama pull mistral:7b-instruct
```

## Detailed Deployment Steps

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin

# Add user to docker group (optional)
sudo usermod -aG docker $USER
```

### 2. Security Configuration

Generate secure credentials:

```bash
cd hoistscraper
sudo python scripts/generate_secrets.py
```

This creates `.env.production` with:
- Database passwords
- Encryption keys
- API authentication tokens

**Important**: Keep this file secure and never commit to version control!

### 3. SSL/HTTPS Setup

For production, always use HTTPS:

```bash
# Run the SSL setup script
sudo ./scripts/setup_ssl.sh yourdomain.com your-email@example.com
```

This will:
- Install Let's Encrypt certbot
- Generate SSL certificates
- Configure nginx for HTTPS
- Set up automatic renewal

### 4. Database Configuration

The PostgreSQL database is automatically configured with:
- Secure passwords from `.env.production`
- Data persistence in Docker volumes
- Automatic initialization on first start

### 5. Deploy the Application

```bash
# Deploy with production configuration
docker-compose --env-file .env.production -f docker-compose-no-redis.yml up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 6. Initialize Ollama LLM

The Ollama service needs to download the language model:

```bash
# Pull the Mistral 7B model (requires ~4GB)
docker exec hoistscraper-ollama ollama pull mistral:7b-instruct

# Verify model is loaded
docker exec hoistscraper-ollama ollama list
```

### 7. Import Initial Data

If you have grant sites to import:

```bash
# Copy CSV file to container
docker cp grants.csv hoistscraper-backend:/tmp/

# Import sites
docker exec hoistscraper-backend python -m hoistscraper.cli import-csv /tmp/grants.csv
```

### 8. Verify Deployment

1. **Check health endpoints**:
   ```bash
   # Backend health
   curl https://yourdomain.com/api/health
   
   # Frontend health
   curl https://yourdomain.com/
   ```

2. **Test scraping**:
   ```bash
   # Get API key from .env.production
   API_KEY=$(grep API_KEY .env.production | cut -d= -f2)
   
   # Trigger a test scrape
   curl -X POST https://yourdomain.com/api/scrape/1/trigger \
        -H "Authorization: Bearer $API_KEY"
   ```

3. **Access the UI**:
   - Open https://yourdomain.com in your browser
   - Navigate to Sites, Jobs, and Opportunities pages

## Production Configuration

### Environment Variables

Key production settings in `.env.production`:

```bash
# Security (REQUIRED - use generated values)
CREDENTIAL_SALT=<generated>
CREDENTIAL_PASSPHRASE=<generated>
API_KEY=<generated>
REQUIRE_AUTH=true

# Database
DB_USER=hoistscraper
DB_PASSWORD=<generated>
DB_NAME=hoistscraper

# Queue Configuration
USE_SIMPLE_QUEUE=true
WORKER_THREADS=4

# Scraping
CRAWL_CONCURRENCY=3
RATE_LIMIT_DELAY=2
```

### Resource Limits

Docker Compose sets memory limits:
- Backend: 1GB
- Frontend: 512MB
- Worker: 2GB
- Ollama: 4GB

Adjust in `docker-compose-no-redis.yml` if needed.

### Nginx Configuration

Production nginx features:
- SSL/TLS encryption
- Security headers
- Rate limiting
- Gzip compression
- Proxy caching

## Monitoring

### Logs

```bash
# View all logs
docker-compose logs

# Follow specific service
docker-compose logs -f worker

# Export logs
docker-compose logs > hoistscraper.log
```

### Health Checks

Monitor these endpoints:
- `https://yourdomain.com/health` - Overall health
- `https://yourdomain.com/api/stats` - Application statistics

### Database Queries

```bash
# Connect to database
docker exec -it hoistscraper-db psql -U hoistscraper

# Check job status
SELECT status, COUNT(*) FROM scrape_job GROUP BY status;

# Recent opportunities
SELECT title, created_at FROM opportunity ORDER BY created_at DESC LIMIT 10;
```

## Maintenance

### Backups

Create automated backups:

```bash
# Backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/hoistscraper"
mkdir -p "$BACKUP_DIR"

# Database backup
docker exec hoistscraper-db pg_dump -U hoistscraper hoistscraper | \
  gzip > "$BACKUP_DIR/db-$(date +%Y%m%d-%H%M%S).sql.gz"

# Keep only last 30 days
find "$BACKUP_DIR" -name "db-*.sql.gz" -mtime +30 -delete
EOF

chmod +x backup.sh

# Add to crontab
echo "0 2 * * * /path/to/backup.sh" | crontab -
```

### Updates

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose --env-file .env.production -f docker-compose-no-redis.yml up -d --build
```

### SSL Certificate Renewal

Certificates auto-renew, but you can test:

```bash
# Test renewal
sudo certbot renew --dry-run

# Force renewal
sudo certbot renew --force-renewal
```

## Troubleshooting

### Common Issues

1. **Worker not processing jobs**
   ```bash
   # Check worker logs
   docker logs hoistscraper-worker
   
   # Restart worker
   docker restart hoistscraper-worker
   ```

2. **Database connection errors**
   ```bash
   # Check database is running
   docker ps | grep hoistscraper-db
   
   # Test connection
   docker exec hoistscraper-backend python -c "from hoistscraper.db import engine; print('DB OK')"
   ```

3. **Ollama not extracting**
   ```bash
   # Check Ollama is running
   docker logs hoistscraper-ollama
   
   # Verify model is loaded
   docker exec hoistscraper-ollama ollama list
   ```

### Reset Application

If needed, completely reset:

```bash
# Stop all containers
docker-compose down

# Remove volumes (WARNING: Deletes all data!)
docker-compose down -v

# Restart fresh
docker-compose --env-file .env.production -f docker-compose-no-redis.yml up -d
```

## Security Hardening

Additional security measures:

1. **Firewall rules**
   ```bash
   # Allow only HTTP/HTTPS
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

2. **Fail2ban for brute force protection**
   ```bash
   sudo apt install fail2ban
   # Configure for nginx
   ```

3. **Regular updates**
   ```bash
   # System updates
   sudo apt update && sudo apt upgrade
   
   # Docker images
   docker-compose pull
   ```

## Performance Tuning

### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_job_status ON scrape_job(status);
CREATE INDEX idx_opportunity_created ON opportunity(created_at DESC);
```

### Worker Scaling

Adjust worker threads based on load:

```bash
# In .env.production
WORKER_THREADS=8  # Increase for more concurrency
CRAWL_CONCURRENCY=5  # More parallel scrapes
```

## Support

For issues:
1. Check logs: `docker-compose logs`
2. Review this guide
3. Check GitHub issues
4. Contact support

Remember to never share:
- `.env.production` file
- SSL private keys
- Database credentials
- API keys