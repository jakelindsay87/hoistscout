# HoistScraper Backup & Recovery Guide

## Overview

HoistScraper includes a comprehensive backup solution for PostgreSQL data with:
- Automated daily backups
- S3 offsite storage support
- Point-in-time recovery
- Health monitoring and alerts
- Easy restore procedures

## Quick Start

### 1. Configure Backup Environment

Add to your `.env.production`:

```bash
# Backup Configuration
BACKUP_RETENTION_DAYS=30
BACKUP_WEBHOOK_URL=https://your-webhook-url/alerts

# S3 Configuration (optional but recommended)
BACKUP_S3_BUCKET=your-backup-bucket
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_DEFAULT_REGION=us-east-1
```

### 2. Start Backup Service

```bash
# Start backup container
docker-compose -f docker-compose.backup.yml up -d

# Verify backup service is running
docker-compose -f docker-compose.backup.yml ps

# Check backup logs
docker logs hoistscraper-backup
```

### 3. Manual Backup

```bash
# Run backup immediately
docker exec hoistscraper-backup backup-postgres

# Or from host system
docker-compose -f docker-compose.backup.yml exec backup backup-postgres
```

## Backup Schedule

Default cron schedule (configured in `scripts/backup-crontab`):

- **Daily**: 2:00 AM - 30 day retention
- **Weekly**: Sunday 3:00 AM - 90 day retention  
- **Monthly**: 1st of month 4:00 AM - 365 day retention (S3 Glacier)
- **Health Check**: Every 6 hours

## Restore Procedures

### Restore from Local Backup

```bash
# List available backups
ls -la /var/lib/docker/volumes/hoistscraper_backup-data/_data/

# Restore specific backup
docker exec hoistscraper-backup restore-postgres \
  /backups/hoistscraper_backup_20240115_020000.sql.gz

# Force restore without confirmation
docker exec hoistscraper-backup restore-postgres \
  /backups/hoistscraper_backup_20240115_020000.sql.gz --force
```

### Restore from S3

```bash
# List S3 backups
aws s3 ls s3://your-backup-bucket/postgres/

# Restore from S3 (automatic download)
docker exec hoistscraper-backup restore-postgres \
  s3://your-backup-bucket/postgres/hoistscraper_backup_20240115_020000.sql.gz
```

### Emergency Recovery

If the main database is corrupted:

1. Stop all services except database:
   ```bash
   docker-compose stop backend worker frontend
   ```

2. Create emergency backup of corrupted data:
   ```bash
   docker exec hoistscraper-db pg_dump -U hoistscraper hoistscraper > emergency_backup.sql
   ```

3. Restore from last known good backup:
   ```bash
   docker exec hoistscraper-backup restore-postgres \
     /backups/[last-good-backup].sql.gz --force
   ```

4. Restart services:
   ```bash
   docker-compose up -d
   ```

## Backup Storage

### Local Storage

Backups are stored in Docker volume: `hoistscraper_backup-data`

Access from host:
```bash
# Default location (may vary by Docker installation)
/var/lib/docker/volumes/hoistscraper_backup-data/_data/
```

### S3 Storage

Structure:
```
s3://your-bucket/
└── postgres/
    ├── hoistscraper_backup_20240115_020000.sql.gz  (daily)
    ├── hoistscraper_backup_20240114_030000.sql.gz  (weekly)
    └── hoistscraper_backup_20240101_040000.sql.gz  (monthly)
```

### Storage Classes

- **Daily**: STANDARD_IA (Infrequent Access)
- **Weekly**: STANDARD_IA
- **Monthly**: GLACIER (Long-term archive)

## Monitoring & Alerts

### Health Checks

The backup system performs automatic health checks every 6 hours:

1. Verifies recent backups exist
2. Checks backup file integrity
3. Tests database connectivity
4. Monitors disk space
5. Validates S3 uploads

### Alert Webhook

Configure `BACKUP_WEBHOOK_URL` to receive alerts:

```json
{
  "status": "error|warning|success",
  "message": "Backup failed: Connection refused",
  "timestamp": "2024-01-15T14:30:00Z"
}
```

### Manual Health Check

```bash
docker exec hoistscraper-backup test-backup
```

