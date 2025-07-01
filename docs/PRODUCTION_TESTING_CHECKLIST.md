# Production Testing Checklist

## Pre-Deployment Verification

### Environment Variables
- [ ] `ADMIN_API_KEY` is set in Render backend service
- [ ] `NEXT_PUBLIC_API_URL` is correctly configured for frontend
- [ ] `DATABASE_URL` is properly configured
- [ ] `REDIS_URL` is properly configured
- [ ] `RENDER=true` is set automatically

## Post-Deployment Testing

### 1. Basic Connectivity Tests

#### API Health Check
```bash
curl https://hoistscraper.onrender.com/health
```
- [ ] Returns 200 OK
- [ ] Shows "healthy" status
- [ ] Response time < 500ms

#### Frontend Loading
```bash
curl -I https://hoistscraper-fe.onrender.com
```
- [ ] Returns 200 OK
- [ ] Page loads without errors
- [ ] No console errors in browser

### 2. Security Tests

#### Admin Endpoints Protection
```bash
# Without auth (should fail)
curl -X POST https://hoistscraper.onrender.com/api/admin/clear-database
```
- [ ] Returns 401 Unauthorized
- [ ] Error message about missing authentication

```bash
# With invalid auth (should fail)
curl -X POST https://hoistscraper.onrender.com/api/admin/clear-database \
  -H "X-API-Key: invalid-key"
```
- [ ] Returns 403 Forbidden
- [ ] Error message about invalid API key

```bash
# With valid auth (should work)
curl -X GET https://hoistscraper.onrender.com/api/admin/stats \
  -H "X-API-Key: Qwl5vPbcrDnhci4Q6MzPPKLRahoJ-rP7j9F3eQzXqpQ"
```
- [ ] Returns 200 OK
- [ ] Shows system statistics

#### Debug Endpoints Blocked
```bash
curl https://hoistscraper.onrender.com/api/debug
```
- [ ] Returns 404 Not Found
- [ ] No sensitive information exposed

#### API Documentation Disabled
```bash
curl https://hoistscraper.onrender.com/docs
```
- [ ] Returns 404 Not Found
- [ ] Swagger UI not accessible

### 3. Security Headers Verification

```bash
curl -I https://hoistscraper.onrender.com/health
```

Check for presence of:
- [ ] `X-Content-Type-Options: nosniff`
- [ ] `X-Frame-Options: DENY`
- [ ] `X-XSS-Protection: 1; mode=block`
- [ ] `Strict-Transport-Security: max-age=31536000`
- [ ] `Content-Security-Policy` header
- [ ] No `Server` header exposing technology

### 4. Frontend API Integration

#### Test API Connectivity
1. Open https://hoistscraper-fe.onrender.com
2. Open browser developer console (F12)
3. Navigate to Network tab
4. Refresh page

- [ ] API calls go to correct backend URL
- [ ] No CORS errors
- [ ] API requests succeed
- [ ] Data loads properly

#### Test User Flows
- [ ] Can view websites list
- [ ] Can view opportunities
- [ ] Can navigate between pages
- [ ] Search functionality works
- [ ] No JavaScript errors in console

### 5. Database Operations

#### Check Website CRUD
```bash
# Get websites (should work)
curl https://hoistscraper.onrender.com/api/websites
```
- [ ] Returns list of websites
- [ ] Includes all expected fields
- [ ] No credential data exposed

### 6. Performance Tests

#### Response Time Checks
```bash
# Measure API response time
time curl https://hoistscraper.onrender.com/health
```
- [ ] Response time < 500ms
- [ ] Consistent response times

#### Load Test (Optional)
```bash
# Simple load test with curl
for i in {1..10}; do
  curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" \
    https://hoistscraper.onrender.com/health &
done
wait
```
- [ ] All requests return 200
- [ ] No significant performance degradation

### 7. Error Handling

#### Test 404 Handling
```bash
curl https://hoistscraper.onrender.com/api/nonexistent
```
- [ ] Returns proper 404 error
- [ ] No stack traces exposed
- [ ] Clean error message

#### Test Invalid Input
```bash
curl -X POST https://hoistscraper.onrender.com/api/websites \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'
```
- [ ] Returns validation error
- [ ] Clear error messages
- [ ] No internal details exposed

### 8. Monitoring Verification

#### Check Logs
Via Render Dashboard:
- [ ] No error spam in logs
- [ ] No deprecation warnings
- [ ] No connection errors
- [ ] Startup completed successfully

#### Resource Usage
Via Render Dashboard:
- [ ] Memory usage < 80%
- [ ] CPU usage normal
- [ ] No memory leaks detected
- [ ] Disk usage acceptable

### 9. Integration Tests

#### Worker Service
- [ ] Worker service is running
- [ ] Can process scraping jobs
- [ ] Results stored correctly
- [ ] No queue backlogs

#### Redis Connection
- [ ] Redis connected successfully
- [ ] Job queuing works
- [ ] No connection timeouts

### 10. Security Audit

#### API Key Security
- [ ] API key not exposed in logs
- [ ] API key not in response headers
- [ ] API key required for admin ops

#### Data Security
- [ ] Credentials field encrypted (if used)
- [ ] No sensitive data in responses
- [ ] Proper error sanitization

## Rollback Plan

If critical issues are found:

1. **Immediate Rollback**:
   ```bash
   # Via Render Dashboard
   # Go to service → Deploys → Previous deploy → Rollback
   ```

2. **Hotfix Process**:
   - Create hotfix branch
   - Apply minimal fix
   - Test locally
   - Deploy hotfix

3. **Communication**:
   - Notify team of issues
   - Document problems found
   - Plan remediation

## Sign-Off

- [ ] All critical tests passed
- [ ] No security vulnerabilities found
- [ ] Performance acceptable
- [ ] Monitoring active
- [ ] Documentation updated

**Tested by**: _________________ **Date**: _________________

**Approved by**: _________________ **Date**: _________________

## Notes

_Add any observations, issues, or recommendations below:_

_______________________________________________________________

_______________________________________________________________

_______________________________________________________________