# YOLO Dataset Builder

**Production-ready web application for YOLO dataset creation and annotation** - A full-stack solution combining automated AI annotation with professional human-in-the-loop review.

## 🎯 Overview

YOLO Dataset Builder is a complete web-based platform for creating high-quality object detection datasets. It combines cutting-edge AI models (YOLOv8, SAM, DETR, Grounding DINO) with an intuitive annotation interface, enabling teams to generate and review datasets 10x faster than traditional manual annotation.

**Live Demo**: [Coming Soon]

## ✨ Features

### Core Capabilities - ✅ Production Ready
- 🌐 **Web Dashboard**: Professional React-based annotation interface
- 🎨 **Advanced Annotation Editor**: 4 modes (View, Draw, Batch, SAM)
- 🤖 **AI-Powered Auto-Annotation**: Multi-model ensemble (YOLOv8, DETR, SAM)
- ⌨️ **Keyboard Shortcuts**: 20+ shortcuts for productivity
- 📐 **Template System**: Reusable annotation templates
- 👥 **Review Workflow**: Approve/reject system with quality control
- 📦 **Multi-Format Export**: COCO, YOLO, Pascal VOC formats
- 🎯 **SAM Integration**: One-click auto-segmentation
- 📊 **Statistics Dashboard**: Real-time metrics and visualizations
- 🐳 **Docker Deployment**: Production-ready containerization

### Technical Stack
- **Frontend**: React 19.1 + Vite 7.1 + Tailwind CSS 4.1
- **Backend**: FastAPI 0.104 + Python 3.11 + PyTorch 2.8.0
- **Database**: SQLite 3 with COCO-compatible schema
- **Deployment**: Docker Compose + Nginx reverse proxy

## 🚀 Quick Start

### Option 1: Docker Deployment (Recommended for Production)

**Prerequisites**: Docker & Docker Compose installed

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/yollo-dataset-builder.git
cd yollo-dataset-builder

# 2. Configure environment
cp backend/.env.example backend/.env
nano backend/.env  # Edit configuration

# 3. Create directories
mkdir -p data/images data/backups logs models

# 4. Deploy with Docker
docker-compose up -d

# 5. Access the application
# Frontend: http://localhost
# API Docs: http://localhost:8000/docs
```

**See [PRODUCTION_SETUP.md](PRODUCTION_SETUP.md) for detailed deployment instructions.**

### Option 2: Development Setup

**Prerequisites**: Python 3.11+, Node.js 18+

```bash
# 1. Clone and setup backend
git clone https://github.com/yourusername/yollo-dataset-builder.git
cd yollo-dataset-builder

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Start backend server
uvicorn app.main:app --reload
# Backend runs at http://localhost:8000

# 2. Setup frontend (new terminal)
cd frontend
npm install
npm run dev
# Frontend runs at http://localhost:5173
```

### First Steps

1. **Upload images**: Place images in `data/images/` directory
2. **Access web interface**: Open http://localhost in browser
3. **Create annotations**: Use the annotation editor
4. **Review & approve**: Use the review workflow
5. **Export dataset**: Export to COCO/YOLO/VOC formats

## 📁 Project Structure

```
yollo-dataset-builder/
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── api/                 # API endpoints (22 total)
│   │   ├── db/                  # Database models & operations
│   │   ├── models/              # Pydantic models
│   │   └── main.py              # FastAPI application
│   ├── requirements.txt         # Python dependencies
│   └── Dockerfile               # Backend container
├── frontend/                    # React frontend
│   ├── src/
│   │   ├── components/          # React components
│   │   │   ├── AnnotationEditorV2.jsx  # Main editor
│   │   │   ├── ImageGallery.jsx
│   │   │   └── Statistics.jsx
│   │   ├── App.jsx              # Main application
│   │   └── main.jsx             # Entry point
│   ├── package.json             # Node dependencies
│   └── Dockerfile               # Frontend container
├── data/                        # Application data
│   ├── images/                  # Uploaded images
│   ├── annotations.db           # SQLite database
│   ├── backups/                 # Database backups
│   └── exports/                 # Temporary export files
├── docs/                        # Documentation
│   ├── architecture/            # System & DB architecture
│   ├── user-guides/             # User manual
│   ├── api/                     # API reference
│   └── development/             # Development docs
├── scripts/                     # Deployment & ops scripts
│   ├── deploy.sh                # Production deployment
│   ├── backup.sh                # Database backup
│   └── health-check.sh          # Health monitoring
├── nginx/                       # Nginx configuration
│   └── nginx.conf               # Reverse proxy config
├── docker-compose.yml           # Container orchestration
├── PRODUCTION_SETUP.md          # Quick deployment guide
└── README.md                    # This file
```

## ⚙️ Configuration

### Environment Variables

Configure the application via `backend/.env`:

```bash
# Application
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# SAM Mode (mock, local, or api)
SAM_MODE=mock

# CORS (update for production domain)
CORS_ORIGINS=http://localhost,http://yourdomain.com

# Security (generate strong keys for production!)
JWT_SECRET_KEY=your-super-secret-key-change-this

