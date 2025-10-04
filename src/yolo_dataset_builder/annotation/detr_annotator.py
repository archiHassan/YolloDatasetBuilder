"""DETR (Detection Transformer) annotation module."""

import torch
import cv2
import numpy as np
from transformers import DetrImageProcessor, DetrForObjectDetection
from PIL import Image
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
import logging

from ..utils.image_utils import ImageUtils

logger = logging.getLogger(__name__)


class DETRAnnotator:
    """DETR-based object detection annotator using Transformers."""
    
    def __init__(self, config: Dict):
        """Initialize DETR annotator.
        
        Args:
            config: Configuration dictionary containing DETR settings
        """
        self.config = config
        self.model_config = config.get('models', {}).get('detr', {})
        
        # Model parameters
        self.model_name = self.model_config.get('model_name', 'facebook/detr-resnet-50')
        self.confidence_threshold = self.model_config.get('confidence_threshold', 0.7)
        self.device = self._setup_device()
        
        # Model components
        self.processor = None
        self.model = None
        self.class_names = None
        
        # Statistics
        self.stats = {
            'images_processed': 0,
            'total_detections': 0,
            'average_detections_per_image': 0
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
        """Load DETR model and processor."""
        try:
            logger.info(f"Loading DETR model: {self.model_name}")
            
            # Load processor and model
            self.processor = DetrImageProcessor.from_pretrained(self.model_name)
            self.model = DetrForObjectDetection.from_pretrained(self.model_name)
            
            # Move to device
            self.model.to(self.device)
            self.model.eval()
            
            # Get class names from model config
            self.class_names = self.model.config.id2label
            
            logger.info(f"DETR model loaded successfully with {len(self.class_names)} classes")
            logger.debug(f"Available classes: {list(self.class_names.values())}")
            
        except Exception as e:
            logger.error(f"Failed to load DETR model: {e}")
            raise RuntimeError(f"Could not load DETR model: {e}")
    
    def annotate_image(
        self,
        image_path: str,
        return_image: bool = False
    ) -> Dict:
        """Annotate single image with DETR object detection.
        
        Args:
            image_path: Path to image file
            return_image: Whether to return the annotated image
            
        Returns:
            Dictionary containing detection results
        """
        if self.model is None:
            raise RuntimeError("DETR model not loaded. Call load_model() first.")
        
        try:
            # Load image
            image = ImageUtils.load_image_pil(image_path)
            if image is None:
                return self._empty_result(image_path, "Failed to load image")
            
            # Preprocess image
            inputs = self.processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Run inference
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Process results
            detections = self._process_results(outputs, image.size)
            
            # Update statistics
            self.stats['images_processed'] += 1
            self.stats['total_detections'] += len(detections)
            self._update_average_detections()
            
            # Create result dictionary
            result = {
                'image_path': image_path,
                'image_shape': [image.height, image.width, 3],
                'detections': detections,
                'detection_count': len(detections),
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
    
    def annotate_batch(
        self,
        image_paths: List[str],
        batch_size: int = 8
    ) -> List[Dict]:
        """Annotate multiple images in batches.
        
        Args:
            image_paths: List of image paths
            batch_size: Number of images to process in each batch
            
        Returns:
            List of detection results
        """
        if self.model is None:
            raise RuntimeError("DETR model not loaded. Call load_model() first.")
        
        logger.info(f"Processing {len(image_paths)} images in batches of {batch_size}")
        
        results = []
        
        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i:i + batch_size]
            logger.debug(f"Processing batch {i//batch_size + 1}: {len(batch_paths)} images")
            
            # Process batch
            batch_results = self._process_batch(batch_paths)
            results.extend(batch_results)
            
            # Log progress
            processed = min(i + batch_size, len(image_paths))
            logger.info(f"Processed {processed}/{len(image_paths)} images")
        
        logger.info("DETR batch annotation completed")
        return results
    
    def _process_batch(self, image_paths: List[str]) -> List[Dict]:
        """Process a batch of images.
        
        Args:
            image_paths: List of image paths in the batch
            
        Returns:
            List of detection results
        """
        try:
            # Load all images in batch
            images = []
            valid_paths = []
            
            for image_path in image_paths:
                image = ImageUtils.load_image_pil(image_path)
                if image is not None:
                    images.append(image)
                    valid_paths.append(image_path)
            
            if not images:
                return [self._empty_result(path, "Failed to load image") for path in image_paths]
            
            # Preprocess batch
            inputs = self.processor(images=images, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Run inference on batch
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Process results for each image in batch
            results = []
            for i, (image_path, image) in enumerate(zip(valid_paths, images)):
                # Extract outputs for this image
                image_outputs = {
                    'logits': outputs.logits[i:i+1],
                    'pred_boxes': outputs.pred_boxes[i:i+1]
                }
                
                detections = self._process_results(image_outputs, image.size)
                
                result = {
                    'image_path': image_path,
                    'image_shape': [image.height, image.width, 3],
                    'detections': detections,
                    'detection_count': len(detections),
                    'success': True,
                    'error': None
                }
                results.append(result)
                
                # Update statistics
                self.stats['images_processed'] += 1
                self.stats['total_detections'] += len(detections)
            
            self._update_average_detections()
            return results
            
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            return [self._empty_result(path, str(e)) for path in image_paths]
    
    def _process_results(self, outputs, image_size: Tuple[int, int]) -> List[Dict]:
        """Process DETR model outputs.
        
        Args:
            outputs: DETR model outputs
            image_size: Image size (width, height)
            
        Returns:
            List of detection dictionaries
        """
        detections = []
        
        # Get predictions
        target_sizes = torch.tensor([image_size[::-1]]).to(self.device)  # (height, width)
        results = self.processor.post_process_object_detection(
            outputs, 
            target_sizes=target_sizes, 
            threshold=self.confidence_threshold
        )[0]
        
        # Convert to our format
        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
            score = float(score)
            label = int(label)
            box = box.cpu().numpy()
            
            # Convert box format [x1, y1, x2, y2] to [x, y, width, height]
            x1, y1, x2, y2 = box
            width = x2 - x1
            height = y2 - y1
            
            # Get class name
            class_name = self.class_names.get(label, f"class_{label}")
            
            detection = {
                'bbox': [x1, y1, width, height],  # COCO format
                'bbox_normalized': [
                    x1 / image_size[0],
                    y1 / image_size[1], 
                    width / image_size[0],
                    height / image_size[1]
                ],
                'bbox_xyxy': [x1, y1, x2, y2],  # For visualization
                'confidence': score,
                'class_id': label,
                'class_name': class_name,
                'area': width * height,
                'model': 'detr'
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
            cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2)
            
            # Draw label
            label = f"{class_name}: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            
            # Background for label
            cv2.rectangle(
                annotated,
                (int(x1), int(y1) - label_size[1] - 10),
                (int(x1) + label_size[0], int(y1)),
                (255, 0, 0),
                -1
            )
            
            # Text
            cv2.putText(
                annotated,
                label,
                (int(x1), int(y1) - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
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
                'num_classes': len(self.class_names) if self.class_names else 0,
                'class_names': list(self.class_names.values()) if self.class_names else []
            },
            'processing_stats': self.stats.copy(),
            'parameters': {
                'confidence_threshold': self.confidence_threshold
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
        
        logger.info("DETR model unloaded")