#!/bin/bash

################################################################################
# Health Check Script for YOLO Dataset Builder
# This script monitors the health of all services and components
################################################################################

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
FRONTEND_URL=${FRONTEND_URL:-"http://localhost:80"}
BACKEND_URL=${BACKEND_URL:-"http://localhost:8000"}
TIMEOUT=${HEALTH_CHECK_TIMEOUT:-5}

# Health check counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((PASSED_CHECKS++))
    ((TOTAL_CHECKS++))
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    ((FAILED_CHECKS++))
    ((TOTAL_CHECKS++))
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
    ((WARNING_CHECKS++))
    ((TOTAL_CHECKS++))
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_docker_running() {
    print_header "Docker Status"

    if command -v docker &> /dev/null; then
        if docker ps &> /dev/null; then
            print_success "Docker daemon is running"
        else
            print_error "Docker daemon is not running"
            return 1
        fi
    else
        print_warning "Docker is not installed"
    fi
}

check_docker_containers() {
    print_header "Docker Containers"

    if ! command -v docker &> /dev/null; then
        print_info "Skipping Docker container checks (Docker not installed)"
        return
    fi

    cd "$PROJECT_ROOT"

    # Check if containers are running
    RUNNING_CONTAINERS=$(docker-compose ps --services --filter "status=running" 2>/dev/null | wc -l)
    TOTAL_CONTAINERS=$(docker-compose ps --services 2>/dev/null | wc -l)

    if [ "$RUNNING_CONTAINERS" -eq "$TOTAL_CONTAINERS" ] && [ "$TOTAL_CONTAINERS" -gt 0 ]; then
        print_success "All Docker containers running ($RUNNING_CONTAINERS/$TOTAL_CONTAINERS)"
        docker-compose ps
    elif [ "$RUNNING_CONTAINERS" -gt 0 ]; then
        print_warning "Some containers are not running ($RUNNING_CONTAINERS/$TOTAL_CONTAINERS)"
        docker-compose ps
    else
        print_error "No Docker containers are running"
    fi
}

check_frontend() {
    print_header "Frontend Health"

    print_info "Checking frontend at $FRONTEND_URL..."

    # Check if frontend is accessible
    if curl -f -s -m $TIMEOUT "$FRONTEND_URL" > /dev/null; then
        print_success "Frontend is accessible"
    else
        print_error "Frontend is not accessible"
    fi

    # Check frontend response time
    RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' -m $TIMEOUT "$FRONTEND_URL" 2>/dev/null || echo "0")
    if [ "$RESPONSE_TIME" != "0" ]; then
        RESPONSE_MS=$(echo "$RESPONSE_TIME * 1000" | bc)
        if (( $(echo "$RESPONSE_TIME < 1.0" | bc -l) )); then
            print_success "Frontend response time: ${RESPONSE_MS}ms"
        elif (( $(echo "$RESPONSE_TIME < 3.0" | bc -l) )); then
            print_warning "Frontend response time: ${RESPONSE_MS}ms (slow)"
        else
            print_error "Frontend response time: ${RESPONSE_MS}ms (very slow)"
        fi
    fi
}

check_backend() {
    print_header "Backend API Health"

    print_info "Checking backend at $BACKEND_URL..."

    # Check if backend is accessible
    if curl -f -s -m $TIMEOUT "${BACKEND_URL}/docs" > /dev/null; then
        print_success "Backend API is accessible"
    else
        print_error "Backend API is not accessible"
    fi

    # Check backend response time
    RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' -m $TIMEOUT "${BACKEND_URL}/docs" 2>/dev/null || echo "0")
    if [ "$RESPONSE_TIME" != "0" ]; then
        RESPONSE_MS=$(echo "$RESPONSE_TIME * 1000" | bc)
        if (( $(echo "$RESPONSE_TIME < 0.5" | bc -l) )); then
            print_success "Backend response time: ${RESPONSE_MS}ms"
        elif (( $(echo "$RESPONSE_TIME < 2.0" | bc -l) )); then
            print_warning "Backend response time: ${RESPONSE_MS}ms (slow)"
        else
            print_error "Backend response time: ${RESPONSE_MS}ms (very slow)"
        fi
    fi

    # Check API endpoints
    print_info "Checking API endpoints..."

    # GET /api/images
    if curl -f -s -m $TIMEOUT "${BACKEND_URL}/api/images" > /dev/null; then
        print_success "GET /api/images is working"
    else
        print_error "GET /api/images is not working"
    fi
}

