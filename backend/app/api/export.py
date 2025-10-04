"""
Export API endpoints - COCO, YOLO, Pascal VOC formats
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Dict, Any, Literal
from pathlib import Path
import json
import logging
import zipfile
import io
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


def coco_to_yolo(bbox: List[float], img_width: int, img_height: int) -> List[float]:
    """
    Convert COCO bbox [x, y, width, height] to YOLO format [x_center, y_center, width, height] (normalized).

    Args:
        bbox: COCO format bounding box [x, y, width, height] in pixels
        img_width: Image width in pixels
        img_height: Image height in pixels

    Returns:
        YOLO format [x_center, y_center, width, height] (normalized 0-1)
    """
    x, y, w, h = bbox

    # Convert to center coordinates
    x_center = x + w / 2
    y_center = y + h / 2

    # Normalize by image dimensions
    x_center_norm = x_center / img_width
    y_center_norm = y_center / img_height
    width_norm = w / img_width
    height_norm = h / img_height

    return [x_center_norm, y_center_norm, width_norm, height_norm]


def load_coco_data() -> Dict[str, Any]:
    """Load COCO format annotations from file."""
    try:
        annotation_files = list(settings.annotations_dir.glob("*.json"))

        if not annotation_files:
            return {"images": [], "annotations": [], "categories": []}

        coco_file = annotation_files[0]
        with open(coco_file, 'r') as f:
            return json.load(f)

    except Exception as e:
        logger.error(f"Error loading COCO data: {e}")
        return {"images": [], "annotations": [], "categories": []}


def get_image_info(coco_data: Dict, image_id: int) -> Dict:
    """Get image information from COCO data."""
    for img in coco_data.get('images', []):
        if img.get('id') == image_id:
            return img
    return None


def create_category_mapping(coco_data: Dict) -> Dict[int, int]:
    """
    Create mapping from COCO category IDs to sequential class IDs (0, 1, 2...).
    YOLO requires class IDs starting from 0.
    """
    categories = coco_data.get('categories', [])
    category_ids = sorted([cat['id'] for cat in categories])
    return {cat_id: idx for idx, cat_id in enumerate(category_ids)}


@router.get("/formats")
async def list_export_formats():
    """List available export formats."""
    return {
        "formats": [
            {
                "name": "coco",
                "description": "COCO JSON format (original)",
                "file_extension": ".json"
            },
            {
                "name": "yolo",
                "description": "YOLO text format (one .txt file per image)",
                "file_extension": ".zip"
            },
            {
                "name": "voc",
                "description": "Pascal VOC XML format",
                "file_extension": ".zip"
            }
        ]
    }


@router.get("/coco")
async def export_coco(
    split: Literal["train", "val", "test", "all"] = Query("all", description="Dataset split to export")
):
    """
    Export annotations in COCO format.

    Returns the original COCO JSON file or filtered by split.
    """
    try:
        coco_data = load_coco_data()

        if not coco_data.get('annotations'):
            raise HTTPException(status_code=404, detail="No annotations found")

        # For MVP, return all data (split filtering can be added later)
        if split != "all":
            logger.warning(f"Split filtering not yet implemented, returning all data")

        # Create temporary file
        export_path = settings.data_dir / f"export_coco_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(export_path, 'w') as f:
            json.dump(coco_data, f, indent=2)

        return FileResponse(
            path=export_path,
            filename=f"annotations_{split}.json",
            media_type="application/json"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting COCO format: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/yolo")
async def export_yolo():
    """
    Export annotations in YOLO format.

    Returns a ZIP file containing:
    - labels/ directory with .txt files (one per image)
    - classes.txt with class names
    - data.yaml with dataset configuration
    """
    try:
        coco_data = load_coco_data()

        if not coco_data.get('annotations'):
            raise HTTPException(status_code=404, detail="No annotations found")

        # Create category mapping
        category_mapping = create_category_mapping(coco_data)

        # Create in-memory ZIP file
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Group annotations by image
            annotations_by_image = {}
            for ann in coco_data.get('annotations', []):
                image_id = ann['image_id']
                if image_id not in annotations_by_image:
                    annotations_by_image[image_id] = []
                annotations_by_image[image_id].append(ann)

            # Create label files
            for image_id, annotations in annotations_by_image.items():
                image_info = get_image_info(coco_data, image_id)
                if not image_info:
                    continue

                img_width = image_info.get('width', 640)
                img_height = image_info.get('height', 480)
                filename = image_info.get('file_name', f'{image_id}.jpg')
                base_name = Path(filename).stem

                # Create YOLO format labels
                yolo_labels = []
                for ann in annotations:
                    bbox = ann.get('bbox', [])
                    if len(bbox) != 4:
                        continue

                    category_id = ann.get('category_id')
                    class_id = category_mapping.get(category_id, 0)

                    # Convert bbox to YOLO format
                    yolo_bbox = coco_to_yolo(bbox, img_width, img_height)

                    # YOLO format: class_id x_center y_center width height
                    yolo_labels.append(
                        f"{class_id} {yolo_bbox[0]:.6f} {yolo_bbox[1]:.6f} {yolo_bbox[2]:.6f} {yolo_bbox[3]:.6f}"
                    )

                # Add label file to ZIP
                if yolo_labels:
                    label_content = '\n'.join(yolo_labels)
                    zip_file.writestr(f"labels/{base_name}.txt", label_content)

            # Create classes.txt
            categories = sorted(coco_data.get('categories', []), key=lambda x: x['id'])
            class_names = [cat['name'] for cat in categories]
            zip_file.writestr("classes.txt", '\n'.join(class_names))

            # Create data.yaml for YOLO training
            yaml_content = f"""# YOLO Dataset Configuration
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

