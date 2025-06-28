#!/bin/bash
# Setup SSL certificates for HoistScraper using Let's Encrypt

set -e

# Configuration
DOMAIN="${1:-}"
EMAIL="${2:-}"
NGINX_SSL_DIR="./nginx/ssl"
CERTBOT_WEBROOT="/var/www/certbot"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_usage() {
    echo "Usage: $0 <domain> <email>"
    echo "Example: $0 example.com admin@example.com"
    echo ""
    echo "This script will:"
    echo "  1. Install certbot if not present"
    echo "  2. Generate SSL certificates for your domain"
    echo "  3. Configure nginx for HTTPS"
    echo "  4. Set up auto-renewal"
}

print_error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
}

print_success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

print_info() {
    echo -e "${YELLOW}INFO: $1${NC}"
}

# Check arguments
if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    print_error "Missing required arguments"
    print_usage
    exit 1
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "This script must be run as root (use sudo)"
    exit 1
fi

print_info "Setting up SSL for domain: $DOMAIN"

# Create necessary directories
print_info "Creating SSL directories..."
mkdir -p "$NGINX_SSL_DIR"
mkdir -p "$CERTBOT_WEBROOT"

# Install certbot if not present
if ! command -v certbot &> /dev/null; then
    print_info "Installing certbot..."
    apt-get update
    apt-get install -y certbot
else
    print_info "Certbot is already installed"
fi

# Stop nginx if running (to free port 80)
if docker ps | grep -q hoistscraper-nginx; then
    print_info "Stopping nginx container..."
    docker stop hoistscraper-nginx || true
fi

# Generate certificates
print_info "Generating SSL certificates..."
certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    --domains "$DOMAIN" \
    --rsa-key-size 4096

# Check if certificates were generated
if [ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    print_error "Certificate generation failed"
    exit 1
fi

# Copy certificates to nginx directory
print_info "Copying certificates to nginx directory..."
cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$NGINX_SSL_DIR/"
cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$NGINX_SSL_DIR/"

# Set proper permissions
chmod 644 "$NGINX_SSL_DIR/fullchain.pem"
chmod 600 "$NGINX_SSL_DIR/privkey.pem"

# Update nginx configuration with domain
print_info "Updating nginx configuration..."
sed -i "s/server_name _;/server_name $DOMAIN;/g" ./nginx/nginx.conf

# Create docker-compose override for production
cat > docker-compose.override.yml << EOF
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    container_name: hoistscraper-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - nginx_logs:/var/log/nginx
      - certbot_webroot:/var/www/certbot:ro
    networks:
      - app-network
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  nginx_logs:
  certbot_webroot:
EOF

# Create renewal script
print_info "Creating renewal script..."
cat > /etc/cron.d/certbot-renewal << EOF
# Renew Let's Encrypt certificates
0 0,12 * * * root certbot renew --quiet --deploy-hook "docker restart hoistscraper-nginx"
EOF

# Create a systemd timer for renewal (more reliable than cron)
cat > /etc/systemd/system/certbot-renewal.service << EOF
[Unit]
Description=Certbot Renewal
After=docker.service

[Service]
Type=oneshot
ExecStart=/usr/bin/certbot renew --quiet --deploy-hook "docker restart hoistscraper-nginx"
EOF

cat > /etc/systemd/system/certbot-renewal.timer << EOF
[Unit]
Description=Run certbot twice daily

[Timer]
OnCalendar=*-*-* 00,12:00:00
RandomizedDelaySec=3600
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Enable the timer
systemctl daemon-reload
systemctl enable certbot-renewal.timer
systemctl start certbot-renewal.timer

# Create environment file with domain
echo "DOMAIN=$DOMAIN" >> .env.production

print_success "SSL setup completed successfully!"
print_info ""
print_info "Next steps:"
print_info "1. Update your .env file with production values"
print_info "2. Start the application with: docker-compose --env-file .env.production up -d"
print_info "3. Verify HTTPS is working at: https://$DOMAIN"
print_info ""
print_info "Certificate details:"
print_info "  - Certificate: $NGINX_SSL_DIR/fullchain.pem"
print_info "  - Private key: $NGINX_SSL_DIR/privkey.pem"
print_info "  - Auto-renewal: Enabled (runs twice daily)"
print_info ""
print_info "To test renewal:"
print_info "  certbot renew --dry-run"