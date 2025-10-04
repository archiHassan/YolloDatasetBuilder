# Web Dashboard Backend - Phase 2.5

FastAPI backend for YOLO Dataset Builder annotation review interface.

## Quick Start

### 1. Install Dependencies

```bash
# From backend directory
cd backend
pip install -r requirements.txt
```

### 2. Run the Server

```bash
# Development mode (with auto-reload)
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --port 8000
```

### 3. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Images
- `GET /api/images` - List all images (paginated)
- `GET /api/images/{id}` - Get image details
- `GET /api/images/{id}/file` - Get image file

### Annotations
- `GET /api/annotations` - List all annotations
- `GET /api/annotations/{image_id}` - Get annotations for image
- `POST /api/annotations` - Create annotation
- `PUT /api/annotations/{id}` - Update annotation
- `DELETE /api/annotations/{id}` - Delete annotation

### Review
- `GET /api/review/queue` - Get review queue
- `POST /api/review/{id}/approve` - Approve image
- `POST /api/review/{id}/reject` - Reject image
- `GET /api/review/statistics` - Get review stats

## Configuration

Edit `app/config.py` to change:
- Data directory paths
- API settings
- CORS origins
- Pagination limits

## Development

### Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app
│   ├── config.py         # Configuration
│   └── api/
│       ├── images.py     # Image endpoints
│       ├── annotations.py # Annotation endpoints
│       └── review.py     # Review endpoints
├── requirements.txt
└── README.md
```

### Testing

```bash
# Test the API is running
curl http://localhost:8000/health

# List images
curl http://localhost:8000/api/images

# Get specific image
curl http://localhost:8000/api/images/1
```

## Next Steps

1. ✅ Basic API working
2. ⏳ Add database persistence (SQLite/PostgreSQL)
3. ⏳ Implement annotation editing
4. ⏳ Add authentication
5. ⏳ Connect to frontend

## Status

**Phase**: MVP (File-based, read-only annotations)
**Version**: 0.1.0
**Ready for**: Frontend development
