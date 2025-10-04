"""Non-Maximum Suppression utilities for detection filtering."""

import numpy as np
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class NonMaxSuppression:
    """Advanced Non-Maximum Suppression implementation with multiple strategies."""
    
    def __init__(self, iou_threshold: float = 0.5, score_threshold: float = 0.0):
        """Initialize NMS processor.
        
        Args:
            iou_threshold: IoU threshold for suppression
            score_threshold: Minimum score threshold
        """
        self.iou_threshold = iou_threshold
        self.score_threshold = score_threshold
    
    def apply_nms(
        self,
        detections: List[Dict],
        method: str = "standard"
    ) -> List[Dict]:
        """Apply Non-Maximum Suppression to detections.
        
        Args:
            detections: List of detection dictionaries
            method: NMS method ("standard", "soft", "adaptive")
            
        Returns:
            Filtered detections after NMS
        """
        if not detections:
            return []
        
        # Filter by score threshold first
        filtered_detections = [
            det for det in detections 
            if det.get('confidence', 0.0) >= self.score_threshold
        ]
        
        if not filtered_detections:
            return []
        
        # Apply the specified NMS method
        if method == "standard":
            return self._standard_nms(filtered_detections)
        elif method == "soft":
            return self._soft_nms(filtered_detections)
        elif method == "adaptive":
            return self._adaptive_nms(filtered_detections)
        else:
            raise ValueError(f"Unknown NMS method: {method}")
    
    def _standard_nms(self, detections: List[Dict]) -> List[Dict]:
        """Apply standard NMS algorithm.
        
        Args:
            detections: List of detection dictionaries
            
        Returns:
            Filtered detections
        """
        # Group by class
        class_groups = self._group_by_class(detections)
        
        final_detections = []
        
        for class_id, class_detections in class_groups.items():
            # Sort by confidence
            sorted_dets = sorted(
                class_detections,
                key=lambda x: x.get('confidence', 0.0),
                reverse=True
            )
            
            selected = []
            suppressed = set()
            
            for i, detection in enumerate(sorted_dets):
                if i in suppressed:
                    continue
                
                selected.append(detection)
                
                # Suppress overlapping detections
                for j in range(i + 1, len(sorted_dets)):
                    if j in suppressed:
                        continue
                    
                    iou = self._calculate_iou(
                        detection['bbox'],
                        sorted_dets[j]['bbox']
                    )
                    
                    if iou > self.iou_threshold:
                        suppressed.add(j)
            
            final_detections.extend(selected)
        
        return final_detections
    
    def _soft_nms(
        self,
        detections: List[Dict],
        sigma: float = 0.5
    ) -> List[Dict]:
        """Apply Soft-NMS algorithm that reduces scores instead of hard suppression.
        
        Args:
            detections: List of detection dictionaries
            sigma: Gaussian parameter for score reduction
            
        Returns:
            Filtered detections with adjusted scores
        """
        # Group by class
        class_groups = self._group_by_class(detections)
        
        final_detections = []
        
        for class_id, class_detections in class_groups.items():
            # Create working copy
            working_dets = [det.copy() for det in class_detections]
            
            selected = []
            
            while working_dets:
                # Find detection with highest score
                max_idx = max(
                    range(len(working_dets)),
                    key=lambda i: working_dets[i].get('confidence', 0.0)
                )
                
                max_det = working_dets.pop(max_idx)
                
                # Only keep if above threshold
                if max_det.get('confidence', 0.0) >= self.score_threshold:
                    selected.append(max_det)
                    
                    # Reduce scores of overlapping detections
                    for det in working_dets:
                        iou = self._calculate_iou(max_det['bbox'], det['bbox'])
                        
                        if iou > 0:
                            # Gaussian score reduction
                            weight = np.exp(-(iou * iou) / sigma)
                            det['confidence'] *= weight
            
            final_detections.extend(selected)
        
        return final_detections
    
    def _adaptive_nms(self, detections: List[Dict]) -> List[Dict]:
        """Apply adaptive NMS that adjusts threshold based on detection density.
        
        Args:
            detections: List of detection dictionaries
            
        Returns:
            Filtered detections
        """
        # Group by class
        class_groups = self._group_by_class(detections)
        
        final_detections = []
        
        for class_id, class_detections in class_groups.items():
            # Calculate adaptive threshold based on detection density
            adaptive_threshold = self._calculate_adaptive_threshold(class_detections)
            
            # Apply NMS with adaptive threshold
            selected = self._apply_nms_with_threshold(
                class_detections,
                adaptive_threshold
            )
            
            final_detections.extend(selected)
        
        return final_detections
    
    def _calculate_adaptive_threshold(self, detections: List[Dict]) -> float:
        """Calculate adaptive IoU threshold based on detection density.
        
        Args:
            detections: List of detections from the same class
            
        Returns:
            Adaptive IoU threshold
        """
        if len(detections) <= 2:
            return self.iou_threshold
        
        # Calculate average overlap between detections
        overlaps = []
        
        for i in range(len(detections)):
            for j in range(i + 1, len(detections)):
                iou = self._calculate_iou(
                    detections[i]['bbox'],
                    detections[j]['bbox']
                )
                overlaps.append(iou)
        
        if not overlaps:
            return self.iou_threshold
        
        avg_overlap = np.mean(overlaps)
        
        # Adjust threshold: lower threshold for high-density areas
        if avg_overlap > 0.3:
            adaptive_threshold = max(0.3, self.iou_threshold * 0.8)
        else:
            adaptive_threshold = self.iou_threshold
        
        return adaptive_threshold
    
    def _apply_nms_with_threshold(
        self,
        detections: List[Dict],
        threshold: float
    ) -> List[Dict]:
        """Apply NMS with specified threshold.
        
        Args:
            detections: List of detections
            threshold: IoU threshold for suppression
            
        Returns:
            Filtered detections
        """
        # Sort by confidence
        sorted_dets = sorted(
            detections,
            key=lambda x: x.get('confidence', 0.0),
            reverse=True
        )
        
        selected = []
        suppressed = set()
        
        for i, detection in enumerate(sorted_dets):
            if i in suppressed:
                continue
            
            selected.append(detection)
            
            # Suppress overlapping detections
            for j in range(i + 1, len(sorted_dets)):
                if j in suppressed:
                    continue
                
                iou = self._calculate_iou(
                    detection['bbox'],
                    sorted_dets[j]['bbox']
                )
                
                if iou > threshold:
                    suppressed.add(j)
        
        return selected
    
    def _group_by_class(self, detections: List[Dict]) -> Dict[int, List[Dict]]:
        """Group detections by class ID.
        
        Args:
            detections: List of detection dictionaries
            
        Returns:
            Dictionary mapping class IDs to detection lists
        """
        class_groups = {}
        
        for detection in detections:
            class_id = detection.get('class_id', 0)
            
            if class_id not in class_groups:
                class_groups[class_id] = []
            
            class_groups[class_id].append(detection)
        
        return class_groups
    
    def _calculate_iou(self, bbox1: List[float], bbox2: List[float]) -> float:
        """Calculate Intersection over Union between two bounding boxes.
        
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
    
    def apply_multi_class_nms(
        self,
        detections: List[Dict],
        class_agnostic: bool = False
    ) -> List[Dict]:
        """Apply NMS across multiple classes.
        
        Args:
            detections: List of detection dictionaries
            class_agnostic: Whether to apply NMS across all classes
            
        Returns:
            Filtered detections
        """
        if class_agnostic:
            # Apply NMS across all classes
            return self._standard_nms_all_classes(detections)
        else:
            # Apply NMS per class (standard behavior)
            return self._standard_nms(detections)
    
    def _standard_nms_all_classes(self, detections: List[Dict]) -> List[Dict]:
        """Apply NMS across all classes (class-agnostic).
        
        Args:
            detections: List of detection dictionaries
            
        Returns:
            Filtered detections
        """
        # Sort by confidence
        sorted_dets = sorted(
            detections,
            key=lambda x: x.get('confidence', 0.0),
            reverse=True
        )
        
        selected = []
        suppressed = set()
        
        for i, detection in enumerate(sorted_dets):
            if i in suppressed:
                continue
            
            selected.append(detection)
            
            # Suppress overlapping detections regardless of class
            for j in range(i + 1, len(sorted_dets)):
                if j in suppressed:
                    continue
                
                iou = self._calculate_iou(
                    detection['bbox'],
                    sorted_dets[j]['bbox']
                )
                
                if iou > self.iou_threshold:
                    suppressed.add(j)
        
        return selected
    
    def calculate_nms_statistics(
        self,
        original_detections: List[Dict],
        filtered_detections: List[Dict]
    ) -> Dict:
        """Calculate NMS filtering statistics.
        
        Args:
            original_detections: Detections before NMS
            filtered_detections: Detections after NMS
            
        Returns:
            Statistics dictionary
        """
        original_count = len(original_detections)
        filtered_count = len(filtered_detections)
        suppressed_count = original_count - filtered_count
        
        # Calculate per-class statistics
        original_classes = self._group_by_class(original_detections)
        filtered_classes = self._group_by_class(filtered_detections)
        
        class_stats = {}
        
        for class_id in original_classes:
            original_class_count = len(original_classes[class_id])
            filtered_class_count = len(filtered_classes.get(class_id, []))
            
            class_stats[class_id] = {
                'original_count': original_class_count,
                'filtered_count': filtered_class_count,
                'suppressed_count': original_class_count - filtered_class_count,
                'retention_rate': (filtered_class_count / original_class_count) * 100
                                if original_class_count > 0 else 0
            }
        
        statistics = {
            'total_original': original_count,
            'total_filtered': filtered_count,
            'total_suppressed': suppressed_count,
            'overall_retention_rate': (filtered_count / original_count) * 100
                                    if original_count > 0 else 0,
            'suppression_rate': (suppressed_count / original_count) * 100
                              if original_count > 0 else 0,
            'class_statistics': class_stats,
            'parameters': {
                'iou_threshold': self.iou_threshold,
                'score_threshold': self.score_threshold
            }
        }
        
        return statistics