"""
FastAPI main application for Web Dashboard
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import logging

from app.config import settings
from app.api import images, annotations, review, export, templates, sam

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug,
    description="Interactive annotation review and management dashboard"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for images
app.mount(
    "/static/images",
    StaticFiles(directory=str(settings.images_dir)),
    name="images"
)

# Include API routers
app.include_router(images.router, prefix=f"{settings.api_prefix}/images", tags=["images"])
app.include_router(annotations.router, prefix=f"{settings.api_prefix}/annotations", tags=["annotations"])
app.include_router(review.router, prefix=f"{settings.api_prefix}/review", tags=["review"])
app.include_router(export.router, prefix=f"{settings.api_prefix}/export", tags=["export"])
app.include_router(templates.router, prefix=f"{settings.api_prefix}/templates", tags=["templates"])
app.include_router(sam.router, prefix=f"{settings.api_prefix}/sam", tags=["sam"])


@app.get("/")
async def root():
    """Root endpoint - API info."""
    return {
        "app": settings.app_name,
        "version": settings.version,
        "status": "running",
        "docs": "/docs",
        "api_prefix": settings.api_prefix
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
