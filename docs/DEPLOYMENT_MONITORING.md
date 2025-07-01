# HoistScraper Deployment Monitoring Guide

## Overview

This guide provides instructions for monitoring the HoistScraper deployment after security updates.

## Key Metrics to Monitor

### 1. Service Health

#### Backend API Health
```bash
# Check API health
curl https://hoistscraper.onrender.com/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-06-28T10:29:13.322460",
  "service": "hoistscraper-backend"
}
```

#### Frontend Health
```bash
# Check frontend is loading
curl -I https://hoistscraper-fe.onrender.com

# Should return HTTP 200
```

### 2. Security Monitoring

#### Authentication Failures
Monitor for repeated authentication failures which may indicate:
- Brute force attempts
- Misconfigured API keys
- Service integration issues

```bash
# Check admin endpoint protection
curl -X POST https://hoistscraper.onrender.com/api/admin/stats

# Should return 401 Unauthorized
```

#### Security Headers Verification
```bash
# Check security headers
curl -I https://hoistscraper.onrender.com/health | grep -E "X-Content-Type-Options|X-Frame-Options|Strict-Transport-Security"

# Should see:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### 3. Performance Metrics

#### Response Times
Monitor API response times for degradation:
- `/health` endpoint: < 100ms
- `/api/websites` endpoint: < 500ms
- Database queries: < 200ms

#### Memory Usage
- Backend service: Monitor for memory leaks
- Worker service: Check memory during scraping jobs
- Frontend builds: Ensure builds complete within memory limits

### 4. Error Monitoring

#### Application Errors
Check Render logs for:
- Python exceptions
- Database connection errors
- Redis connection issues
- CORS errors

```bash
# Common error patterns to watch for:
- "DatabaseError"
- "ConnectionRefusedError"
- "CORS policy"
- "Authentication failed"
- "Rate limit exceeded"
```

#### 404 Errors
Monitor for unexpected 404s which might indicate:
- Routing issues
- Missing static files
- API endpoint problems

## Monitoring Tools Setup

### 1. Render Dashboard Monitoring

1. **Enable Notifications**:
   - Go to Render Dashboard
   - Settings → Notifications
   - Enable email/Slack alerts for:
     - Deploy failures
     - Service crashes
     - High memory usage

2. **Log Streaming**:
   - Use Render's log streaming
   - Filter by severity level
   - Search for error patterns

### 2. External Monitoring

#### Uptime Monitoring
Set up external monitoring with services like:
- UptimeRobot
- Pingdom
- StatusCake

Monitor these endpoints:
```
https://hoistscraper.onrender.com/health
https://hoistscraper-fe.onrender.com/
```

#### Synthetic Monitoring
Create synthetic tests that:
1. Check API health
2. Verify authentication works
3. Test critical user flows
4. Monitor response times

### 3. Custom Monitoring Script

```bash
#!/bin/bash
# monitoring.sh - Run every 5 minutes via cron

API_URL="https://hoistscraper.onrender.com"
FRONTEND_URL="https://hoistscraper-fe.onrender.com"
WEBHOOK_URL="your-slack-webhook-url"

# Check API health
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $API_URL/health)
if [ "$API_STATUS" != "200" ]; then
    curl -X POST $WEBHOOK_URL -d "{\"text\":\"🚨 API Health Check Failed: $API_STATUS\"}"
fi

# Check Frontend
FE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $FRONTEND_URL)
if [ "$FE_STATUS" != "200" ]; then
    curl -X POST $WEBHOOK_URL -d "{\"text\":\"🚨 Frontend Check Failed: $FE_STATUS\"}"
fi

# Check Security Headers
HEADERS=$(curl -sI $API_URL/health)
if ! echo "$HEADERS" | grep -q "X-Content-Type-Options"; then
    curl -X POST $WEBHOOK_URL -d "{\"text\":\"⚠️ Security Headers Missing\"}"
fi
```

## Alert Configuration

### Critical Alerts (Immediate Action)
- Service down > 2 minutes
- Database connection failed
- Authentication bypass detected
- Memory usage > 90%
- Disk usage > 90%

### Warning Alerts (Review Within 1 Hour)
- Response time > 2 seconds
- Failed login attempts > 10/minute
- Memory usage > 80%
- Error rate > 5%

### Info Alerts (Daily Review)
- New user registrations
- API usage statistics
- Successful admin operations
- Deployment completions

## Incident Response Playbook

### 1. Service Down
1. Check Render dashboard for crash logs
2. Verify database connectivity
3. Check for recent deployments
4. Rollback if necessary
5. Scale up if resource-related

### 2. Security Incident
1. Check authentication logs
2. Review access patterns
3. Rotate API keys if compromised
4. Block suspicious IPs
5. Review audit logs

### 3. Performance Degradation
1. Check current load
2. Review slow query logs
3. Check Redis performance
4. Scale services if needed
5. Optimize problematic queries

## Daily Monitoring Checklist

- [ ] Check service health endpoints
- [ ] Review error logs for patterns
- [ ] Monitor authentication failures
- [ ] Check response times
- [ ] Review resource usage
- [ ] Verify backup completion
- [ ] Check for security alerts

## Weekly Review

1. **Performance Analysis**:
   - Average response times
   - Error rates
   - Resource utilization trends

2. **Security Review**:
   - Failed authentication attempts
   - Unusual access patterns
   - API key usage

3. **Capacity Planning**:
   - Growth trends
   - Resource needs
   - Scaling requirements

## Monitoring Dashboard Links

- **Render Dashboard**: https://dashboard.render.com
- **Database Metrics**: Check PostgreSQL dashboard
- **Redis Monitoring**: Via Render Redis service
- **API Documentation**: Internal use only

## Contact Information

- **On-Call Engineer**: [Your contact]
- **Escalation**: [Management contact]
- **Security Incidents**: security@yourcompany.com
- **Render Support**: https://render.com/support

## Useful Commands

```bash
# Check all services
./verify_deployment.sh

# Tail backend logs
# (Use Render dashboard log viewer)

# Test admin endpoint
curl -H "X-API-Key: YOUR_KEY" https://hoistscraper.onrender.com/api/admin/stats

# Check current deployments
# (Via Render dashboard)
```

This monitoring guide should be reviewed and updated monthly to ensure it remains current with your deployment needs.