# CLAUDE.md - HoistScraper Frontend

## Project Overview

HoistScraper is a web scraping platform designed to automate the discovery and extraction of job opportunities from various websites. The frontend is built with Next.js 14 and provides a user interface for managing scraping sites, viewing job opportunities, monitoring scraping jobs, and reviewing results.

## Architecture Context

### System Components
- **Frontend**: Next.js 14 with React 18, TypeScript, and Tailwind CSS
- **Backend**: FastAPI server providing RESTful APIs (running on port 8000)
- **Database**: SQLite (development) / PostgreSQL (production)
- **Job Queue**: Redis + RQ for background scraping tasks
- **AI Service**: Ollama with Mistral 7B for content analysis
- **Scraping Engine**: Playwright-based crawler with anti-detection features

### Current Development State
- **Current Branch**: `feature/csv-ingest-v2`
- **Recently Completed**: CSV ingestion feature for bulk website import
- **In Progress**: Frontend development following the feature/dashboard-mvp plan

## Frontend Structure

### Pages
1. **Home** (`/`) - Landing page
2. **Sites** (`/sites`) - Manage scraping targets
   - List all configured sites
   - Add new sites via form or CSV upload
   - Manage site credentials for authenticated scraping
3. **Jobs** (`/jobs`) - Monitor scraping jobs
   - View job status (pending, in_progress, completed, failed)
   - Trigger new scrape jobs
   - Real-time status updates
4. **Opportunities** (`/opportunities`) - Browse discovered job opportunities
   - List view with filtering/sorting
   - Detail view for individual opportunities
5. **Results** (`/results`) - View raw scraping results
   - JSON viewer for debugging
   - Download capabilities

### Key Components
- **ErrorBoundary**: Global error handling
- **LoadingSpinner**: Consistent loading states
- **Sites Components**:
  - `AddSitesModal`: Form and CSV upload for adding sites
  - `SecretsModal`: Secure credential management
  - `SitesDataGrid`: Table view with sorting/filtering
- **UI Components**: Button and Toast from shadcn/ui

### State Management
- **React Query**: For server state management and caching
- **Custom Hooks**:
  - `useSites`: Site CRUD operations
  - `useJobs`: Job monitoring and triggering
  - `useResults`: Fetching scrape results

### API Integration
- **Base URL**: `http://localhost:8000` (dev) / configured via `NEXT_PUBLIC_API_URL`
- **Key Endpoints**:
  - `GET/POST /api/sites` - Site management
  - `POST /api/ingest/csv` - Bulk CSV import
  - `POST /api/scrape/{site_id}` - Trigger scraping
  - `GET /api/jobs` - List jobs with status
  - `GET /data/{job_id}.json` - Fetch results

## Development Guidelines

### Code Style
- **TypeScript**: Strict mode enabled, all code must be properly typed
- **React**: Functional components with hooks
- **Styling**: Tailwind CSS with custom theme tokens
- **Testing**: Vitest for unit tests, MSW for API mocking

### Key Development Principles
1. **Test-Driven Development**: Write tests before implementation
2. **Type Safety**: No `any` types, proper error handling
3. **Performance**: Code splitting, lazy loading, optimistic updates
4. **Accessibility**: WCAG compliance, semantic HTML
5. **Security**: No sensitive data in frontend code, proper input validation

### Current Tasks (from task-breakdown.md)

#### Feature: Dashboard MVP
- [x] Create API client infrastructure (`lib/apiFetch.ts`)
- [ ] Implement React Query hooks
  - [ ] `useSites` - list and create sites
  - [ ] `useJobs` - list and monitor jobs  
  - [ ] `useResults` - fetch job results
- [ ] Create page components with proper loading/error states
- [ ] Add CSV upload functionality to Sites page
- [ ] Implement real-time job status updates
- [ ] Add JSON viewer for results page

### Testing Requirements
- Unit test coverage ≥ 90%
- All pages must render without errors
- API integration tests with MSW
- Build verification (`npm run build` must succeed)

## Common Commands

```bash
# Development
npm run dev              # Start development server
npm run build           # Build for production
npm run test            # Run tests with Vitest
npm run typecheck       # Check TypeScript types
npm run lint            # Run ESLint

# Testing specific files
npm test -- sites       # Test sites-related code
npm test -- --watch     # Run tests in watch mode
```

## Environment Variables

```bash
# Required
NEXT_PUBLIC_API_URL=http://localhost:8000  # Backend API URL

# Optional (future)
NEXT_PUBLIC_SENTRY_DSN=     # Error tracking
NEXT_PUBLIC_GA_ID=          # Analytics
```

## Current Issues & TODOs

1. **Immediate**:
   - Complete React Query hook implementations
   - Add loading skeletons for better UX
   - Implement CSV upload with progress tracking
   - Add error boundaries to all pages

2. **Next Phase**:
   - Implement TanStack Table for advanced data grids
   - Add dark mode support
   - Improve mobile responsiveness
   - Add JSON syntax highlighting in results viewer

3. **Future Enhancements**:
   - WebSocket support for real-time updates
   - Advanced filtering/search capabilities
   - Export functionality for results
   - Batch operations for sites/jobs

## Security Considerations

- All API calls use the centralized `apiFetch` wrapper
- Credentials are never stored in frontend code
- Input validation on all forms
- XSS prevention through React's automatic escaping
- CORS properly configured for production

## Performance Guidelines

- Bundle size target: < 500KB gzipped
- Page load time: < 2 seconds
- Use React.lazy() for route-based code splitting
- Implement virtual scrolling for large data sets
- Cache API responses with React Query

## Debugging Tips

1. **API Issues**: Check browser DevTools Network tab
2. **State Problems**: Use React DevTools extension
3. **Type Errors**: Run `npm run typecheck`
4. **Build Failures**: Check `npm run build` output
5. **Test Failures**: Run tests with `--reporter=verbose`

## Related Documentation

- `/docs/task-breakdown.md` - Detailed feature development tasks
- `/docs/master-prd-v2.md` - Product requirements and specifications
- `/docs/architecture.md` - System architecture and data flow
- Backend README at `/backend/README.md`

## Contact & Support

This is part of the HoistScraper mono-repo. For backend-related issues, see the backend CLAUDE.md. For deployment and CI/CD, refer to the root-level documentation.