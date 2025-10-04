"""
Uncertainty sampling for active learning.
"""

import logging
from typing import Dict, List, Tuple, Optional, Any, Union
import numpy as np
from pathlib import Path
import json
from collections import defaultdict

logger = logging.getLogger(__name__)


class UncertaintySampler:
    """Uncertainty-based sample selection for active learning."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize uncertainty sampler.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.uncertainty_config = config.get('uncertainty_sampling', {})
        
        # Sampling configuration
        self.sampling_strategy = self.uncertainty_config.get('strategy', 'entropy')
        self.batch_size = self.uncertainty_config.get('batch_size', 10)
        self.diversity_weight = self.uncertainty_config.get('diversity_weight', 0.1)
        self.min_confidence_threshold = self.uncertainty_config.get('min_confidence_threshold', 0.1)
        self.max_confidence_threshold = self.uncertainty_config.get('max_confidence_threshold', 0.9)
        
        # Supported strategies
        self.strategies = {
            'entropy': self._entropy_sampling,
            'margin': self._margin_sampling,
            'least_confidence': self._least_confidence_sampling,
            'variance': self._variance_sampling,
            'disagreement': self._disagreement_sampling
        }
        
        # Statistics tracking
        self.sampling_history = []
        self.uncertainty_stats = defaultdict(list)
        
        logger.info(f"Initialized uncertainty sampler with strategy: {self.sampling_strategy}")
    
    def select_samples(self, 
                      samples: List[Dict[str, Any]], 
                      predictions: List[Dict[str, Any]], 
                      num_samples: Optional[int] = None) -> List[Tuple[int, float]]:
        """
        Select samples based on uncertainty.
        
        Args:
            samples: List of sample data (images, metadata)
            predictions: List of model predictions with confidence scores
            num_samples: Number of samples to select (uses batch_size if None)
            
        Returns:
            List of (sample_index, uncertainty_score) tuples
        """
        if num_samples is None:
            num_samples = self.batch_size
        
        if len(samples) != len(predictions):
            raise ValueError("Number of samples must match number of predictions")
        
        # Calculate uncertainty scores
        uncertainty_scores = self._calculate_uncertainty_scores(predictions)
        
        # Apply confidence thresholds
        filtered_indices = self._apply_confidence_filters(uncertainty_scores, predictions)
        
        # Select samples using chosen strategy
        if self.sampling_strategy in self.strategies:
            selected_indices = self.strategies[self.sampling_strategy](
                filtered_indices, uncertainty_scores, predictions, num_samples
            )
        else:
            logger.warning(f"Unknown strategy '{self.sampling_strategy}', using entropy")
            selected_indices = self._entropy_sampling(
                filtered_indices, uncertainty_scores, predictions, num_samples
            )
        
        # Create result with uncertainty scores
        selected_samples = [(idx, uncertainty_scores[idx]) for idx in selected_indices]
        
        # Update statistics
        self._update_statistics(selected_samples, predictions)
        
        logger.info(f"Selected {len(selected_samples)} samples using {self.sampling_strategy} strategy")
        return selected_samples
    
    def calculate_ensemble_uncertainty(self, 
                                     ensemble_predictions: List[List[Dict[str, Any]]]) -> List[float]:
        """
        Calculate uncertainty from ensemble predictions.
        
        Args:
            ensemble_predictions: List of prediction lists from different models
            
        Returns:
            List of uncertainty scores
        """
        if not ensemble_predictions or not ensemble_predictions[0]:
            return []
        
        num_samples = len(ensemble_predictions[0])
        uncertainty_scores = []
        
        for sample_idx in range(num_samples):
            # Get predictions for this sample from all models
            sample_predictions = [preds[sample_idx] for preds in ensemble_predictions]
            
            # Calculate uncertainty based on model disagreement
            uncertainty = self._calculate_model_disagreement(sample_predictions)
            uncertainty_scores.append(uncertainty)
        
        return uncertainty_scores
    
    def get_uncertainty_distribution(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze uncertainty distribution in predictions.
        
        Args:
            predictions: Model predictions
            
        Returns:
            Dictionary with uncertainty statistics
        """
        uncertainty_scores = self._calculate_uncertainty_scores(predictions)
        
        return {
            'mean_uncertainty': float(np.mean(uncertainty_scores)),
            'std_uncertainty': float(np.std(uncertainty_scores)),
            'min_uncertainty': float(np.min(uncertainty_scores)),
            'max_uncertainty': float(np.max(uncertainty_scores)),
            'median_uncertainty': float(np.median(uncertainty_scores)),
            'high_uncertainty_ratio': float(np.mean(np.array(uncertainty_scores) > 0.7)),
            'low_uncertainty_ratio': float(np.mean(np.array(uncertainty_scores) < 0.3)),
            'uncertainty_distribution': {
                'bins': [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
                'counts': np.histogram(uncertainty_scores, bins=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0])[0].tolist()
            }
        }
    
    def export_sampling_history(self, filepath: str):
        """Export sampling history to file."""
        export_data = {
            'sampling_history': self.sampling_history,
            'uncertainty_stats': dict(self.uncertainty_stats),
            'config': self.uncertainty_config
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported sampling history to {filepath}")
    
    def _calculate_uncertainty_scores(self, predictions: List[Dict[str, Any]]) -> List[float]:
        """Calculate uncertainty scores for predictions."""
        uncertainty_scores = []
        
        for pred in predictions:
            if 'confidence' in pred:
                # Simple confidence-based uncertainty
                confidence = pred['confidence']
                uncertainty = 1.0 - confidence
            elif 'annotations' in pred:
                # Calculate uncertainty from multiple annotations
                confidences = [ann.get('confidence', 0.0) for ann in pred['annotations']]
                if confidences:
                    # Use entropy of confidence distribution
                    uncertainty = self._calculate_entropy(confidences)
                else:
                    uncertainty = 1.0  # Maximum uncertainty if no annotations
            else:
                uncertainty = 1.0  # Maximum uncertainty for unknown format
            
            uncertainty_scores.append(uncertainty)
        
        return uncertainty_scores
    
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
    
    def _calculate_model_disagreement(self, sample_predictions: List[Dict[str, Any]]) -> float:
        """Calculate disagreement between model predictions."""
        if len(sample_predictions) < 2:
            return 0.0
        
        # Extract confidence scores or categories
        confidences = []
        categories = []
        
        for pred in sample_predictions:
            if 'confidence' in pred:
                confidences.append(pred['confidence'])
            if 'category' in pred:
                categories.append(pred['category'])
            elif 'annotations' in pred and pred['annotations']:
                # Use highest confidence annotation
                best_ann = max(pred['annotations'], key=lambda x: x.get('confidence', 0))
                if 'category' in best_ann:
                    categories.append(best_ann['category'])
        
        disagreement = 0.0
        
        # Confidence-based disagreement
        if confidences:
            conf_std = np.std(confidences)
            disagreement += conf_std
        
        # Category-based disagreement
        if categories:
            unique_categories = len(set(categories))
            total_predictions = len(categories)
            category_disagreement = (unique_categories - 1) / max(total_predictions - 1, 1)
            disagreement += category_disagreement
        
        return min(disagreement, 1.0)  # Clamp to [0, 1]
    
    def _apply_confidence_filters(self, 
                                uncertainty_scores: List[float], 
                                predictions: List[Dict[str, Any]]) -> List[int]:
        """Apply confidence-based filtering."""
        filtered_indices = []
        
        for i, (uncertainty, pred) in enumerate(zip(uncertainty_scores, predictions)):
            confidence = 1.0 - uncertainty
            
            # Filter based on confidence thresholds
            if (confidence >= self.min_confidence_threshold and 
                confidence <= self.max_confidence_threshold):
                filtered_indices.append(i)
        
        return filtered_indices
    
    def _entropy_sampling(self, 
                         indices: List[int], 
                         uncertainty_scores: List[float], 
                         predictions: List[Dict[str, Any]], 
                         num_samples: int) -> List[int]:
        """Select samples with highest entropy."""
        # Sort by uncertainty (descending)
        sorted_indices = sorted(indices, key=lambda i: uncertainty_scores[i], reverse=True)
        return sorted_indices[:num_samples]
    
    def _margin_sampling(self, 
                        indices: List[int], 
                        uncertainty_scores: List[float], 
                        predictions: List[Dict[str, Any]], 
                        num_samples: int) -> List[int]:
        """Select samples with smallest margin between top predictions."""
        margin_scores = []
        
        for i in indices:
            pred = predictions[i]
            if 'annotations' in pred and len(pred['annotations']) >= 2:
                # Sort annotations by confidence
                sorted_anns = sorted(pred['annotations'], 
                                   key=lambda x: x.get('confidence', 0), 
                                   reverse=True)
                
                # Calculate margin between top 2
                margin = sorted_anns[0].get('confidence', 0) - sorted_anns[1].get('confidence', 0)
                margin_scores.append((i, 1.0 - margin))  # Convert to uncertainty
            else:
                margin_scores.append((i, uncertainty_scores[i]))
        
        # Sort by margin uncertainty (descending)
        margin_scores.sort(key=lambda x: x[1], reverse=True)
        return [idx for idx, _ in margin_scores[:num_samples]]
    
    def _least_confidence_sampling(self, 
                                  indices: List[int], 
                                  uncertainty_scores: List[float], 
                                  predictions: List[Dict[str, Any]], 
                                  num_samples: int) -> List[int]:
        """Select samples with lowest confidence."""
        confidence_scores = [(i, 1.0 - uncertainty_scores[i]) for i in indices]
        confidence_scores.sort(key=lambda x: x[1])  # Sort by confidence (ascending)
        return [idx for idx, _ in confidence_scores[:num_samples]]
    
    def _variance_sampling(self, 
                          indices: List[int], 
                          uncertainty_scores: List[float], 
                          predictions: List[Dict[str, Any]], 
                          num_samples: int) -> List[int]:
        """Select samples with highest prediction variance."""
        variance_scores = []
        
        for i in indices:
            pred = predictions[i]
            if 'annotations' in pred:
                confidences = [ann.get('confidence', 0) for ann in pred['annotations']]
                variance = np.var(confidences) if confidences else uncertainty_scores[i]
                variance_scores.append((i, variance))
            else:
                variance_scores.append((i, uncertainty_scores[i]))
        
        # Sort by variance (descending)
        variance_scores.sort(key=lambda x: x[1], reverse=True)
        return [idx for idx, _ in variance_scores[:num_samples]]
    
    def _disagreement_sampling(self, 
                              indices: List[int], 
                              uncertainty_scores: List[float], 
                              predictions: List[Dict[str, Any]], 
                              num_samples: int) -> List[int]:
        """Select samples with highest model disagreement."""
        # This requires ensemble predictions - fall back to entropy if not available
        return self._entropy_sampling(indices, uncertainty_scores, predictions, num_samples)
    
    def _update_statistics(self, 
                          selected_samples: List[Tuple[int, float]], 
                          predictions: List[Dict[str, Any]]):
        """Update sampling statistics."""
        if not selected_samples:
            return
        
        # Record sampling round
        round_info = {
            'strategy': self.sampling_strategy,
            'num_selected': len(selected_samples),
            'uncertainty_scores': [score for _, score in selected_samples],
            'mean_uncertainty': np.mean([score for _, score in selected_samples]),
            'selected_indices': [idx for idx, _ in selected_samples]
        }
        
        self.sampling_history.append(round_info)
        
        # Update running statistics
        for _, uncertainty in selected_samples:
            self.uncertainty_stats[self.sampling_strategy].append(uncertainty)


def create_uncertainty_sampler(config: Dict[str, Any]) -> UncertaintySampler:
    """Factory function to create uncertainty sampler."""
    return UncertaintySampler(config)