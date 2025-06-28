#!/bin/bash

# Let's Encrypt SSL Setup Script for HoistScraper
# This script helps obtain and configure SSL certificates

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

# Get domain from environment or prompt
if [ -z "$DOMAIN" ]; then
    read -p "Enter your domain name (e.g., example.com): " DOMAIN
fi

if [ -z "$EMAIL" ]; then
    read -p "Enter your email for Let's Encrypt notifications: " EMAIL
fi

echo -e "${GREEN}Setting up Let's Encrypt SSL for domain: $DOMAIN${NC}"

# Create necessary directories
echo "Creating certificate directories..."
mkdir -p ./certbot/conf
mkdir -p ./certbot/www

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Stop existing containers if running
echo "Stopping existing containers..."
docker-compose -f docker-compose-secure.yml down || true

# Start nginx temporarily for certificate verification
echo "Starting temporary nginx for certificate verification..."
cat > ./nginx/nginx-temp.conf << EOF
events {
    worker_connections 1024;
}

http {
    server {
        listen 80;
        server_name $DOMAIN www.$DOMAIN;
        
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
        
        location / {
            return 200 'Setting up SSL...';
            add_header Content-Type text/plain;
        }
    }
}
EOF

# Run temporary nginx
docker run -d \
    --name nginx-temp \
    -p 80:80 \
    -v $(pwd)/nginx/nginx-temp.conf:/etc/nginx/nginx.conf:ro \
    -v $(pwd)/certbot/www:/var/www/certbot:ro \
    nginx:alpine

# Wait for nginx to start
sleep 5

# Obtain certificate
echo -e "${YELLOW}Obtaining SSL certificate from Let's Encrypt...${NC}"
docker run -it --rm \
    -v $(pwd)/certbot/conf:/etc/letsencrypt \
    -v $(pwd)/certbot/www:/var/www/certbot \
    certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN \
    -d www.$DOMAIN

# Stop temporary nginx
docker stop nginx-temp
docker rm nginx-temp

# Check if certificate was obtained
if [ ! -f "./certbot/conf/live/$DOMAIN/fullchain.pem" ]; then
    echo -e "${RED}Failed to obtain SSL certificate${NC}"
    exit 1
fi

echo -e "${GREEN}SSL certificate obtained successfully!${NC}"

# Create environment file for Docker Compose
echo "Creating environment configuration..."
cat >> .env << EOF

# SSL Configuration
DOMAIN=$DOMAIN
SSL_CERT_PATH=/etc/letsencrypt/live/$DOMAIN/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/$DOMAIN/privkey.pem
EOF

# Set up auto-renewal cron job
echo "Setting up auto-renewal..."
cat > ./scripts/renew_ssl.sh << 'EOF'
#!/bin/bash
# SSL Certificate Renewal Script

cd /root/hoistscraper
docker-compose -f docker-compose-secure.yml run --rm certbot renew
docker-compose -f docker-compose-secure.yml exec nginx nginx -s reload
EOF

chmod +x ./scripts/renew_ssl.sh

# Add cron job for renewal (twice daily as recommended by Let's Encrypt)
CRON_CMD="0 0,12 * * * /root/hoistscraper/scripts/renew_ssl.sh >> /var/log/letsencrypt-renewal.log 2>&1"
(crontab -l 2>/dev/null | grep -v "renew_ssl.sh" ; echo "$CRON_CMD") | crontab -

echo -e "${GREEN}Auto-renewal cron job added${NC}"

# Create production deployment script
cat > ./scripts/deploy_production.sh << 'EOF'
#!/bin/bash
# Production Deployment Script

set -e

echo "Deploying HoistScraper in production mode..."

# Load environment variables
source .env

# Pull latest images
docker-compose -f docker-compose-secure.yml pull

# Start services
docker-compose -f docker-compose-secure.yml up -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 30

# Check health
docker-compose -f docker-compose-secure.yml ps

# Pull Ollama model if not already present
echo "Ensuring Ollama model is available..."
docker exec hoistscraper-ollama ollama pull mistral:7b-instruct || true

echo "Deployment complete!"
echo "Your application is now available at https://$DOMAIN"
EOF

chmod +x ./scripts/deploy_production.sh

# Final instructions
echo ""
echo -e "${GREEN}=== SSL Setup Complete! ===${NC}"
echo ""
echo "Next steps:"
echo "1. Review and update your .env file with production values"
echo "2. Run the production deployment:"
echo "   ./scripts/deploy_production.sh"
echo ""
echo "Your application will be available at:"
echo "   https://$DOMAIN"
echo ""
echo "SSL certificates will auto-renew via cron job"
echo ""
echo -e "${YELLOW}Important: Make sure port 80 and 443 are open in your firewall${NC}"