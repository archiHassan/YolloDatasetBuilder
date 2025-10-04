#!/bin/bash

################################################################################
# Production Deployment Script for YOLO Dataset Builder
# This script automates the deployment process for production environments
################################################################################

set -e  # Exit immediately if a command exits with a non-zero status

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_ROOT/data/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    print_success "Docker is installed"

    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    print_success "Docker Compose is installed"

    # Check if .env file exists
    if [ ! -f "$PROJECT_ROOT/backend/.env" ]; then
        print_warning ".env file not found. Please create one from .env.example"
        print_info "Run: cp backend/.env.example backend/.env"
        print_info "Then edit backend/.env with your production values"
        exit 1
    fi
    print_success ".env file exists"

    # Check if data directory exists
    if [ ! -d "$PROJECT_ROOT/data" ]; then
        print_info "Creating data directory..."
        mkdir -p "$PROJECT_ROOT/data/images"
        mkdir -p "$PROJECT_ROOT/data/backups"
        mkdir -p "$PROJECT_ROOT/data/exports"
    fi
    print_success "Data directories exist"
}

backup_database() {
    print_header "Backing Up Database"

    if [ -f "$PROJECT_ROOT/data/annotations.db" ]; then
        mkdir -p "$BACKUP_DIR"
        BACKUP_FILE="$BACKUP_DIR/annotations_${TIMESTAMP}.db"
        cp "$PROJECT_ROOT/data/annotations.db" "$BACKUP_FILE"
        print_success "Database backed up to $BACKUP_FILE"
    else
        print_info "No existing database found, skipping backup"
    fi
}

build_frontend() {
    print_header "Building Frontend"

    cd "$PROJECT_ROOT/frontend"

    print_info "Installing frontend dependencies..."
    npm install --production
    print_success "Frontend dependencies installed"

    print_info "Building frontend for production..."
    npm run build
    print_success "Frontend built successfully"

    # Verify build output
    if [ ! -d "dist" ]; then
        print_error "Frontend build failed - dist directory not found"
        exit 1
    fi

    BUILD_SIZE=$(du -sh dist | cut -f1)
    print_success "Frontend build size: $BUILD_SIZE"
}

build_docker_images() {
    print_header "Building Docker Images"

    cd "$PROJECT_ROOT"

    print_info "Building Docker images..."
    docker-compose build --no-cache
    print_success "Docker images built successfully"

    # List built images
    print_info "Docker images:"
    docker images | grep yollo-dataset-builder
}

stop_existing_containers() {
    print_header "Stopping Existing Containers"

    cd "$PROJECT_ROOT"

    if docker-compose ps | grep -q "Up"; then
        print_info "Stopping running containers..."
        docker-compose down
        print_success "Containers stopped"
    else
        print_info "No running containers found"
    fi
}

start_containers() {
    print_header "Starting Docker Containers"

    cd "$PROJECT_ROOT"

    print_info "Starting containers in detached mode..."
    docker-compose up -d
    print_success "Containers started"

    # Wait for services to be ready
    print_info "Waiting for services to be ready..."
    sleep 5

    # Check if containers are running
    if docker-compose ps | grep -q "Up"; then
        print_success "All containers are running"
        docker-compose ps
    else
        print_error "Some containers failed to start"
        docker-compose logs
        exit 1
    fi
}

run_health_checks() {
    print_header "Running Health Checks"

    # Check frontend
    print_info "Checking frontend..."
    if curl -f -s http://localhost:80 > /dev/null; then
        print_success "Frontend is accessible"
    else
        print_error "Frontend is not accessible"
    fi

    # Check backend API
    print_info "Checking backend API..."
    if curl -f -s http://localhost:8000/docs > /dev/null; then
        print_success "Backend API is accessible"
    else
        print_error "Backend API is not accessible"
    fi

    # Check database
    print_info "Checking database..."
    if [ -f "$PROJECT_ROOT/data/annotations.db" ]; then
        print_success "Database file exists"
    else
        print_warning "Database file not found (will be created on first request)"
    fi
}

show_deployment_info() {
    print_header "Deployment Information"

    echo ""
    echo -e "${GREEN}Deployment completed successfully!${NC}"
    echo ""
    echo "Access points:"
    echo "  - Frontend:     http://localhost:80"
    echo "  - Backend API:  http://localhost:8000"
    echo "  - API Docs:     http://localhost:8000/docs"
    echo ""
    echo "Useful commands:"
    echo "  - View logs:           docker-compose logs -f"
    echo "  - Stop containers:     docker-compose down"
    echo "  - Restart containers:  docker-compose restart"
    echo "  - View status:         docker-compose ps"
    echo ""
    echo "Data locations:"
    echo "  - Images:      $PROJECT_ROOT/data/images/"
    echo "  - Database:    $PROJECT_ROOT/data/annotations.db"
    echo "  - Backups:     $PROJECT_ROOT/data/backups/"
    echo ""
}

rollback() {
    print_header "Rolling Back Deployment"

    print_warning "Rolling back to previous version..."

    # Stop new containers
    docker-compose down

    # Restore database from backup
    if [ -f "$BACKUP_FILE" ]; then
        print_info "Restoring database from backup..."
        cp "$BACKUP_FILE" "$PROJECT_ROOT/data/annotations.db"
        print_success "Database restored"
    fi

    print_success "Rollback completed"
}

# Main deployment flow
main() {
    print_header "YOLO Dataset Builder - Production Deployment"
    echo "Timestamp: $TIMESTAMP"
    echo ""

    # Trap errors and rollback
    trap 'print_error "Deployment failed! Rolling back..."; rollback; exit 1' ERR

    # Run deployment steps
    check_prerequisites
    backup_database
    build_frontend
    build_docker_images
    stop_existing_containers
    start_containers
    run_health_checks
    show_deployment_info

    print_success "Deployment completed successfully!"
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --help, -h          Show this help message"
        echo "  --skip-build        Skip building frontend and Docker images"
        echo "  --no-backup         Skip database backup"
        echo ""
        exit 0
        ;;
    --skip-build)
        print_warning "Skipping build steps"
        check_prerequisites
        backup_database
        stop_existing_containers
        start_containers
        run_health_checks
        show_deployment_info
        ;;
    --no-backup)
        print_warning "Skipping database backup"
        check_prerequisites
        build_frontend
        build_docker_images
        stop_existing_containers
        start_containers
        run_health_checks
        show_deployment_info
        ;;
    *)
        main
        ;;
esac
