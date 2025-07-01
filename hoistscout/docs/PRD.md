# HoistScout - Technical Product Requirements Document

## Executive Summary

HoistScout is a bulletproof web scraping platform designed to extract tender and grant opportunities from 1000+ websites while processing 5M+ PDF documents with zero manual intervention. The system uses intelligent LLM-based extraction with enterprise-grade reliability, security, and scalability.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Load Balancer                              │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────────┐
│                         FastAPI Backend                              │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐   │
│  │   Auth API  │  │ Scraping API │  │  Opportunities API      │   │
│  └─────────────┘  └──────────────┘  └─────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────────┐
│                        Core Services Layer                           │
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────────┐    │
│  │ ScrapeGraphAI  │  │ Anti-Detection  │  │  PDF Processor   │    │
│  │   Scraper      │  │    Manager      │  │  (Unstructured)  │    │
│  └────────────────┘  └─────────────────┘  └──────────────────┘    │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────────┐
│                      Infrastructure Layer                            │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────┐  ┌─────────────┐ │
│  │ PostgreSQL  │  │    Redis     │  │  MinIO  │  │   Celery    │ │
│  │  (Data)     │  │ (Cache/Queue)│  │ (Files) │  │  (Workers)  │ │
│  └─────────────┘  └──────────────┘  └─────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

#### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI with async support
- **ORM**: SQLAlchemy 2.0 with asyncpg
- **Task Queue**: Celery with Redis backend
- **LLM**: Ollama with Llama 3.1 (local inference)

#### Frontend
- **Framework**: Next.js 14+ with App Router
- **Language**: TypeScript
- **Styling**: TailwindCSS with shadcn/ui
- **State**: React Query + Zustand
- **Real-time**: Socket.IO

#### Infrastructure
- **Database**: PostgreSQL 15+ with partitioning
- **Cache**: Redis 7+
- **Storage**: MinIO for documents
- **Monitoring**: Prometheus + Grafana
- **Logging**: Structured JSON logs
- **Error Tracking**: Sentry

## Core Components

### 1. Bulletproof Scraping Engine

```python
class BulletproofTenderScraper:
    """
    Core scraping engine with intelligent extraction and anti-detection.
    """
    def __init__(self):
        self.scraper = SmartScraperGraph(
            llm_config={
                "model": "ollama/llama3.1",
                "temperature": 0.1,
                "base_url": "http://localhost:11434"
            }
        )
        self.anti_detection = AntiDetectionManager()
        self.pdf_processor = PDFProcessor()
        self.credential_manager = SecureCredentialManager()
    
    async def scrape_website(self, website_config: WebsiteConfig) -> ScrapingResult:
        """
        Scrape a website with full anti-detection and error recovery.
        
        Features:
        - Cloudflare bypass with FlareSolverr
        - CAPTCHA solving with 2captcha
        - Proxy rotation with health checking
        - Automatic retry with exponential backoff
        - PDF discovery and processing
        """
        # Implementation details in scraper.py
```

### 2. Anti-Detection System

```python
class AntiDetectionManager:
    """
    Manages all anti-detection strategies.
    """
    components = {
        "cloudflare_bypass": FlareSolverrClient(),
        "captcha_solver": TwoCaptchaClient(),
        "proxy_rotator": ProxyRotator(),
        "browser_stealth": UndetectedChromeDriver(),
        "request_throttler": DomainThrottler()
    }
```

### 3. Document Processing Pipeline

```python
class PDFProcessor:
    """
    Processes 5M+ PDFs with intelligent extraction.
    
    Features:
    - Parallel processing with Celery
    - OCR for scanned documents
    - Table extraction
    - LLM-powered content analysis
    - MinIO storage integration
    """
    async def process_pdf(self, pdf_url: str) -> ProcessedDocument:
        # Download to MinIO
        # Extract with Unstructured
        # Analyze with LLM
        # Store results
```

### 4. Database Schema

