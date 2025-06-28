# HoistScraper Monitoring Setup

This directory contains configuration files for monitoring HoistScraper with Prometheus, Grafana, and Alertmanager.

## Components

- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Alertmanager**: Alert routing and notifications
- **Sentry**: Error tracking (configured via environment variables)

## Quick Start

### 1. Set Environment Variables

Add these to your `.env.production` file:

```bash
# Sentry Configuration
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
ENVIRONMENT=production

# Grafana Admin Credentials
GRAFANA_USER=admin
GRAFANA_PASSWORD=your-secure-password

# Prometheus Configuration (optional)
PROMETHEUS_ENABLED=true
```

### 2. Start Monitoring Stack

```bash
# Create the shared network if it doesn't exist
docker network create hoistscraper-network

# Start monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

# Verify services are running
docker-compose -f docker-compose.monitoring.yml ps
```

### 3. Access Services

- **Grafana**: http://localhost:3001 (admin/admin by default)
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

### 4. Configure Alerts

Edit `alertmanager.yml` to add your notification channels:

- Email notifications
- Slack webhooks
- PagerDuty integration
- Custom webhooks

## Available Metrics

### Application Metrics

- `hoistscraper_scrape_jobs_total`: Total scrape jobs by status
- `hoistscraper_scrape_job_duration_seconds`: Job execution time
- `hoistscraper_opportunities_extracted_total`: Opportunities found
- `hoistscraper_active_scrape_jobs`: Currently running jobs
- `hoistscraper_websites_total`: Total websites by status
- `hoistscraper_api_requests_total`: API request counts
- `hoistscraper_api_request_duration_seconds`: API response times
- `hoistscraper_worker_health_status`: Worker health (0/1)
- `hoistscraper_database_connections_active`: Active DB connections
- `hoistscraper_ollama_model_loaded`: Ollama model status (0/1)

### Pre-configured Alerts

- **Critical**:
  - Worker down for >5 minutes
  - Database connection pool exhausted
  - >50% scrape failure rate
  - Queue processing stopped

- **Warning**:
  - High database connections
  - >25% scrape failure rate
  - High API latency (>2s)
  - Long-running scrape jobs (>10min)
  - High queue backlog (>100 jobs)

## Grafana Dashboard

The pre-configured dashboard includes:

- Worker health status
- Active scrape jobs gauge
- Scrape failure rate graph
- API request rate by endpoint
- API response time (95th percentile)
- Opportunities extracted (24h)
- Active websites count

## Customization

### Adding Custom Metrics

1. Add metric definition in `backend/hoistscraper/monitoring.py`
2. Update code to track the metric
3. Add visualization to Grafana dashboard

### Adding Custom Alerts

1. Edit `prometheus-alerts.yml`
2. Restart Prometheus: `docker-compose -f docker-compose.monitoring.yml restart prometheus`
3. Configure notification in `alertmanager.yml`

### Creating New Dashboards

1. Create dashboard in Grafana UI
2. Export as JSON
3. Save to `grafana-dashboards/` directory
4. Restart Grafana to auto-provision

## Production Deployment

### With Main Application

```bash
# Start everything together
docker-compose -f docker-compose.secure.yml -f docker-compose.monitoring.yml up -d
```

### Separate Monitoring Infrastructure

Deploy monitoring stack on a dedicated server and configure Prometheus to scrape your production endpoints remotely.

## Troubleshooting

### Metrics Not Appearing

1. Check backend logs for metric tracking
2. Verify `/metrics` endpoint is accessible
3. Check Prometheus targets: http://localhost:9090/targets

### Alerts Not Firing

1. Check alert rules in Prometheus UI
2. Verify Alertmanager configuration
3. Test with manual alert: `amtool alert add test`

### Grafana Dashboard Empty

1. Verify Prometheus datasource is configured
2. Check time range in dashboard
3. Ensure metrics are being collected

## Security Considerations

1. Change default Grafana password immediately
2. Use strong authentication for all services
3. Restrict network access in production
4. Enable HTTPS for external access
5. Regularly update monitoring images