#!/bin/bash

# Backup Test Script for HoistScraper
# This script verifies that backups are working correctly

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups}"
TEST_DB_NAME="hoistscraper_test_$$"
ALERT_THRESHOLD_HOURS="${BACKUP_ALERT_THRESHOLD:-48}"

# Load environment variables
if [ -f "/app/.env.production" ]; then
    export $(cat /app/.env.production | grep -v '^#' | xargs)
fi

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] BACKUP_TEST: $1"
}

# Function to send alert
send_alert() {
    local severity=$1
    local message=$2
    
    if [ ! -z "$BACKUP_WEBHOOK_URL" ]; then
        curl -X POST "$BACKUP_WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"severity\": \"$severity\", \"test\": \"backup\", \"message\": \"$message\", \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" \
            2>/dev/null || true
    fi
    
    # Also log to syslog if available
    if command -v logger &> /dev/null; then
        logger -t "hoistscraper-backup" -p "user.$severity" "$message"
    fi
}

# Test 1: Check if recent backups exist
log "Test 1: Checking for recent backups..."

# Find most recent local backup
if [ -d "$BACKUP_DIR" ]; then
    LATEST_BACKUP=$(find "$BACKUP_DIR" -name "hoistscraper_backup_*.sql.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -f2- -d" ")
    
    if [ -z "$LATEST_BACKUP" ]; then
        log "ERROR: No backup files found in $BACKUP_DIR"
        send_alert "error" "No backup files found in backup directory"
        exit 1
    fi
    
    # Check backup age
    BACKUP_AGE_SECONDS=$(( $(date +%s) - $(stat -c %Y "$LATEST_BACKUP") ))
    BACKUP_AGE_HOURS=$(( $BACKUP_AGE_SECONDS / 3600 ))
    
    log "Latest backup: $(basename $LATEST_BACKUP) (${BACKUP_AGE_HOURS} hours old)"
    
    if [ $BACKUP_AGE_HOURS -gt $ALERT_THRESHOLD_HOURS ]; then
        log "WARNING: Latest backup is older than ${ALERT_THRESHOLD_HOURS} hours"
        send_alert "warning" "Latest backup is ${BACKUP_AGE_HOURS} hours old (threshold: ${ALERT_THRESHOLD_HOURS})"
    fi
else
    log "WARNING: Backup directory does not exist: $BACKUP_DIR"
fi

# Test 2: Check S3 backups if configured
if [ ! -z "$BACKUP_S3_BUCKET" ] && [ ! -z "$AWS_ACCESS_KEY_ID" ]; then
    log "Test 2: Checking S3 backups..."
    
    # Get latest S3 backup
    LATEST_S3_BACKUP=$(aws s3 ls "s3://$BACKUP_S3_BUCKET/postgres/" | grep "hoistscraper_backup_" | sort | tail -1 | awk '{print $4}')
    
    if [ -z "$LATEST_S3_BACKUP" ]; then
        log "ERROR: No backup files found in S3 bucket"
        send_alert "error" "No backup files found in S3 bucket: $BACKUP_S3_BUCKET"
    else
        log "Latest S3 backup: $LATEST_S3_BACKUP"
        
        # Download backup metadata
        BACKUP_SIZE=$(aws s3 ls "s3://$BACKUP_S3_BUCKET/postgres/$LATEST_S3_BACKUP" | awk '{print $3}')
        BACKUP_SIZE_MB=$(( $BACKUP_SIZE / 1024 / 1024 ))
        
        if [ $BACKUP_SIZE -lt 1024 ]; then
            log "WARNING: S3 backup suspiciously small: ${BACKUP_SIZE} bytes"
            send_alert "warning" "S3 backup file is suspiciously small: ${BACKUP_SIZE} bytes"
        else
            log "S3 backup size: ${BACKUP_SIZE_MB} MB"
        fi
    fi
fi

# Test 3: Verify backup integrity (if recent backup exists)
if [ ! -z "$LATEST_BACKUP" ] && [ -f "$LATEST_BACKUP" ]; then
    log "Test 3: Verifying backup integrity..."
    
    # Test gzip integrity
    if gzip -t "$LATEST_BACKUP" 2>/dev/null; then
        log "Backup compression is valid"
    else
        log "ERROR: Backup file is corrupted"
        send_alert "error" "Backup file is corrupted: $(basename $LATEST_BACKUP)"
        exit 1
    fi
    
    # Check backup content (first few lines)
    BACKUP_HEADER=$(gunzip -c "$LATEST_BACKUP" | head -n 20)
    if echo "$BACKUP_HEADER" | grep -q "PostgreSQL database dump"; then
        log "Backup header is valid"
        
        # Count tables in backup
        TABLE_COUNT=$(gunzip -c "$LATEST_BACKUP" | grep -c "CREATE TABLE" || true)
        log "Backup contains $TABLE_COUNT table definitions"
        
        if [ $TABLE_COUNT -lt 3 ]; then
            log "WARNING: Backup contains fewer tables than expected"
            send_alert "warning" "Backup contains only $TABLE_COUNT tables"
        fi
    else
        log "ERROR: Backup does not appear to be a valid PostgreSQL dump"
        send_alert "error" "Invalid backup format detected"
        exit 1
    fi
fi

# Test 4: Test database connectivity
if [ ! -z "$DATABASE_URL" ]; then
    log "Test 4: Testing database connectivity..."
    
    # Parse DATABASE_URL
    DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
    DB_PASS=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
    DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
    
    export PGPASSWORD="$DB_PASS"
    
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" &>/dev/null; then
        log "Database connection successful"
    else
        log "ERROR: Cannot connect to database"
        send_alert "error" "Cannot connect to PostgreSQL database"
        unset PGPASSWORD
        exit 1
    fi
    
    unset PGPASSWORD
fi

# Test 5: Check backup process resources
log "Test 5: Checking system resources..."

# Check disk space
if [ -d "$BACKUP_DIR" ]; then
    DISK_USAGE=$(df -h "$BACKUP_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
    log "Backup disk usage: ${DISK_USAGE}%"
    
    if [ $DISK_USAGE -gt 90 ]; then
        send_alert "error" "Backup disk space critical: ${DISK_USAGE}% used"
    elif [ $DISK_USAGE -gt 80 ]; then
        send_alert "warning" "Backup disk space warning: ${DISK_USAGE}% used"
    fi
fi

# Summary
log "Backup health check completed"

# Send success notification if all tests passed
if [ $? -eq 0 ]; then
    # Only send success notification once per day
    LAST_SUCCESS_FILE="/tmp/hoistscraper_backup_test_success"
    if [ ! -f "$LAST_SUCCESS_FILE" ] || [ $(find "$LAST_SUCCESS_FILE" -mtime +1 -print 2>/dev/null) ]; then
        send_alert "info" "All backup health checks passed"
        touch "$LAST_SUCCESS_FILE"
    fi
fi