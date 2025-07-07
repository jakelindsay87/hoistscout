# HoistScout Scraping Workflow - Fixed Issues & Complete Flow

## Summary of Fixes Applied

### 1. **Frontend Fixes**
- ✅ Fixed jobs endpoint from `/api/scrape-jobs` to `/api/scraping/jobs`
- ✅ Updated `useJobs` hook to use correct endpoint
- ✅ Fixed `useCreateJob` to send proper payload format:
  ```json
  {
    "website_id": 123,
    "job_type": "full",
    "priority": 5
  }
  ```

### 2. **Backend Fixes**
- ✅ Updated demo user to have EDITOR role (was defaulting to VIEWER)
- ✅ Added support for "demo" username login (maps to demo@hoistscout.com)
- ✅ Connected jobs API to Celery worker (was TODO)

### 3. **Authentication Fixes**
- ✅ Dashboard page created and added to authenticated layout
- ✅ Opportunities page moved to authenticated layout
- ✅ Fixed login redirect to `/dashboard`
- ✅ Fixed API authentication in dashboard

## Complete End-to-End Workflow

### Step 1: Authentication
```
POST /api/auth/login
Body: username=demo&password=demo123
Returns: { access_token, refresh_token }
```

### Step 2: Add Website
```
POST /api/websites
Headers: Authorization: Bearer <token>
Body: {
  "name": "Grants Portal",
  "url": "https://www.grants.gov",
  "is_active": true
}
Returns: { id, name, url, ... }
```

### Step 3: Trigger Scraping
```
POST /api/scraping/jobs
Headers: Authorization: Bearer <token>
Body: {
  "website_id": 123,
  "job_type": "full",
  "priority": 5
}
Returns: { id, status: "pending", ... }
```

### Step 4: Monitor Job Status
```
GET /api/scraping/jobs/{job_id}
Headers: Authorization: Bearer <token>
Returns: { id, status, started_at, completed_at, ... }
```

### Step 5: View Opportunities
```
GET /api/opportunities?website_id=123
Headers: Authorization: Bearer <token>
Returns: [{ title, deadline, value, source_url, ... }]
```

## Architecture Overview

```
Frontend (Next.js)          Backend (FastAPI)         Worker (Celery)
     |                           |                         |
     |------ Add Website ------->|                         |
     |                           |                         |
     |------ Create Job -------->|                         |
     |                           |---Queue with Celery---->|
     |                           |                         |
     |------ Poll Status ------->|                         |
     |                           |<---Update Job Status----|
     |                           |                         |
     |---- Get Opportunities --->|                         |
     |                           |                         |
```

## Key Components

### Frontend Hooks
- `useSites()` - Manage websites
- `useCreateSite()` - Add new websites
- `useJobs()` - List scraping jobs
- `useCreateJob()` - Trigger new scrape
- `useOpportunities()` - View scraped data

### Backend Endpoints
- `/api/websites` - CRUD for websites
- `/api/scraping/jobs` - Create and monitor jobs
- `/api/opportunities` - View scraped opportunities
- `/api/auth/*` - Authentication endpoints

### Worker Tasks
- `scrape_website_task` - Main scraping task
- `scrape_all_active_websites` - Periodic task (every 6 hours)
- `cleanup_old_jobs` - Maintenance task (daily)

## Testing

### Manual Testing
1. Login at https://hoistscout-frontend.onrender.com
   - Username: `demo`
   - Password: `demo123`

2. Navigate to Sites page
3. Add a new website
4. Click "Run Scrape" button
5. Go to Jobs page to monitor progress
6. View results in Opportunities page

### Automated Testing
Run the end-to-end test script:
```bash
python test_end_to_end_scraping.py
```

## Deployment Considerations

### Required Services
- PostgreSQL database
- Redis for Celery broker
- Celery worker process
- FastAPI backend
- Next.js frontend

### Environment Variables
Backend needs:
- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `DEMO_USER_ENABLED=true`

Worker needs:
- Same as backend
- Plus access to scraping dependencies

## Known Issues & TODOs

1. **Scraper Implementation**: The `BulletproofTenderScraper` is referenced but may not be fully implemented
2. **PDF Processing**: PDF processor task exists but implementation is incomplete
3. **Credentials Management**: Website credentials encryption is setup but not used in scraping
4. **Rate Limiting**: No rate limiting on scraping to avoid overwhelming target sites
5. **Error Recovery**: Limited retry logic for failed scrapes

## Next Steps

1. Implement actual scraping logic in `core/scraper.py`
2. Add rate limiting and respect robots.txt
3. Implement credential-based authentication for protected sites
4. Add more sophisticated error handling and retry logic
5. Implement opportunity deduplication
6. Add email notifications for completed scrapes