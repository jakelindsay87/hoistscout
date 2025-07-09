# HoistScout Product Requirements Document (PRD)

## Overview

HoistScout is a lead generation and data scraping platform designed to help businesses identify and connect with potential customers. The system automates the process of gathering contact information from various sources and provides a user-friendly interface for managing leads.

## Architecture Decisions

### External Redis Provider

**Decision**: Use an external Redis provider instead of self-hosted Redis on Render.

**Rationale**:
- Render does not offer a free Redis tier
- External providers offer free tiers suitable for development and small-scale production
- Reduces infrastructure complexity on the primary hosting platform

**Chosen Solutions**:
1. **Primary Option: Upstash**
   - Free tier includes 10,000 commands/day
   - 256MB storage
   - Built-in REST API for serverless compatibility
   - Global replication available

2. **Alternative Option: Railway**
   - Free tier with $5 credit/month
   - 512MB memory limit
   - Easy integration with environment variables
   - Good developer experience

**Impact on Deployment**:
- Additional service to provision and manage
- Requires secure credential management
- Network latency considerations for cross-service communication
- Potential cold start delays with serverless Redis

**Monitoring Requirements**:
- Redis connection health checks
- Command usage tracking (for free tier limits)
- Memory usage monitoring
- Latency metrics for queue operations
- Error rate tracking for Redis operations

## Infrastructure Requirements

### Core Services

1. **Web Application**
   - Python/Flask or Django application
   - Hosted on Render (free tier compatible)
   - Environment: Python 3.11+

2. **Background Task Queue**
   - Celery for task processing
   - Redis as message broker (external provider)
   - Worker processes for scraping tasks

3. **Database**
   - PostgreSQL (Render's free tier)
   - 1GB storage limit on free tier
   - Automatic backups

4. **Redis (External Provider)**
   - Provider: Upstash or Railway
   - Minimum: 25MB storage
   - Used for: Task queue, caching, session storage
   - Connection: TLS/SSL required

### Environment Variables

**Required Variables**:
```
# Database
DATABASE_URL=postgresql://...

# Redis (External)
REDIS_URL=redis://username:password@host:port
REDIS_TLS_URL=rediss://... (if using TLS)

# Application
SECRET_KEY=<secure-random-key>
FLASK_ENV=production
DEBUG=False

# Celery
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# Optional monitoring
SENTRY_DSN=<if-using-sentry>
```

### Service Dependencies

1. **Render Services**:
   - Web Service (Flask/Django app)
   - Background Worker (Celery)
   - PostgreSQL Database

2. **External Services**:
   - Redis Provider (Upstash/Railway)
   - Optional: Error tracking (Sentry)
   - Optional: Log aggregation

## Deployment Process

### Step-by-Step Deployment

1. **Provision External Redis**
   - Sign up for Upstash or Railway
   - Create Redis instance
   - Note connection URL and credentials
   - Test connection from local environment

2. **Configure Render Services**
   - Create new Web Service from GitHub repo
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `gunicorn app:app` (adjust for your app)
   - Add all required environment variables

3. **Database Setup**
   - Provision PostgreSQL on Render
   - Run migrations: `python manage.py migrate`
   - Create initial admin user

4. **Background Worker Setup**
   - Create new Background Worker on Render
   - Set command: `celery -A app.celery worker --loglevel=info`
   - Use same environment variables as web service

5. **Environment Variable Configuration**
   - Add REDIS_URL from external provider
   - Set DATABASE_URL from Render PostgreSQL
   - Generate and set SECRET_KEY
   - Configure any API keys for scraping

6. **Health Check Requirements**
   - Web service: HTTP endpoint at `/health`
   - Redis: Connection test on startup
   - Database: Connection pool validation
   - Celery: Worker heartbeat monitoring

### Deployment Checklist

- [ ] Redis instance provisioned and accessible
- [ ] All environment variables configured
- [ ] Database migrations completed
- [ ] Static files properly served
- [ ] Health check endpoints responding
- [ ] Background workers processing tasks
- [ ] Error tracking configured
- [ ] Logs accessible for debugging

## Future Considerations

### Redis Migration Path

**When to Migrate to Paid Redis**:
- Exceeding 10,000 commands/day (Upstash limit)
- Need for persistent connections
- Requiring more than 256MB storage
- Latency becomes critical issue

**Migration Options**:
1. **Upstash Paid Tier**: $10/month for 100K commands/day
2. **Redis Cloud**: $0/month with 30MB, scales as needed
3. **Self-hosted on VPS**: Full control, higher maintenance

### Alternative Task Queue Options

**Database-Backed Queues** (if Redis becomes constraint):
1. **Django-Q**:
   - Uses PostgreSQL for queue
   - No Redis dependency
   - Good for low-medium volume

2. **Celery with Database Broker**:
   - Django-celery-beat for scheduling
   - SQLAlchemy as broker
   - Higher latency than Redis

3. **PostgreSQL LISTEN/NOTIFY**:
   - Native PostgreSQL feature
   - Very lightweight
   - Limited features compared to Celery

### Scaling Considerations

1. **Horizontal Scaling**:
   - Add more Celery workers
   - Implement rate limiting
   - Use Redis clustering

2. **Performance Optimization**:
   - Implement caching strategy
   - Optimize database queries
   - Use connection pooling

3. **Cost Management**:
   - Monitor free tier usage
   - Implement usage alerts
   - Plan for graduated pricing

## Technical Specifications

### API Endpoints

- `/api/leads` - CRUD operations for leads
- `/api/campaigns` - Campaign management
- `/api/scrape` - Initiate scraping tasks
- `/api/status` - Task status checking
- `/health` - Health check endpoint

### Data Models

1. **Lead**:
   - Email, name, company
   - Source URL
   - Verification status
   - Created/updated timestamps

2. **Campaign**:
   - Name, description
   - Target criteria
   - Status (active/paused/completed)
   - Lead associations

3. **ScrapingTask**:
   - URL/source
   - Status
   - Result count
   - Error messages

### Security Considerations

- All external connections use TLS/SSL
- API authentication required
- Rate limiting on public endpoints
- Input validation and sanitization
- Regular security updates

## Development Guidelines

### Local Development

1. Use Docker Compose for local services
2. Environment variables in `.env` file
3. Redis can be local for development
4. Use development database

### Testing Strategy

- Unit tests for business logic
- Integration tests for API endpoints
- Mock external services in tests
- Celery task testing with eager mode

### Monitoring and Logging

- Structured logging (JSON format)
- Error tracking with Sentry
- Performance monitoring
- Uptime monitoring for all services