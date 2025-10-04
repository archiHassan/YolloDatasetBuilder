"""
Image management API endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from typing import List, Optional
from pathlib import Path
import logging

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def list_images(
    skip: int = Query(0, ge=0, description="Number of images to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of images to return"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """
    List all images in the dataset.

    Returns paginated list of images with metadata.
    """
    try:
        # Get all image files from images directory
        image_files = []
        supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}

        for ext in supported_extensions:
            image_files.extend(settings.images_dir.glob(f"*{ext}"))
            image_files.extend(settings.images_dir.glob(f"*{ext.upper()}"))

        # Sort by filename
        image_files = sorted(image_files, key=lambda x: x.name)

        # Apply pagination
        total = len(image_files)
        paginated_files = image_files[skip:skip + limit]

        # Build response
        images = []
        for idx, img_path in enumerate(paginated_files, start=skip):
            images.append({
                "id": idx + 1,
                "filename": img_path.name,
                "path": f"/static/images/{img_path.name}",
                "size": img_path.stat().st_size,
                "status": "pending"  # TODO: Get from database
            })

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "images": images
        }

    except Exception as e:
        logger.error(f"Error listing images: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{image_id}")
async def get_image(image_id: int):
    """
    Get details for a specific image.
    """
    try:
        # Get all image files
        image_files = []
        supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}

        for ext in supported_extensions:
            image_files.extend(settings.images_dir.glob(f"*{ext}"))
            image_files.extend(settings.images_dir.glob(f"*{ext.upper()}"))

        image_files = sorted(image_files, key=lambda x: x.name)

        # Get image by index
        if image_id < 1 or image_id > len(image_files):
            raise HTTPException(status_code=404, detail="Image not found")

        img_path = image_files[image_id - 1]

        # Get image dimensions (optional, requires PIL)
        try:
            from PIL import Image
            with Image.open(img_path) as img:
                width, height = img.size
        except:
            width, height = None, None

        return {
            "id": image_id,
            "filename": img_path.name,
            "path": f"/static/images/{img_path.name}",
            "size": img_path.stat().st_size,
            "width": width,
            "height": height,
            "status": "pending"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting image {image_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{image_id}/file")
async def get_image_file(image_id: int):
    """
    Serve the actual image file.
    """
    try:
        # Get image path
        image_files = []
        supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}

        for ext in supported_extensions:
            image_files.extend(settings.images_dir.glob(f"*{ext}"))
            image_files.extend(settings.images_dir.glob(f"*{ext.upper()}"))

        image_files = sorted(image_files, key=lambda x: x.name)

        if image_id < 1 or image_id > len(image_files):
            raise HTTPException(status_code=404, detail="Image not found")

        img_path = image_files[image_id - 1]

        return FileResponse(img_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving image file {image_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
