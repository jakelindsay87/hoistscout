#!/bin/bash

# PostgreSQL Backup Script for HoistScraper
# This script creates automated backups of the PostgreSQL database
# and optionally uploads them to S3 or other cloud storage

set -e

# Load environment variables
if [ -f "/app/.env.production" ]; then
    export $(cat /app/.env.production | grep -v '^#' | xargs)
fi

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILENAME="hoistscraper_backup_${TIMESTAMP}.sql.gz"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILENAME}"

# Database configuration from DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL not set"
    exit 1
fi

# Parse DATABASE_URL
# Format: postgresql://user:password@host:port/database
DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
DB_PASS=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to send notification
send_notification() {
    local status=$1
    local message=$2
    
    # If webhook URL is configured, send notification
    if [ ! -z "$BACKUP_WEBHOOK_URL" ]; then
        curl -X POST "$BACKUP_WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"status\": \"$status\", \"message\": \"$message\", \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" \
            2>/dev/null || true
    fi
}

# Start backup
log "Starting PostgreSQL backup for database: $DB_NAME"

# Set PGPASSWORD to avoid password prompt
export PGPASSWORD="$DB_PASS"

# Create backup
if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --verbose --no-owner --no-acl --clean --if-exists | gzip > "$BACKUP_PATH"; then
    
    BACKUP_SIZE=$(du -h "$BACKUP_PATH" | cut -f1)
    log "Backup created successfully: $BACKUP_FILENAME (Size: $BACKUP_SIZE)"
    
    # Upload to S3 if configured
    if [ ! -z "$BACKUP_S3_BUCKET" ] && [ ! -z "$AWS_ACCESS_KEY_ID" ]; then
        log "Uploading backup to S3 bucket: $BACKUP_S3_BUCKET"
        
        if aws s3 cp "$BACKUP_PATH" "s3://$BACKUP_S3_BUCKET/postgres/$BACKUP_FILENAME" \
            --storage-class "${BACKUP_S3_STORAGE_CLASS:-STANDARD_IA}"; then
            log "Backup uploaded to S3 successfully"
            
            # Remove local backup if S3 upload succeeded and configured to do so
            if [ "$BACKUP_KEEP_LOCAL" != "true" ]; then
                rm -f "$BACKUP_PATH"
                log "Local backup removed (stored in S3)"
            fi
        else
            log "ERROR: Failed to upload backup to S3"
            send_notification "error" "PostgreSQL backup created but S3 upload failed"
        fi
    fi
    
    # Clean up old local backups
    if [ -d "$BACKUP_DIR" ]; then
        log "Cleaning up backups older than $BACKUP_RETENTION_DAYS days"
        find "$BACKUP_DIR" -name "hoistscraper_backup_*.sql.gz" -type f -mtime +$BACKUP_RETENTION_DAYS -delete
    fi
    
    # Clean up old S3 backups if configured
    if [ ! -z "$BACKUP_S3_BUCKET" ] && [ "$BACKUP_S3_LIFECYCLE" != "false" ]; then
        log "Cleaning up S3 backups older than $BACKUP_RETENTION_DAYS days"
        aws s3 ls "s3://$BACKUP_S3_BUCKET/postgres/" | while read -r line; do
            createDate=$(echo $line | awk '{print $1" "$2}')
            createDate=$(date -d "$createDate" +%s)
            olderThan=$(date -d "$BACKUP_RETENTION_DAYS days ago" +%s)
            if [[ $createDate -lt $olderThan ]]; then
                fileName=$(echo $line | awk '{print $4}')
                if [[ $fileName == hoistscraper_backup_* ]]; then
                    aws s3 rm "s3://$BACKUP_S3_BUCKET/postgres/$fileName"
                    log "Deleted old S3 backup: $fileName"
                fi
            fi
        done
    fi
    
    send_notification "success" "PostgreSQL backup completed successfully: $BACKUP_FILENAME ($BACKUP_SIZE)"
    log "Backup process completed successfully"
    
else
    log "ERROR: Backup failed"
    send_notification "error" "PostgreSQL backup failed"
    exit 1
fi

# Unset password
unset PGPASSWORD