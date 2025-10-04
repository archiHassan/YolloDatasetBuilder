"""YOLOv8 annotation module for object detection."""

import torch
import cv2
import numpy as np
from ultralytics import YOLO
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
import logging

from ..utils.image_utils import ImageUtils

logger = logging.getLogger(__name__)


class YOLOAnnotator:
    """YOLOv8-based object detection annotator."""
    
    def __init__(self, config: Dict):
        """Initialize YOLO annotator.
        
        Args:
            config: Configuration dictionary containing YOLO settings
        """
        self.config = config
        self.model_config = config.get('models', {}).get('yolo', {})
        
        # Model parameters
        self.model_name = self.model_config.get('model_name', 'yolov8n.pt')
        self.confidence_threshold = self.model_config.get('confidence_threshold', 0.25)
        self.iou_threshold = self.model_config.get('iou_threshold', 0.45)
        self.device = self._setup_device()
        
        # Load model
        self.model = None
        self.class_names = None
        self._load_model()
        
        # Statistics
        self.stats = {
            'images_processed': 0,
            'total_detections': 0,
            'filtered_detections': 0
        }
    
    def _setup_device(self) -> str:
        """Setup computing device (CPU/CUDA).
        
        Returns:
            Device string
        """
        device_config = self.model_config.get('device', 'auto')
        
        if device_config == 'auto':
            if torch.cuda.is_available():
                device = 'cuda'
                logger.info(f"Using CUDA device: {torch.cuda.get_device_name()}")
            else:
                device = 'cpu'
                logger.info("Using CPU device")
        else:
            device = device_config
            logger.info(f"Using specified device: {device}")
        
        return device
    
    def load_model(self) -> None:
        """Load YOLOv8 model (public interface)."""
        self._load_model()
    
    def _load_model(self) -> None:
        """Load YOLOv8 model."""
        try:
            logger.info(f"Loading YOLOv8 model: {self.model_name}")
            
            # Load model (will download if not exists)
            self.model = YOLO(self.model_name)
            
            # Move to device
            self.model.to(self.device)
            
            # Get class names
            self.class_names = self.model.names
            
            logger.info(f"Model loaded successfully with {len(self.class_names)} classes")
            logger.debug(f"Available classes: {list(self.class_names.values())}")
            
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise RuntimeError(f"Could not load YOLO model: {e}")
    
    def annotate_image(
        self,
        image_path: str,
        return_image: bool = False
    ) -> Dict:
        """Annotate single image with object detections.
        
        Args:
            image_path: Path to image file
            return_image: Whether to return the annotated image
            
        Returns:
            Dictionary containing detection results
        """
        try:
            # Load image
            image = ImageUtils.load_image(image_path)
            if image is None:
                return self._empty_result(image_path, "Failed to load image")
            
            # Run inference
            results = self.model(image, conf=self.confidence_threshold, iou=self.iou_threshold)
            
            # Process results
            detections = self._process_results(results[0], image.shape)
            
            # Update statistics
            self.stats['images_processed'] += 1
            self.stats['total_detections'] += len(detections)
            
            # Create result dictionary
            result = {
                'image_path': image_path,
                'image_shape': image.shape,
                'detections': detections,
                'detection_count': len(detections),
                'success': True,
                'error': None
            }
            
            if return_image:
                annotated_image = self._draw_annotations(image, detections)
                result['annotated_image'] = annotated_image
            
            return result
            
        except Exception as e:
            logger.error(f"Error annotating image {image_path}: {e}")
            return self._empty_result(image_path, str(e))
    
    def annotate_batch(
        self,
        image_paths: List[str],
        batch_size: int = 16
    ) -> List[Dict]:
        """Annotate multiple images in batches.
        
        Args:
            image_paths: List of image paths
            batch_size: Number of images to process in each batch
            
        Returns:
            List of detection results
        """
        logger.info(f"Processing {len(image_paths)} images in batches of {batch_size}")
        
        results = []
        
        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i:i + batch_size]
            logger.debug(f"Processing batch {i//batch_size + 1}: {len(batch_paths)} images")
            
            batch_results = []
            for image_path in batch_paths:
                result = self.annotate_image(image_path)
                batch_results.append(result)
            
            results.extend(batch_results)
            
            # Log progress
            processed = min(i + batch_size, len(image_paths))
            logger.info(f"Processed {processed}/{len(image_paths)} images")
        
        logger.info("Batch annotation completed")
        return results
    
    def _process_results(self, result, image_shape: Tuple[int, int, int]) -> List[Dict]:
        """Process YOLO detection results.
        
        Args:
            result: YOLO result object
            image_shape: Image shape (H, W, C)
            
        Returns:
            List of detection dictionaries
        """
        detections = []
        
        if result.boxes is None:
            return detections
        
        boxes = result.boxes.xyxy.cpu().numpy()  # x1, y1, x2, y2
        confidences = result.boxes.conf.cpu().numpy()
        class_ids = result.boxes.cls.cpu().numpy().astype(int)
        
        height, width = image_shape[:2]
        
        for i in range(len(boxes)):
            x1, y1, x2, y2 = boxes[i]
            confidence = float(confidences[i])
            class_id = int(class_ids[i])
            
            # Convert to COCO format (x, y, width, height)
            bbox_width = x2 - x1
            bbox_height = y2 - y1
            
            # Normalize coordinates (0-1)
            normalized_bbox = [
                x1 / width,
                y1 / height,
                bbox_width / width,
                bbox_height / height
            ]
            
            detection = {
                'bbox': [x1, y1, bbox_width, bbox_height],  # COCO format
                'bbox_normalized': normalized_bbox,
                'bbox_xyxy': [x1, y1, x2, y2],  # For visualization
                'confidence': confidence,
                'class_id': class_id,
                'class_name': self.class_names.get(class_id, f"class_{class_id}"),
                'area': bbox_width * bbox_height,
                'model': 'yolov8'
            }
            
            detections.append(detection)
        
        return detections
    
    def _draw_annotations(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """Draw annotations on image for visualization.
        
        Args:
            image: Input image
            detections: List of detections
            
        Returns:
            Annotated image
        """
        annotated = image.copy()
        
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox_xyxy']
            confidence = detection['confidence']
            class_name = detection['class_name']
            
            # Draw bounding box
            cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            
            # Draw label
            label = f"{class_name}: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            
            # Background for label
            cv2.rectangle(
                annotated,
                (int(x1), int(y1) - label_size[1] - 10),
                (int(x1) + label_size[0], int(y1)),
                (0, 255, 0),
                -1
            )
            
            # Text
            cv2.putText(
                annotated,
                label,
                (int(x1), int(y1) - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                2
            )
        
        return annotated
    
    def _empty_result(self, image_path: str, error_message: str) -> Dict:
        """Create empty result for failed processing.
        
        Args:
            image_path: Path to image
            error_message: Error description
            
        Returns:
            Empty result dictionary
        """
        return {
            'image_path': image_path,
            'image_shape': None,
            'detections': [],
            'detection_count': 0,
            'success': False,
            'error': error_message
        }
    
    def filter_detections(
        self,
        detections: List[Dict],
        min_confidence: float = 0.5,
        min_area: int = 100,
        max_area_ratio: float = 0.8,
        min_aspect_ratio: float = 0.1,
        max_aspect_ratio: float = 10.0
    ) -> List[Dict]:
        """Filter detections based on confidence and geometric constraints.
        
        Args:
            detections: List of detection dictionaries
            min_confidence: Minimum confidence threshold
            min_area: Minimum bounding box area
            max_area_ratio: Maximum ratio of image area
            min_aspect_ratio: Minimum aspect ratio
            max_aspect_ratio: Maximum aspect ratio
            
        Returns:
            Filtered detections
        """
        filtered = []
        
        for detection in detections:
            # Check confidence
            if detection['confidence'] < min_confidence:
                continue
            
            # Check area
            area = detection['area']
            if area < min_area:
                continue
            
            # Check area ratio (would need image dimensions)
            # This is simplified - in practice, you'd pass image dimensions
            
            # Check aspect ratio
            bbox = detection['bbox']
            width, height = bbox[2], bbox[3]
            if height > 0:
                aspect_ratio = width / height
                if aspect_ratio < min_aspect_ratio or aspect_ratio > max_aspect_ratio:
                    continue
            
            filtered.append(detection)
        
        self.stats['filtered_detections'] += len(filtered)
        return filtered
    
    def get_statistics(self) -> Dict:
        """Get annotation statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'model_info': {
                'model_name': self.model_name,
                'device': self.device,
                'num_classes': len(self.class_names) if self.class_names else 0,
                'class_names': list(self.class_names.values()) if self.class_names else []
            },
            'processing_stats': self.stats.copy(),
            'parameters': {
                'confidence_threshold': self.confidence_threshold,
                'iou_threshold': self.iou_threshold
            }
        }
    
    def save_model_info(self, output_path: str) -> None:
        """Save model information to file.
        
        Args:
            output_path: Path to save model info
        """
        import json
        
        info = self.get_statistics()
        
        with open(output_path, 'w') as f:
            json.dump(info, f, indent=2)
        
        logger.info(f"Model information saved to {output_path}")
    
    def unload_model(self) -> None:
        """Unload model to free memory."""
        if self.model is not None:
            del self.model
            self.model = None
            
            # Clear CUDA cache if using GPU
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info("YOLO model unloaded")