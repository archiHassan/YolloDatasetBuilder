"""
SAM (Segment Anything Model) API endpoints for automatic segmentation
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Tuple
import numpy as np
from pathlib import Path
import base64
import io
from PIL import Image
import json

router = APIRouter()

# SAM integration options:
# 1. Local ONNX model (fast, no API costs)
# 2. API-based (Replicate, Hugging Face)
SAM_MODE = "api"  # or "local"

class SAMPoint(BaseModel):
    x: float
    y: float
    label: int  # 1 for foreground, 0 for background

class SAMRequest(BaseModel):
    image_path: str
    points: List[SAMPoint]
    box: Optional[List[float]] = None  # [x, y, width, height]

class SAMResponse(BaseModel):
    mask: str  # Base64 encoded mask
    polygon: List[List[float]]  # Polygon points extracted from mask
    confidence: float

def mask_to_polygon(mask: np.ndarray, simplify_tolerance: float = 2.0) -> List[List[float]]:
    """
    Convert binary mask to polygon points
    Uses contour detection to extract boundary
    """
    try:
        import cv2
    except ImportError:
        raise HTTPException(status_code=500, detail="opencv-python not installed. Run: pip install opencv-python")

    # Find contours
    contours, _ = cv2.findContours(
        mask.astype(np.uint8),
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return []

    # Get largest contour
    largest_contour = max(contours, key=cv2.contourArea)

    # Simplify polygon using Douglas-Peucker algorithm
    epsilon = simplify_tolerance
    approx = cv2.approxPolyDP(largest_contour, epsilon, True)

    # Convert to list of [x, y] points
    polygon = [[float(point[0][0]), float(point[0][1])] for point in approx]

    return polygon

def encode_mask(mask: np.ndarray) -> str:
    """Encode mask as base64 PNG"""
    # Convert to PIL Image
    mask_img = Image.fromarray((mask * 255).astype(np.uint8))

    # Save to bytes
    buffer = io.BytesIO()
    mask_img.save(buffer, format='PNG')
    buffer.seek(0)

    # Encode to base64
    encoded = base64.b64encode(buffer.read()).decode('utf-8')
    return encoded

async def generate_sam_mask_api(image_path: str, points: List[SAMPoint], box: Optional[List[float]] = None) -> Tuple[np.ndarray, float]:
    """
    Generate SAM mask using API service (placeholder)
    In production, integrate with Replicate, Hugging Face, or custom SAM API
    """
    # TODO: Integrate with actual SAM API
    # Example with Replicate:
    # import replicate
    # output = replicate.run(
    #     "meta/sam-2:...",
    #     input={
    #         "image": open(image_path, "rb"),
    #         "point_coords": [[p.x, p.y] for p in points],
    #         "point_labels": [p.label for p in points]
    #     }
    # )

    # For now, return dummy mask
    raise HTTPException(
        status_code=501,
        detail="SAM API integration not implemented. Set up Replicate API key or use local model."
    )

async def generate_sam_mask_local(image_path: str, points: List[SAMPoint], box: Optional[List[float]] = None) -> Tuple[np.ndarray, float]:
    """
    Generate SAM mask using local ONNX model
    Requires: onnxruntime, segment-anything
    """
    try:
        # Try importing SAM dependencies
        import onnxruntime
        from segment_anything import sam_model_registry, SamPredictor
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="SAM dependencies not installed. Run: pip install segment-anything onnxruntime"
        )

    # TODO: Load and initialize SAM model
    # model_path = "models/sam_vit_h.pth"  # Download from SAM repo
    # sam = sam_model_registry["vit_h"](checkpoint=model_path)
    # predictor = SamPredictor(sam)

    # Load image
    # image = np.array(Image.open(image_path))
    # predictor.set_image(image)

    # Prepare points
    # input_points = np.array([[p.x, p.y] for p in points])
    # input_labels = np.array([p.label for p in points])

    # Generate mask
    # masks, scores, _ = predictor.predict(
    #     point_coords=input_points,
    #     point_labels=input_labels,
    #     box=np.array(box) if box else None,
    #     multimask_output=True
    # )

    # Return best mask
    # best_idx = np.argmax(scores)
    # return masks[best_idx], float(scores[best_idx])

    raise HTTPException(
        status_code=501,
        detail="Local SAM model not configured. Download SAM weights and configure path."
    )

@router.post("/generate", response_model=SAMResponse)
async def generate_segmentation_mask(request: SAMRequest):
    """
    Generate segmentation mask using SAM based on point prompts
    """
    # Validate image exists
    image_path = Path(request.image_path)
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    # Generate mask based on mode
    try:
        if SAM_MODE == "local":
            mask, confidence = await generate_sam_mask_local(
                str(image_path),
                request.points,
                request.box
            )
        else:
            mask, confidence = await generate_sam_mask_api(
                str(image_path),
                request.points,
                request.box
            )

        # Convert mask to polygon
        polygon = mask_to_polygon(mask)

        # Encode mask
        encoded_mask = encode_mask(mask)

        return SAMResponse(
            mask=encoded_mask,
            polygon=polygon,
            confidence=confidence
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SAM generation failed: {str(e)}")

@router.post("/generate-mock", response_model=SAMResponse)
async def generate_mock_segmentation(request: SAMRequest):
    """
    Generate mock segmentation for testing (creates circular polygon around click point)
    Use this while SAM integration is being set up
    """
    if not request.points:
        raise HTTPException(status_code=400, detail="At least one point required")

    # Get first point as center
    center_point = request.points[0]

    # Create circular polygon around point
    import math
    radius = 50  # pixels
    num_points = 16

    polygon = []
    for i in range(num_points):
        angle = (2 * math.pi * i) / num_points
        x = center_point.x + radius * math.cos(angle)
        y = center_point.y + radius * math.sin(angle)
        polygon.append([x, y])

    # Create simple mock mask (all zeros for now)
    mock_mask = np.zeros((100, 100), dtype=np.uint8)
    encoded_mask = encode_mask(mock_mask)

    return SAMResponse(
        mask=encoded_mask,
        polygon=polygon,
        confidence=0.85
    )

@router.get("/status")
async def sam_status():
    """Get SAM integration status"""
    status = {
        "mode": SAM_MODE,
        "available": False,
        "model_loaded": False,
        "api_configured": False
    }

    if SAM_MODE == "local":
        try:
            import onnxruntime
            from segment_anything import sam_model_registry
            status["dependencies_installed"] = True

            # Check if model file exists
            model_path = Path("models/sam_vit_h.pth")
            status["model_loaded"] = model_path.exists()
            status["available"] = status["model_loaded"]
        except ImportError:
            status["dependencies_installed"] = False

    elif SAM_MODE == "api":
        # Check for API keys
        import os
        status["api_configured"] = bool(os.getenv("REPLICATE_API_TOKEN"))
        status["available"] = status["api_configured"]

    return status
