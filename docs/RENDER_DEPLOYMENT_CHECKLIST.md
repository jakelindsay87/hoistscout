# Render Deployment Verification Checklist

## Pre-Deployment Verification

### 1. Database Setup
- [ ] PostgreSQL database `hoistscraper-db` is created
- [ ] Database connection string is available
- [ ] Database has proper backups configured

### 2. Environment Variables
Verify these are set in Render Dashboard:

#### Backend Service (hoistscraper)
- [ ] `DATABASE_URL` - Auto-configured from database
- [ ] `REDIS_URL` - Auto-configured from Redis service
- [ ] `SMTP_USER` - Set manually (if email notifications needed)
- [ ] `SMTP_PASSWORD` - Set manually (if email notifications needed)
- [ ] `NOTIFY_EMAIL` - Set manually (if email notifications needed)

#### Frontend Service (hoistscraper-fe)
- [ ] `NEXT_PUBLIC_API_URL` - Should be `https://hoistscraper.onrender.com`
- [ ] `NODE_OPTIONS` - Should be `--max-old-space-size=512`

#### Worker Service (hoistscraper-worker)
- [ ] `DATABASE_URL` - Auto-configured from database
- [ ] `REDIS_URL` - Auto-configured from Redis service

## Post-Deployment Verification

### 1. Service Health Checks
- [ ] Backend API: Check `https://hoistscraper.onrender.com/health`
- [ ] Frontend: Check `https://hoistscraper-fe.onrender.com`
- [ ] Redis: Verify service is running in Render dashboard
- [ ] Worker: Check logs for successful startup

### 2. Database Migration
- [ ] Verify tables are created:
  ```sql
  -- Connect to database and run:
  SELECT table_name FROM information_schema.tables 
  WHERE table_schema = 'public';
  ```
- [ ] Verify `credentials` column exists in `website` table:
  ```sql
  SELECT column_name FROM information_schema.columns 
  WHERE table_name = 'website' AND column_name = 'credentials';
  ```

### 3. API Functionality
- [ ] Test API docs: `https://hoistscraper.onrender.com/docs`
- [ ] Test CORS: Frontend should connect without errors
- [ ] Test website creation via API
- [ ] Test scraping job creation

### 4. Frontend Functionality
- [ ] Pages load without errors
- [ ] API calls work (check browser console)
- [ ] Can create/view websites
- [ ] Can trigger scraping jobs
- [ ] Job status updates properly

### 5. Worker Functionality
- [ ] Check worker logs for job processing
- [ ] Verify scraping results are saved
- [ ] Check Redis queue for job processing

### 6. Monitoring
- [ ] Set up alerts for service failures
- [ ] Monitor memory usage (especially frontend builds)
- [ ] Check disk usage for data storage
- [ ] Review error logs regularly

## Troubleshooting

### Common Issues

1. **Frontend can't connect to API**
   - Verify `NEXT_PUBLIC_API_URL` is set correctly
   - Check CORS configuration includes frontend URL
   - Verify backend service is running

2. **Database connection errors**
   - Check `DATABASE_URL` format
   - Verify database is accessible
   - Check for connection pool exhaustion

3. **Memory issues during build**
   - Increase `NODE_OPTIONS` memory limit
   - Consider using build cache
   - Check for memory leaks

4. **Worker not processing jobs**
   - Verify Redis connection
   - Check worker logs for errors
   - Ensure RQ is properly configured

5. **CORS errors**
   - Verify frontend URL in CORS origins
   - Check for trailing slashes in URLs
   - Ensure credentials are allowed

## Performance Optimization

- [ ] Enable caching where appropriate
- [ ] Configure CDN for static assets
- [ ] Set up database indexes for common queries
- [ ] Monitor and optimize slow queries
- [ ] Configure rate limiting for API endpoints

## Security Checklist

- [ ] All sensitive environment variables are encrypted
- [ ] Database connections use SSL
- [ ] API endpoints have proper authentication (if enabled)
- [ ] No debug mode in production
- [ ] Proper input validation on all endpoints
- [ ] Rate limiting configured
- [ ] CORS properly restricted to known origins

## Backup and Recovery

- [ ] Database backups configured
- [ ] Test restore procedure
- [ ] Document recovery steps
- [ ] Keep configuration backed up
- [ ] Version control for infrastructure changes