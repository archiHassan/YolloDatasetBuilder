#!/bin/bash

################################################################################
# Automated Backup Script for YOLO Dataset Builder
# This script backs up the database and optionally images
################################################################################

set -e  # Exit immediately if a command exits with a non-zero status

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_ROOT/data/backups"
DATABASE_PATH="$PROJECT_ROOT/data/annotations.db"
IMAGES_DIR="$PROJECT_ROOT/data/images"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DATE_ONLY=$(date +"%Y%m%d")

# Configuration
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-7}  # Default 7 days
INCLUDE_IMAGES=${BACKUP_INCLUDE_IMAGES:-false}
COMPRESS=${BACKUP_COMPRESS:-true}

# Functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

create_backup_dir() {
    mkdir -p "$BACKUP_DIR"
    print_success "Backup directory ready: $BACKUP_DIR"
}

backup_database() {
    print_info "Backing up database..."

    if [ ! -f "$DATABASE_PATH" ]; then
        print_error "Database not found at $DATABASE_PATH"
        exit 1
    fi

    BACKUP_FILE="$BACKUP_DIR/annotations_${TIMESTAMP}.db"
    cp "$DATABASE_PATH" "$BACKUP_FILE"

    # Get database size
    DB_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    print_success "Database backed up: $BACKUP_FILE (Size: $DB_SIZE)"

    # Compress if enabled
    if [ "$COMPRESS" = true ]; then
        print_info "Compressing backup..."
        gzip -9 "$BACKUP_FILE"
        COMPRESSED_SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
        print_success "Backup compressed: ${BACKUP_FILE}.gz (Size: $COMPRESSED_SIZE)"
    fi
}

backup_images() {
    if [ "$INCLUDE_IMAGES" != true ]; then
        print_info "Skipping images backup (not enabled)"
        return
    fi

    print_info "Backing up images..."

    if [ ! -d "$IMAGES_DIR" ]; then
        print_warning "Images directory not found, skipping"
        return
    fi

    IMAGE_COUNT=$(find "$IMAGES_DIR" -type f | wc -l)
    if [ "$IMAGE_COUNT" -eq 0 ]; then
        print_warning "No images found, skipping"
        return
    fi

    IMAGES_BACKUP_FILE="$BACKUP_DIR/images_${TIMESTAMP}.tar.gz"
    tar -czf "$IMAGES_BACKUP_FILE" -C "$PROJECT_ROOT/data" images/

    IMAGES_SIZE=$(du -h "$IMAGES_BACKUP_FILE" | cut -f1)
    print_success "Images backed up: $IMAGES_BACKUP_FILE (Files: $IMAGE_COUNT, Size: $IMAGES_SIZE)"
}

cleanup_old_backups() {
    print_info "Cleaning up old backups (retention: $RETENTION_DAYS days)..."

    # Find and delete old database backups
    DELETED_COUNT=0
    find "$BACKUP_DIR" -name "annotations_*.db*" -type f -mtime +$RETENTION_DAYS -print -delete | while read file; do
        ((DELETED_COUNT++))
    done

    # Find and delete old image backups
    find "$BACKUP_DIR" -name "images_*.tar.gz" -type f -mtime +$RETENTION_DAYS -print -delete

    if [ "$DELETED_COUNT" -gt 0 ]; then
        print_success "Deleted $DELETED_COUNT old backup(s)"
    else
        print_info "No old backups to delete"
    fi
}

verify_backup() {
    print_info "Verifying backup integrity..."

    # Verify database backup
    if [ "$COMPRESS" = true ]; then
        BACKUP_TO_CHECK="${BACKUP_DIR}/annotations_${TIMESTAMP}.db.gz"
        if gzip -t "$BACKUP_TO_CHECK" 2>/dev/null; then
            print_success "Database backup integrity verified"
        else
            print_error "Database backup is corrupted!"
            exit 1
        fi
    else
        BACKUP_TO_CHECK="${BACKUP_DIR}/annotations_${TIMESTAMP}.db"
        if [ -f "$BACKUP_TO_CHECK" ]; then
            print_success "Database backup file exists"
        else
            print_error "Database backup file not found!"
            exit 1
        fi
    fi

    # Verify images backup if created
    if [ "$INCLUDE_IMAGES" = true ] && [ -f "${BACKUP_DIR}/images_${TIMESTAMP}.tar.gz" ]; then
        if tar -tzf "${BACKUP_DIR}/images_${TIMESTAMP}.tar.gz" > /dev/null 2>&1; then
            print_success "Images backup integrity verified"
        else
            print_error "Images backup is corrupted!"
            exit 1
        fi
    fi
}

show_backup_summary() {
    echo ""
    echo -e "${GREEN}Backup Summary${NC}"
    echo "=================="
    echo "Timestamp:        $TIMESTAMP"
    echo "Backup directory: $BACKUP_DIR"
    echo "Retention days:   $RETENTION_DAYS"
    echo ""

    # List all backups
    echo "All backups:"
    ls -lh "$BACKUP_DIR" | grep -E "annotations_.*\.(db|gz)$" | tail -5
    echo ""

    # Total backup size
    TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
    echo "Total backup size: $TOTAL_SIZE"
    echo ""
}

# Main backup flow
main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}YOLO Dataset Builder - Backup${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo "Started at: $(date)"
    echo ""

    create_backup_dir
    backup_database
    backup_images
    verify_backup
    cleanup_old_backups
    show_backup_summary

    print_success "Backup completed successfully!"
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --help, -h              Show this help message"
        echo "  --include-images        Include images in backup"
        echo "  --no-compress           Don't compress database backup"
        echo "  --retention-days N      Keep backups for N days (default: 7)"
        echo ""
        echo "Environment variables:"
        echo "  BACKUP_RETENTION_DAYS   Number of days to keep backups (default: 7)"
        echo "  BACKUP_INCLUDE_IMAGES   Include images (true/false, default: false)"
        echo "  BACKUP_COMPRESS         Compress backups (true/false, default: true)"
        echo ""
        echo "Examples:"
        echo "  $0                                  # Basic backup (database only)"
        echo "  $0 --include-images                 # Backup database and images"
        echo "  $0 --retention-days 30              # Keep backups for 30 days"
        echo "  BACKUP_INCLUDE_IMAGES=true $0       # Using environment variable"
        echo ""
        exit 0
        ;;
    --include-images)
        INCLUDE_IMAGES=true
        main
        ;;
    --no-compress)
        COMPRESS=false
        main
        ;;
    --retention-days)
        if [ -z "$2" ]; then
            print_error "Please specify retention days"
            exit 1
        fi
        RETENTION_DAYS=$2
        shift
        main
        ;;
    *)
        main
        ;;
esac
