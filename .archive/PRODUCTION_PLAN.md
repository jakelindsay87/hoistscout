# HoistScraper Production Plan

## Architecture Overview

### Option 1: Playwright + Ollama (Recommended)
```
Website → Playwright (scrape) → Raw HTML → Ollama (extract) → Structured Opportunities → Database
```

### Option 2: Playwright + Enhanced BeautifulSoup
```
Website → Playwright (scrape) → Raw HTML → Custom Parser → Structured Opportunities → Database
```

## Implementation Steps

### Phase 1: Fix Core Infrastructure (Week 1)

#### 1.1 Fix Worker/Queue System
- **Option A**: Fix Redis/RQ integration
  - Add job enqueueing when scrape job is created
  - Fix worker connection issues
  - Add proper retry logic
  
- **Option B**: Replace with simpler async approach
  - Use FastAPI BackgroundTasks
  - Or use Celery with PostgreSQL as broker
  - Or simple cron-based polling

#### 1.2 Add Ollama Integration
```yaml
# docker-compose.yml addition
ollama:
  image: ollama/ollama:latest
  container_name: hoistscraper-ollama
  ports:
    - "11434:11434"
  volumes:
    - ollama_data:/root/.ollama
  networks:
    - app-network
```

#### 1.3 Implement Proper Extraction Pipeline
```python
# New extraction flow
async def process_scraped_content(job_id: int, html_content: str):
    # 1. Extract all tender links from listing page
    tender_urls = extract_tender_urls(html_content)
    
    # 2. For each tender URL, scrape detail page
    for url in tender_urls:
        detail_html = await scrape_page(url)
        
        # 3. Use Ollama to extract structured data
        opportunity = await extract_with_ollama(detail_html, url)
        
        # 4. Save to database
        save_opportunity(opportunity)
```

### Phase 2: Implement Missing Features (Week 2)

#### 2.1 Add Trigger Endpoint
```python
@app.post("/api/scrape/{website_id}")
async def trigger_scrape(website_id: int, background_tasks: BackgroundTasks):
    """Trigger scraping for a specific website."""
    job = create_scrape_job(website_id)
    background_tasks.add_task(execute_scrape_job, job.id)
    return job
```

#### 2.2 Implement Ollama Extraction
```python
async def extract_with_ollama(html: str, url: str) -> Dict:
    prompt = f"""
    Extract grant/tender information from this HTML.
    Return JSON with:
    - title: Grant/tender title
    - organization: Issuing organization
    - description: Full description
    - deadline: Closing date/deadline
    - amount: Funding amount if specified
    - eligibility: Who can apply
    - contact: Contact information
    - documents: List of downloadable documents
    
    HTML: {html[:10000]}  # Truncate for context limit
    """
    
    response = await ollama.generate(
        model="mistral:7b",
        prompt=prompt,
        format="json"
    )
    return json.loads(response['response'])
```

#### 2.3 Handle Pagination
```python
async def scrape_listing_page(url: str, page: int = 1):
    """Scrape paginated listing pages."""
    all_opportunities = []
    
    while True:
        page_url = f"{url}?page={page}"
        html = await scrape_with_playwright(page_url)
        
        # Extract opportunities
        opportunities = extract_listing_items(html)
        if not opportunities:
            break
            
        all_opportunities.extend(opportunities)
        
        # Check for next page
        if not has_next_page(html):
            break
            
        page += 1
        await asyncio.sleep(2)  # Rate limiting
    
    return all_opportunities
```

### Phase 3: Authentication & Credentials (Week 3)

#### 3.1 Add Credential Storage
```python
class WebsiteCredential(SQLModel, table=True):
    id: int = Field(primary_key=True)
    website_id: int = Field(foreign_key="website.id")
    username: str
    password_encrypted: str  # Use Fernet encryption
    login_url: str
    login_method: str  # "form", "oauth", "session"
    additional_fields: dict = Field(default={})  # JSON field
```

#### 3.2 Implement Login Flow
```python
async def login_to_website(page: Page, website: Website):
    """Handle website authentication."""
    if not website.requires_auth:
        return
        
    creds = get_website_credentials(website.id)
    if not creds:
        raise AuthenticationError("No credentials found")
    
    # Navigate to login page
    await page.goto(creds.login_url)
    
    # Fill login form
    await page.fill('input[name="username"]', creds.username)
    await page.fill('input[name="password"]', decrypt(creds.password_encrypted))
    await page.click('button[type="submit"]')
    
    # Wait for login to complete
    await page.wait_for_navigation()
```

### Phase 4: Production Deployment (Week 4)

#### 4.1 Environment Configuration
```env
# .env.production
DATABASE_URL=postgresql://user:pass@db:5432/hoistscraper
REDIS_URL=redis://redis:6379/0
OLLAMA_HOST=http://ollama:11434
ENCRYPTION_KEY=your-fernet-key-here
RATE_LIMIT_DELAY=2
MAX_CONCURRENT_SCRAPES=3
```

#### 4.2 Monitoring & Logging
- Add Sentry for error tracking
- Implement structured logging with correlation IDs
- Add health checks for all services
- Monitor Ollama model performance

#### 4.3 Scaling Considerations
- Use connection pooling for PostgreSQL
- Implement caching for frequently accessed data
- Add CDN for static assets
- Consider horizontal scaling for workers

## Quick Wins for Immediate Value

### 1. Fix Job Triggering (1 day)
```python
# In create_scrape_job endpoint
from hoistscraper.queue import enqueue_job
from hoistscraper.worker import scrape_website_job

@app.post("/api/scrape-jobs")
def create_scrape_job(job: models.ScrapeJobCreate, session: Session = Depends(db.get_session)):
    # ... existing code ...
    
    # Add this: Enqueue the job
    enqueue_job(
        scrape_website_job,
        website_id=db_job.website_id,
        job_id=db_job.id,
        queue_name="scraper"
    )
    
    return db_job
```

### 2. Add Simple Opportunities View (2 days)
- Implement the missing `/opportunities` page in frontend
- Use existing API endpoints
- Display scraped data in a table

### 3. Manual Trigger Endpoint (1 day)
```python
@app.post("/api/scrape/{website_id}/trigger")
async def trigger_scrape_manual(website_id: int, session: Session = Depends(db.get_session)):
    """Manually trigger a scrape job."""
    # Create job
    job = models.ScrapeJob(website_id=website_id, status="pending")
    session.add(job)
    session.commit()
    
    # Execute directly (for testing)
    from hoistscraper.worker import ScraperWorker
    worker = ScraperWorker()
    try:
        result = worker.scrape_website(website_id, job.id)
        return {"status": "completed", "result": result}
    finally:
        worker.cleanup()
```

## Migration Path

1. **Immediate**: Fix job triggering to make existing code work
2. **Next Sprint**: Add Ollama for proper extraction
3. **Following Sprint**: Implement authentication system
4. **Future**: Scale with better queue management

## Technology Decisions

### Use Ollama Because:
- Local LLM, no API costs
- Good at structured extraction
- Can handle Australian government terminology
- Privacy-compliant (data stays local)

### Keep Playwright Because:
- Handles JavaScript-heavy sites
- Built-in anti-detection
- Good for authenticated sessions
- Already implemented

### PostgreSQL + Redis Because:
- PostgreSQL for persistent data
- Redis for job queuing (or replace with Celery/RabbitMQ)
- Both are production-proven

## Next Steps

1. Fix the job enqueueing issue (critical)
2. Add Ollama container to docker-compose
3. Implement proper extraction pipeline
4. Build the opportunities UI
5. Add authentication system
6. Deploy to production