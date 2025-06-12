# Architecture Overview

This document describes the architecture and data flow of the HoistScraper application.

## System Architecture

```mermaid
graph TB
    subgraph "Frontend (Next.js)"
        UI[Web Interface]
        API_CLIENT[API Client]
    end
    
    subgraph "Backend Services"
        API[FastAPI Server]
        CRAWLER[Crawler Engine]
        SCHEDULER[Job Scheduler]
        ANALYZER[Content Analyzer]
    end
    
    subgraph "External Services"
        OLLAMA[Ollama AI Service]
        SMTP[Email Service]
        PROXIES[Proxy Pool]
    end
    
    subgraph "Data Layer"
        DB[(Database)]
        SITES_CONFIG[sites.yml]
        ROBOTS[robots.txt Cache]
    end
    
    subgraph "Target Sites"
        SITE1[Job Site 1]
        SITE2[Job Site 2]
        SITEN[Job Site N]
    end
    
    %% User interactions
    USER[User] --> UI
    UI --> API_CLIENT
    API_CLIENT --> API
    
    %% API endpoints
    API --> DB
    API --> CRAWLER
    API --> SCHEDULER
    
    %% Crawler flow
    CRAWLER --> SITES_CONFIG
    CRAWLER --> ROBOTS
    CRAWLER --> PROXIES
    CRAWLER --> SITE1
    CRAWLER --> SITE2
    CRAWLER --> SITEN
    
    %% Content analysis
    CRAWLER --> ANALYZER
    ANALYZER --> OLLAMA
    ANALYZER --> DB
    
    %% Notifications
    ANALYZER --> SMTP
    
    %% Scheduled jobs
    SCHEDULER --> CRAWLER
    
    %% Data persistence
    SCHEDULER --> DB
    CRAWLER --> DB
```

## Data Flow

### 1. Site Configuration
- Sites are configured in `sites.yml` with crawling parameters
- Each site has specific selectors, pagination rules, and crawl limits
- Configuration includes proxy settings and authentication details

### 2. Crawling Process
```mermaid
sequenceDiagram
    participant S as Scheduler
    participant C as Crawler
    participant P as Proxy Pool
    participant T as Target Site
    participant A as Analyzer
    participant O as Ollama
    participant D as Database
    participant E as Email Service
    
    S->>C: Trigger crawl job
    C->>D: Check robots.txt cache
    C->>P: Get random proxy
    C->>T: Fetch job listings (with stealth)
    T-->>C: HTML content
    C->>A: Extract opportunities
    A->>O: Analyze content with AI
    O-->>A: Classification results
    A->>D: Store opportunities
    A->>E: Send notifications (if new)
    C->>D: Update crawl status
```

### 3. Anti-Detection Measures
- **User Agent Rotation**: Random realistic user agents
- **Proxy Rotation**: Distributed requests across proxy pool
- **Stealth Mode**: Playwright stealth to avoid detection
- **Delay Jitter**: Random delays (0.8-2.4s) between actions
- **Headless/Headed Mix**: 10% headed sessions for fingerprint diversity

### 4. Pagination Strategy
1. **Primary**: CSS selector from `sites.yml`
2. **Fallback**: Link text matching `/(next|›)/i`
3. **Stop Conditions**: Repeat URL detection or configured limit

### 5. Content Analysis
- Extract job opportunities using site-specific selectors
- Classify content using Ollama AI service
- Filter based on configured terms and criteria
- Store structured data with metadata

## Component Responsibilities

### Frontend (Next.js)
- **Pages**: Site management, opportunity browsing, dashboard
- **Components**: Reusable UI components with Tailwind CSS
- **State**: SWR for data fetching and caching
- **API Integration**: RESTful API calls to backend

### Backend (FastAPI)
- **API Endpoints**: CRUD operations for sites and opportunities
- **Authentication**: Session-based auth (if implemented)
- **Validation**: Pydantic models for request/response validation
- **Error Handling**: Structured error responses

### Crawler Engine
- **Base Crawler**: Abstract class with common functionality
- **Site Crawlers**: Site-specific implementations
- **Stealth Features**: Anti-detection and proxy support
- **Error Recovery**: Retry logic and graceful degradation

### Content Analyzer
- **Text Extraction**: Clean and structure job posting content
- **AI Classification**: Use Ollama for content analysis
- **Term Filtering**: Apply configured inclusion/exclusion rules
- **Deduplication**: Prevent duplicate opportunity storage

### Job Scheduler
- **Cron Jobs**: Daily crawl execution
- **Queue Management**: Handle multiple site crawls
- **Status Tracking**: Monitor crawl progress and failures
- **Retry Logic**: Automatic retry for failed crawls

## Deployment Architecture

### Docker Compose (Development)
```mermaid
graph LR
    subgraph "Docker Network"
        FE[Frontend:3000]
        BE[Backend:8000]
        OL[Ollama:11434]
        DB[(SQLite)]
    end
    
    FE --> BE
    BE --> OL
    BE --> DB
```

### Render.com (Production)
```mermaid
graph TB
    subgraph "Render Services"
        FE_PROD[Frontend Service]
        BE_PROD[Backend Service]
        OL_PROD[Ollama Service]
        DB_PROD[(PostgreSQL)]
        CRON[Cron Job]
    end
    
    FE_PROD --> BE_PROD
    BE_PROD --> OL_PROD
    BE_PROD --> DB_PROD
    CRON --> BE_PROD
```

## Security Considerations

1. **Rate Limiting**: Respect target site limits
2. **Robots.txt Compliance**: Check and honor robots.txt
3. **Legal Compliance**: Analyze terms of service
4. **Data Privacy**: Secure storage of crawled data
5. **Proxy Security**: Secure proxy authentication
6. **Environment Variables**: Sensitive data in env vars

## Scalability

- **Horizontal Scaling**: Multiple crawler instances
- **Database Sharding**: Partition by site or date
- **Caching**: Redis for frequently accessed data
- **CDN**: Static asset delivery
- **Load Balancing**: Distribute API requests

## Monitoring & Observability

- **Health Checks**: Service availability monitoring
- **Metrics**: Crawl success rates, response times
- **Logging**: Structured logging with correlation IDs
- **Alerts**: Email notifications for failures
- **Dashboards**: Real-time status visualization 