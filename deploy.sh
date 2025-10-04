#!/bin/bash
# Production Deployment Script for YOLO Dataset Builder

set -e  # Exit on error

echo "========================================="
echo "YOLO Dataset Builder - Deployment Script"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from .env.example..."
    cp .env.example .env
    print_warning "Please edit .env file with your configuration before proceeding."
    read -p "Press Enter to continue after editing .env..."
fi

# Create necessary directories
print_status "Creating data directories..."
mkdir -p data/raw data/annotations data/reviewed

# Build Docker images
print_status "Building Docker images..."
docker-compose build

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose down

# Start services
print_status "Starting services..."
docker-compose up -d

# Wait for services to be ready
print_status "Waiting for services to start..."
sleep 5

# Check backend health
print_status "Checking backend health..."
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    print_status "Backend is healthy ✓"
else
    print_error "Backend health check failed"
    docker-compose logs backend
    exit 1
fi

# Check frontend health
print_status "Checking frontend health..."
if curl -s http://localhost/health | grep -q "healthy"; then
    print_status "Frontend is healthy ✓"
else
    print_error "Frontend health check failed"
    docker-compose logs frontend
    exit 1
fi

echo ""
echo "========================================="
echo -e "${GREEN}Deployment Successful!${NC}"
echo "========================================="
echo ""
echo "Access your application at:"
echo "  Frontend: http://localhost"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "View logs with:"
echo "  docker-compose logs -f"
echo ""
echo "Stop services with:"
echo "  docker-compose down"
echo ""
