# HoistScraper Security Deployment Checklist

## Pre-Deployment Security Tasks

### 1. Environment Configuration
- [ ] Generated .env.production with strong passwords
- [ ] Stored credentials in secure password manager
- [ ] Removed all hardcoded credentials from code
- [ ] Set REQUIRE_AUTH=true
- [ ] Configured ALLOWED_ORIGINS with actual domain

### 2. SSL/TLS Setup
- [ ] Obtained SSL certificate (Let's Encrypt or commercial)
- [ ] Generated DH parameters (2048-bit minimum)
- [ ] Configured nginx with SSL
- [ ] Tested SSL configuration (ssllabs.com)
- [ ] Enabled HSTS with preload

### 3. Dependency Updates
- [ ] Updated all Python dependencies: `cd backend && poetry update`
- [ ] Updated all Node.js dependencies: `cd frontend && npm update`
- [ ] Ran vulnerability scan: `cd backend && pip-audit`
- [ ] No critical vulnerabilities remain

### 4. Access Control
- [ ] Removed exposed database ports from docker-compose
- [ ] Configured firewall rules (ports 80/443 only)
- [ ] Set up API authentication for all endpoints
- [ ] Tested authentication is enforced

### 5. Monitoring Setup
- [ ] Configured Sentry DSN for error tracking
- [ ] Set up log aggregation
- [ ] Configured alerts for security events
- [ ] Set up uptime monitoring

### 6. Backup Configuration
- [ ] Set up automated database backups
- [ ] Tested backup restoration process
- [ ] Configured offsite backup storage
- [ ] Documented recovery procedures

### 7. Security Testing
- [ ] Ran OWASP ZAP scan
- [ ] Tested for SQL injection
- [ ] Tested for XSS vulnerabilities
- [ ] Verified rate limiting works
- [ ] Tested authentication bypass attempts

### 8. Documentation
- [ ] Documented all security configurations
- [ ] Created incident response plan
- [ ] Documented secret rotation procedure
- [ ] Created security contact list

## Deployment Steps

1. **Use secure Docker Compose**:
   ```bash
   docker-compose -f docker-compose.secure.yml --env-file .env.production up -d
   ```

2. **Verify services are running**:
   ```bash
   docker-compose -f docker-compose.secure.yml ps
   ```

3. **Check logs for errors**:
   ```bash
   docker-compose -f docker-compose.secure.yml logs
   ```

4. **Test authentication**:
   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" https://yourdomain.com/api/websites
   ```

## Post-Deployment Security Tasks

- [ ] Remove default credentials
- [ ] Disable debug mode
- [ ] Set up security scanning in CI/CD
- [ ] Schedule security audit for 30 days
- [ ] Monitor logs for suspicious activity
- [ ] Test backup restoration

## Emergency Contacts

- Security Lead: ________________
- DevOps Lead: _________________
- Incident Response: ____________

## Notes

_Add any deployment-specific notes here_

---

Deployment Date: ________________
Deployed By: ____________________
Security Review: ________________