```sql
-- Websites table with encrypted credentials
CREATE TABLE websites (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL UNIQUE,
    category VARCHAR(50),
    credentials BYTEA, -- Encrypted JSON
    auth_type VARCHAR(50), -- 'none', 'basic', 'oauth', 'form'
    scraping_config JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Opportunities table with full-text search
CREATE TABLE opportunities (
    id SERIAL PRIMARY KEY,
    website_id INT REFERENCES websites(id),
    title TEXT NOT NULL,
    description TEXT,
    deadline TIMESTAMP,
    value DECIMAL(15, 2),
    currency VARCHAR(3) DEFAULT 'USD',
    reference_number VARCHAR(255),
    source_url TEXT NOT NULL UNIQUE,
    categories TEXT[],
    location VARCHAR(255),
    extracted_data JSONB, -- Full LLM extraction
    confidence_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create GIN indexes for performance
CREATE INDEX idx_opportunities_search ON opportunities 
USING GIN(to_tsvector('english', title || ' ' || description));

CREATE INDEX idx_opportunities_deadline ON opportunities(deadline);
CREATE INDEX idx_opportunities_value ON opportunities(value);

-- Documents table for PDF storage
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    opportunity_id INT REFERENCES opportunities(id),
    filename VARCHAR(255),
    minio_object_key VARCHAR(500) UNIQUE,
    file_size BIGINT,
    mime_type VARCHAR(100),
    extracted_text TEXT,
    extracted_data JSONB,
    processing_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Jobs table for scraping status
CREATE TABLE scraping_jobs (
    id SERIAL PRIMARY KEY,
    website_id INT REFERENCES websites(id),
    job_type VARCHAR(50), -- 'full', 'incremental', 'test'
    status VARCHAR(50) DEFAULT 'pending',
    priority INT DEFAULT 5,
    scheduled_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    stats JSONB, -- pages_scraped, pdfs_found, etc.
    created_at TIMESTAMP DEFAULT NOW()
);

-- Users table with RBAC
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'viewer', -- 'admin', 'editor', 'viewer'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- Audit log for security
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    action VARCHAR(100),
    resource_type VARCHAR(50),
    resource_id INT,
    details JSONB,
    ip_address INET,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table partitioning for scale
CREATE TABLE opportunities_2024 PARTITION OF opportunities 
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

### 5. API Endpoints

#### Authentication
```python
POST   /api/auth/login      # JWT login
POST   /api/auth/refresh    # Refresh token
POST   /api/auth/logout     # Invalidate token
GET    /api/auth/profile    # User profile
```

#### Website Management
```python
GET    /api/websites                  # List websites
POST   /api/websites                  # Add website
PUT    /api/websites/{id}             # Update website
DELETE /api/websites/{id}             # Delete website
POST   /api/websites/{id}/test        # Test scraping
POST   /api/websites/{id}/credentials # Update credentials
```

#### Scraping Control
```python
POST   /api/scraping/jobs             # Create scraping job
GET    /api/scraping/jobs             # List jobs
GET    /api/scraping/jobs/{id}        # Job details
POST   /api/scraping/jobs/{id}/cancel # Cancel job
GET    /api/scraping/jobs/{id}/logs   # Stream logs
```

#### Opportunities
```python
GET    /api/opportunities             # Search with filters
GET    /api/opportunities/{id}        # Get details
POST   /api/opportunities/export      # Export data
GET    /api/opportunities/stats       # Statistics
```

#### Documents
```python
GET    /api/documents/{id}            # Document metadata
GET    /api/documents/{id}/download   # Download file
GET    /api/documents/{id}/content    # Extracted content
```

### 6. Background Workers

```python
# Celery task definitions
@celery_app.task(bind=True, max_retries=3)
def scrape_website_task(self, website_id: int):
    """Scrape a website with retry logic."""
    
@celery_app.task
def process_pdf_task(document_id: int):
    """Process PDF with Unstructured."""
    
@celery_app.task
def export_opportunities_task(filter_params: dict, format: str):
    """Generate export file."""
    
@celery_app.task
def validate_data_quality_task(opportunity_id: int):
    """Validate extracted data quality."""
```

## Security Features

### 1. Credential Management
```python
class SecureCredentialManager:
    """
    Encrypts website credentials using Fernet.
    """
    def encrypt_credentials(self, credentials: dict) -> bytes:
        # AES encryption with key rotation
        
    def decrypt_credentials(self, encrypted: bytes) -> dict:
        # Secure decryption with audit logging
