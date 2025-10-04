"""Confidence filtering and quality assessment for annotations."""

import numpy as np
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ConfidenceFilter:
    """Filter and assess quality of annotations based on confidence and geometric constraints."""
    
    def __init__(self, config: Dict):
        """Initialize confidence filter.
        
        Args:
            config: Configuration dictionary containing filtering settings
        """
        self.config = config
        self.filtering_config = config.get('filtering', {})
        
        # Confidence filtering parameters
        confidence_config = self.filtering_config.get('confidence', {})
        self.min_confidence = confidence_config.get('min_confidence', 0.5)
        self.use_nms = confidence_config.get('use_nms', True)
        self.nms_threshold = confidence_config.get('nms_threshold', 0.5)
        
        # Box constraint parameters
        box_config = self.filtering_config.get('box_constraints', {})
        self.min_area = box_config.get('min_area', 100)
        self.max_area_ratio = box_config.get('max_area_ratio', 0.8)
        self.min_aspect_ratio = box_config.get('min_aspect_ratio', 0.1)
        self.max_aspect_ratio = box_config.get('max_aspect_ratio', 10.0)
        
        # Statistics
        self.stats = {
            'total_detections': 0,
            'confidence_filtered': 0,
            'area_filtered': 0,
            'aspect_ratio_filtered': 0,
            'nms_filtered': 0,
            'final_detections': 0
        }
    
    def filter_detections(
        self,
        detections: List[Dict],
        image_shape: Optional[Tuple[int, int, int]] = None
    ) -> List[Dict]:
        """Apply all filtering criteria to detections.
        
        Args:
            detections: List of detection dictionaries
            image_shape: Image shape (H, W, C) for area ratio calculations
            
        Returns:
            Filtered detections
        """
        if not detections:
            return []
        
        self.stats['total_detections'] += len(detections)
        
        # Step 1: Filter by confidence
        confidence_filtered = self._filter_by_confidence(detections)
        
        # Step 2: Filter by geometric constraints
        geometry_filtered = self._filter_by_geometry(confidence_filtered, image_shape)
        
        # Step 3: Apply Non-Maximum Suppression if enabled
        if self.use_nms:
            final_detections = self._apply_nms(geometry_filtered)
        else:
            final_detections = geometry_filtered
        
        self.stats['final_detections'] += len(final_detections)
        
        logger.debug(f"Filtered {len(detections)} -> {len(final_detections)} detections")
        return final_detections
    
    def _filter_by_confidence(self, detections: List[Dict]) -> List[Dict]:
        """Filter detections by confidence threshold.
        
        Args:
            detections: List of detection dictionaries
            
        Returns:
            Detections above confidence threshold
        """
        filtered = []
        
        for detection in detections:
            confidence = detection.get('confidence', 0.0)
            
            if confidence >= self.min_confidence:
                filtered.append(detection)
            else:
                self.stats['confidence_filtered'] += 1
        
        return filtered
    
    def _filter_by_geometry(
        self,
        detections: List[Dict],
        image_shape: Optional[Tuple[int, int, int]] = None
    ) -> List[Dict]:
        """Filter detections by geometric constraints.
        
        Args:
            detections: List of detection dictionaries
            image_shape: Image shape for area ratio calculations
            
        Returns:
            Geometrically valid detections
        """
        filtered = []
        
        for detection in detections:
            bbox = detection.get('bbox', [0, 0, 0, 0])  # [x, y, width, height]
            x, y, width, height = bbox
            
            # Check minimum area
            area = width * height
            if area < self.min_area:
                self.stats['area_filtered'] += 1
                continue
            
            # Check maximum area ratio (if image shape provided)
            if image_shape:
                image_height, image_width = image_shape[:2]
                image_area = image_height * image_width
                area_ratio = area / image_area
                
                if area_ratio > self.max_area_ratio:
                    self.stats['area_filtered'] += 1
                    continue
            
            # Check aspect ratio
            if height > 0:
                aspect_ratio = width / height
                
                if (aspect_ratio < self.min_aspect_ratio or 
                    aspect_ratio > self.max_aspect_ratio):
                    self.stats['aspect_ratio_filtered'] += 1
                    continue
            
            filtered.append(detection)
        
        return filtered
    
    def _apply_nms(self, detections: List[Dict]) -> List[Dict]:
        """Apply Non-Maximum Suppression to remove overlapping detections.
        
        Args:
            detections: List of detection dictionaries
            
        Returns:
            Detections after NMS
        """
        if len(detections) <= 1:
            return detections
        
        # Group detections by class
        class_groups = {}
        for detection in detections:
            class_id = detection.get('class_id', 0)
            if class_id not in class_groups:
                class_groups[class_id] = []
            class_groups[class_id].append(detection)
        
        # Apply NMS per class
        filtered_detections = []
        initial_count = len(detections)
        
        for class_id, class_detections in class_groups.items():
            nms_filtered = self._nms_single_class(class_detections)
            filtered_detections.extend(nms_filtered)
        
        self.stats['nms_filtered'] += initial_count - len(filtered_detections)
        
        return filtered_detections
    
    def _nms_single_class(self, detections: List[Dict]) -> List[Dict]:
        """Apply NMS to detections of a single class.
        
        Args:
            detections: List of detections from the same class
            
        Returns:
            Filtered detections after NMS
        """
        if len(detections) <= 1:
            return detections
        
        # Sort by confidence (highest first)
        sorted_detections = sorted(
            detections,
            key=lambda x: x.get('confidence', 0.0),
            reverse=True
        )
        
        selected = []
        suppressed = set()
        
        for i, detection in enumerate(sorted_detections):
            if i in suppressed:
                continue
            
            selected.append(detection)
            
            # Suppress overlapping detections
            for j in range(i + 1, len(sorted_detections)):
                if j in suppressed:
                    continue
                
                iou = self._calculate_iou(detection['bbox'], sorted_detections[j]['bbox'])
                
                if iou > self.nms_threshold:
                    suppressed.add(j)
        
        return selected
    
    def _calculate_iou(self, bbox1: List[float], bbox2: List[float]) -> float:
        """Calculate Intersection over Union (IoU) between two bounding boxes.
        
        Args:
            bbox1: First bounding box [x, y, width, height]
            bbox2: Second bounding box [x, y, width, height]
            
        Returns:
            IoU value between 0 and 1
        """
        x1, y1, w1, h1 = bbox1
        x2, y2, w2, h2 = bbox2
        
        # Calculate intersection coordinates
        x_left = max(x1, x2)
        y_top = max(y1, y2)
        x_right = min(x1 + w1, x2 + w2)
        y_bottom = min(y1 + h1, y2 + h2)
        
        # Check if there's no intersection
        if x_right < x_left or y_bottom < y_top:
            return 0.0
        
        # Calculate intersection area
        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        
        # Calculate union area
        area1 = w1 * h1
        area2 = w2 * h2
        union_area = area1 + area2 - intersection_area
        
        # Calculate IoU
        if union_area <= 0:
            return 0.0
        
        return intersection_area / union_area
    
    def assess_detection_quality(self, detection: Dict) -> Dict:
        """Assess the quality of a single detection.
        
        Args:
            detection: Detection dictionary
            
        Returns:
            Quality assessment dictionary
        """
        bbox = detection.get('bbox', [0, 0, 0, 0])
        confidence = detection.get('confidence', 0.0)
        area = detection.get('area', bbox[2] * bbox[3])
        
        # Calculate quality metrics
        quality_score = confidence  # Base score is confidence
        
        # Adjust for area (prefer medium-sized objects)
        if area > 0:
            # Normalize area score (optimal around 10000 pixels)
            optimal_area = 10000
            area_score = 1.0 - abs(np.log(area / optimal_area)) / 10
            area_score = max(0.0, min(1.0, area_score))
            quality_score *= (0.7 + 0.3 * area_score)
        
        # Adjust for aspect ratio (prefer balanced ratios)
        width, height = bbox[2], bbox[3]
        if height > 0:
            aspect_ratio = width / height
            # Optimal aspect ratio is around 1.0
            aspect_score = 1.0 - abs(np.log(aspect_ratio)) / 3
            aspect_score = max(0.0, min(1.0, aspect_score))
            quality_score *= (0.8 + 0.2 * aspect_score)
        
        quality_assessment = {
            'overall_score': quality_score,
            'confidence_score': confidence,
            'area_score': area_score if area > 0 else 0.0,
            'aspect_score': aspect_score if height > 0 else 0.0,
            'quality_tier': self._get_quality_tier(quality_score)
        }
        
        return quality_assessment
    
    def _get_quality_tier(self, score: float) -> str:
        """Get quality tier based on score.
        
        Args:
            score: Quality score between 0 and 1
            
        Returns:
            Quality tier string
        """
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "fair"
        else:
            return "poor"
    
    def filter_by_quality_tier(
        self,
        detections: List[Dict],
        min_tier: str = "fair"
    ) -> List[Dict]:
        """Filter detections by quality tier.
        
        Args:
            detections: List of detection dictionaries
            min_tier: Minimum quality tier to keep
            
        Returns:
            Filtered detections
        """
        tier_hierarchy = {"poor": 0, "fair": 1, "good": 2, "excellent": 3}
        min_tier_value = tier_hierarchy.get(min_tier, 1)
        
        filtered = []
        
        for detection in detections:
            quality = self.assess_detection_quality(detection)
            detection['quality_assessment'] = quality
            
            tier_value = tier_hierarchy.get(quality['quality_tier'], 0)
            
            if tier_value >= min_tier_value:
                filtered.append(detection)
        
        return filtered
    
    def get_filtering_report(self) -> Dict:
        """Generate filtering statistics report.
        
        Returns:
            Report dictionary with filtering statistics
        """
        total = self.stats['total_detections']
        
        report = {
            'total_input_detections': total,
            'final_detections': self.stats['final_detections'],
            'filtered_counts': {
                'confidence_filtered': self.stats['confidence_filtered'],
                'area_filtered': self.stats['area_filtered'],
                'aspect_ratio_filtered': self.stats['aspect_ratio_filtered'],
                'nms_filtered': self.stats['nms_filtered']
            },
            'filtering_rates': {},
            'configuration': {
                'min_confidence': self.min_confidence,
                'use_nms': self.use_nms,
                'nms_threshold': self.nms_threshold,
                'min_area': self.min_area,
                'max_area_ratio': self.max_area_ratio,
                'min_aspect_ratio': self.min_aspect_ratio,
                'max_aspect_ratio': self.max_aspect_ratio
            }
        }
        
        # Calculate filtering rates
        if total > 0:
            for key, value in self.stats.items():
                if key.endswith('_filtered'):
                    rate_key = key.replace('_filtered', '_rate')
                    report['filtering_rates'][rate_key] = (value / total) * 100
            
            report['retention_rate'] = (self.stats['final_detections'] / total) * 100
        
        return report
    
    def reset_statistics(self) -> None:
        """Reset filtering statistics."""
        for key in self.stats:
            self.stats[key] = 0
    
    def update_thresholds(self, **kwargs) -> None:
        """Update filtering thresholds.
        
        Args:
            **kwargs: Threshold parameters to update
        """
        if 'min_confidence' in kwargs:
            self.min_confidence = kwargs['min_confidence']
        if 'nms_threshold' in kwargs:
            self.nms_threshold = kwargs['nms_threshold']
        if 'min_area' in kwargs:
            self.min_area = kwargs['min_area']
        if 'max_area_ratio' in kwargs:
            self.max_area_ratio = kwargs['max_area_ratio']
        if 'min_aspect_ratio' in kwargs:
            self.min_aspect_ratio = kwargs['min_aspect_ratio']
        if 'max_aspect_ratio' in kwargs:
            self.max_aspect_ratio = kwargs['max_aspect_ratio']
        
        logger.info("Filtering thresholds updated")