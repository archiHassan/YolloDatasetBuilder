"""
Annotation priority scoring for active learning.
"""

import logging
from typing import Dict, List, Tuple, Optional, Any, Union
import numpy as np
from pathlib import Path
import json
from collections import defaultdict, Counter
from datetime import datetime

logger = logging.getLogger(__name__)


class PriorityScorer:
    """System for scoring annotation priority based on multiple factors."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize priority scorer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.priority_config = config.get('priority_scoring', {})
        
        # Scoring weights
        self.weights = {
            'uncertainty': self.priority_config.get('uncertainty_weight', 0.4),
            'diversity': self.priority_config.get('diversity_weight', 0.2),
            'representativeness': self.priority_config.get('representativeness_weight', 0.2),
            'rarity': self.priority_config.get('rarity_weight', 0.1),
            'quality': self.priority_config.get('quality_weight', 0.1)
        }
        
        # Normalization method
        self.normalization_method = self.priority_config.get('normalization', 'min_max')
        
        # Priority boosting factors
        self.boost_factors = {
            'new_categories': self.priority_config.get('new_category_boost', 1.5),
            'error_prone': self.priority_config.get('error_prone_boost', 1.3),
            'high_impact': self.priority_config.get('high_impact_boost', 1.2)
        }
        
        # Statistics tracking
        self.scoring_history = []
        self.category_stats = defaultdict(lambda: {'count': 0, 'avg_priority': 0.0})
        self.feature_importance = defaultdict(list)
        
        logger.info("Initialized annotation priority scorer")
    
    def score_samples(self, 
                     samples: List[Dict[str, Any]], 
                     predictions: List[Dict[str, Any]],
                     metadata: Optional[List[Dict[str, Any]]] = None) -> List[Tuple[int, float, Dict[str, float]]]:
        """
        Score samples for annotation priority.
        
        Args:
            samples: List of sample data
            predictions: Model predictions for samples
            metadata: Optional metadata for each sample
            
        Returns:
            List of (sample_index, priority_score, score_breakdown) tuples
        """
        if len(samples) != len(predictions):
            raise ValueError("Number of samples must match number of predictions")
        
        if metadata is None:
            metadata = [{}] * len(samples)
        
        scored_samples = []
        
        for i, (sample, prediction, meta) in enumerate(zip(samples, predictions, metadata)):
            # Calculate individual score components
            scores = self._calculate_component_scores(sample, prediction, meta, i)
            
            # Calculate weighted priority score
            priority_score = self._calculate_weighted_score(scores)
            
            # Apply boosting factors
            priority_score = self._apply_boosting_factors(priority_score, sample, prediction, meta)
            
            scored_samples.append((i, priority_score, scores))
            
            # Update statistics
            self._update_category_stats(prediction, priority_score)
        
        # Normalize scores if requested
        if self.normalization_method:
            scored_samples = self._normalize_scores(scored_samples)
        
        # Sort by priority (descending)
        scored_samples.sort(key=lambda x: x[1], reverse=True)
        
        # Update scoring history
        self._update_scoring_history(scored_samples)
        
        logger.info(f"Scored {len(scored_samples)} samples for annotation priority")
        return scored_samples
    
    def get_top_priority_samples(self, 
                                scored_samples: List[Tuple[int, float, Dict[str, float]]], 
                                num_samples: int,
                                diversity_threshold: float = 0.1) -> List[Tuple[int, float, Dict[str, float]]]:
        """
        Get top priority samples with diversity constraint.
        
        Args:
            scored_samples: Scored samples from score_samples()
            num_samples: Number of samples to select
            diversity_threshold: Minimum diversity threshold
            
        Returns:
            List of selected high-priority samples
        """
        if num_samples >= len(scored_samples):
            return scored_samples
        
        selected_samples = []
        candidate_pool = scored_samples.copy()
        
        # Always select the highest priority sample first
        if candidate_pool:
            selected_samples.append(candidate_pool.pop(0))
        
        # Select remaining samples with diversity constraint
        while len(selected_samples) < num_samples and candidate_pool:
            best_candidate = None
            best_score = -1
            
            for candidate in candidate_pool:
                # Calculate diversity with already selected samples
                diversity_score = self._calculate_diversity_with_selected(
                    candidate, selected_samples, scored_samples
                )
                
                # Combine priority and diversity
                combined_score = candidate[1] + diversity_threshold * diversity_score
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_candidate = candidate
            
            if best_candidate:
                selected_samples.append(best_candidate)
                candidate_pool.remove(best_candidate)
        
        logger.info(f"Selected {len(selected_samples)} top priority samples with diversity constraint")
        return selected_samples
    
    def analyze_priority_factors(self, 
                                scored_samples: List[Tuple[int, float, Dict[str, float]]]) -> Dict[str, Any]:
        """
        Analyze which factors contribute most to priority scores.
        
        Args:
            scored_samples: Scored samples
            
        Returns:
            Analysis results
        """
        if not scored_samples:
            return {}
        
        # Extract scores by component
        component_scores = defaultdict(list)
        priority_scores = []
        
        for _, priority, breakdown in scored_samples:
            priority_scores.append(priority)
            for component, score in breakdown.items():
                component_scores[component].append(score)
        
        # Calculate correlations
        correlations = {}
        for component, scores in component_scores.items():
            if len(scores) > 1:
                correlation = np.corrcoef(scores, priority_scores)[0, 1]
                correlations[component] = correlation if not np.isnan(correlation) else 0.0
        
        # Calculate feature importance (variance contribution)
        feature_importance = {}
        total_variance = np.var(priority_scores) if len(priority_scores) > 1 else 0
        
        for component, scores in component_scores.items():
            if len(scores) > 1:
                weighted_scores = [score * self.weights.get(component, 0) for score in scores]
                component_variance = np.var(weighted_scores)
                feature_importance[component] = (component_variance / total_variance 
                                               if total_variance > 0 else 0)
        
        return {
            'component_statistics': {
                component: {
                    'mean': float(np.mean(scores)),
                    'std': float(np.std(scores)),
                    'min': float(np.min(scores)),
                    'max': float(np.max(scores))
                }
                for component, scores in component_scores.items()
            },
            'correlations_with_priority': correlations,
            'feature_importance': feature_importance,
            'priority_statistics': {
                'mean': float(np.mean(priority_scores)),
                'std': float(np.std(priority_scores)),
                'min': float(np.min(priority_scores)),
                'max': float(np.max(priority_scores))
            }
        }
    
    def update_weights(self, new_weights: Dict[str, float]):
        """Update scoring weights based on feedback."""
        # Normalize weights to sum to 1
        total_weight = sum(new_weights.values())
        if total_weight > 0:
            self.weights.update({k: v / total_weight for k, v in new_weights.items()})
            logger.info(f"Updated scoring weights: {self.weights}")
    
    def export_scoring_analysis(self, filepath: str):
        """Export scoring analysis to file."""
        analysis_data = {
            'weights': self.weights,
            'boost_factors': self.boost_factors,
            'scoring_history': self.scoring_history,
            'category_stats': dict(self.category_stats),
            'feature_importance_history': dict(self.feature_importance),
            'config': self.priority_config
        }
        
        with open(filepath, 'w') as f:
            json.dump(analysis_data, f, indent=2)
        
        logger.info(f"Exported scoring analysis to {filepath}")
    
    def _calculate_component_scores(self, 
                                   sample: Dict[str, Any], 
                                   prediction: Dict[str, Any], 
                                   metadata: Dict[str, Any],
                                   sample_idx: int) -> Dict[str, float]:
        """Calculate individual component scores."""
        scores = {}
        
        # 1. Uncertainty score
        scores['uncertainty'] = self._calculate_uncertainty_score(prediction)
        
        # 2. Diversity score
        scores['diversity'] = self._calculate_diversity_score(sample, prediction, metadata)
        
        # 3. Representativeness score
        scores['representativeness'] = self._calculate_representativeness_score(sample, prediction)
        
        # 4. Rarity score
        scores['rarity'] = self._calculate_rarity_score(prediction)
        
        # 5. Quality score
        scores['quality'] = self._calculate_quality_score(sample, prediction, metadata)
        
        return scores
    
    def _calculate_uncertainty_score(self, prediction: Dict[str, Any]) -> float:
        """Calculate uncertainty-based score."""
        if 'confidence' in prediction:
            return 1.0 - prediction['confidence']
        elif 'annotations' in prediction:
            confidences = [ann.get('confidence', 0.0) for ann in prediction['annotations']]
            if confidences:
                # Use entropy of confidence distribution
                return self._calculate_entropy(confidences)
        
        return 1.0  # Maximum uncertainty for unknown format
    
    def _calculate_diversity_score(self, 
                                  sample: Dict[str, Any], 
                                  prediction: Dict[str, Any], 
                                  metadata: Dict[str, Any]) -> float:
        """Calculate diversity-based score."""
        diversity_factors = []
        
        # Category diversity
        if 'annotations' in prediction:
            categories = [ann.get('category', '') for ann in prediction['annotations']]
            unique_categories = len(set(categories))
            total_categories = len(categories)
            if total_categories > 0:
                category_diversity = unique_categories / total_categories
                diversity_factors.append(category_diversity)
        
        # Image property diversity (if available)
        if 'image_properties' in metadata:
            props = metadata['image_properties']
            # Normalize image dimensions, aspect ratio, etc.
            if 'width' in props and 'height' in props:
                aspect_ratio = props['width'] / props['height']
                # Score based on how different this aspect ratio is from square (1.0)
                aspect_diversity = abs(aspect_ratio - 1.0) / max(aspect_ratio, 1.0)
                diversity_factors.append(min(aspect_diversity, 1.0))
        
        return np.mean(diversity_factors) if diversity_factors else 0.5
    
    def _calculate_representativeness_score(self, 
                                          sample: Dict[str, Any], 
                                          prediction: Dict[str, Any]) -> float:
        """Calculate representativeness score."""
        # This is a simplified version - in practice, you'd use feature embeddings
        # to calculate how representative this sample is of the dataset distribution
        
        # For now, use number of objects as a proxy for representativeness
        if 'annotations' in prediction:
            num_objects = len(prediction['annotations'])
            # Prefer samples with moderate number of objects (2-5)
            if 2 <= num_objects <= 5:
                return 1.0
            elif num_objects == 1 or num_objects == 6:
                return 0.8
            else:
                return 0.5
        
        return 0.5
    
    def _calculate_rarity_score(self, prediction: Dict[str, Any]) -> float:
        """Calculate rarity-based score."""
        rarity_factors = []
        
        if 'annotations' in prediction:
            for ann in prediction['annotations']:
                category = ann.get('category', '')
                if category:
                    # Use category statistics to determine rarity
                    category_count = self.category_stats[category]['count']
                    # Rare categories get higher scores
                    rarity = 1.0 / (1.0 + category_count * 0.1)
                    rarity_factors.append(rarity)
        
        return max(rarity_factors) if rarity_factors else 0.5
    
    def _calculate_quality_score(self, 
                                sample: Dict[str, Any], 
                                prediction: Dict[str, Any], 
                                metadata: Dict[str, Any]) -> float:
        """Calculate quality-based score."""
        quality_factors = []
        
        # Image quality indicators
        if 'image_properties' in metadata:
            props = metadata['image_properties']
            
            # Resolution quality
            if 'width' in props and 'height' in props:
                resolution = props['width'] * props['height']
                # Prefer medium to high resolution (not too low, not excessively high)
                if resolution >= 480 * 640:  # Decent resolution
                    quality_factors.append(0.8)
                else:
                    quality_factors.append(0.4)
            
            # File size as quality indicator
            if 'file_size' in props:
                size_mb = props['file_size'] / (1024 * 1024)
                if 0.1 <= size_mb <= 10:  # Reasonable file size
                    quality_factors.append(0.8)
                else:
                    quality_factors.append(0.4)
        
        # Prediction quality
        if 'annotations' in prediction:
            confidences = [ann.get('confidence', 0.0) for ann in prediction['annotations']]
            if confidences:
                avg_confidence = np.mean(confidences)
                # Prefer medium confidence (indicates interesting cases)
                if 0.3 <= avg_confidence <= 0.7:
                    quality_factors.append(0.9)
                elif 0.1 <= avg_confidence < 0.3 or 0.7 < avg_confidence <= 0.9:
                    quality_factors.append(0.7)
                else:
                    quality_factors.append(0.5)
        
        return np.mean(quality_factors) if quality_factors else 0.5
    
    def _calculate_weighted_score(self, scores: Dict[str, float]) -> float:
        """Calculate weighted priority score."""
        weighted_score = 0.0
        total_weight = 0.0
        
        for component, score in scores.items():
            weight = self.weights.get(component, 0.0)
            weighted_score += score * weight
            total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _apply_boosting_factors(self, 
                               priority_score: float, 
                               sample: Dict[str, Any], 
                               prediction: Dict[str, Any], 
                               metadata: Dict[str, Any]) -> float:
        """Apply boosting factors to priority score."""
        boosted_score = priority_score
        
        # New category boost
        if self._is_new_category(prediction):
            boosted_score *= self.boost_factors['new_categories']
        
        # Error-prone sample boost
        if self._is_error_prone(sample, prediction, metadata):
            boosted_score *= self.boost_factors['error_prone']
        
        # High impact boost
        if self._is_high_impact(sample, prediction, metadata):
            boosted_score *= self.boost_factors['high_impact']
        
        return min(boosted_score, 2.0)  # Cap at 2.0 to prevent extreme scores
    
    def _is_new_category(self, prediction: Dict[str, Any]) -> bool:
        """Check if prediction contains new/rare categories."""
        if 'annotations' in prediction:
            for ann in prediction['annotations']:
                category = ann.get('category', '')
                if category and self.category_stats[category]['count'] < 5:
                    return True
        return False
    
    def _is_error_prone(self,
                       sample: Dict[str, Any],
                       prediction: Dict[str, Any],
                       metadata: Dict[str, Any]) -> bool:
        """Check if sample is likely to be error-prone."""
        # This is a heuristic - in practice, you'd use historical error data

        if 'annotations' in prediction:
            # Multiple conflicting predictions
            categories = [ann.get('category', '') for ann in prediction['annotations']]
            confidences = [ann.get('confidence', 0.0) for ann in prediction['annotations']]

            # Skip if no annotations present
            if len(categories) == 0:
                return False

            # High disagreement in categories
            if len(set(categories)) / len(categories) > 0.7:
                return True

            # Low confidence with multiple predictions
            if len(confidences) > 1 and np.mean(confidences) < 0.4:
                return True

        return False
    
    def _is_high_impact(self, 
                       sample: Dict[str, Any], 
                       prediction: Dict[str, Any], 
                       metadata: Dict[str, Any]) -> bool:
        """Check if sample is high-impact for learning."""
        # This could be based on feature importance, model disagreement, etc.
        # For now, use a simple heuristic
        
        if 'annotations' in prediction:
            num_objects = len(prediction['annotations'])
            # Complex scenes with multiple objects
            if num_objects >= 3:
                return True
        
        return False
    
    def _calculate_diversity_with_selected(self, 
                                          candidate: Tuple[int, float, Dict[str, float]], 
                                          selected_samples: List[Tuple[int, float, Dict[str, float]]],
                                          all_samples: List[Tuple[int, float, Dict[str, float]]]) -> float:
        """Calculate diversity of candidate with already selected samples."""
        if not selected_samples:
            return 1.0
        
        # Simple diversity based on score differences
        candidate_scores = candidate[2]
        diversities = []
        
        for selected_sample in selected_samples:
            selected_scores = selected_sample[2]
            
            # Calculate Euclidean distance in score space
            distance = 0.0
            for component in candidate_scores:
                if component in selected_scores:
                    distance += (candidate_scores[component] - selected_scores[component]) ** 2
            
            diversity = np.sqrt(distance)
            diversities.append(diversity)
        
        # Return average diversity
        return np.mean(diversities)
    
    def _normalize_scores(self, 
                         scored_samples: List[Tuple[int, float, Dict[str, float]]]) -> List[Tuple[int, float, Dict[str, float]]]:
        """Normalize priority scores."""
        if not scored_samples:
            return scored_samples
        
        scores = [score for _, score, _ in scored_samples]
        
        if self.normalization_method == 'min_max':
            min_score = min(scores)
            max_score = max(scores)
            if max_score > min_score:
                normalized_samples = []
                for idx, score, breakdown in scored_samples:
                    normalized_score = (score - min_score) / (max_score - min_score)
                    normalized_samples.append((idx, normalized_score, breakdown))
                return normalized_samples
        
        elif self.normalization_method == 'z_score':
            mean_score = np.mean(scores)
            std_score = np.std(scores)
            if std_score > 0:
                normalized_samples = []
                for idx, score, breakdown in scored_samples:
                    normalized_score = (score - mean_score) / std_score
                    # Convert to [0, 1] range using sigmoid
                    normalized_score = 1.0 / (1.0 + np.exp(-normalized_score))
                    normalized_samples.append((idx, normalized_score, breakdown))
                return normalized_samples
        
        return scored_samples
    
    def _calculate_entropy(self, confidences: List[float]) -> float:
        """Calculate entropy from confidence scores."""
        if not confidences:
            return 1.0
        
        # Normalize confidences to probabilities
        total = sum(confidences)
        if total == 0:
            return 1.0
        
        probs = [c / total for c in confidences]
        
        # Calculate entropy
        entropy = 0.0
        for p in probs:
            if p > 0:
                entropy -= p * np.log2(p)
        
        # Normalize to [0, 1]
        max_entropy = np.log2(len(probs)) if len(probs) > 1 else 1.0
        return entropy / max_entropy if max_entropy > 0 else 0.0
    
    def _update_category_stats(self, prediction: Dict[str, Any], priority_score: float):
        """Update category statistics."""
        if 'annotations' in prediction:
            for ann in prediction['annotations']:
                category = ann.get('category', '')
                if category:
                    stats = self.category_stats[category]
                    stats['count'] += 1
                    # Update running average
                    old_avg = stats['avg_priority']
                    stats['avg_priority'] = old_avg + (priority_score - old_avg) / stats['count']
    
    def _update_scoring_history(self, scored_samples: List[Tuple[int, float, Dict[str, float]]]):
        """Update scoring history."""
        if not scored_samples:
            return
        
        round_info = {
            'timestamp': datetime.now().isoformat(),
            'num_samples': len(scored_samples),
            'mean_priority': np.mean([score for _, score, _ in scored_samples]),
            'std_priority': np.std([score for _, score, _ in scored_samples]),
            'weights_used': self.weights.copy()
        }
        
        self.scoring_history.append(round_info)


def create_priority_scorer(config: Dict[str, Any]) -> PriorityScorer:
    """Factory function to create priority scorer."""
    return PriorityScorer(config)