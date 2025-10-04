"""
Sample selection algorithms for active learning.
"""

import logging
from typing import Dict, List, Tuple, Optional, Any, Union, Set
import numpy as np
from pathlib import Path
import json
from collections import defaultdict, Counter
import random
from datetime import datetime

logger = logging.getLogger(__name__)


class SampleSelector:
    """Advanced sample selection algorithms for active learning."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize sample selector.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.selection_config = config.get('sample_selection', {})
        
        # Selection strategy
        self.strategy = self.selection_config.get('strategy', 'uncertainty_diversity')
        self.batch_size = self.selection_config.get('batch_size', 10)
        
        # Strategy parameters
        self.diversity_threshold = self.selection_config.get('diversity_threshold', 0.1)
        self.uncertainty_weight = self.selection_config.get('uncertainty_weight', 0.7)
        self.diversity_weight = self.selection_config.get('diversity_weight', 0.3)
        self.representativeness_weight = self.selection_config.get('representativeness_weight', 0.2)
        
        # Coverage and balancing
        self.ensure_category_coverage = self.selection_config.get('ensure_category_coverage', True)
        self.max_samples_per_category = self.selection_config.get('max_samples_per_category', None)
        self.min_samples_per_category = self.selection_config.get('min_samples_per_category', 1)
        
        # Quality control
        self.quality_threshold = self.selection_config.get('quality_threshold', 0.1)
        self.avoid_duplicates = self.selection_config.get('avoid_duplicates', True)
        
        # Selection history
        self.selection_history = []
        self.selected_indices = set()
        self.category_selection_counts = Counter()
        
        # Available strategies
        self.strategies = {
            'random': self._random_selection,
            'uncertainty': self._uncertainty_selection,
            'diversity': self._diversity_selection,
            'uncertainty_diversity': self._uncertainty_diversity_selection,
            'representative': self._representative_selection,
            'balanced': self._balanced_selection,
            'query_by_committee': self._query_by_committee_selection,
            'expected_model_change': self._expected_model_change_selection
        }
        
        logger.info(f"Initialized sample selector with strategy: {self.strategy}")
    
    def select_samples(self, 
                      samples: List[Dict[str, Any]], 
                      predictions: List[Dict[str, Any]],
                      uncertainty_scores: Optional[List[float]] = None,
                      priority_scores: Optional[List[Tuple[int, float, Dict[str, float]]]] = None,
                      num_samples: Optional[int] = None) -> List[int]:
        """
        Select samples for annotation using the configured strategy.
        
        Args:
            samples: List of sample data
            predictions: Model predictions for samples
            uncertainty_scores: Pre-computed uncertainty scores
            priority_scores: Pre-computed priority scores
            num_samples: Number of samples to select (uses batch_size if None)
            
        Returns:
            List of selected sample indices
        """
        if num_samples is None:
            num_samples = self.batch_size
        
        # Filter out already selected samples if avoiding duplicates
        available_indices = list(range(len(samples)))
        if self.avoid_duplicates:
            available_indices = [i for i in available_indices if i not in self.selected_indices]
        
        if not available_indices:
            logger.warning("No available samples for selection")
            return []
        
        if num_samples >= len(available_indices):
            selected = available_indices
        else:
            # Use the configured strategy
            if self.strategy in self.strategies:
                selected = self.strategies[self.strategy](
                    samples, predictions, available_indices, num_samples,
                    uncertainty_scores, priority_scores
                )
            else:
                logger.warning(f"Unknown strategy '{self.strategy}', using uncertainty_diversity")
                selected = self._uncertainty_diversity_selection(
                    samples, predictions, available_indices, num_samples,
                    uncertainty_scores, priority_scores
                )
        
        # Apply post-processing constraints
        selected = self._apply_selection_constraints(
            selected, samples, predictions, num_samples
        )
        
        # Update tracking
        self._update_selection_tracking(selected, samples, predictions)
        
        logger.info(f"Selected {len(selected)} samples using {self.strategy} strategy")
        return selected
    
    def select_balanced_batch(self, 
                             samples: List[Dict[str, Any]], 
                             predictions: List[Dict[str, Any]],
                             target_categories: List[str],
                             samples_per_category: Optional[int] = None) -> Dict[str, List[int]]:
        """
        Select balanced batch ensuring representation across categories.
        
        Args:
            samples: List of sample data
            predictions: Model predictions
            target_categories: Categories to ensure coverage
            samples_per_category: Samples per category (auto-calculated if None)
            
        Returns:
            Dictionary mapping categories to selected sample indices
        """
        if samples_per_category is None:
            samples_per_category = max(1, self.batch_size // len(target_categories))
        
        category_selections = {}
        
        # Group samples by predicted category
        category_samples = defaultdict(list)
        for i, prediction in enumerate(predictions):
            if i in self.selected_indices and self.avoid_duplicates:
                continue
                
            categories = self._extract_categories(prediction)
            for category in categories:
                if category in target_categories:
                    category_samples[category].append(i)
        
        # Select samples for each category
        for category in target_categories:
            available_samples = category_samples[category]
            
            if not available_samples:
                category_selections[category] = []
                continue
            
            # Select best samples for this category
            if len(available_samples) <= samples_per_category:
                category_selections[category] = available_samples
            else:
                # Use uncertainty-based selection within category
                category_predictions = [predictions[i] for i in available_samples]
                category_data = [samples[i] for i in available_samples]
                
                selected_local = self._uncertainty_selection(
                    category_data, category_predictions, 
                    list(range(len(available_samples))), samples_per_category
                )
                
                category_selections[category] = [available_samples[i] for i in selected_local]
        
        # Update tracking
        all_selected = []
        for indices in category_selections.values():
            all_selected.extend(indices)
        self._update_selection_tracking(all_selected, samples, predictions)
        
        return category_selections
    
    def get_selection_statistics(self) -> Dict[str, Any]:
        """Get statistics about selection history and performance."""
        if not self.selection_history:
            return {}
        
        total_selected = sum(len(round_data['selected_indices']) for round_data in self.selection_history)
        
        return {
            'total_selections': len(self.selection_history),
            'total_samples_selected': total_selected,
            'avg_batch_size': total_selected / len(self.selection_history),
            'category_distribution': dict(self.category_selection_counts),
            'strategy_used': self.strategy,
            'selection_rounds': len(self.selection_history),
            'currently_selected_count': len(self.selected_indices),
            'last_selection': self.selection_history[-1] if self.selection_history else None
        }
    
    def reset_selection_history(self):
        """Reset selection history and tracking."""
        self.selection_history = []
        self.selected_indices = set()
        self.category_selection_counts = Counter()
        logger.info("Reset selection history")
    
    def export_selection_history(self, filepath: str):
        """Export selection history to file."""
        export_data = {
            'selection_history': self.selection_history,
            'selected_indices': list(self.selected_indices),
            'category_selection_counts': dict(self.category_selection_counts),
            'config': self.selection_config,
            'statistics': self.get_selection_statistics()
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported selection history to {filepath}")
    
    def _random_selection(self, 
                         samples: List[Dict[str, Any]], 
                         predictions: List[Dict[str, Any]],
                         available_indices: List[int], 
                         num_samples: int,
                         uncertainty_scores: Optional[List[float]] = None,
                         priority_scores: Optional[List[Tuple[int, float, Dict[str, float]]]] = None) -> List[int]:
        """Random sample selection."""
        return random.sample(available_indices, min(num_samples, len(available_indices)))
    
    def _uncertainty_selection(self, 
                              samples: List[Dict[str, Any]], 
                              predictions: List[Dict[str, Any]],
                              available_indices: List[int], 
                              num_samples: int,
                              uncertainty_scores: Optional[List[float]] = None,
                              priority_scores: Optional[List[Tuple[int, float, Dict[str, float]]]] = None) -> List[int]:
        """Uncertainty-based sample selection."""
        if uncertainty_scores is None:
            uncertainty_scores = self._calculate_uncertainty_scores(predictions)
        
        # Sort available indices by uncertainty (descending)
        sorted_indices = sorted(available_indices, 
                              key=lambda i: uncertainty_scores[i], 
                              reverse=True)
        
        return sorted_indices[:num_samples]
    
    def _diversity_selection(self, 
                            samples: List[Dict[str, Any]], 
                            predictions: List[Dict[str, Any]],
                            available_indices: List[int], 
                            num_samples: int,
                            uncertainty_scores: Optional[List[float]] = None,
                            priority_scores: Optional[List[Tuple[int, float, Dict[str, float]]]] = None) -> List[int]:
        """Diversity-based sample selection using maximum diversity sampling."""
        if num_samples >= len(available_indices):
            return available_indices
        
        selected = []
        remaining = available_indices.copy()
        
        # Start with most uncertain sample
        if uncertainty_scores is None:
            uncertainty_scores = self._calculate_uncertainty_scores(predictions)
        
        # Select first sample with highest uncertainty
        first_idx = max(remaining, key=lambda i: uncertainty_scores[i])
        selected.append(first_idx)
        remaining.remove(first_idx)
        
        # Iteratively select most diverse samples
        while len(selected) < num_samples and remaining:
            best_candidate = None
            best_diversity = -1
            
            for candidate in remaining:
                # Calculate diversity with already selected samples
                diversity = self._calculate_sample_diversity(
                    candidate, selected, predictions
                )
                
                if diversity > best_diversity:
                    best_diversity = diversity
                    best_candidate = candidate
            
            if best_candidate is not None:
                selected.append(best_candidate)
                remaining.remove(best_candidate)
        
        return selected
    
    def _uncertainty_diversity_selection(self, 
                                        samples: List[Dict[str, Any]], 
                                        predictions: List[Dict[str, Any]],
                                        available_indices: List[int], 
                                        num_samples: int,
                                        uncertainty_scores: Optional[List[float]] = None,
                                        priority_scores: Optional[List[Tuple[int, float, Dict[str, float]]]] = None) -> List[int]:
        """Combined uncertainty and diversity selection."""
        if uncertainty_scores is None:
            uncertainty_scores = self._calculate_uncertainty_scores(predictions)
        
        selected = []
        remaining = available_indices.copy()
        
        while len(selected) < num_samples and remaining:
            best_candidate = None
            best_score = -1
            
            for candidate in remaining:
                # Uncertainty component
                uncertainty = uncertainty_scores[candidate]
                
                # Diversity component
                if selected:
                    diversity = self._calculate_sample_diversity(
                        candidate, selected, predictions
                    )
                else:
                    diversity = 1.0  # First sample gets full diversity score
                
                # Combined score
                combined_score = (self.uncertainty_weight * uncertainty + 
                                self.diversity_weight * diversity)
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_candidate = candidate
            
            if best_candidate is not None:
                selected.append(best_candidate)
                remaining.remove(best_candidate)
        
        return selected
    
    def _representative_selection(self, 
                                 samples: List[Dict[str, Any]], 
                                 predictions: List[Dict[str, Any]],
                                 available_indices: List[int], 
                                 num_samples: int,
                                 uncertainty_scores: Optional[List[float]] = None,
                                 priority_scores: Optional[List[Tuple[int, float, Dict[str, float]]]] = None) -> List[int]:
        """Representative sample selection using clustering."""
        # This is a simplified version - in practice, you'd use feature embeddings
        # For now, use category distribution as a proxy for representativeness
        
        # Group samples by category
        category_groups = defaultdict(list)
        for idx in available_indices:
            categories = self._extract_categories(predictions[idx])
            main_category = categories[0] if categories else 'unknown'
            category_groups[main_category].append(idx)
        
        # Select representatives from each category
        selected = []
        categories = list(category_groups.keys())
        samples_per_category = max(1, num_samples // len(categories))
        
        for category in categories:
            category_indices = category_groups[category]
            category_samples = min(samples_per_category, len(category_indices))
            
            # Within each category, select by uncertainty
            if uncertainty_scores is None:
                uncertainty_scores = self._calculate_uncertainty_scores(predictions)
            
            category_sorted = sorted(category_indices, 
                                   key=lambda i: uncertainty_scores[i], 
                                   reverse=True)
            
            selected.extend(category_sorted[:category_samples])
        
        # If we haven't selected enough, add more from high-uncertainty samples
        if len(selected) < num_samples:
            remaining = [i for i in available_indices if i not in selected]
            if remaining:
                remaining_sorted = sorted(remaining, 
                                        key=lambda i: uncertainty_scores[i], 
                                        reverse=True)
                additional_needed = num_samples - len(selected)
                selected.extend(remaining_sorted[:additional_needed])
        
        return selected[:num_samples]
    
    def _balanced_selection(self, 
                           samples: List[Dict[str, Any]], 
                           predictions: List[Dict[str, Any]],
                           available_indices: List[int], 
                           num_samples: int,
                           uncertainty_scores: Optional[List[float]] = None,
                           priority_scores: Optional[List[Tuple[int, float, Dict[str, float]]]] = None) -> List[int]:
        """Balanced selection ensuring equal representation across categories."""
        # Extract all categories from predictions
        all_categories = set()
        for idx in available_indices:
            categories = self._extract_categories(predictions[idx])
            all_categories.update(categories)
        
        if not all_categories:
            return self._uncertainty_selection(samples, predictions, available_indices, 
                                             num_samples, uncertainty_scores, priority_scores)
        
        # Use balanced batch selection
        target_categories = list(all_categories)
        balanced_selections = self.select_balanced_batch(
            samples, predictions, target_categories
        )
        
        # Flatten selections
        selected = []
        for indices in balanced_selections.values():
            selected.extend(indices[:num_samples // len(target_categories)])
        
        return selected[:num_samples]
    
    def _query_by_committee_selection(self, 
                                     samples: List[Dict[str, Any]], 
                                     predictions: List[Dict[str, Any]],
                                     available_indices: List[int], 
                                     num_samples: int,
                                     uncertainty_scores: Optional[List[float]] = None,
                                     priority_scores: Optional[List[Tuple[int, float, Dict[str, float]]]] = None) -> List[int]:
        """Query by committee selection (requires ensemble predictions)."""
        # This would require ensemble predictions - fall back to uncertainty for now
        logger.info("Query by committee requires ensemble predictions, using uncertainty selection")
        return self._uncertainty_selection(samples, predictions, available_indices, 
                                         num_samples, uncertainty_scores, priority_scores)
    
    def _expected_model_change_selection(self, 
                                        samples: List[Dict[str, Any]], 
                                        predictions: List[Dict[str, Any]],
                                        available_indices: List[int], 
                                        num_samples: int,
                                        uncertainty_scores: Optional[List[float]] = None,
                                        priority_scores: Optional[List[Tuple[int, float, Dict[str, float]]]] = None) -> List[int]:
        """Expected model change selection (requires gradient information)."""
        # This would require gradient computation - fall back to uncertainty for now
        logger.info("Expected model change requires gradient information, using uncertainty selection")
        return self._uncertainty_selection(samples, predictions, available_indices, 
                                         num_samples, uncertainty_scores, priority_scores)
    
    def _calculate_uncertainty_scores(self, predictions: List[Dict[str, Any]]) -> List[float]:
        """Calculate uncertainty scores from predictions."""
        uncertainty_scores = []
        
        for pred in predictions:
            if 'confidence' in pred:
                uncertainty = 1.0 - pred['confidence']
            elif 'annotations' in pred:
                confidences = [ann.get('confidence', 0.0) for ann in pred['annotations']]
                if confidences:
                    # Use entropy of confidence distribution
                    uncertainty = self._calculate_entropy(confidences)
                else:
                    uncertainty = 1.0
            else:
                uncertainty = 1.0
            
            uncertainty_scores.append(uncertainty)
        
        return uncertainty_scores
    
    def _calculate_sample_diversity(self, 
                                   candidate_idx: int, 
                                   selected_indices: List[int], 
                                   predictions: List[Dict[str, Any]]) -> float:
        """Calculate diversity of candidate sample with selected samples."""
        if not selected_indices:
            return 1.0
        
        candidate_pred = predictions[candidate_idx]
        candidate_categories = set(self._extract_categories(candidate_pred))
        
        diversities = []
        for selected_idx in selected_indices:
            selected_pred = predictions[selected_idx]
            selected_categories = set(self._extract_categories(selected_pred))
            
            # Calculate Jaccard distance
            if candidate_categories or selected_categories:
                intersection = len(candidate_categories & selected_categories)
                union = len(candidate_categories | selected_categories)
                jaccard_similarity = intersection / union if union > 0 else 0
                diversity = 1.0 - jaccard_similarity
            else:
                diversity = 0.0
            
            diversities.append(diversity)
        
        # Return minimum diversity (most conservative)
        return min(diversities)
    
    def _extract_categories(self, prediction: Dict[str, Any]) -> List[str]:
        """Extract categories from prediction."""
        categories = []
        
        if 'category' in prediction:
            categories.append(prediction['category'])
        elif 'annotations' in prediction:
            for ann in prediction['annotations']:
                if 'category' in ann:
                    categories.append(ann['category'])
        
        return categories
    
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
    
    def _apply_selection_constraints(self, 
                                   selected: List[int], 
                                   samples: List[Dict[str, Any]], 
                                   predictions: List[Dict[str, Any]],
                                   target_num_samples: int) -> List[int]:
        """Apply post-processing constraints to selection."""
        # Quality threshold filtering
        if self.quality_threshold > 0:
            filtered_selected = []
            for idx in selected:
                if self._meets_quality_threshold(samples[idx], predictions[idx]):
                    filtered_selected.append(idx)
            selected = filtered_selected
        
        # Category coverage constraints
        if self.ensure_category_coverage:
            selected = self._ensure_category_coverage(selected, predictions, target_num_samples)
        
        # Max samples per category constraint
        if self.max_samples_per_category:
            selected = self._apply_category_limits(selected, predictions)
        
        return selected
    
    def _meets_quality_threshold(self, 
                                sample: Dict[str, Any], 
                                prediction: Dict[str, Any]) -> bool:
        """Check if sample meets quality threshold."""
        # Simple quality check based on prediction confidence
        if 'confidence' in prediction:
            return prediction['confidence'] >= self.quality_threshold
        elif 'annotations' in prediction:
            confidences = [ann.get('confidence', 0.0) for ann in prediction['annotations']]
            if confidences:
                return max(confidences) >= self.quality_threshold
        
        return True  # If can't determine quality, assume it's good
    
    def _ensure_category_coverage(self, 
                                 selected: List[int], 
                                 predictions: List[Dict[str, Any]],
                                 target_num_samples: int) -> List[int]:
        """Ensure category coverage in selection."""
        if not selected:
            return selected
        
        # Get categories in selection
        selected_categories = set()
        for idx in selected:
            categories = self._extract_categories(predictions[idx])
            selected_categories.update(categories)
        
        # This is a basic implementation - could be enhanced with more sophisticated coverage
        return selected
    
    def _apply_category_limits(self, 
                              selected: List[int], 
                              predictions: List[Dict[str, Any]]) -> List[int]:
        """Apply maximum samples per category constraint."""
        category_counts = Counter()
        filtered_selected = []
        
        for idx in selected:
            categories = self._extract_categories(predictions[idx])
            main_category = categories[0] if categories else 'unknown'
            
            if category_counts[main_category] < self.max_samples_per_category:
                filtered_selected.append(idx)
                category_counts[main_category] += 1
        
        return filtered_selected
    
    def _update_selection_tracking(self, 
                                  selected: List[int], 
                                  samples: List[Dict[str, Any]], 
                                  predictions: List[Dict[str, Any]]):
        """Update selection tracking and history."""
        # Update selected indices
        self.selected_indices.update(selected)
        
        # Update category counts
        for idx in selected:
            categories = self._extract_categories(predictions[idx])
            for category in categories:
                self.category_selection_counts[category] += 1
        
        # Add to history
        round_info = {
            'timestamp': datetime.now().isoformat(),
            'strategy': self.strategy,
            'num_samples': len(selected),
            'selected_indices': selected,
            'categories_selected': list(set(
                cat for idx in selected 
                for cat in self._extract_categories(predictions[idx])
            ))
        }
        
        self.selection_history.append(round_info)


def create_sample_selector(config: Dict[str, Any]) -> SampleSelector:
    """Factory function to create sample selector."""
    return SampleSelector(config)