# File Upload
MAX_UPLOAD_SIZE=52428800  # 50MB
ALLOWED_IMAGE_FORMATS=jpg,jpeg,png,bmp,tiff
```

**See `backend/.env.example` for all available configuration options.**

### SAM Configuration

Three SAM modes available:

1. **Mock Mode** (Default, no setup needed):
   ```bash
   SAM_MODE=mock
   ```

2. **Local Mode** (Best performance, requires model download):
   ```bash
   SAM_MODE=local
   SAM_MODEL_PATH=/app/models/sam_vit_h_4b8939.pth
   # Download: https://github.com/facebookresearch/segment-anything
   ```

3. **API Mode** (Easiest, requires API key):
   ```bash
   SAM_MODE=api
   SAM_API_KEY=your_replicate_api_key
   ```

## 💻 System Requirements

### Client (Browser)
- Modern web browser (Chrome, Firefox, Edge, Safari)
- 4GB RAM minimum
- Internet connection (or local network access)

### Server (Production Deployment)
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum (16GB recommended with SAM)
- **Disk**: 20GB minimum free space
- **OS**: Linux (Ubuntu 20.04+), macOS, or Windows with WSL2
- **Docker**: 20.10+ and Docker Compose 1.29+

### Development Environment
- **Python**: 3.11+
- **Node.js**: 18+
- **npm**: 9+

## 📖 Documentation

Comprehensive documentation available in the `docs/` directory:

| Document | Description |
|----------|-------------|
| [User Guide](docs/user-guides/USER_GUIDE.md) | Complete manual for end-users |
| [API Reference](docs/api/API_REFERENCE.md) | All 22 API endpoints documented |
| [System Architecture](docs/architecture/SYSTEM_ARCHITECTURE.md) | Technical architecture overview |
| [Database Schema](docs/architecture/DATABASE_SCHEMA.md) | ERD and database design |
| [Production Deployment](docs/PRODUCTION_DEPLOYMENT.md) | Complete deployment guide |
| [Production Setup](PRODUCTION_SETUP.md) | Quick deployment instructions |

## 🎯 API Endpoints

**22 endpoints across 6 categories:**

- **Images** (5 endpoints): CRUD operations for images
- **Annotations** (4 endpoints): Create, read, update, delete annotations
- **Review** (3 endpoints): Approve/reject workflow
- **Export** (5 endpoints): COCO, YOLO, Pascal VOC formats
- **Templates** (7 endpoints): Annotation template management
- **SAM** (3 endpoints): Auto-segmentation integration

**Interactive API Documentation**: http://localhost:8000/docs

## 🎨 Annotation Features

### 4 Annotation Modes

1. **View Mode** 👁️: Select, move, resize annotations
2. **Draw Mode** ✏️: Create bounding boxes or polygons
3. **Batch Mode** ☑️: Multi-select and bulk operations
4. **SAM Mode** 🎯: AI-powered auto-segmentation

### Keyboard Shortcuts (20+)

- `Esc` - Cancel/Exit
- `Delete` - Delete annotation
- `Ctrl+Z` / `Ctrl+Y` - Undo/Redo
- `C` / `X` / `Ctrl+V` - Copy/Cut/Paste
- `Arrow keys` - Move annotation
- `Space` - Toggle visibility
- And more... (see User Guide)

## 📦 Export Formats

Export to 3 industry-standard formats:

1. **COCO JSON**: For PyTorch, Detectron2, MMDetection
2. **YOLO TXT**: For YOLOv5, YOLOv8, Ultralytics
3. **Pascal VOC XML**: For TensorFlow Object Detection API

## 🚀 Deployment Options

### Docker (Production)
```bash
docker-compose up -d
```

### Manual (Development)
```bash
# Backend
cd backend && uvicorn app.main:app --reload

# Frontend
cd frontend && npm run dev
```

### Scripts Available
- `scripts/deploy.sh` - Automated production deployment
- `scripts/backup.sh` - Database backup automation
- `scripts/health-check.sh` - System health monitoring

## 🔍 Troubleshooting

### Frontend Issues
```bash
# Clear npm cache
npm cache clean --force
cd frontend && npm install

# Rebuild
npm run build
```

### Backend Issues
```bash
# Check logs
docker-compose logs backend

# Restart service
docker-compose restart backend
```

### Database Issues
```bash
# Check database file
ls -la data/annotations.db

# Restore from backup
cp data/backups/annotations_YYYYMMDD_HHMMSS.db.gz data/
gunzip data/annotations_YYYYMMDD_HHMMSS.db.gz
mv data/annotations_YYYYMMDD_HHMMSS.db data/annotations.db
```

**See [Troubleshooting Guide](docs/user-guides/USER_GUIDE.md#troubleshooting) for more help.**

## 📊 Project Statistics

- **Total Code**: ~15,000 lines
- **API Endpoints**: 22
- **Frontend Components**: 8 major components
- **Database Tables**: 3 (images, annotations, templates)
- **Documentation Pages**: 10+
- **Keyboard Shortcuts**: 20+
- **Export Formats**: 3 (COCO, YOLO, VOC)

## 🗺️ Roadmap

### Completed ✅
- Phase 1: CLI pipeline (YOLOv8, SAM, COCO export)
- Phase 2: Multi-model ensemble (DETR, Grounding DINO)
- Phase 2.5: Web dashboard (React + FastAPI)
- Phase 3: Advanced features (Templates, Keyboard shortcuts, Review workflow)
- Production Readiness: Docker, documentation, deployment scripts

### Planned 🔮
- Authentication & multi-user support (JWT)
- Active learning loop
- Cloud storage integration (S3, GCS)
- Advanced analytics dashboard
- Model fine-tuning integration
- Batch image upload via UI
- Video annotation support

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📧 Support

- **Documentation**: Check `docs/` directory
- **Issues**: [GitHub Issues](https://github.com/yourusername/yollo-dataset-builder/issues)
- **API Docs**: http://localhost:8000/docs

---

**Built with ❤️ for the computer vision community**