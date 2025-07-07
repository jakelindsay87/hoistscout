# HoistScraper - Final Production Task List

## 🎯 Project Status Summary

**What Works**: Backend infrastructure, 244 sites imported, API endpoints exist
**What's Missing**: Frontend UI for opportunities/jobs, automatic job processing
**What's Broken**: Worker/Redis connection, some imports, security vulnerabilities

## 📋 Prioritized Task List for Production

### 🔴 CRITICAL - Week 1 (Must Have for MVP)

#### Day 1-2: Fix Breaking Issues
- [ ] **Fix Import Path** (15 min)
  ```bash
  mkdir -p backend/cli
  mv backend/import_csv.py backend/cli/
  ```
- [ ] **Fix Frontend Dependencies** (15 min)
  ```bash
  cd frontend && npm install
  ```
- [ ] **Fix Worker/Redis** (1 day)
  - Option A: Debug Redis connection in docker-compose
  - Option B: Replace with FastAPI BackgroundTasks
  - Option C: Use Celery instead of RQ

#### Day 3-4: Build Opportunities Page (CORE VALUE)
- [ ] Create `/frontend/src/app/opportunities/page.tsx`
- [ ] Add data table with columns: Title, Source, Deadline, Amount
- [ ] Add filters: website, date range, keyword
- [ ] Add CSV export button
- [ ] Test with real scraped data

#### Day 5: Build Jobs Page  
- [ ] Create `/frontend/src/app/jobs/page.tsx`
- [ ] Show job status table
- [ ] Add "Trigger Scrape" button
- [ ] Add status badges (pending/running/completed/failed)
- [ ] Basic log viewer

### 🟡 HIGH PRIORITY - Week 2 (Should Have)

#### Security Fixes (2 days)
- [ ] **Fix Hardcoded Encryption Salt**
  - Use environment variable for salt
  - Generate random salt if not provided
- [ ] **Add Basic Authentication**
  - Simple API key or basic auth
  - Protect all endpoints except health
- [ ] **Add Input Validation**
  - URL format validation
  - Field length limits
  - Sanitize HTML inputs

#### Stability Improvements (3 days)
- [ ] Add proper error handling (specific exceptions)
- [ ] Add request logging with correlation IDs
- [ ] Fix memory leaks in worker
- [ ] Add retry logic for failed scrapes
- [ ] Implement job timeout handling

### 🟢 MEDIUM PRIORITY - Week 3 (Nice to Have)

#### Testing Suite (3 days)
- [ ] Backend unit tests (pytest)
  - API endpoint tests
  - Model validation tests
  - Credential encryption tests
- [ ] Integration tests
  - Scraping workflow tests
  - Database transaction tests
- [ ] Frontend component tests

#### Performance (2 days)
- [ ] Add pagination to all list endpoints
- [ ] Fix N+1 queries in stats endpoint
- [ ] Add database indexes
- [ ] Implement caching for stats

### 🔵 LOW PRIORITY - Week 4 (Future Enhancement)

#### Monitoring & Operations
- [ ] Add Sentry error tracking
- [ ] Add Prometheus metrics
- [ ] Create operational dashboard
- [ ] Add health check endpoints
- [ ] Setup log aggregation

#### Documentation
- [ ] API documentation (OpenAPI)
- [ ] Deployment guide
- [ ] User manual
- [ ] Troubleshooting guide

## 🚀 Quick Start Commands

### Fix Immediate Issues
```bash
# Fix imports
mkdir -p backend/cli
mv backend/import_csv.py backend/cli/

# Fix frontend
cd frontend
npm install
npm run build

# Test backend
cd ../backend
poetry install
poetry run python -m hoistscraper.main
```

### Deploy with Docker
```bash
# Quick fix deployment
chmod +x deploy_quick_fix.sh
./deploy_quick_fix.sh

# OR production deployment
docker-compose -f docker-compose.prod.yml up -d
```

### Test Scraping
```bash
# Manual trigger
curl -X POST http://localhost:8000/api/scrape/2/trigger

# Check opportunities
curl http://localhost:8000/api/opportunities
```

## ✅ Definition of Done

The system is production-ready when:

1. **Opportunities Page** shows scraped grant data with filtering
2. **Jobs Page** allows monitoring and triggering scrapes  
3. **Worker** processes jobs automatically without manual intervention
4. **Security** has authentication and input validation
5. **Stability** handles errors gracefully with proper logging
6. **Performance** responds in < 1 second for all endpoints
7. **Tests** have > 70% code coverage
8. **Documentation** enables new developers to contribute

## 📊 Current vs Required State

| Component | Current State | Required State | Effort |
|-----------|--------------|----------------|--------|
| Opportunities UI | ❌ Missing | ✅ Full CRUD with filters | 2 days |
| Jobs UI | ❌ Missing | ✅ Status monitoring | 1 day |
| Worker | 🔴 Broken | ✅ Auto-processing | 1 day |
| Security | 🔴 Vulnerable | ✅ Basic auth + validation | 2 days |
| Testing | ❌ None | ✅ 70% coverage | 3 days |
| Docs | ⚠️ Partial | ✅ Complete | 1 day |

**Total Effort**: ~10 days for MVP, 15 days for production-ready

## 🎯 Success Metrics

- **User can**: View all scraped opportunities in a table
- **System can**: Automatically scrape sites on schedule
- **Security**: No public access to sensitive data
- **Reliability**: < 1% error rate on scraping
- **Performance**: < 1s page load time
- **Maintainability**: New developer productive in < 1 day

## 📝 Next Action

**RIGHT NOW**: 
1. Fix the import path issue (5 min)
2. Install frontend dependencies (10 min)
3. Start building the Opportunities page (highest value)

The project has solid foundations but needs the UI layer to deliver value. Focus on getting the Opportunities page working first - that's the core user need.