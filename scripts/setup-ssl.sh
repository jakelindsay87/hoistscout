#!/bin/bash

# SSL Setup Script for HoistScraper
# This script helps set up SSL certificates and DH parameters for production deployment

set -e

echo "=== HoistScraper SSL Setup Script ==="
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
   echo "Please run as root (use sudo)"
   exit 1
fi

# Variables
DOMAIN="${1:-yourdomain.com}"
EMAIL="${2:-admin@yourdomain.com}"

echo "Setting up SSL for domain: $DOMAIN"
echo "Email for Let's Encrypt: $EMAIL"
echo

# Function to generate DH parameters
generate_dhparam() {
    echo "Generating DH parameters (this may take a while)..."
    if [ ! -f /etc/nginx/dhparam.pem ]; then
        openssl dhparam -out /etc/nginx/dhparam.pem 2048
        echo "DH parameters generated successfully"
    else
        echo "DH parameters already exist"
    fi
}

# Function to setup Let's Encrypt
setup_letsencrypt() {
    echo "Setting up Let's Encrypt certificates..."
    
    # Install certbot if not installed
    if ! command -v certbot &> /dev/null; then
        echo "Installing certbot..."
        apt-get update
        apt-get install -y certbot python3-certbot-nginx
    fi
    
    # Stop nginx if running to avoid port conflicts
    systemctl stop nginx 2>/dev/null || true
    
    # Get certificates
    certbot certonly --standalone \
        -d "$DOMAIN" \
        --non-interactive \
        --agree-tos \
        --email "$EMAIL" \
        --no-eff-email
    
    echo "SSL certificates obtained successfully"
}

# Function to setup nginx configuration
setup_nginx_config() {
    echo "Setting up nginx configuration..."
    
    # Create nginx directory if it doesn't exist
    mkdir -p /etc/nginx/sites-available
    mkdir -p /etc/nginx/sites-enabled
    
    # Copy nginx configuration
    cp nginx.conf /etc/nginx/sites-available/hoistscraper
    
    # Update domain in configuration
    sed -i "s/yourdomain.com/$DOMAIN/g" /etc/nginx/sites-available/hoistscraper
    
    # Enable the site
    ln -sf /etc/nginx/sites-available/hoistscraper /etc/nginx/sites-enabled/
    
    # Test nginx configuration
    nginx -t
    
    echo "Nginx configuration updated"
}

# Function to setup auto-renewal
setup_auto_renewal() {
    echo "Setting up automatic certificate renewal..."
    
    # Create renewal hook script
    cat > /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh << 'EOF'
#!/bin/bash
systemctl reload nginx
EOF
    
    chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
    
    # Add cron job for renewal
    (crontab -l 2>/dev/null; echo "0 2 * * * /usr/bin/certbot renew --quiet") | crontab -
    
    echo "Auto-renewal configured"
}

# Main execution
echo "1. Generating DH parameters..."
generate_dhparam

echo
echo "2. Setting up Let's Encrypt..."
setup_letsencrypt

echo
echo "3. Configuring nginx..."
setup_nginx_config

echo
echo "4. Setting up auto-renewal..."
setup_auto_renewal

echo
echo "=== SSL Setup Complete ==="
echo
echo "Next steps:"
echo "1. Update your .env.production file with the correct domain"
echo "2. Update ALLOWED_ORIGINS in your backend configuration"
echo "3. Start nginx: systemctl start nginx"
echo "4. Verify SSL: https://$DOMAIN"
echo
echo "To test certificate renewal:"
echo "  certbot renew --dry-run"
echo