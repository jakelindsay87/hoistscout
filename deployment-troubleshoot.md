# Deployment Troubleshooting Guide

## Issues Fixed

### 1. YAML Indentation Issues in render.yaml
- **Problem**: Inconsistent indentation causing YAML parsing errors
- **Solution**: Fixed indentation and switched frontend from Node.js runtime to Docker runtime

### 2. Frontend Runtime Issues
- **Problem**: Node.js runtime having issues with TypeScript compilation
- **Solution**: Changed to Docker runtime using the existing Dockerfile

### 3. CORS Configuration
- **Problem**: Backend CORS only allowing localhost, blocking production frontend
- **Solution**: Added production frontend URL to CORS allowed origins

## Current Configuration

### Backend (hoistscraper-api)
- Runtime: Docker
- Dockerfile: `./backend/Dockerfile`
- Health Check: `/health`
- Port: 8000

### Frontend (hoistscraper-fe)
- Runtime: Docker
- Dockerfile: `./frontend/Dockerfile`
- Port: 3000
- Environment: `NEXT_PUBLIC_API_URL=https://hoistscraper-api.onrender.com`

## Environment Variables to Set in Render Dashboard

### Backend Service
Set these in the Render dashboard (marked as `sync: false` in render.yaml):

1. `DATABASE_URL` - PostgreSQL connection string
2. `SMTP_USER` - Gmail SMTP username
3. `SMTP_PASSWORD` - Gmail app password
4. `NOTIFY_EMAIL` - Email for notifications

### Frontend Service
These are already configured in render.yaml:
- `NEXT_PUBLIC_API_URL=https://hoistscraper-api.onrender.com`
- `NODE_ENV=production`

## Deployment Order

1. **Database** - Deploy first (hoistscraper-db)
2. **Backend** - Deploy second (hoistscraper-api)
3. **Frontend** - Deploy last (hoistscraper-fe)

## Common Issues and Solutions

### Backend Issues
- **Health check failing**: Ensure `/health` endpoint is accessible
- **Database connection**: Set `DATABASE_URL` in environment variables
- **SMTP errors**: Configure SMTP environment variables

### Frontend Issues
- **API connection**: Verify `NEXT_PUBLIC_API_URL` points to backend
- **Build errors**: Check Node.js version compatibility (using Node 18)
- **CORS errors**: Ensure backend allows frontend domain

## Testing Deployment

### Backend Health Check
```bash
curl https://hoistscraper-api.onrender.com/health
```
Expected response:
```json
{"status": "healthy", "service": "hoistscraper-api"}
```

### Frontend Access
Visit: https://hoistscraper-fe.onrender.com

### API Documentation
Visit: https://hoistscraper-api.onrender.com/docs

## Next Steps

1. Deploy the updated render.yaml configuration
2. Set the required environment variables in Render dashboard
3. Monitor deployment logs for any remaining issues
4. Test the health endpoints once deployed 