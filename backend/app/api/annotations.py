"""
Annotation management API endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pathlib import Path
import json
import logging

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


def load_annotations_from_coco(coco_file: Path) -> Dict[str, List[Dict]]:
    """Load annotations from COCO JSON file and group by image."""
    try:
        if not coco_file.exists():
            return {}

        with open(coco_file, 'r') as f:
            coco_data = json.load(f)

        # Group annotations by image_id
        annotations_by_image = {}
        for ann in coco_data.get('annotations', []):
            image_id = ann.get('image_id')
            if image_id not in annotations_by_image:
                annotations_by_image[image_id] = []

            annotations_by_image[image_id].append({
                'id': ann.get('id'),
                'bbox': ann.get('bbox', []),  # [x, y, width, height]
                'category_id': ann.get('category_id'),
                'category': get_category_name(coco_data, ann.get('category_id')),
                'confidence': ann.get('score', 1.0),
                'area': ann.get('area', 0),
                'status': 'pending'
            })

        return annotations_by_image

    except Exception as e:
        logger.error(f"Error loading COCO annotations: {e}")
        return {}


def get_category_name(coco_data: Dict, category_id: int) -> str:
    """Get category name from category ID."""
    for cat in coco_data.get('categories', []):
        if cat.get('id') == category_id:
            return cat.get('name', 'unknown')
    return 'unknown'


@router.get("/")
async def list_annotations():
    """
    List all annotations across all images.
    """
    try:
        # Look for COCO annotation files
        annotation_files = list(settings.annotations_dir.glob("*.json"))

        if not annotation_files:
            return {"total": 0, "annotations": []}

        # Load from first COCO file found
        coco_file = annotation_files[0]
        annotations_by_image = load_annotations_from_coco(coco_file)

        # Flatten to list
        all_annotations = []
        for image_id, anns in annotations_by_image.items():
            for ann in anns:
                ann['image_id'] = image_id
                all_annotations.append(ann)

        return {
            "total": len(all_annotations),
            "annotations": all_annotations
        }

    except Exception as e:
        logger.error(f"Error listing annotations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{image_id}")
async def get_annotations_for_image(image_id: int):
    """
    Get all annotations for a specific image.
    """
    try:
        # Look for COCO annotation files
        annotation_files = list(settings.annotations_dir.glob("*.json"))

        if not annotation_files:
            return {"image_id": image_id, "annotations": []}

        # Load from first COCO file found
        coco_file = annotation_files[0]
        annotations_by_image = load_annotations_from_coco(coco_file)

        # Get annotations for this image
        annotations = annotations_by_image.get(image_id, [])

        return {
            "image_id": image_id,
            "count": len(annotations),
            "annotations": annotations
        }

    except Exception as e:
        logger.error(f"Error getting annotations for image {image_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_annotation(annotation: Dict[str, Any]):
    """
    Create a new annotation.

    For MVP, this will just validate and return the annotation.
    Database persistence will be added later.
    """
    try:
        # Validate required fields
        required_fields = ['image_id', 'bbox', 'category']
        for field in required_fields:
            if field not in annotation:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )

        # Add default values
        annotation.setdefault('confidence', 1.0)
        annotation.setdefault('status', 'pending')
        annotation.setdefault('source', 'human')

        logger.info(f"Created annotation for image {annotation['image_id']}")

        return {
            "success": True,
            "annotation": annotation
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating annotation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{annotation_id}")
async def update_annotation(annotation_id: int, annotation: Dict[str, Any]):
    """
    Update an existing annotation.

    For MVP, this will just validate and return the annotation.
    """
    try:
        annotation['id'] = annotation_id
        logger.info(f"Updated annotation {annotation_id}")

        return {
            "success": True,
            "annotation": annotation
        }

    except Exception as e:
        logger.error(f"Error updating annotation {annotation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{annotation_id}")
async def delete_annotation(annotation_id: int):
    """
    Delete an annotation.

    For MVP, this will just return success.
    """
    try:
        logger.info(f"Deleted annotation {annotation_id}")

        return {
            "success": True,
            "message": f"Annotation {annotation_id} deleted"
        }

    except Exception as e:
        logger.error(f"Error deleting annotation {annotation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