## Backup Security

### Encryption

1. **In Transit**: Use SSL/TLS for S3 uploads
2. **At Rest**: Enable S3 bucket encryption
3. **Local**: Encrypt Docker volume

### Access Control

1. Restrict S3 bucket access with IAM policies
2. Use separate AWS credentials for backups
3. Rotate credentials regularly
4. Monitor access logs

### Example IAM Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-backup-bucket/*",
        "arn:aws:s3:::your-backup-bucket"
      ]
    }
  ]
}
```

## Testing Backups

### Automated Testing

1. Create test database:
   ```bash
   docker exec hoistscraper-db createdb -U hoistscraper hoistscraper_test
   ```

2. Restore to test database:
   ```bash
   DATABASE_URL=postgresql://user:pass@db:5432/hoistscraper_test \
     docker exec hoistscraper-backup restore-postgres /backups/latest.sql.gz
   ```

3. Verify data:
   ```bash
   docker exec hoistscraper-db psql -U hoistscraper hoistscraper_test \
     -c "SELECT COUNT(*) FROM website;"
   ```

4. Clean up:
   ```bash
   docker exec hoistscraper-db dropdb -U hoistscraper hoistscraper_test
   ```

### Recovery Time Testing

Regularly test full recovery procedure:

1. Note start time
2. Simulate failure
3. Execute restore
4. Verify application functionality
5. Calculate Recovery Time Objective (RTO)

Target RTO: < 30 minutes

## Troubleshooting

### Common Issues

1. **Backup Fails with "Permission Denied"**
   ```bash
   # Fix permissions
   docker exec hoistscraper-backup chown -R backup:backup /backups
   ```

2. **S3 Upload Timeout**
   ```bash
   # Check AWS credentials
   docker exec hoistscraper-backup aws s3 ls
   
   # Test connectivity
   docker exec hoistscraper-backup aws s3 cp /etc/hosts s3://bucket/test.txt
   ```

3. **Out of Disk Space**
   ```bash
   # Check disk usage
   df -h /var/lib/docker/volumes/
   
   # Clean old backups
   docker exec hoistscraper-backup \
     find /backups -name "*.sql.gz" -mtime +30 -delete
   ```

4. **Restore Fails**
   ```bash
   # Check backup integrity
   docker exec hoistscraper-backup gzip -t /backups/backup.sql.gz
   
   # View backup header
   docker exec hoistscraper-backup gunzip -c /backups/backup.sql.gz | head -20
   ```

### Logs

View backup logs:
```bash
# Container logs
docker logs hoistscraper-backup

# Backup operation logs
docker exec hoistscraper-backup tail -f /var/log/hoistscraper-backup.log

# Cron logs
docker exec hoistscraper-backup tail -f /var/log/cron.log
```

## Best Practices

1. **Test Restores Regularly**: Monthly restore drills
2. **Monitor Backup Size**: Track growth trends
3. **Verify Offsite Copies**: Ensure S3 uploads succeed
4. **Document Procedures**: Keep runbooks updated
5. **Secure Credentials**: Use AWS IAM roles when possible
6. **Automate Monitoring**: Set up alerts for failures
7. **Retention Policy**: Balance storage costs vs recovery needs

## Disaster Recovery Plan

### Scenario 1: Database Corruption

1. Stop application services
2. Restore from most recent backup
3. Verify data integrity
4. Resume services
5. Investigate corruption cause

### Scenario 2: Complete System Failure

1. Provision new infrastructure
2. Deploy application stack
3. Restore database from S3
4. Update DNS/load balancers
5. Verify functionality

### Scenario 3: Ransomware/Security Breach

1. Isolate affected systems
2. Assess backup integrity
3. Restore to clean infrastructure
4. Reset all credentials
5. Implement additional security measures

## Maintenance Windows

Recommended backup maintenance:

- **Weekly**: Verify backup logs
- **Monthly**: Test restore procedure
- **Quarterly**: Review retention policy
- **Annually**: Disaster recovery drill

## Support

For backup-related issues:

1. Check logs in `/var/log/hoistscraper-backup.log`
2. Verify environment variables
3. Test database connectivity
4. Check disk space and permissions
5. Review S3 bucket policies