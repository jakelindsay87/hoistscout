# HoistScraper UI Requirements - Realistic Implementation

Build a focused admin dashboard for managing Australian grant/funding opportunity scraping. This is an internal tool for managing 244 pre-configured grant sites and viewing scraped opportunities.

## **Technical Stack**
- Next.js 14 with TypeScript (already implemented)
- Tailwind CSS + shadcn/ui components 
- SWR for API state management (already implemented)
- Real API endpoints (no placeholder data)

## **Current State Analysis**
- ✅ Working FastAPI backend with Website and ScrapeJob models
- ✅ 244 legitimate Australian grant sites imported 
- ✅ Basic Next.js frontend with sites management
- ✅ CSV import functionality working
- ❌ Missing opportunities/results display (core output)
- ❌ Missing job management interface
- ❌ Basic dashboard needs enhancement

## **Core Pages**

### **1. Enhanced Dashboard (/) - PRIORITY: Medium**
**Current State:** Basic navigation only
**Required API Endpoints:**
- GET /api/stats - Overall statistics
- GET /api/jobs/recent - Recent job activity
- GET /api/opportunities/recent - Latest opportunities found

**UI Enhancements:**
- Stats cards:
  - Total sites configured (244)
  - Jobs run this week
  - Opportunities found this month
  - Last scraping run timestamp
- Recent activity feed (last 10 jobs/opportunities)
- Quick actions:
  - "Run Full Scrape" button
  - "View Latest Opportunities" link
  - "Check Job Status" link

### **2. Opportunities Page (/opportunities) - PRIORITY: High** 
**MISSING - Core functionality!**
**Required API Endpoints:**
- GET /api/opportunities - List all scraped opportunities
- GET /api/opportunities/export - Export to CSV/JSON
- DELETE /api/opportunities/:id - Remove opportunity

**UI Components:**
- Filterable data table:
  - Title
  - Source website
  - Description preview
  - Deadline date
  - Amount/Value
  - Date scraped
  - View details link
- Filters:
  - By source website
  - By date range
  - By amount range
  - By keyword search
- Bulk export functionality
- Opportunity detail modal with full description

### **3. Jobs Page (/jobs) - PRIORITY: High**
**Current State:** ScrapeJob model exists but no UI
**Required API Endpoints:**
- GET /api/jobs - List all scraping jobs
- POST /api/jobs - Trigger new scraping job
- PUT /api/jobs/:id/cancel - Cancel running job
- GET /api/jobs/:id/logs - Get job execution logs

**UI Components:**
- Jobs table:
  - Job ID
  - Website name
  - Status (pending/running/completed/failed)
  - Start time
  - Duration
  - Opportunities found
  - Actions (view logs, cancel if running)
- "Run New Scrape" button with website selection
- Job detail modal with logs and results
- Filter by status and date range

### **4. Enhanced Sites Page (/sites) - PRIORITY: Low**
**Current State:** ✅ Working well
**Minor Enhancements:**
- Bulk enable/disable operations
- Last scraped timestamp per site
- Success rate indicator
- Test scraping button per site

### **5. Settings Page (/settings) - PRIORITY: Low**
**Required API Endpoints:**
- GET /api/settings - Get configuration
- PUT /api/settings - Update configuration

**UI Components:**
- Simple configuration form:
  - Scraping frequency (daily/weekly)
  - Concurrent job limit
  - Request timeout
  - Results retention period
- Import/Export site configurations
- Clear old opportunities button

## **Backend API Additions Required**

### **Opportunity Model** (MISSING)
```python
class Opportunity(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str | None = None
    source_url: str
    website_id: int = Field(foreign_key="website.id")
    deadline: datetime | None = None
    amount: str | None = None
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    job_id: int = Field(foreign_key="scrapejob.id")
```

### **Stats Endpoint**
```python
@app.get("/api/stats")
def get_stats():
    return {
        "total_sites": count_websites(),
        "jobs_this_week": count_recent_jobs(),
        "opportunities_found": count_opportunities(),
        "last_scrape": get_last_scrape_time()
    }
```

## **Implementation Priority**

### **Phase 1: Core Missing Functionality**
1. Create Opportunity model and API endpoints
2. Build Opportunities page (/opportunities)
3. Create Jobs page (/jobs) with basic functionality

### **Phase 2: Enhanced Experience**  
1. Enhanced Dashboard with real stats
2. Settings page
3. Improved Sites page features

### **Phase 3: Polish**
1. Better error handling and loading states
2. Export functionality
3. Job scheduling interface

## **Design Principles**
- **Functionality over aesthetics** - Working features first
- **Real data only** - No placeholder content
- **Simple and focused** - This is not a general-purpose platform
- **Mobile-friendly** - Responsive design for tablets/phones

## **Out of Scope**
- Complex authentication systems
- Real-time WebSocket updates
- Advanced proxy management
- File extraction/OCR
- LLM integration
- Complex queue management interfaces
- Enterprise monitoring dashboards

This focused approach delivers the core value: managing Australian grant sites and viewing the opportunities they contain.