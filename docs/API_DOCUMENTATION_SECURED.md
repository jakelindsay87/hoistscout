# HoistScraper API Documentation (Secured)

## Overview

This document describes the HoistScraper API endpoints with the new security measures implemented.

## Authentication

### API Key Authentication

Admin endpoints require an `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key-here" https://hoistscraper.onrender.com/api/admin/stats
```

### Future: JWT Authentication

Once user authentication is implemented:

```bash
curl -H "Authorization: Bearer your-jwt-token" https://hoistscraper.onrender.com/api/protected
```

## Base URL

- Production: `https://hoistscraper.onrender.com`
- Development: `http://localhost:8000`

## Public Endpoints

### Health Check

Check service health status.

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-06-28T10:29:13.322460",
  "service": "hoistscraper-backend"
}
```

### Get Websites

Retrieve all websites with pagination.

```http
GET /api/websites?page=1&size=50
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `size` (int): Items per page (default: 50, max: 100)
- `government_level` (string): Filter by government level
- `region` (string): Filter by region
- `grant_type` (string): Filter by grant type

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "url": "https://example.gov.au",
      "name": "Example Government Grants",
      "description": "Grant opportunities",
      "active": true,
      "region": "NSW",
      "government_level": "state",
      "grant_type": "business",
      "created_at": "2024-06-28T10:00:00Z",
      "updated_at": "2024-06-28T10:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "size": 50,
  "pages": 2
}
```

### Get Single Website

```http
GET /api/websites/{website_id}
```

**Response:**
```json
{
  "id": 1,
  "url": "https://example.gov.au",
  "name": "Example Government Grants",
  "description": "Grant opportunities",
  "active": true,
  "region": "NSW",
  "government_level": "state",
  "grant_type": "business",
  "created_at": "2024-06-28T10:00:00Z",
  "updated_at": "2024-06-28T10:00:00Z"
}
```

### Get Opportunities

```http
GET /api/opportunities?page=1&size=50
```

**Query Parameters:**
- `page` (int): Page number
- `size` (int): Items per page
- `website_id` (int): Filter by website
- `job_id` (int): Filter by scrape job

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "title": "Small Business Grant",
      "description": "Funding for small businesses",
      "funding_amount": "$10,000 - $50,000",
      "deadline": "2024-12-31T00:00:00Z",
      "eligibility": "Small businesses with < 20 employees",
      "application_url": "https://apply.example.gov.au",
      "source_url": "https://example.gov.au/grants/123",
      "website_id": 1,
      "scrape_job_id": 456,
      "created_at": "2024-06-28T10:00:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "size": 50,
  "pages": 1
}
```

### Get Jobs

```http
GET /api/jobs?status=completed&website_id=1
```

**Query Parameters:**
- `page` (int): Page number
- `size` (int): Items per page
- `status` (string): Filter by status (pending, running, completed, failed)
- `website_id` (int): Filter by website

## Protected Endpoints (Require Authentication)

### Create Website

```http
POST /api/websites
Content-Type: application/json

{
  "url": "https://newsite.gov.au",
  "name": "New Grant Site",
  "description": "Description of the site",
  "active": true,
  "region": "VIC",
  "government_level": "state",
  "grant_type": "research"
}
```

**Response:** 201 Created
```json
{
  "id": 123,
  "url": "https://newsite.gov.au",
  "name": "New Grant Site",
  ...
}
```

### Update Website

```http
PUT /api/websites/{website_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "active": false
}
```

### Delete Website

```http
DELETE /api/websites/{website_id}
```

### Trigger Scrape

```http
POST /api/websites/{website_id}/scrape
```

**Response:**
```json
{
  "id": 789,
  "website_id": 1,
  "status": "pending",
  "created_at": "2024-06-28T10:00:00Z"
}
```

## Admin Endpoints (Require X-API-Key)

### Get Admin Statistics

```http
GET /api/admin/stats
X-API-Key: your-admin-api-key
```

**Response:**
```json
{
  "websites": {
    "total": 100,
    "active": 85,
    "inactive": 15
  },
  "jobs": {
    "total": 5000,
    "pending": 10,
    "running": 5,
    "completed": 4900,
    "failed": 85
  },
  "opportunities": {
    "total": 25000
  },
  "timestamp": "2024-06-28T10:00:00Z"
}
```

### Clear Database (DANGEROUS)

```http
POST /api/admin/clear-database?confirm=true&tables=opportunity,scrapejob
X-API-Key: your-admin-api-key
```

**Query Parameters:**
- `confirm` (bool): Must be true to execute
- `tables` (string): Comma-separated list of tables to clear

**Response:**
```json
{
  "status": "success",
  "cleared_tables": [
    "opportunity (25000 records)",
    "scrapejob (5000 records)"
  ],
  "timestamp": "2024-06-28T10:00:00Z"
}
```

**Note:** This endpoint is disabled in production unless `ALLOW_PROD_DB_CLEAR=true` is set.

## Debug Endpoints (Development Only)

These endpoints return 404 in production:

### Debug Info

```http
GET /api/debug
```

### Deployment Info

```http
GET /api/debug/deployment
```

### Schema Info

```http
GET /api/debug/schema
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 401 Unauthorized
```json
{
  "detail": "Admin API key required"
}
```

### 403 Forbidden
```json
{
  "detail": "Invalid API key"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

- Default: 100 requests per minute per IP
- Applies to all endpoints except `/health`
- Returns 429 status code when exceeded

## Security Headers

All responses include:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000`
- `Content-Security-Policy: [policy]`

## CORS Configuration

Allowed origins:
- `http://localhost:3000` (development)
- `https://hoistscraper-fe.onrender.com` (production)

## Pagination

All list endpoints support pagination:

```json
{
  "items": [...],
  "total": 1000,
  "page": 1,
  "size": 50,
  "pages": 20
}
```

## Webhooks (Future)

Planned webhook events:
- `website.created`
- `website.updated`
- `website.deleted`
- `scrape.started`
- `scrape.completed`
- `scrape.failed`
- `opportunity.found`

## API Versioning (Future)

Future versions will use URL versioning:
- v1: `/api/v1/websites`
- v2: `/api/v2/websites`

## Client Libraries (Future)

Planned client libraries:
- Python: `pip install hoistscraper-client`
- JavaScript: `npm install @hoistscraper/client`
- Go: `go get github.com/hoistscraper/client-go`

## Support

For API support:
- Documentation: This document
- Issues: GitHub repository
- Email: api-support@hoistscraper.com (future)