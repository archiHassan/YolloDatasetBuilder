"""Segment Anything Model (SAM) annotation module for segmentation."""

import torch
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
import logging
import urllib.request
import os

from ..utils.image_utils import ImageUtils

logger = logging.getLogger(__name__)


class SAMAnnotator:
    """Segment Anything Model (SAM) annotator for segmentation masks."""
    
    def __init__(self, config: Dict):
        """Initialize SAM annotator.
        
        Args:
            config: Configuration dictionary containing SAM settings
        """
        self.config = config
        self.model_config = config.get('models', {}).get('sam', {})
        
        # Model parameters
        self.model_type = self.model_config.get('model_type', 'vit_b')
        self.checkpoint_url = self.model_config.get('checkpoint_url')
        self.device = self._setup_device()
        
        # Model components
        self.sam_model = None
        self.mask_generator = None
        self.predictor = None
        
        # Model paths
        self.checkpoint_path = None
        
        # Statistics
        self.stats = {
            'images_processed': 0,
            'total_masks': 0,
            'average_masks_per_image': 0
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
    
    def _download_checkpoint(self) -> str:
        """Download SAM checkpoint if not exists.
        
        Returns:
            Path to checkpoint file
        """
        # Create models directory
        models_dir = Path("models")
        models_dir.mkdir(exist_ok=True)
        
        # Define checkpoint filename based on model type
        checkpoint_filenames = {
            'vit_b': 'sam_vit_b_01ec64.pth',
            'vit_l': 'sam_vit_l_0b3195.pth',
            'vit_h': 'sam_vit_h_4b8939.pth'
        }
        
        checkpoint_filename = checkpoint_filenames.get(self.model_type, 'sam_vit_b_01ec64.pth')
        checkpoint_path = models_dir / checkpoint_filename
        
        # Download if not exists
        if not checkpoint_path.exists():
            if not self.checkpoint_url:
                # Default URLs
                urls = {
                    'vit_b': 'https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth',
                    'vit_l': 'https://dl.fbaipublicfiles.com/segment_anything/sam_vit_l_0b3195.pth',
                    'vit_h': 'https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth'
                }
                self.checkpoint_url = urls.get(self.model_type)
            
            if self.checkpoint_url:
                logger.info(f"Downloading SAM checkpoint: {checkpoint_filename}")
                try:
                    urllib.request.urlretrieve(self.checkpoint_url, checkpoint_path)
                    logger.info("Checkpoint downloaded successfully")
                except Exception as e:
                    logger.error(f"Failed to download checkpoint: {e}")
                    raise RuntimeError(f"Could not download SAM checkpoint: {e}")
            else:
                raise ValueError(f"No checkpoint URL provided for model type: {self.model_type}")
        
        return str(checkpoint_path)
    
    def load_model(self) -> None:
        """Load SAM model."""
        try:
            # Import SAM (this would require segment-anything package)
            try:
                from segment_anything import sam_model_registry, SamAutomaticMaskGenerator, SamPredictor
            except ImportError:
                logger.error("segment-anything package not installed. Please install it first.")
                logger.info("Install with: pip install git+https://github.com/facebookresearch/segment-anything.git")
                raise ImportError("segment-anything package required")
            
            # Download checkpoint
            self.checkpoint_path = self._download_checkpoint()
            
            logger.info(f"Loading SAM model: {self.model_type}")
            
            # Load model
            self.sam_model = sam_model_registry[self.model_type](checkpoint=self.checkpoint_path)
            self.sam_model.to(device=self.device)
            
            # Initialize mask generator for automatic segmentation
            self.mask_generator = SamAutomaticMaskGenerator(self.sam_model)
            
            # Initialize predictor for prompt-based segmentation
            self.predictor = SamPredictor(self.sam_model)
            
            logger.info("SAM model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load SAM model: {e}")
            raise RuntimeError(f"Could not load SAM model: {e}")
    
    def generate_masks(self, image_path: str) -> Dict:
        """Generate segmentation masks for entire image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary containing mask results
        """
        if self.mask_generator is None:
            raise RuntimeError("SAM model not loaded. Call load_model() first.")
        
        try:
            # Load image in RGB format
            image = ImageUtils.load_image_pil(image_path)
            if image is None:
                return self._empty_result(image_path, "Failed to load image")
            
            # Convert to numpy array
            image_array = np.array(image)
            
            # Generate masks
            masks = self.mask_generator.generate(image_array)
            
            # Process masks
            processed_masks = self._process_masks(masks, image_array.shape)
            
            # Update statistics
            self.stats['images_processed'] += 1
            self.stats['total_masks'] += len(processed_masks)
            self._update_average_masks()
            
            result = {
                'image_path': image_path,
                'image_shape': image_array.shape,
                'masks': processed_masks,
                'mask_count': len(processed_masks),
                'success': True,
                'error': None
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating masks for {image_path}: {e}")
            return self._empty_result(image_path, str(e))
    
    def generate_masks_from_boxes(
        self,
        image_path: str,
        bounding_boxes: List[List[float]]
    ) -> Dict:
        """Generate segmentation masks from bounding box prompts.
        
        Args:
            image_path: Path to image file
            bounding_boxes: List of bounding boxes in [x, y, width, height] format
            
        Returns:
            Dictionary containing mask results
        """
        if self.predictor is None:
            raise RuntimeError("SAM model not loaded. Call load_model() first.")
        
        try:
            # Load image
            image = ImageUtils.load_image_pil(image_path)
            if image is None:
                return self._empty_result(image_path, "Failed to load image")
            
            image_array = np.array(image)
            
            # Set image for predictor
            self.predictor.set_image(image_array)
            
            masks = []
            for bbox in bounding_boxes:
                # Convert from [x, y, width, height] to [x1, y1, x2, y2]
                x, y, w, h = bbox
                box_prompt = np.array([x, y, x + w, y + h])
                
                # Generate mask
                mask_result, scores, logits = self.predictor.predict(
                    box=box_prompt,
                    multimask_output=False
                )
                
                if len(mask_result) > 0:
                    mask_data = {
                        'segmentation': mask_result[0],
                        'bbox': bbox,
                        'area': np.sum(mask_result[0]),
                        'stability_score': float(scores[0]) if len(scores) > 0 else 0.0,
                        'crop_box': [x, y, x + w, y + h]
                    }
                    masks.append(mask_data)
            
            # Update statistics
            self.stats['images_processed'] += 1
            self.stats['total_masks'] += len(masks)
            self._update_average_masks()
            
            result = {
                'image_path': image_path,
                'image_shape': image_array.shape,
                'masks': masks,
                'mask_count': len(masks),
                'success': True,
                'error': None
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating masks from boxes for {image_path}: {e}")
            return self._empty_result(image_path, str(e))
    
    def _process_masks(self, masks: List[Dict], image_shape: Tuple[int, int, int]) -> List[Dict]:
        """Process SAM mask results.
        
        Args:
            masks: Raw mask results from SAM
            image_shape: Image shape (H, W, C)
            
        Returns:
            Processed mask list
        """
        processed = []
        
        for mask_data in masks:
            # Extract mask information
            segmentation = mask_data['segmentation']
            bbox = mask_data['bbox']  # x, y, w, h
            area = mask_data['area']
            stability_score = mask_data.get('stability_score', 0.0)
            
            # Convert segmentation to RLE format for COCO
            rle = self._mask_to_rle(segmentation)
            
            processed_mask = {
                'segmentation': segmentation,  # Binary mask
                'segmentation_rle': rle,       # RLE format for COCO
                'bbox': bbox,                  # Bounding box
                'area': int(area),            # Mask area in pixels
                'stability_score': float(stability_score),
                'model': 'sam'
            }
            
            processed.append(processed_mask)
        
        # Sort by area (largest first)
        processed.sort(key=lambda x: x['area'], reverse=True)
        
        return processed
    
    def _mask_to_rle(self, mask: np.ndarray) -> Dict:
        """Convert binary mask to RLE (Run Length Encoding) format.
        
        Args:
            mask: Binary mask as numpy array
            
        Returns:
            RLE dictionary compatible with COCO format
        """
        # This is a simplified RLE implementation
        # For production, use pycocotools.mask.encode()
        
        # Flatten mask
        mask_flat = mask.flatten()
        
        # Find run lengths
        runs = []
        current_val = mask_flat[0]
        run_length = 1
        
        for i in range(1, len(mask_flat)):
            if mask_flat[i] == current_val:
                run_length += 1
            else:
                runs.append(run_length)
                current_val = mask_flat[i]
                run_length = 1
        runs.append(run_length)
        
        # COCO RLE format starts with 0s, so adjust if needed
        if mask_flat[0] == 1:
            runs = [0] + runs
        
        rle = {
            'counts': runs,
            'size': [mask.shape[0], mask.shape[1]]
        }
        
        return rle
    
    def combine_with_detections(
        self,
        detection_results: Dict,
        mask_results: Dict
    ) -> Dict:
        """Combine YOLO detections with SAM segmentation masks.
        
        Args:
            detection_results: Results from YOLO annotator
            mask_results: Results from SAM annotator
            
        Returns:
            Combined results with detections enhanced by segmentation
        """
        if not detection_results['success'] or not mask_results['success']:
            logger.warning("Cannot combine results - one or both failed")
            return detection_results
        
        detections = detection_results['detections']
        masks = mask_results['masks']
        
        enhanced_detections = []
        
        for detection in detections:
            # Find best matching mask based on IoU
            best_mask = self._find_best_matching_mask(detection['bbox'], masks)
            
            # Add mask information to detection
            enhanced_detection = detection.copy()
            if best_mask:
                enhanced_detection.update({
                    'segmentation': best_mask['segmentation'],
                    'segmentation_rle': best_mask['segmentation_rle'],
                    'mask_area': best_mask['area'],
                    'stability_score': best_mask['stability_score'],
                    'has_mask': True
                })
            else:
                enhanced_detection['has_mask'] = False
            
            enhanced_detections.append(enhanced_detection)
        
        # Update result
        combined_result = detection_results.copy()
        combined_result['detections'] = enhanced_detections
        combined_result['mask_count'] = len(masks)
        combined_result['enhanced_with_sam'] = True
        
        return combined_result
    
    def _find_best_matching_mask(
        self,
        detection_bbox: List[float],
        masks: List[Dict],
        min_iou: float = 0.3
    ) -> Optional[Dict]:
        """Find the best matching mask for a detection bounding box.
        
        Args:
            detection_bbox: Detection bounding box [x, y, width, height]
            masks: List of mask dictionaries
            min_iou: Minimum IoU threshold for matching
            
        Returns:
            Best matching mask or None
        """
        best_mask = None
        best_iou = min_iou
        
        for mask in masks:
            mask_bbox = mask['bbox']
            iou = self._calculate_bbox_iou(detection_bbox, mask_bbox)
            
            if iou > best_iou:
                best_iou = iou
                best_mask = mask
        
        return best_mask
    
    def _calculate_bbox_iou(self, bbox1: List[float], bbox2: List[float]) -> float:
        """Calculate IoU between two bounding boxes.
        
        Args:
            bbox1: First bounding box [x, y, width, height]
            bbox2: Second bounding box [x, y, width, height]
            
        Returns:
            IoU value
        """
        x1, y1, w1, h1 = bbox1
        x2, y2, w2, h2 = bbox2
        
        # Calculate intersection
        x_left = max(x1, x2)
        y_top = max(y1, y2)
        x_right = min(x1 + w1, x2 + w2)
        y_bottom = min(y1 + h1, y2 + h2)
        
        if x_right < x_left or y_bottom < y_top:
            return 0.0
        
        intersection = (x_right - x_left) * (y_bottom - y_top)
        
        # Calculate union
        area1 = w1 * h1
        area2 = w2 * h2
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def _update_average_masks(self) -> None:
        """Update average masks per image statistic."""
        if self.stats['images_processed'] > 0:
            self.stats['average_masks_per_image'] = (
                self.stats['total_masks'] / self.stats['images_processed']
            )
    
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
            'masks': [],
            'mask_count': 0,
            'success': False,
            'error': error_message
        }
    
    def get_statistics(self) -> Dict:
        """Get annotation statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'model_info': {
                'model_type': self.model_type,
                'device': self.device,
                'checkpoint_path': self.checkpoint_path
            },
            'processing_stats': self.stats.copy()
        }
    
    def unload_model(self) -> None:
        """Unload model to free memory."""
        if self.sam_model is not None:
            del self.sam_model
            self.sam_model = None
            self.mask_generator = None
            self.predictor = None
            
            # Clear CUDA cache if using GPU
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info("SAM model unloaded")