# Production Deployment Guide
## YOLO Dataset Builder - Complete Production Setup

**Version**: 1.0
**Last Updated**: October 2025
**Target**: Production-ready deployment

---

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Docker Deployment](#docker-deployment)
3. [Manual Deployment](#manual-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Database Setup](#database-setup)
6. [SAM Integration](#sam-integration)
7. [Security Hardening](#security-hardening)
8. [Monitoring & Logging](#monitoring-logging)
9. [Backup & Recovery](#backup-recovery)
10. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### Required Before Production

#### ✅ Completed
- [x] Backend API functional (22 endpoints)
- [x] Frontend built and tested
- [x] Database schema created
- [x] Export functionality working (3 formats)
- [x] Template system functional
- [x] Keyboard shortcuts implemented
- [x] Documentation complete

#### ⏳ Production Requirements
- [ ] Authentication system (if multi-user)
- [ ] HTTPS/TLS certificates
- [ ] Environment variables configured
- [ ] Database backups automated
- [ ] Monitoring setup
- [ ] Error tracking enabled
- [ ] Rate limiting configured
- [ ] Input validation strengthened
- [ ] Real SAM model (optional)
- [ ] Production server (cloud/on-prem)

---

## Docker Deployment

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM minimum
- 20GB disk space

### Quick Start

#### 1. Build Images
```bash
# Build all images
docker-compose build

# Or build individually
docker-compose build frontend
docker-compose build backend
```

#### 2. Start Services
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### 3. Access Application
```
Frontend: http://localhost
Backend API: http://localhost/api
API Docs: http://localhost/api/docs
```

### Docker Compose Configuration

**File**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  # Frontend (React SPA)
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    image: yolo-dataset-builder-frontend:latest
    container_name: yolo-frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    environment:
      - VITE_API_URL=http://localhost:8000
    volumes:
      - ./frontend/dist:/usr/share/nginx/html:ro
    restart: unless-stopped

  # Backend (FastAPI)
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    image: yolo-dataset-builder-backend:latest
    container_name: yolo-backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///data/annotations.db
      - DEBUG=False
      - CORS_ORIGINS=http://localhost,http://localhost:80
    volumes:
      - ./data:/app/data
      - ./models:/app/models
    restart: unless-stopped
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000

  # Nginx (Reverse Proxy)
  nginx:
    image: nginx:alpine
    container_name: yolo-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./frontend/dist:/usr/share/nginx/html:ro
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  data:
    driver: local
  models:
    driver: local
```

### Frontend Dockerfile

**File**: `frontend/Dockerfile`

```dockerfile
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source
COPY . .

# Build app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built app
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Backend Dockerfile

**File**: `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory
RUN mkdir -p /app/data /app/models

# Initialize database
RUN python -m app.db.init_db
RUN python -m app.db.init_templates

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Nginx Configuration

**File**: `nginx/nginx.conf`

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static files
    location /static {
        alias /app/data/images;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}

# HTTPS (uncomment when certificates are ready)
# server {
#     listen 443 ssl http2;
#     server_name your-domain.com;
#
#     ssl_certificate /etc/nginx/ssl/fullchain.pem;
#     ssl_certificate_key /etc/nginx/ssl/privkey.pem;
#
#     # Same config as port 80
# }
```

---

## Manual Deployment

### Server Requirements
- Ubuntu 22.04 LTS (or similar)
- Python 3.11+
- Node.js 18+
- nginx
- 8GB RAM minimum
- 20GB disk space

### Step-by-Step Setup

#### 1. Update System
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip nginx git
```

#### 2. Clone Repository
```bash
cd /opt
sudo git clone <your-repo-url> yolo-dataset-builder
cd yolo-dataset-builder
sudo chown -R $USER:$USER .
```

#### 3. Setup Backend
```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -m app.db.init_db
python -m app.db.init_templates

# Test backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 4. Setup Frontend
```bash
cd frontend

# Install dependencies
npm ci

# Build production bundle
npm run build

# Copy to nginx
sudo cp -r dist/* /var/www/yolo-frontend/
```

#### 5. Configure nginx
```bash
sudo nano /etc/nginx/sites-available/yolo-dataset-builder
```

Add configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /var/www/yolo-frontend;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/yolo-dataset-builder /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 6. Setup systemd Service
```bash
sudo nano /etc/systemd/system/yolo-backend.service
```

Add:
```ini
[Unit]
Description=YOLO Dataset Builder Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/yolo-dataset-builder/backend
Environment="PATH=/opt/yolo-dataset-builder/backend/venv/bin"
ExecStart=/opt/yolo-dataset-builder/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable yolo-backend
sudo systemctl start yolo-backend
sudo systemctl status yolo-backend
```

---

## Environment Configuration

### Environment Variables

**Backend** (`.env` file):
```bash
# Database
DATABASE_URL=sqlite:///data/annotations.db

# API Settings
DEBUG=False
API_PREFIX=/api
CORS_ORIGINS=http://localhost,http://your-domain.com

# Upload Settings
MAX_UPLOAD_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=jpg,jpeg,png,bmp,tiff

# SAM Settings
SAM_MODE=mock  # or 'local' or 'api'
REPLICATE_API_TOKEN=your_api_token_here  # if using SAM API

# Security (future)
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Frontend** (`.env.production`):
```bash
VITE_API_URL=https://your-domain.com/api
VITE_APP_NAME=YOLO Dataset Builder
VITE_VERSION=1.0
```

### Loading Environment Variables

**Backend** (`backend/app/config.py`):
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "YOLO Dataset Builder"
    version: str = "1.0"
    debug: bool = False
    api_prefix: str = "/api"
    cors_origins: list = ["http://localhost:5173"]
    database_url: str = "sqlite:///data/annotations.db"

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Database Setup

### Initialize Database

```bash
cd backend

# Initialize main database
python -m app.db.init_db

# Initialize templates
python -m app.db.init_templates

# Verify
sqlite3 data/annotations.db ".tables"
```

### Database Migrations

**Current**: No migration system
**Future**: Use Alembic

```bash
# Install Alembic
pip install alembic

# Initialize
alembic init migrations

# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

### Database Backup

**Automated Backup Script** (`scripts/backup_db.sh`):
```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/yolo-db"
DB_PATH="/opt/yolo-dataset-builder/data/annotations.db"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
cp $DB_PATH "$BACKUP_DIR/annotations_$DATE.db"

# Keep only last 30 days
find $BACKUP_DIR -name "*.db" -mtime +30 -delete

# Compress old backups
find $BACKUP_DIR -name "*.db" -mtime +7 -exec gzip {} \;
```

**Cron Job** (daily at 2 AM):
```bash
crontab -e

# Add:
0 2 * * * /opt/yolo-dataset-builder/scripts/backup_db.sh
```

---

## SAM Integration

### Option 1: Mock SAM (Current)
- Already configured
- Generates circular polygons
- Good for testing

### Option 2: Local SAM Model

#### Download Weights
```bash
cd models
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth
```

#### Install Dependencies
```bash
pip install segment-anything onnxruntime opencv-python
```

#### Configure
In `backend/app/api/sam.py`:
```python
SAM_MODE = "local"  # Change from "api"
```

#### Test
```bash
python -c "from app.api import sam; print('SAM loaded')"
```

### Option 3: API-based SAM (Replicate)

#### Get API Key
1. Sign up at https://replicate.com
2. Get API token
3. Add to `.env`:
```bash
REPLICATE_API_TOKEN=r8_xxxxxxxxxxxxx
```

#### Configure
```python
SAM_MODE = "api"
```

#### Install Client
```bash
pip install replicate
```

---

## Security Hardening

### Current Security Status
- ❌ No authentication
- ❌ No authorization
- ❌ No input sanitization (basic only)
- ✅ SQL injection protected (parameterized queries)
- ✅ CORS configured
- ❌ No rate limiting
- ❌ No HTTPS

### Essential Security Steps

#### 1. Enable HTTPS

**Let's Encrypt (Free)**:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

**nginx config** will be auto-updated with SSL

#### 2. Add Authentication (JWT)

**Install**:
```bash
pip install python-jose[cryptography] passlib[bcrypt]
```

**Implementation** (basic):
```python
# backend/app/auth.py
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Verify JWT token
    # Return user
    pass
```

#### 3. Add Rate Limiting

**Install**:
```bash
pip install slowapi
```

**Configure**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/images")
@limiter.limit("100/minute")
async def list_images():
    pass
```

#### 4. Input Validation

**Strengthen Pydantic models**:
```python
from pydantic import BaseModel, validator, constr

class AnnotationCreate(BaseModel):
    category_name: constr(min_length=1, max_length=50)
    confidence: confloat(ge=0.0, le=1.0)

    @validator('category_name')
    def validate_category(cls, v):
        if not v.isalnum():
            raise ValueError('Category must be alphanumeric')
        return v
```

#### 5. Secure File Upload

```python
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_image(file):
    # Check extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Invalid file type")

    # Check size
    file.file.seek(0, 2)
    size = file.file.tell()
    if size > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large")

    file.file.seek(0)
```

---

## Monitoring & Logging

### Logging Setup

**Configure** (`backend/app/main.py`):
```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            'logs/app.log',
            maxBytes=10485760,  # 10MB
            backupCount=5
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

### Monitoring with Prometheus (Optional)

**Install**:
```bash
pip install prometheus-fastapi-instrumentator
```

**Configure**:
```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# Add Prometheus metrics
Instrumentator().instrument(app).expose(app)
```

**Access metrics**:
```
http://localhost:8000/metrics
```

### Error Tracking with Sentry (Optional)

**Install**:
```bash
pip install sentry-sdk[fastapi]
```

**Configure**:
```python
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0,
)
```

---

## Backup & Recovery

### What to Backup
1. **Database**: `data/annotations.db`
2. **Images**: `data/images/`
3. **Configuration**: `.env`, `docker-compose.yml`
4. **Models** (optional): `models/` (large files)

### Backup Script

**File**: `scripts/full_backup.sh`

```bash
#!/bin/bash
BACKUP_ROOT="/opt/backups/yolo"
PROJECT_ROOT="/opt/yolo-dataset-builder"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/$DATE"

mkdir -p $BACKUP_DIR

# Backup database
cp $PROJECT_ROOT/data/annotations.db $BACKUP_DIR/

# Backup images (if small enough)
tar -czf $BACKUP_DIR/images.tar.gz -C $PROJECT_ROOT/data images/

# Backup config
cp $PROJECT_ROOT/.env $BACKUP_DIR/
cp $PROJECT_ROOT/docker-compose.yml $BACKUP_DIR/

# Remove old backups (keep 30 days)
find $BACKUP_ROOT -maxdepth 1 -type d -mtime +30 -exec rm -rf {} \;

echo "Backup completed: $BACKUP_DIR"
```

### Recovery

```bash
# Stop services
docker-compose down

# Restore database
cp /opt/backups/yolo/20251003_020000/annotations.db data/

# Restore images
tar -xzf /opt/backups/yolo/20251003_020000/images.tar.gz -C data/

# Restart services
docker-compose up -d
```

---

## Troubleshooting

### Backend won't start

**Check logs**:
```bash
docker-compose logs backend
# or
journalctl -u yolo-backend -f
```

**Common issues**:
- Port 8000 already in use
- Database file permissions
- Missing dependencies

**Solutions**:
```bash
# Kill process on port 8000
sudo lsof -ti:8000 | xargs kill -9

# Fix permissions
chmod 644 data/annotations.db

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Frontend shows blank page

**Check**:
1. Build succeeded: `npm run build`
2. nginx serving files: `ls /var/www/yolo-frontend`
3. API connection: Browser console (F12)

**Fix**:
```bash
# Rebuild frontend
cd frontend
npm run build

# Copy to nginx
sudo rm -rf /var/www/yolo-frontend/*
sudo cp -r dist/* /var/www/yolo-frontend/
```

### Database locked

**Cause**: Multiple connections, file permissions

**Fix**:
```bash
# Stop all services
docker-compose down

# Check locks
fuser data/annotations.db

# Restart
docker-compose up -d
```

### SAM not working

**Check status**:
```bash
curl http://localhost:8000/api/sam/status
```

**Use mock for now**:
- Mock SAM always works
- Real SAM needs model weights

---

## Production Checklist

### Before Go-Live

- [ ] Environment variables configured
- [ ] HTTPS enabled with valid certificate
- [ ] Database backups automated
- [ ] Log rotation configured
- [ ] Monitoring enabled
- [ ] Error tracking setup
- [ ] Security hardening applied
- [ ] Performance testing done
- [ ] Documentation updated
- [ ] Team trained on system

### Post-Deployment

- [ ] Monitor logs for errors
- [ ] Check disk space weekly
- [ ] Review backup integrity monthly
- [ ] Update dependencies quarterly
- [ ] Security audit annually

---

**Document Status**: ✅ Complete
**Last Updated**: October 2025
**Next Review**: January 2026
