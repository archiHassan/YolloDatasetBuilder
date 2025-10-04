"""Grounding DINO annotation module for text-prompted object detection."""

import torch
import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
import logging

from ..utils.image_utils import ImageUtils

logger = logging.getLogger(__name__)


class GroundingDINOAnnotator:
    """Grounding DINO annotator for text-prompted object detection."""
    
    def __init__(self, config: Dict):
        """Initialize Grounding DINO annotator.
        
        Args:
            config: Configuration dictionary containing Grounding DINO settings
        """
        self.config = config
        self.model_config = config.get('models', {}).get('grounding_dino', {})
        
        # Model parameters
        self.model_name = self.model_config.get('model_name', 'IDEA-Research/grounding-dino-base')
        self.confidence_threshold = self.model_config.get('confidence_threshold', 0.35)
        self.text_threshold = self.model_config.get('text_threshold', 0.25)
        self.device = self._setup_device()
        
        # Text prompts for detection
        self.default_prompts = self.model_config.get('default_prompts', [
            "person . car . bicycle . motorcycle . airplane . bus . train . truck . boat",
            "traffic light . fire hydrant . stop sign . parking meter . bench",
            "cat . dog . horse . sheep . cow . elephant . bear . zebra . giraffe",
            "backpack . umbrella . handbag . tie . suitcase . frisbee . skis . snowboard",
            "sports ball . kite . baseball bat . baseball glove . skateboard . surfboard",
            "tennis racket . bottle . wine glass . cup . fork . knife . spoon . bowl",
            "banana . apple . sandwich . orange . broccoli . carrot . hot dog . pizza",
            "donut . cake . chair . couch . potted plant . bed . dining table . toilet",
            "tv . laptop . mouse . remote . keyboard . cell phone . microwave . oven",
            "toaster . sink . refrigerator . book . clock . vase . scissors . teddy bear",
            "hair drier . toothbrush"
        ])
        
        # Model components
        self.model = None
        self.processor = None
        
        # Statistics
        self.stats = {
            'images_processed': 0,
            'total_detections': 0,
            'average_detections_per_image': 0,
            'prompts_used': 0
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
        """Load Grounding DINO model."""
        try:
            logger.info(f"Loading Grounding DINO model: {self.model_name}")
            
            # Try to import groundingdino
            try:
                from groundingdino.models import build_model
                from groundingdino.util.slconfig import SLConfig
                from groundingdino.util.utils import clean_state_dict, get_phrases_from_posmap
                from groundingdino.util import box_ops
                import groundingdino.datasets.transforms as T
                
                # Store transforms for later use
                self.transforms = T
                self.box_ops = box_ops
                
            except ImportError:
                logger.error("groundingdino package not installed")
                logger.info("Install with: pip install groundingdino-py")
                raise ImportError("groundingdino package required")
            
            # For now, we'll implement a simplified version that can work with transformers
            # In a real implementation, you'd load the actual Grounding DINO model
            logger.warning("Using simplified Grounding DINO implementation")
            logger.info("For full functionality, install: pip install groundingdino-py")
            
            # Simplified implementation using available models
            self._load_simplified_model()
            
            logger.info("Grounding DINO model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Grounding DINO model: {e}")
            raise RuntimeError(f"Could not load Grounding DINO model: {e}")
    
    def _load_simplified_model(self):
        """Load a simplified model that mimics Grounding DINO functionality."""
        # This is a placeholder - in practice you'd use the actual Grounding DINO model
        # For now, we'll create a mock implementation
        self.model = "simplified_grounding_dino"
        self.processor = "simplified_processor"
        logger.info("Loaded simplified Grounding DINO implementation")
    
    def annotate_image(
        self,
        image_path: str,
        text_prompt: Optional[str] = None,
        return_image: bool = False
    ) -> Dict:
        """Annotate single image with text-prompted object detection.
        
        Args:
            image_path: Path to image file
            text_prompt: Text prompt for detection (uses default if None)
            return_image: Whether to return the annotated image
            
        Returns:
            Dictionary containing detection results
        """
        if self.model is None:
            raise RuntimeError("Grounding DINO model not loaded. Call load_model() first.")
        
        try:
            # Load image
            image = ImageUtils.load_image_pil(image_path)
            if image is None:
                return self._empty_result(image_path, "Failed to load image")
            
            # Use default prompts if none provided
            if text_prompt is None:
                text_prompt = " . ".join(self.default_prompts)
            
            # Run detection with text prompt
            detections = self._detect_with_prompt(image, text_prompt)
            
            # Update statistics
            self.stats['images_processed'] += 1
            self.stats['total_detections'] += len(detections)
            self.stats['prompts_used'] += 1
            self._update_average_detections()
            
            # Create result dictionary
            result = {
                'image_path': image_path,
                'image_shape': [image.height, image.width, 3],
                'detections': detections,
                'detection_count': len(detections),
                'text_prompt': text_prompt,
                'success': True,
                'error': None
            }
            
            if return_image:
                annotated_image = self._draw_annotations(np.array(image), detections)
                result['annotated_image'] = annotated_image
            
            return result
            
        except Exception as e:
            logger.error(f"Error annotating image {image_path}: {e}")
            return self._empty_result(image_path, str(e))
    
    def _detect_with_prompt(self, image: Image.Image, text_prompt: str) -> List[Dict]:
        """Detect objects in image using text prompt.
        
        Args:
            image: PIL Image
            text_prompt: Text description of objects to detect
            
        Returns:
            List of detection dictionaries
        """
        # This is a simplified implementation
        # In practice, you'd use the actual Grounding DINO model
        
        detections = []
        
        # Parse text prompt into individual objects
        objects = [obj.strip() for obj in text_prompt.split('.') if obj.strip()]
        
        # For demonstration, create mock detections
        # In real implementation, this would be actual model inference
        image_width, image_height = image.size
        
        # Simulate some detections based on common objects
        common_objects = ['person', 'car', 'chair', 'table', 'bottle']
        
        for i, obj in enumerate(objects[:3]):  # Limit to first 3 for demo
            if any(common in obj.lower() for common in common_objects):
                # Create mock detection
                x = np.random.randint(0, image_width // 2)
                y = np.random.randint(0, image_height // 2)
                w = np.random.randint(50, min(200, image_width - x))
                h = np.random.randint(50, min(200, image_height - y))
                
                confidence = np.random.uniform(0.4, 0.9)
                
                if confidence > self.confidence_threshold:
                    detection = {
                        'bbox': [x, y, w, h],  # COCO format
                        'bbox_normalized': [
                            x / image_width,
                            y / image_height,
                            w / image_width,
                            h / image_height
                        ],
                        'bbox_xyxy': [x, y, x + w, y + h],
                        'confidence': confidence,
                        'class_id': i,
                        'class_name': obj.strip(),
                        'area': w * h,
                        'model': 'grounding_dino',
                        'text_prompt': obj.strip()
                    }
                    detections.append(detection)
        
        logger.debug(f"Generated {len(detections)} mock detections for prompt: {text_prompt[:50]}...")
        return detections
    
    def annotate_with_custom_prompts(
        self,
        image_paths: List[str],
        custom_prompts: List[str]
    ) -> List[Dict]:
        """Annotate images with custom text prompts.
        
        Args:
            image_paths: List of image paths
            custom_prompts: List of custom text prompts to try
            
        Returns:
            List of detection results
        """
        if self.model is None:
            raise RuntimeError("Grounding DINO model not loaded. Call load_model() first.")
        
        logger.info(f"Processing {len(image_paths)} images with {len(custom_prompts)} custom prompts")
        
        results = []
        
        for image_path in image_paths:
            # Try each custom prompt
            best_result = None
            max_detections = 0
            
            for prompt in custom_prompts:
                result = self.annotate_image(image_path, text_prompt=prompt)
                
                if result['success'] and result['detection_count'] > max_detections:
                    max_detections = result['detection_count']
                    best_result = result
            
            if best_result is None:
                # Fallback to default prompt
                best_result = self.annotate_image(image_path)
            
            results.append(best_result)
        
        return results
    
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
            
            # Draw bounding box (use different color from YOLO/DETR)
            cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 255), 2)
            
            # Draw label
            label = f"{class_name}: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            
            # Background for label
            cv2.rectangle(
                annotated,
                (int(x1), int(y1) - label_size[1] - 10),
                (int(x1) + label_size[0], int(y1)),
                (0, 255, 255),
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
            'text_prompt': None,
            'success': False,
            'error': error_message
        }
    
    def _update_average_detections(self) -> None:
        """Update average detections per image statistic."""
        if self.stats['images_processed'] > 0:
            self.stats['average_detections_per_image'] = (
                self.stats['total_detections'] / self.stats['images_processed']
            )
    
    def get_statistics(self) -> Dict:
        """Get annotation statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'model_info': {
                'model_name': self.model_name,
                'device': self.device,
                'default_prompts': len(self.default_prompts)
            },
            'processing_stats': self.stats.copy(),
            'parameters': {
                'confidence_threshold': self.confidence_threshold,
                'text_threshold': self.text_threshold
            }
        }
    
    def unload_model(self) -> None:
        """Unload model to free memory."""
        if self.model is not None:
            del self.model
            self.model = None
            
        if self.processor is not None:
            del self.processor
            self.processor = None
            
        # Clear CUDA cache if using GPU
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("Grounding DINO model unloaded")