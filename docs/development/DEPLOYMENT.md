# Deployment Guide - YOLO Dataset Builder

**Version**: 1.0.0
**Date**: October 2, 2025

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Docker Deployment](#docker-deployment)
3. [Manual Deployment](#manual-deployment)
4. [Production Checklist](#production-checklist)
5. [Environment Configuration](#environment-configuration)
6. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Prerequisites

- **Docker**: Version 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose**: Version 2.0+ (included with Docker Desktop)
- **Git**: For cloning the repository

### Deploy with Docker (Recommended)

```bash
# 1. Clone repository
git clone <repository-url>
cd yollo-dataset-builder

# 2. Create environment file
cp .env.example .env
# Edit .env with your configuration

# 3. Build and start services
docker-compose up -d

# 4. Check status
docker-compose ps

# 5. View logs
docker-compose logs -f

# Access the application
# Frontend: http://localhost
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**That's it!** Your annotation platform is now running. 🎉

---

## 🐳 Docker Deployment

### Architecture

```
┌─────────────────┐
│   Nginx (80)    │  ← Frontend (React)
│   Frontend      │
└────────┬────────┘
         │
         ↓ API Calls
┌─────────────────┐
│ FastAPI (8000)  │  ← Backend (Python)
│   Backend       │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Data Volumes   │  ← Persistent Storage
└─────────────────┘
```

### Services

**Backend**:
- Base: Python 3.11-slim
- Port: 8000
- Health check: `/health` endpoint
- Volume: `./data` → `/app/data`

**Frontend**:
- Build: Node 22 Alpine
- Runtime: Nginx Alpine
- Port: 80
- Proxies API calls to backend

### Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart a service
docker-compose restart backend

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Rebuild after code changes
docker-compose up -d --build

# Remove everything (including volumes)
docker-compose down -v
```

### Data Persistence

Data is stored in volumes and bind mounts:

```bash
# Local directories (persisted)
./data/raw/          # Images
./data/annotations/  # Annotation files
./data/reviewed/     # Reviewed annotations

# To backup
tar -czf backup.tar.gz data/

# To restore
tar -xzf backup.tar.gz
```

---

## 🔧 Manual Deployment

### Backend Setup

```bash
# 1. Create virtual environment
cd backend
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp ../.env.example ../.env
# Edit .env

# 4. Run backend
python -m app.main
# OR with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

```bash
# 1. Install dependencies
cd frontend
npm install

# 2. Configure environment
cp .env .env.local
# Edit VITE_API_URL if needed

# 3. Development mode
npm run dev

# 4. Production build
npm run build
npm run preview

# 5. Serve with nginx/apache
# Build files are in: frontend/dist/
```

---

## ✅ Production Checklist

### Security

- [ ] Change DEBUG=false in .env
- [ ] Generate secure SECRET_KEY
- [ ] Configure CORS_ORIGINS properly
- [ ] Enable HTTPS/SSL certificates
- [ ] Set up firewall rules
- [ ] Implement authentication (if needed)
- [ ] Regular security updates

### Performance

- [ ] Enable gzip compression (nginx)
- [ ] Configure caching headers
- [ ] Set up CDN (optional)
- [ ] Monitor resource usage
- [ ] Set up log rotation
- [ ] Database optimization (if using DB)

### Monitoring

- [ ] Set up health checks
- [ ] Configure error logging
- [ ] Set up uptime monitoring
- [ ] Configure alerts
- [ ] Track performance metrics

### Backup

- [ ] Regular data backups
- [ ] Database backups (if applicable)
- [ ] Configuration backups
- [ ] Test restore procedures

---

## 🔐 Environment Configuration

### Backend Environment Variables

```bash
# Application
DEBUG=false                    # Disable debug mode in production
APP_NAME="YOLO Dataset Builder"
VERSION="1.0.0"

# API
API_PREFIX="/api"
CORS_ORIGINS="https://yourdomain.com"

# Paths
DATA_DIR="./data"
IMAGES_DIR="./data/raw"
ANNOTATIONS_DIR="./data/annotations"

# Database (future)
DATABASE_URL="postgresql://user:pass@localhost/dbname"
```

### Frontend Environment Variables

```bash
# API Connection
VITE_API_URL="https://api.yourdomain.com"

# Build settings (vite.config.js)
# No environment variables needed for production build
```

---

## 🌐 Nginx Configuration (Manual Deployment)

### Sample nginx.conf

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL certificates
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Frontend
    location / {
        root /var/www/yolo-dataset-builder;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static images
    location /static {
        proxy_pass http://localhost:8000;
    }
}
```

---

## 🐛 Troubleshooting

### Container Issues

**Problem**: Container won't start
```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Check if ports are in use
netstat -tulpn | grep :8000
netstat -tulpn | grep :80

# Restart services
docker-compose restart
```

**Problem**: Can't connect to backend
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check network
docker network ls
docker network inspect yolo-dataset-network

# Check CORS settings in .env
```

### Data Issues

**Problem**: Images not loading
```bash
# Check data directory
ls -la data/raw/

# Check permissions
chmod -R 755 data/

# Verify volume mounts
docker-compose config
```

**Problem**: Annotations not saving
```bash
# Check annotations directory
ls -la data/annotations/

# Check write permissions
mkdir -p data/annotations
chmod -R 755 data/annotations/
```

### Frontend Issues

**Problem**: API calls failing
```bash
# Check VITE_API_URL in .env
cat frontend/.env

# Verify backend is accessible
curl http://localhost:8000/api/images/

# Check browser console for CORS errors
```

**Problem**: Build errors
```bash
# Clear node_modules and rebuild
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

---

## 📊 Performance Tuning

### Backend

```python
# app/main.py
# Increase workers for uvicorn
uvicorn.run(
    "app.main:app",
    host="0.0.0.0",
    port=8000,
    workers=4,  # Number of worker processes
    reload=False
)
```

### Frontend

```bash
# Optimize build
npm run build -- --mode production

# Analyze bundle size
npm run build -- --mode production --report
```

### Docker

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

---

## 🔄 Updates & Maintenance

### Updating the Application

```bash
# 1. Pull latest code
git pull origin main

# 2. Rebuild containers
docker-compose down
docker-compose up -d --build

# 3. Check health
docker-compose ps
```

### Database Migrations (Future)

```bash
# When database is added
docker-compose exec backend alembic upgrade head
```

---

## 📞 Support

### Logs Location

- **Docker**: `docker-compose logs`
- **Backend**: `logs/backend.log`
- **Frontend**: Browser console
- **Nginx**: `/var/log/nginx/`

### Health Checks

- Backend: `http://localhost:8000/health`
- Frontend: `http://localhost/health`
- API Docs: `http://localhost:8000/docs`

---

## 🎯 Quick Reference

### Essential Commands

```bash
# Start everything
docker-compose up -d

# Stop everything
docker-compose down

# View logs
docker-compose logs -f

# Restart backend
docker-compose restart backend

# Rebuild
docker-compose up -d --build

# Backup data
tar -czf backup-$(date +%Y%m%d).tar.gz data/
```

### URLs

- **Frontend**: http://localhost (or http://yourdomain.com)
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

**Last Updated**: October 2, 2025
**Version**: 1.0.0
**Status**: Production Ready ✅
