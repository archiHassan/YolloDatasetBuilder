"""Multi-model ensemble system for combining multiple detection models."""

import numpy as np
from typing import List, Dict, Optional, Tuple, Any
import logging
from pathlib import Path

from ..annotation.yolo_annotator import YOLOAnnotator
from ..annotation.sam_annotator import SAMAnnotator
from ..annotation.detr_annotator import DETRAnnotator
from ..annotation.grounding_dino_annotator import GroundingDINOAnnotator
from ..annotation.clip_annotator import CLIPAnnotator
from ..annotation.blip_annotator import BLIPAnnotator
from .confidence_filter import ConfidenceFilter

logger = logging.getLogger(__name__)


class MultiModelEnsemble:
    """Multi-model ensemble system for improved detection accuracy."""
    
    def __init__(self, config: Dict):
        """Initialize multi-model ensemble.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.ensemble_config = config.get('ensemble', {})
        
        # Ensemble parameters
        self.voting_strategy = self.ensemble_config.get('voting_strategy', 'weighted_average')
        self.consensus_threshold = self.ensemble_config.get('consensus_threshold', 0.5)
        self.model_weights = self.ensemble_config.get('model_weights', {
            'yolo': 1.0,
            'detr': 0.8,
            'grounding_dino': 0.9,
            'sam': 0.7,  # Lower weight as SAM is used for refinement
            'clip': 0.6,  # Enhancement model
            'blip': 0.5   # Caption enhancement model
        })
        
        # Initialize models based on configuration
        self.models = {}
        self.active_models = []
        
        # Always include YOLO as the primary model
        self.models['yolo'] = YOLOAnnotator(config)
        self.active_models.append('yolo')
        
        # Optional models based on configuration
        model_configs = config.get('models', {})
        
        if model_configs.get('detr', {}).get('enabled', False):
            try:
                self.models['detr'] = DETRAnnotator(config)
                self.active_models.append('detr')
                logger.info("DETR model enabled in ensemble")
            except Exception as e:
                logger.warning(f"Failed to initialize DETR: {e}")
        
        if model_configs.get('grounding_dino', {}).get('enabled', False):
            try:
                self.models['grounding_dino'] = GroundingDINOAnnotator(config)
                self.active_models.append('grounding_dino')
                logger.info("Grounding DINO model enabled in ensemble")
            except Exception as e:
                logger.warning(f"Failed to initialize Grounding DINO: {e}")
        
        if model_configs.get('sam', {}).get('enabled', True):  # SAM enabled by default
            try:
                self.models['sam'] = SAMAnnotator(config)
                self.active_models.append('sam')
                logger.info("SAM model enabled in ensemble")
            except Exception as e:
                logger.warning(f"Failed to initialize SAM: {e}")
        
        if model_configs.get('clip', {}).get('enabled', False):
            try:
                self.models['clip'] = CLIPAnnotator(config)
                self.active_models.append('clip')
                logger.info("CLIP model enabled in ensemble")
            except Exception as e:
                logger.warning(f"Failed to initialize CLIP: {e}")
        
        if model_configs.get('blip', {}).get('enabled', False):
            try:
                self.models['blip'] = BLIPAnnotator(config)
                self.active_models.append('blip')
                logger.info("BLIP model enabled in ensemble")
            except Exception as e:
                logger.warning(f"Failed to initialize BLIP: {e}")
        
        # Initialize confidence filter
        self.confidence_filter = ConfidenceFilter(config)
        
        # Statistics
        self.stats = {
            'images_processed': 0,
            'total_detections': 0,
            'consensus_detections': 0,
            'model_agreement_rate': 0.0
        }
        
        logger.info(f"MultiModelEnsemble initialized with models: {self.active_models}")
    
    def load_models(self) -> None:
        """Load all active models."""
        logger.info("Loading ensemble models...")
        
        for model_name in self.active_models:
            try:
                logger.info(f"Loading {model_name} model...")
                self.models[model_name].load_model()
                logger.info(f"{model_name} model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load {model_name} model: {e}")
                # Remove failed model from active list
                if model_name in self.active_models:
                    self.active_models.remove(model_name)
        
        logger.info(f"Ensemble loaded with {len(self.active_models)} active models")
    
    def annotate_image(
        self, 
        image_path: str,
        use_sam_refinement: bool = True,
        use_clip_enhancement: bool = False
    ) -> Dict:
        """Annotate image using ensemble of models.
        
        Args:
            image_path: Path to image file
            use_sam_refinement: Whether to use SAM for mask refinement
            use_clip_enhancement: Whether to use CLIP for label enhancement
            
        Returns:
            Dictionary containing ensemble detection results
        """
        logger.debug(f"Processing image with ensemble: {image_path}")
        
        # Collect detections from all models
        model_results = {}
        all_detections = []
        
        # Primary detection models
        for model_name in ['yolo', 'detr', 'grounding_dino']:
            if model_name in self.active_models:
                try:
                    if model_name == 'grounding_dino':
                        result = self.models[model_name].annotate_image(image_path)
                    else:
                        result = self.models[model_name].annotate_image(image_path)
                    
                    if result['success']:
                        model_results[model_name] = result
                        all_detections.extend(result['detections'])
                        logger.debug(f"{model_name}: {len(result['detections'])} detections")
                    else:
                        logger.warning(f"{model_name} failed: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    logger.error(f"Error in {model_name} annotation: {e}")
        
        # Apply ensemble voting/consensus
        consensus_detections = self._apply_consensus(all_detections, model_results)
        
        # SAM refinement (if enabled and SAM is available)
        if use_sam_refinement and 'sam' in self.active_models:
            try:
                consensus_detections = self._apply_sam_refinement(
                    image_path, consensus_detections
                )
            except Exception as e:
                logger.warning(f"SAM refinement failed: {e}")
        
        # CLIP enhancement (if enabled and CLIP is available)
        if use_clip_enhancement and 'clip' in self.active_models:
            try:
                consensus_detections = self._apply_clip_enhancement(
                    image_path, consensus_detections
                )
            except Exception as e:
                logger.warning(f"CLIP enhancement failed: {e}")
        
        # Apply confidence filtering
        filtered_detections = self.confidence_filter.filter_detections(consensus_detections)
        
        # Update statistics
        self.stats['images_processed'] += 1
        self.stats['total_detections'] += len(all_detections)
        self.stats['consensus_detections'] += len(filtered_detections)
        self._update_agreement_rate(model_results)
        
        # Create result
        result = {
            'image_path': image_path,
            'detections': filtered_detections,
            'detection_count': len(filtered_detections),
            'ensemble_info': {
                'active_models': self.active_models,
                'model_detection_counts': {
                    name: len(result['detections']) 
                    for name, result in model_results.items()
                },
                'consensus_method': self.voting_strategy,
                'sam_refinement_used': use_sam_refinement and 'sam' in self.active_models,
                'clip_enhancement_used': use_clip_enhancement and 'clip' in self.active_models
            },
            'success': True,
            'error': None
        }
        
        return result
    
    def _apply_consensus(
        self, 
        all_detections: List[Dict], 
        model_results: Dict
    ) -> List[Dict]:
        """Apply consensus algorithm to combine detections from multiple models.
        
        Args:
            all_detections: All detections from all models
            model_results: Results from each model
            
        Returns:
            List of consensus detections
        """
        if not all_detections:
            return []
        
        if self.voting_strategy == 'weighted_average':
            return self._weighted_average_consensus(all_detections, model_results)
        elif self.voting_strategy == 'majority_vote':
            return self._majority_vote_consensus(all_detections, model_results)
        elif self.voting_strategy == 'highest_confidence':
            return self._highest_confidence_consensus(all_detections)
        else:
            logger.warning(f"Unknown voting strategy: {self.voting_strategy}, using weighted_average")
            return self._weighted_average_consensus(all_detections, model_results)
    
    def _weighted_average_consensus(
        self, 
        all_detections: List[Dict], 
        model_results: Dict
    ) -> List[Dict]:
        """Apply weighted average consensus."""
        # Group similar detections (using IoU threshold)
        detection_groups = self._group_similar_detections(all_detections)
        
        consensus_detections = []
        
        for group in detection_groups:
            if len(group) >= max(1, len(self.active_models) * self.consensus_threshold):
                # Calculate weighted average
                consensus_detection = self._calculate_weighted_average(group, model_results)
                consensus_detections.append(consensus_detection)
        
        return consensus_detections
    
    def _majority_vote_consensus(
        self, 
        all_detections: List[Dict], 
        model_results: Dict
    ) -> List[Dict]:
        """Apply majority vote consensus."""
        detection_groups = self._group_similar_detections(all_detections)
        
        consensus_detections = []
        min_votes = max(1, len(self.active_models) // 2 + 1)
        
        for group in detection_groups:
            if len(group) >= min_votes:
                # Take detection with highest confidence in the group
                best_detection = max(group, key=lambda x: x['confidence'])
                best_detection['consensus_votes'] = len(group)
                consensus_detections.append(best_detection)
        
        return consensus_detections
    
    def _highest_confidence_consensus(self, all_detections: List[Dict]) -> List[Dict]:
        """Apply highest confidence consensus (NMS-based)."""
        # Apply Non-Maximum Suppression to get best detections
        return self.confidence_filter._apply_nms(all_detections, iou_threshold=0.5)
    
    def _group_similar_detections(
        self, 
        detections: List[Dict], 
        iou_threshold: float = 0.5
    ) -> List[List[Dict]]:
        """Group similar detections using IoU threshold."""
        groups = []
        used = set()
        
        for i, det1 in enumerate(detections):
            if i in used:
                continue
                
            group = [det1]
            used.add(i)
            
            for j, det2 in enumerate(detections[i+1:], i+1):
                if j in used:
                    continue
                    
                # Check if same class and high IoU
                if (det1['class_name'] == det2['class_name'] and 
                    self._calculate_iou(det1['bbox'], det2['bbox']) > iou_threshold):
                    group.append(det2)
                    used.add(j)
            
            groups.append(group)
        
        return groups
    
    def _calculate_iou(self, bbox1: List[float], bbox2: List[float]) -> float:
        """Calculate IoU between two bounding boxes."""
        x1, y1, w1, h1 = bbox1
        x2, y2, w2, h2 = bbox2
        
        # Convert to x1, y1, x2, y2 format
        box1 = [x1, y1, x1 + w1, y1 + h1]
        box2 = [x2, y2, x2 + w2, y2 + h2]
        
        # Calculate intersection
        x_left = max(box1[0], box2[0])
        y_top = max(box1[1], box2[1])
        x_right = min(box1[2], box2[2])
        y_bottom = min(box1[3], box2[3])
        
        if x_right <= x_left or y_bottom <= y_top:
            return 0.0
        
        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        
        # Calculate union
        box1_area = w1 * h1
        box2_area = w2 * h2
        union_area = box1_area + box2_area - intersection_area
        
        return intersection_area / union_area if union_area > 0 else 0.0
    
    def _calculate_weighted_average(
        self, 
        group: List[Dict], 
        model_results: Dict
    ) -> Dict:
        """Calculate weighted average of detection group."""
        total_weight = 0
        weighted_bbox = [0, 0, 0, 0]
        weighted_confidence = 0
        class_name = group[0]['class_name']
        
        for detection in group:
            model_name = detection.get('model', 'unknown')
            weight = self.model_weights.get(model_name, 1.0)
            
            total_weight += weight
            
            # Weighted average of bbox
            bbox = detection['bbox']
            for i in range(4):
                weighted_bbox[i] += bbox[i] * weight
            
            # Weighted average of confidence
            weighted_confidence += detection['confidence'] * weight
        
        # Normalize by total weight
        if total_weight > 0:
            weighted_bbox = [coord / total_weight for coord in weighted_bbox]
            weighted_confidence /= total_weight
        
        # Create consensus detection
        x, y, w, h = weighted_bbox
        consensus_detection = {
            'bbox': weighted_bbox,
            'bbox_normalized': [
                x / 1000,  # Placeholder - should use actual image dimensions
                y / 1000,
                w / 1000,
                h / 1000
            ],
            'bbox_xyxy': [x, y, x + w, y + h],
            'confidence': weighted_confidence,
            'class_name': class_name,
            'area': w * h,
            'model': 'ensemble',
            'consensus_votes': len(group),
            'source_models': [det.get('model', 'unknown') for det in group]
        }
        
        return consensus_detection
    
    def _apply_sam_refinement(
        self, 
        image_path: str, 
        detections: List[Dict]
    ) -> List[Dict]:
        """Apply SAM refinement to improve detection masks."""
        if 'sam' not in self.models:
            return detections
        
        try:
            # Use SAM to refine bounding boxes with precise masks
            sam_result = self.models['sam'].annotate_image(image_path, detections)
            
            if sam_result['success']:
                return sam_result['detections']
            else:
                logger.warning("SAM refinement failed, using original detections")
                return detections
                
        except Exception as e:
            logger.error(f"SAM refinement error: {e}")
            return detections
    
    def _apply_clip_enhancement(
        self, 
        image_path: str, 
        detections: List[Dict]
    ) -> List[Dict]:
        """Apply CLIP enhancement to improve detection labels."""
        if 'clip' not in self.models:
            return detections
        
        try:
            # Use CLIP to enhance detection labels
            enhanced_detections = self.models['clip'].enhance_detection_labels(
                detections, image_path
            )
            return enhanced_detections
            
        except Exception as e:
            logger.error(f"CLIP enhancement error: {e}")
            return detections
    
    def _update_agreement_rate(self, model_results: Dict) -> None:
        """Update model agreement rate statistics."""
        if len(model_results) < 2:
            return
        
        # Simple agreement rate calculation
        # Count how many models detected at least one object
        detecting_models = sum(1 for result in model_results.values() 
                             if result['detection_count'] > 0)
        
        agreement_rate = detecting_models / len(model_results)
        
        # Running average
        n = self.stats['images_processed']
        current_rate = self.stats['model_agreement_rate']
        self.stats['model_agreement_rate'] = (
            (current_rate * (n - 1) + agreement_rate) / n
        )
    
    def get_statistics(self) -> Dict:
        """Get ensemble statistics."""
        return {
            'ensemble_info': {
                'active_models': self.active_models,
                'voting_strategy': self.voting_strategy,
                'model_weights': self.model_weights,
                'consensus_threshold': self.consensus_threshold
            },
            'processing_stats': self.stats.copy(),
            'individual_model_stats': {
                name: model.get_statistics() 
                for name, model in self.models.items() 
                if name in self.active_models
            }
        }
    
    def unload_models(self) -> None:
        """Unload all models to free memory."""
        for model_name, model in self.models.items():
            try:
                model.unload_model()
                logger.info(f"Unloaded {model_name} model")
            except Exception as e:
                logger.error(f"Error unloading {model_name}: {e}")
        
        logger.info("All ensemble models unloaded")