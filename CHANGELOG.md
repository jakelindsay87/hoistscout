# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- End-to-end test suite with Playwright
- Architecture documentation with Mermaid diagrams
- Contributing guidelines with pre-commit setup
- Conventional commit configuration

### Changed
- Enhanced crawler base class with anti-bot rules documentation

### Fixed
- N/A

### Removed
- N/A

## [0.1.0] - 2024-01-15

### Added
- **MVP Scraper Implementation**
  - Base crawler framework with stealth capabilities
  - Site-specific crawler implementations
  - Playwright-based web scraping with anti-detection measures
  - Proxy rotation and user agent randomization
  - CAPTCHA detection and authentication handling
  - FastAPI backend with RESTful endpoints
  - Next.js frontend with modern UI components
  - Docker Compose development environment
  - Ollama AI integration for content analysis
  - Site configuration via YAML files
  - Opportunity extraction and storage
  - Email notification system
  - Scheduled crawling with cron jobs
  - Render.com deployment configuration
  - Basic error handling and logging
  - Health check endpoints
  - Database models for sites and opportunities
  - SWR-based data fetching in frontend
  - Tailwind CSS styling with responsive design
  - Component library with Radix UI primitives

### Technical Features
- **Anti-Detection Measures**
  - Random delays (0.8-2.4s jitter) between actions
  - 10% headed sessions for fingerprint diversity
  - Realistic user agent rotation
  - Proxy pool support
  - Stealth mode with playwright-stealth
- **Pagination Handling**
  - CSS selector-based navigation from sites.yml
  - Fallback to text-based next link detection
  - Duplicate URL prevention
  - Configurable page limits
- **Content Analysis**
  - AI-powered opportunity classification
  - Term-based filtering and analysis
  - Legal compliance checking
  - Structured data extraction
- **Deployment Ready**
  - Docker containerization
  - Environment-based configuration
  - Production deployment on Render.com
  - Database migrations and seeding
  - Health monitoring and alerts

### Security & Compliance
- Robots.txt compliance checking
- Terms of service analysis
- Rate limiting and respectful crawling
- Secure credential management
- Environment variable configuration
- HTTPS-only communication in production

### Documentation
- Comprehensive README with setup instructions
- API documentation
- Docker Compose configuration
- Environment variable documentation
- Basic troubleshooting guide

---

## Release Notes

### v0.1.0 - MVP Scraper

This initial release provides a complete minimum viable product for automated job opportunity scraping. The system can:

1. **Crawl Multiple Job Sites**: Configure sites via YAML with custom selectors and rules
2. **Extract Opportunities**: Parse job listings with AI-powered content analysis
3. **Store and Manage Data**: RESTful API with database persistence
4. **Provide Web Interface**: Modern React-based frontend for management
5. **Deploy to Production**: Ready for cloud deployment with Docker

**Key Capabilities:**
- Stealth crawling with anti-detection measures
- Intelligent pagination handling
- AI-powered content classification
- Email notifications for new opportunities
- Scheduled daily crawls
- Responsive web interface
- Production-ready deployment

**Getting Started:**
```bash
# Clone and start development environment
git clone https://github.com/your-org/hoistscraper.git
cd hoistscraper
docker compose up -d

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:8000
# Ollama: http://localhost:11434
```

**Next Steps:**
- Add more site-specific crawlers
- Implement advanced filtering options
- Add user authentication
- Enhance monitoring and analytics
- Improve error recovery mechanisms 