path: ../datasets  # dataset root dir
train: images/train
val: images/val

# Classes
names:
"""
            for idx, name in enumerate(class_names):
                yaml_content += f"  {idx}: {name}\n"

            zip_file.writestr("data.yaml", yaml_content)

            # Create README
            readme_content = f"""# YOLO Format Export

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Images: {len(annotations_by_image)}
Total Annotations: {len(coco_data.get('annotations', []))}
Classes: {len(class_names)}

## Directory Structure
```
labels/          - Label files (one .txt per image)
classes.txt      - Class names (one per line)
data.yaml        - YOLO training configuration
```

## Label Format
Each line in label files: `class_id x_center y_center width height`
All coordinates are normalized (0-1).

## Usage with YOLO
1. Copy your images to `images/train/` or `images/val/`
2. Update the `path` in data.yaml
3. Train: `yolo train data=data.yaml model=yolov8n.pt epochs=100`
"""
            zip_file.writestr("README.md", readme_content)

        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=yolo_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting YOLO format: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voc")
async def export_voc():
    """
    Export annotations in Pascal VOC XML format.

    Returns a ZIP file containing XML annotation files (one per image).
    """
    try:
        coco_data = load_coco_data()

        if not coco_data.get('annotations'):
            raise HTTPException(status_code=404, detail="No annotations found")

        # Create in-memory ZIP file
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Group annotations by image
            annotations_by_image = {}
            for ann in coco_data.get('annotations', []):
                image_id = ann['image_id']
                if image_id not in annotations_by_image:
                    annotations_by_image[image_id] = []
                annotations_by_image[image_id].append(ann)

            # Create VOC XML files
            for image_id, annotations in annotations_by_image.items():
                image_info = get_image_info(coco_data, image_id)
                if not image_info:
                    continue

                filename = image_info.get('file_name', f'{image_id}.jpg')
                base_name = Path(filename).stem
                img_width = image_info.get('width', 640)
                img_height = image_info.get('height', 480)

                # Create VOC XML
                xml_content = f"""<annotation>
    <folder>images</folder>
    <filename>{filename}</filename>
    <size>
        <width>{img_width}</width>
        <height>{img_height}</height>
        <depth>3</depth>
    </size>
    <segmented>0</segmented>
"""

                # Add objects
                for ann in annotations:
                    bbox = ann.get('bbox', [])
                    if len(bbox) != 4:
                        continue

                    x, y, w, h = bbox
                    xmin = int(x)
                    ymin = int(y)
                    xmax = int(x + w)
                    ymax = int(y + h)

                    # Get category name
                    category_id = ann.get('category_id')
                    category_name = 'unknown'
                    for cat in coco_data.get('categories', []):
                        if cat['id'] == category_id:
                            category_name = cat['name']
                            break

                    xml_content += f"""    <object>
        <name>{category_name}</name>
        <pose>Unspecified</pose>
        <truncated>0</truncated>
        <difficult>0</difficult>
        <bndbox>
            <xmin>{xmin}</xmin>
            <ymin>{ymin}</ymin>
            <xmax>{xmax}</xmax>
            <ymax>{ymax}</ymax>
        </bndbox>
    </object>
"""

                xml_content += "</annotation>\n"

                # Add XML file to ZIP
                zip_file.writestr(f"Annotations/{base_name}.xml", xml_content)

            # Create README
            readme_content = f"""# Pascal VOC Format Export

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Images: {len(annotations_by_image)}
Total Annotations: {len(coco_data.get('annotations', []))}

## Directory Structure
```
Annotations/     - XML annotation files (one per image)
```

## Usage
Compatible with Pascal VOC dataset format used by many frameworks.
Each XML file contains image metadata and object bounding boxes.
"""
            zip_file.writestr("README.md", readme_content)

        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=voc_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting VOC format: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_export_statistics():
    """Get statistics about exportable data."""
    try:
        coco_data = load_coco_data()

        # Count annotations by category
        category_counts = {}
        for ann in coco_data.get('annotations', []):
            cat_id = ann.get('category_id')
            category_counts[cat_id] = category_counts.get(cat_id, 0) + 1

        # Get category names
        category_stats = []
        for cat in coco_data.get('categories', []):
            cat_id = cat['id']
            category_stats.append({
                'id': cat_id,
                'name': cat['name'],
                'count': category_counts.get(cat_id, 0)
            })

        return {
            "total_images": len(coco_data.get('images', [])),
            "total_annotations": len(coco_data.get('annotations', [])),
            "total_categories": len(coco_data.get('categories', [])),
            "category_distribution": category_stats,
            "avg_annotations_per_image": (
                len(coco_data.get('annotations', [])) / len(coco_data.get('images', []))
                if coco_data.get('images') else 0
            )
        }

    except Exception as e:
        logger.error(f"Error getting export statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
