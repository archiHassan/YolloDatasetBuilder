# Web Dashboard Frontend - Phase 2.5

React-based frontend for YOLO Dataset Builder annotation review interface.

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure API URL

Create `.env` file (already created):
```
VITE_API_URL=http://localhost:8000
```

### 3. Start Backend Server

Make sure the backend is running first:
```bash
cd backend
python -m app.main
# OR
../venv/Scripts/python.exe -m app.main
```

Backend will start at: http://localhost:8000

### 4. Start Frontend Development Server

```bash
cd frontend
npm run dev
```

Frontend will start at: http://localhost:5173 (or similar port)

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.js          # API client with all endpoints
│   ├── components/
│   │   ├── ImageGallery.jsx   # Main image gallery view
│   │   ├── ImageViewer.jsx    # Single image viewer with annotations
│   │   ├── ReviewQueue.jsx    # Review queue (placeholder)
│   │   └── Statistics.jsx     # Statistics dashboard (placeholder)
│   ├── App.jsx                 # Main app with routing
│   ├── main.jsx                # Entry point
│   └── index.css               # Tailwind styles
├── .env                        # Environment variables
├── vite.config.js              # Vite configuration
├── tailwind.config.js          # Tailwind configuration
└── package.json                # Dependencies
```

## Features Implemented

### Day 2 (October 2, 2025)

✅ **Core Frontend Setup**:
- React app with Vite
- Tailwind CSS for styling
- React Router for navigation
- Axios for API calls

✅ **API Integration**:
- Full API client with all backend endpoints
- Images API (list, get, serve)
- Annotations API (CRUD operations)
- Review API (queue, approve, reject, stats)

✅ **Components**:
- **ImageGallery**: Displays images in grid with pagination
- **ImageViewer**: Shows single image with annotations
- **Navigation**: Top navbar with routing
- **ReviewQueue**: Placeholder for review workflow
- **Statistics**: Placeholder for stats dashboard

### Image Gallery Features:
- Grid layout (responsive: 1-4 columns)
- Pagination (20 images per page)
- Image thumbnails with metadata
- Status badges (pending/approved)
- File size display
- Error handling and retry

### Image Viewer Features:
- Full-size image display
- Annotation list with details
- Bounding box coordinates
- Confidence scores
- Category labels
- Back to gallery navigation

## API Endpoints Used

All endpoints are defined in `src/api/client.js`:

**Images**:
- `getImages(skip, limit)` - List images with pagination
- `getImage(id)` - Get single image details
- `getImageUrl(filename)` - Get image URL for display

**Annotations**:
- `getAnnotations(imageId)` - Get annotations for image
- `createAnnotation(annotation)` - Create new annotation
- `updateAnnotation(id, annotation)` - Update annotation
- `deleteAnnotation(id)` - Delete annotation

**Review**:
- `getReviewQueue(limit)` - Get review queue
- `approveImage(imageId)` - Approve image
- `rejectImage(imageId, reason)` - Reject image
- `getReviewStatistics()` - Get review stats

## Technology Stack

- **React 19.1.1** - UI framework
- **Vite 7.1.7** - Build tool and dev server
- **React Router 7.9.3** - Client-side routing
- **Axios 1.12.2** - HTTP client
- **Tailwind CSS 4.1.14** - Utility-first CSS framework

## Development

### Running the App

1. Start backend: `cd backend && python -m app.main`
2. Start frontend: `cd frontend && npm run dev`
3. Open browser to http://localhost:5173

### Building for Production

```bash
npm run build
```

Build output will be in `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Next Steps (Day 3-4)

- [ ] Implement annotation drawing on images
- [ ] Add bounding box visualization
- [ ] Create interactive editing tools
- [ ] Implement review workflow UI
- [ ] Add keyboard shortcuts
- [ ] Create statistics dashboard

## Status

**Phase**: Day 2 Complete - Frontend MVP
**Version**: 0.1.0
**Ready for**: Manual testing and iteration