```

### 2. Authentication & Authorization
- JWT tokens with refresh mechanism
- Role-based access control (RBAC)
- API key authentication for programmatic access
- Multi-factor authentication support

### 3. Security Measures
- Input validation on all endpoints
- SQL injection prevention with parameterized queries
- XSS protection in frontend
- CORS configuration
- Rate limiting per user/IP
- Audit logging for sensitive operations

## Performance Requirements

### Scalability Targets
- **Concurrent Scraping**: 1000 sessions
- **PDF Processing**: 5000 documents/hour
- **Database**: 5M+ opportunities
- **API Response**: <500ms for 95th percentile
- **Search Performance**: <100ms for full-text search
- **Export Generation**: <30s for 100K records

### Optimization Strategies
1. **Database**
   - Table partitioning by date
   - Proper indexing strategy
   - Connection pooling
   - Read replicas for search

2. **Caching**
   - Redis for hot data
   - CDN for static assets
   - Browser caching headers
   - Query result caching

3. **Async Processing**
   - FastAPI async endpoints
   - Celery for background jobs
   - Concurrent PDF processing
   - Batch operations

## Monitoring & Observability

### Metrics Collection
```python
# Prometheus metrics
scraping_jobs_total = Counter('scraping_jobs_total', 'Total scraping jobs')
pdf_processing_duration = Histogram('pdf_processing_duration_seconds', 'PDF processing time')
api_request_duration = Histogram('api_request_duration_seconds', 'API request duration')
active_scrapers = Gauge('active_scrapers', 'Currently active scrapers')
```

### Logging Strategy
```python
# Structured logging with correlation IDs
logger.info("Scraping started", extra={
    "job_id": job.id,
    "website_id": website.id,
    "correlation_id": request_id,
    "user_id": current_user.id
})
```

### Health Checks
```python
GET /health          # Basic health check
GET /health/ready    # Readiness probe
GET /health/live     # Liveness probe
GET /health/detailed # Detailed component status
```

## Frontend Architecture

### Component Structure
```
frontend/
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/
│   │   ├── page.tsx          # Main dashboard
│   │   ├── websites/         # Website management
│   │   ├── opportunities/    # Opportunity browser
│   │   ├── jobs/            # Job monitoring
│   │   └── settings/        # User settings
│   └── api/                 # API routes
├── components/
│   ├── ui/                  # shadcn/ui components
│   ├── dashboard/           # Dashboard widgets
│   ├── tables/              # Data tables
│   └── forms/               # Form components
└── lib/
    ├── api.ts               # API client
    ├── auth.ts              # Auth utilities
    └── utils.ts             # Helper functions
```

### Key Features
1. **Real-time Updates**
   - WebSocket integration for job status
   - Server-sent events for new opportunities
   - Live progress indicators

2. **Advanced Search**
   - Full-text search with highlighting
   - Faceted filtering
   - Saved searches
   - Search history

3. **Data Export**
   - Multiple formats (CSV, Excel, JSON, XML)
   - Custom field selection
   - Scheduled exports
   - Email delivery

## Development Timeline

### Phase 1: Core Infrastructure (Weeks 1-2)
- [x] Project setup and dependencies
- [ ] Database schema and models
- [ ] Basic FastAPI structure
- [ ] Authentication system
- [ ] Docker development environment

### Phase 2: Scraping Engine (Weeks 3-4)
- [ ] ScrapeGraphAI integration
- [ ] Anti-detection components
- [ ] PDF processing pipeline
- [ ] Credential management
- [ ] Job queue system

### Phase 3: Frontend Development (Weeks 5-6)
- [ ] Next.js setup with TypeScript
- [ ] Authentication flow
- [ ] Dashboard components
- [ ] Website management
- [ ] Opportunity browser

### Phase 4: Production Readiness (Weeks 7-8)
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Monitoring setup
- [ ] Documentation
- [ ] Deployment automation

## Success Metrics

### Technical Metrics
- **Scraping Success Rate**: >95%
- **PDF Processing Accuracy**: >90%
- **System Uptime**: 99.9%
- **API Response Time**: <500ms (p95)
- **Database Query Time**: <100ms
- **Zero Data Loss**: During normal operations

### Business Metrics
- **Sites Supported**: 1000+ without custom code
- **Documents Processed**: 5M+ total capacity
- **Time to Add Site**: <5 minutes
- **Export Generation**: <30 seconds
- **User Capacity**: 10,000+ concurrent

## Risk Mitigation

### Technical Risks
1. **Site Blocking**
   - Mitigation: Robust anti-detection, proxy rotation
   
2. **Data Quality**
   - Mitigation: LLM validation, confidence scoring
   
3. **Performance Degradation**
   - Mitigation: Horizontal scaling, caching

### Operational Risks
1. **Credential Compromise**
   - Mitigation: Encryption, audit logging, rotation
   
2. **System Overload**
   - Mitigation: Rate limiting, queue management
   
3. **Data Loss**
   - Mitigation: Backups, replication, transactions

## Conclusion

HoistScout represents a next-generation approach to tender aggregation, combining intelligent extraction with enterprise-grade reliability. By leveraging modern LLM capabilities while maintaining strict performance and security requirements, the system can scale to meet the demands of government-scale data aggregation.