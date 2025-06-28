# HoistScraper Security Guide

## Overview
This guide covers security best practices for deploying HoistScraper in production.

## Required Security Configuration

### 1. Environment Variables

Before deploying to production, you MUST set the following environment variables:

```bash
# Generate secure values using the provided script
python scripts/generate_secrets.py
```

Required variables:
- `CREDENTIAL_SALT`: Random salt for credential encryption (min 32 chars)
- `CREDENTIAL_PASSPHRASE`: Secure passphrase for credential encryption (min 32 chars) 
- `API_KEY`: API authentication key for protecting endpoints
- `DB_PASSWORD`: PostgreSQL database password

### 2. Generate Secrets

Use the provided script to generate secure values:

```bash
cd /root/hoistscraper
python scripts/generate_secrets.py
```

This will:
- Generate cryptographically secure passwords
- Create proper encryption keys
- Output a complete .env configuration

### 3. SSL/HTTPS Configuration

For production, always use HTTPS:

1. **Using Let's Encrypt (Recommended)**
   ```bash
   # Install certbot
   apt-get update && apt-get install -y certbot
   
   # Generate certificate
   certbot certonly --standalone -d yourdomain.com
   
   # Certificates will be in:
   # /etc/letsencrypt/live/yourdomain.com/fullchain.pem
   # /etc/letsencrypt/live/yourdomain.com/privkey.pem
   ```

2. **Update nginx configuration**
   ```bash
   # Copy SSL certificates to nginx volume
   cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./nginx/ssl/
   cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./nginx/ssl/
   
   # Update server_name in nginx.conf
   sed -i 's/server_name _;/server_name yourdomain.com;/g' nginx/nginx.conf
   ```

3. **Auto-renewal**
   ```bash
   # Add to crontab
   0 0 * * * certbot renew --quiet --deploy-hook "docker restart hoistscraper-nginx"
   ```

### 4. API Authentication

Enable API key authentication for production:

```bash
# In your .env file
REQUIRE_AUTH=true
API_KEY=your-secure-api-key-here
```

To call protected endpoints:
```bash
curl -H "Authorization: Bearer your-secure-api-key-here" \
     https://yourdomain.com/api/scrape-jobs
```

### 5. Database Security

1. **Use strong passwords**
   ```bash
   DB_USER=hoistscraper
   DB_PASSWORD=very-secure-password-here
   ```

2. **Restrict network access**
   - Don't expose PostgreSQL port (5432) publicly
   - Use Docker networks for internal communication

3. **Regular backups**
   ```bash
   # Backup script
   docker exec hoistscraper-db pg_dump -U hoistscraper hoistscraper | gzip > backup-$(date +%Y%m%d).sql.gz
   ```

### 6. Credential Storage Security

Website credentials are encrypted using:
- PBKDF2 key derivation
- Fernet symmetric encryption
- Secure salt and passphrase

**Never**:
- Store credentials in plain text
- Commit credentials to version control
- Use default/weak encryption keys

### 7. Docker Security

1. **Run containers as non-root**
   ```yaml
   # In Dockerfile
   USER 1000:1000
   ```

2. **Limit resources**
   ```yaml
   deploy:
     resources:
       limits:
         memory: 1G
         cpus: '2'
   ```

3. **Use read-only filesystems where possible**
   ```yaml
   read_only: true
   tmpfs:
     - /tmp
   ```

### 8. Network Security

1. **Use nginx as reverse proxy**
   - Hides internal service details
   - Provides rate limiting
   - Adds security headers

2. **Rate limiting**
   ```nginx
   limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
   limit_req zone=api burst=20 nodelay;
   ```

3. **Security headers**
   - X-Frame-Options: SAMEORIGIN
   - X-Content-Type-Options: nosniff
   - X-XSS-Protection: 1; mode=block
   - Strict-Transport-Security: max-age=63072000

### 9. Monitoring & Alerts

1. **Log aggregation**
   ```yaml
   logging:
     driver: json-file
     options:
       max-size: "10m"
       max-file: "3"
   ```

2. **Error tracking (Sentry)**
   ```bash
   SENTRY_DSN=https://your-key@sentry.io/project-id
   ```

3. **Health checks**
   - Backend: http://localhost:8000/health
   - Worker: Check for running processes
   - Database: pg_isready

### 10. Security Checklist

Before going to production:

- [ ] Generated secure passwords and keys
- [ ] Set all required environment variables
- [ ] Enabled HTTPS with valid certificates
- [ ] Enabled API authentication
- [ ] Configured database with strong credentials
- [ ] Set up automated backups
- [ ] Configured log rotation
- [ ] Tested restore procedures
- [ ] Reviewed and applied security headers
- [ ] Implemented rate limiting
- [ ] Set up monitoring and alerts
- [ ] Documented emergency procedures

## Incident Response

If credentials are compromised:

1. **Immediately rotate all secrets**
   ```bash
   python scripts/generate_secrets.py
   ```

2. **Update all services**
   ```bash
   docker-compose down
   # Update .env with new values
   docker-compose up -d
   ```

3. **Audit logs for unauthorized access**
   ```bash
   docker logs hoistscraper-backend | grep -i "auth\|error"
   ```

4. **Notify affected users if applicable**

## Security Contacts

Report security issues to: security@yourdomain.com

## Regular Security Tasks

### Weekly
- Review logs for anomalies
- Check for failed authentication attempts
- Verify backups are working

### Monthly
- Rotate API keys
- Update Docker images
- Review and update dependencies

### Quarterly
- Full security audit
- Penetration testing
- Update this documentation

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)