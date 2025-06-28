#!/bin/bash

# PostgreSQL Restore Script for HoistScraper
# This script restores a PostgreSQL database from a backup file

set -e

# Check if backup file is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup-file> [--force]"
    echo "Example: $0 /backups/hoistscraper_backup_20240115_120000.sql.gz"
    echo "         $0 s3://bucket/postgres/hoistscraper_backup_20240115_120000.sql.gz"
    echo ""
    echo "Options:"
    echo "  --force    Skip confirmation prompt"
    exit 1
fi

BACKUP_FILE=$1
FORCE_RESTORE=$2
TEMP_DIR="/tmp/hoistscraper_restore_$$"

# Load environment variables
if [ -f "/app/.env.production" ]; then
    export $(cat /app/.env.production | grep -v '^#' | xargs)
fi

# Database configuration from DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL not set"
    exit 1
fi

# Parse DATABASE_URL
DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
DB_PASS=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Create temp directory
mkdir -p "$TEMP_DIR"

# Download from S3 if needed
if [[ $BACKUP_FILE == s3://* ]]; then
    log "Downloading backup from S3..."
    LOCAL_BACKUP="$TEMP_DIR/$(basename $BACKUP_FILE)"
    
    if ! aws s3 cp "$BACKUP_FILE" "$LOCAL_BACKUP"; then
        log "ERROR: Failed to download backup from S3"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
    
    BACKUP_FILE="$LOCAL_BACKUP"
fi

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    log "ERROR: Backup file not found: $BACKUP_FILE"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Confirmation prompt
if [ "$FORCE_RESTORE" != "--force" ]; then
    echo ""
    echo "WARNING: This will restore the database from: $(basename $BACKUP_FILE)"
    echo "Database: $DB_NAME on $DB_HOST:$DB_PORT"
    echo ""
    echo "This operation will:"
    echo "1. Drop all existing data in the database"
    echo "2. Restore data from the backup file"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " confirmation
    
    if [ "$confirmation" != "yes" ]; then
        log "Restore cancelled by user"
        rm -rf "$TEMP_DIR"
        exit 0
    fi
fi

# Set PGPASSWORD
export PGPASSWORD="$DB_PASS"

# Stop applications if running
log "Checking for running applications..."
if command -v docker &> /dev/null; then
    # Stop worker to prevent job processing during restore
    docker-compose stop worker 2>/dev/null || true
    log "Stopped worker service"
fi

# Create restore point
log "Creating current database backup before restore..."
RESTORE_POINT="/tmp/restore_point_$(date +%Y%m%d_%H%M%S).sql.gz"
if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --no-owner --no-acl --clean --if-exists | gzip > "$RESTORE_POINT"; then
    log "Restore point created: $RESTORE_POINT"
else
    log "WARNING: Failed to create restore point"
fi

# Perform restore
log "Starting database restore..."

if [[ $BACKUP_FILE == *.gz ]]; then
    # Compressed backup
    if gunzip -c "$BACKUP_FILE" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --single-transaction --set ON_ERROR_STOP=on; then
        log "Database restored successfully"
    else
        log "ERROR: Restore failed"
        
        # Attempt to restore from restore point
        if [ -f "$RESTORE_POINT" ]; then
            log "Attempting to restore from restore point..."
            gunzip -c "$RESTORE_POINT" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
                --single-transaction --set ON_ERROR_STOP=on || true
        fi
        
        rm -rf "$TEMP_DIR"
        unset PGPASSWORD
        exit 1
    fi
else
    # Uncompressed backup
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --single-transaction --set ON_ERROR_STOP=on < "$BACKUP_FILE"; then
        log "Database restored successfully"
    else
        log "ERROR: Restore failed"
        
        # Attempt to restore from restore point
        if [ -f "$RESTORE_POINT" ]; then
            log "Attempting to restore from restore point..."
            gunzip -c "$RESTORE_POINT" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
                --single-transaction --set ON_ERROR_STOP=on || true
        fi
        
        rm -rf "$TEMP_DIR"
        unset PGPASSWORD
        exit 1
    fi
fi

# Verify restore
log "Verifying restore..."
WEBSITE_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    -t -c "SELECT COUNT(*) FROM website;" 2>/dev/null || echo "0")
OPPORTUNITY_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    -t -c "SELECT COUNT(*) FROM opportunity;" 2>/dev/null || echo "0")

log "Restore complete. Database contains:"
log "  - Websites: $WEBSITE_COUNT"
log "  - Opportunities: $OPPORTUNITY_COUNT"

# Restart applications if they were stopped
if command -v docker &> /dev/null; then
    docker-compose start worker 2>/dev/null || true
    log "Restarted worker service"
fi

# Cleanup
rm -rf "$TEMP_DIR"
rm -f "$RESTORE_POINT"
unset PGPASSWORD

log "Restore process completed successfully"