check_database() {
    print_header "Database Health"

    DATABASE_PATH="$PROJECT_ROOT/data/annotations.db"

    # Check if database file exists
    if [ -f "$DATABASE_PATH" ]; then
        print_success "Database file exists"

        # Get database size
        DB_SIZE=$(du -h "$DATABASE_PATH" | cut -f1)
        print_info "Database size: $DB_SIZE"

        # Check if database is writable
        if [ -w "$DATABASE_PATH" ]; then
            print_success "Database is writable"
        else
            print_error "Database is not writable"
        fi

        # Check database integrity (requires sqlite3)
        if command -v sqlite3 &> /dev/null; then
            INTEGRITY_CHECK=$(sqlite3 "$DATABASE_PATH" "PRAGMA integrity_check;" 2>&1)
            if [ "$INTEGRITY_CHECK" = "ok" ]; then
                print_success "Database integrity check passed"
            else
                print_error "Database integrity check failed: $INTEGRITY_CHECK"
            fi

            # Get table count
            TABLE_COUNT=$(sqlite3 "$DATABASE_PATH" "SELECT count(*) FROM sqlite_master WHERE type='table';" 2>/dev/null)
            print_info "Database has $TABLE_COUNT tables"

            # Get image count
            IMAGE_COUNT=$(sqlite3 "$DATABASE_PATH" "SELECT count(*) FROM images;" 2>/dev/null || echo "0")
            print_info "Database has $IMAGE_COUNT images"

            # Get annotation count
            ANNOTATION_COUNT=$(sqlite3 "$DATABASE_PATH" "SELECT count(*) FROM annotations;" 2>/dev/null || echo "0")
            print_info "Database has $ANNOTATION_COUNT annotations"
        else
            print_warning "sqlite3 not installed, skipping detailed database checks"
        fi
    else
        print_warning "Database file does not exist (will be created on first use)"
    fi
}

check_filesystem() {
    print_header "File System Health"

    # Check data directory
    if [ -d "$PROJECT_ROOT/data" ]; then
        print_success "Data directory exists"

        # Check disk space
        DISK_USAGE=$(df -h "$PROJECT_ROOT/data" | tail -1 | awk '{print $5}' | sed 's/%//')
        if [ "$DISK_USAGE" -lt 80 ]; then
            print_success "Disk usage: ${DISK_USAGE}%"
        elif [ "$DISK_USAGE" -lt 90 ]; then
            print_warning "Disk usage: ${DISK_USAGE}% (approaching limit)"
        else
            print_error "Disk usage: ${DISK_USAGE}% (critical)"
        fi

        # Check images directory
        if [ -d "$PROJECT_ROOT/data/images" ]; then
            IMAGE_COUNT=$(find "$PROJECT_ROOT/data/images" -type f | wc -l)
            print_info "Images directory has $IMAGE_COUNT files"
        else
            print_warning "Images directory does not exist"
        fi

        # Check backups directory
        if [ -d "$PROJECT_ROOT/data/backups" ]; then
            BACKUP_COUNT=$(find "$PROJECT_ROOT/data/backups" -type f -name "*.db*" | wc -l)
            print_info "Backups directory has $BACKUP_COUNT backup(s)"
        else
            print_warning "Backups directory does not exist"
        fi
    else
        print_error "Data directory does not exist"
    fi

    # Check permissions
    if [ -w "$PROJECT_ROOT/data" ]; then
        print_success "Data directory is writable"
    else
        print_error "Data directory is not writable"
    fi
}

check_dependencies() {
    print_header "Dependencies"

    # Check Python
    if command -v python &> /dev/null; then
        PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
        print_success "Python installed: $PYTHON_VERSION"
    else
        print_warning "Python not found in PATH"
    fi

    # Check Node.js
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        print_success "Node.js installed: $NODE_VERSION"
    else
        print_warning "Node.js not found in PATH"
    fi

    # Check npm
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        print_success "npm installed: $NPM_VERSION"
    else
        print_warning "npm not found in PATH"
    fi
}

show_summary() {
    print_header "Health Check Summary"

    echo ""
    echo "Total checks:   $TOTAL_CHECKS"
    echo -e "${GREEN}Passed:         $PASSED_CHECKS${NC}"
    echo -e "${YELLOW}Warnings:       $WARNING_CHECKS${NC}"
    echo -e "${RED}Failed:         $FAILED_CHECKS${NC}"
    echo ""

    # Calculate health percentage
    HEALTH_PERCENTAGE=$(echo "scale=1; ($PASSED_CHECKS / $TOTAL_CHECKS) * 100" | bc)

    if (( $(echo "$HEALTH_PERCENTAGE >= 90" | bc -l) )); then
        echo -e "${GREEN}Overall Health: ${HEALTH_PERCENTAGE}% (Healthy)${NC}"
        exit 0
    elif (( $(echo "$HEALTH_PERCENTAGE >= 70" | bc -l) )); then
        echo -e "${YELLOW}Overall Health: ${HEALTH_PERCENTAGE}% (Warning)${NC}"
        exit 1
    else
        echo -e "${RED}Overall Health: ${HEALTH_PERCENTAGE}% (Critical)${NC}"
        exit 2
    fi
}

# Main health check flow
main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}YOLO Dataset Builder - Health Check${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo "Timestamp: $(date)"
    echo ""

    check_docker_running
    check_docker_containers
    check_frontend
    check_backend
    check_database
    check_filesystem
    check_dependencies
    show_summary
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --help, -h          Show this help message"
        echo "  --quick             Quick check (Docker and services only)"
        echo "  --json              Output in JSON format"
        echo ""
        echo "Environment variables:"
        echo "  FRONTEND_URL               Frontend URL (default: http://localhost:80)"
        echo "  BACKEND_URL                Backend URL (default: http://localhost:8000)"
        echo "  HEALTH_CHECK_TIMEOUT       Timeout in seconds (default: 5)"
        echo ""
        echo "Exit codes:"
        echo "  0 - Healthy (>90%)"
        echo "  1 - Warning (70-90%)"
        echo "  2 - Critical (<70%)"
        echo ""
        exit 0
        ;;
    --quick)
        check_docker_running
        check_docker_containers
        check_frontend
        check_backend
        show_summary
        ;;
    *)
        main
        ;;
esac
