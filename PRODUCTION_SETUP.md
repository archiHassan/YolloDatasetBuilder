# Production Setup Guide
## Quick Start for YOLO Dataset Builder

This guide provides quick instructions for deploying YOLO Dataset Builder to production.

---

## Prerequisites

Before you begin, ensure you have:

- **Docker** (version 20.10+) and **Docker Compose** (version 1.29+)
- **Ubuntu 20.04+** or similar Linux distribution (recommended)
- **At least 8GB RAM** and **20GB disk space**
- **Domain name** (optional, for HTTPS)

---

## Quick Deployment (5 Minutes)

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/yollo-dataset-builder.git
cd yollo-dataset-builder
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp backend/.env.example backend/.env

# Edit configuration (use your favorite editor)
nano backend/.env

# Minimum required changes:
# - Set SAM_MODE (mock, local, or api)
# - Set CORS_ORIGINS to your domain
# - Change JWT_SECRET_KEY to a random string
```

### Step 3: Create Required Directories

```bash
mkdir -p data/images data/backups data/exports logs models nginx/ssl
```

### Step 4: Deploy with Docker Compose

```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 5: Verify Deployment

```bash
# Run health check
bash scripts/health-check.sh

# Or manually test:
curl http://localhost/
curl http://localhost:8000/docs
```

**Access the application**:
- Frontend: http://localhost (or http://your-domain.com)
- API Docs: http://localhost:8000/docs

---

## Configuration Options

### Environment Variables

Key variables in `backend/.env`:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `APP_ENV` | Environment (development/production) | production | Yes |
| `DEBUG` | Enable debug mode | false | Yes |
| `SAM_MODE` | SAM mode (mock/local/api) | mock | Yes |
| `CORS_ORIGINS` | Allowed CORS origins | localhost | Yes |
| `JWT_SECRET_KEY` | Secret key for JWT | (generate) | Yes |
| `DATABASE_URL` | Database path | /app/data/annotations.db | No |
| `MAX_UPLOAD_SIZE` | Max file size in bytes | 52428800 (50MB) | No |

### SAM Configuration

**Option 1: Mock SAM** (No setup required, testing only)
```bash
SAM_MODE=mock
```

**Option 2: Local SAM** (Best performance, requires model download)
```bash
SAM_MODE=local
SAM_MODEL_PATH=/app/models/sam_vit_h_4b8939.pth
SAM_MODEL_VARIANT=vit_h

# Download model weights (3.6GB)
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth -P models/
```

**Option 3: API SAM** (Easiest, requires API key)
```bash
SAM_MODE=api
SAM_API_URL=https://api.replicate.com/v1/predictions
SAM_API_KEY=your_replicate_api_key_here
```

---

## HTTPS Setup (Production)

### Option 1: Let's Encrypt (Free SSL)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot certonly --standalone -d your-domain.com

# Certificates will be at:
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem

# Copy to nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/
```

### Option 2: Custom SSL Certificate

```bash
# Place your certificate files in nginx/ssl/
cp /path/to/fullchain.pem nginx/ssl/
cp /path/to/privkey.pem nginx/ssl/
```

### Enable HTTPS in Nginx

Edit `nginx/nginx.conf` and uncomment the HTTPS server block, then restart:

```bash
docker-compose restart nginx
```

---

## Backup Configuration

### Automated Backups

**Set up daily backups with cron**:

```bash
# Make backup script executable
chmod +x scripts/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e

# Add this line:
0 2 * * * /path/to/yollo-dataset-builder/scripts/backup.sh --include-images
```

### Manual Backup

```bash
# Database only
bash scripts/backup.sh

# Database + images
bash scripts/backup.sh --include-images

# Custom retention (30 days)
bash scripts/backup.sh --retention-days 30
```

### Restore from Backup

```bash
# Find backup
ls -lh data/backups/

# Restore database
gunzip -c data/backups/annotations_20251003_120000.db.gz > data/annotations.db

# Restart services
docker-compose restart
```

---

## Monitoring & Health Checks

### Built-in Health Check

```bash
# Run comprehensive health check
bash scripts/health-check.sh

# Quick check (Docker + services only)
bash scripts/health-check.sh --quick
```

### Health Check Endpoints

- Frontend: `http://localhost/health`
- Backend: `http://localhost:8000/docs`

### Monitoring with Uptime Robot

1. Sign up at https://uptimerobot.com
2. Add HTTP(s) monitor for your domain
3. Set alert contacts (email, SMS, Slack)

---

## Scaling & Performance

### Increase Backend Workers

Edit `docker-compose.yml`:

```yaml
backend:
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 8
```

### Resource Limits

Add resource limits to `docker-compose.yml`:

```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 4G
      reservations:
        cpus: '1.0'
        memory: 2G
```

---

## Troubleshooting

### Issue: Frontend not accessible

**Solution**:
```bash
# Check if container is running
docker-compose ps

# View logs
docker-compose logs frontend

# Rebuild if necessary
docker-compose build frontend
docker-compose up -d frontend
```

### Issue: Backend API errors

**Solution**:
```bash
# Check backend logs
docker-compose logs backend

# Check database permissions
ls -la data/

# Restart backend
docker-compose restart backend
```

### Issue: Database locked

**Solution**:
```bash
# Stop all services
docker-compose down

# Check for stale lock file
rm data/annotations.db-wal
rm data/annotations.db-shm

# Restart services
docker-compose up -d
```

### Issue: Out of disk space

**Solution**:
```bash
# Check disk usage
df -h

# Clean old Docker images
docker system prune -a

# Clean old backups
find data/backups -type f -mtime +30 -delete

# Clean old exports
rm -rf data/exports/*
```

---

## Security Checklist

Before going live:

- [ ] Change `JWT_SECRET_KEY` to a strong random value
- [ ] Set `DEBUG=false` in `.env`
- [ ] Configure HTTPS with valid SSL certificate
- [ ] Set appropriate `CORS_ORIGINS` (your domain only)
- [ ] Enable firewall (allow only 80, 443, 22)
- [ ] Set up automated backups
- [ ] Configure monitoring/alerting
- [ ] Review and set file upload limits
- [ ] Enable rate limiting (if needed)
- [ ] Keep Docker and system packages updated

---

## Updating the Application

```bash
# Pull latest changes
git pull origin master

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check health
bash scripts/health-check.sh
```

---

## Complete Deployment Script

For automated deployment, use the included script:

```bash
# Make script executable
chmod +x scripts/deploy.sh

# Run deployment
bash scripts/deploy.sh

# Or with options:
bash scripts/deploy.sh --skip-build    # Skip building (faster)
bash scripts/deploy.sh --no-backup     # Skip database backup
```

---

## Support & Documentation

- **Full Documentation**: `docs/` directory
- **API Reference**: http://localhost:8000/docs
- **User Guide**: `docs/user-guides/USER_GUIDE.md`
- **Architecture**: `docs/architecture/SYSTEM_ARCHITECTURE.md`

---

## Next Steps

After deployment:

1. Upload test images to `data/images/`
2. Access the web interface
3. Create annotations and test workflow
4. Set up regular backups
5. Configure monitoring
6. Train your team on the interface

---

**Quick Command Reference**:

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart a service
docker-compose restart backend

# Rebuild a service
docker-compose build backend

# Health check
bash scripts/health-check.sh

# Backup
bash scripts/backup.sh

# Deploy updates
bash scripts/deploy.sh
```

---

**Document Status**: ✅ Ready for Production
**Last Updated**: October 2025
