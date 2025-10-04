"""
Feedback loop implementation for active learning.
"""

import logging
from typing import Dict, List, Tuple, Optional, Any, Union, Callable
import numpy as np
from pathlib import Path
import json
from collections import defaultdict, Counter
from datetime import datetime
import copy

logger = logging.getLogger(__name__)


class FeedbackLoop:
    """Basic feedback loop system for active learning."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize feedback loop.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.feedback_config = config.get('feedback_loop', {})
        
        # Feedback parameters
        self.learning_rate = self.feedback_config.get('learning_rate', 0.1)
        self.adaptation_threshold = self.feedback_config.get('adaptation_threshold', 0.1)
        self.feedback_memory = self.feedback_config.get('feedback_memory', 100)
        self.enable_parameter_adaptation = self.feedback_config.get('enable_parameter_adaptation', True)
        
        # Feedback storage
        self.feedback_history = []
        self.correction_patterns = defaultdict(list)
        self.performance_metrics = defaultdict(list)
        self.adaptation_history = []
        
        # Model performance tracking
        self.model_accuracy_history = defaultdict(list)
        self.category_performance = defaultdict(lambda: {'correct': 0, 'total': 0, 'accuracy': 0.0})
        
        # Parameter adaptation tracking
        self.adaptive_parameters = {
            'confidence_thresholds': {},
            'selection_weights': {},
            'priority_weights': {}
        }
        
        logger.info("Initialized active learning feedback loop")
    
    def process_annotation_feedback(self, 
                                   original_predictions: List[Dict[str, Any]], 
                                   human_annotations: List[Dict[str, Any]],
                                   sample_indices: List[int]) -> Dict[str, Any]:
        """
        Process feedback from human annotations.
        
        Args:
            original_predictions: Original model predictions
            human_annotations: Human-corrected annotations
            sample_indices: Indices of samples that were annotated
            
        Returns:
            Feedback analysis results
        """
        if len(original_predictions) != len(human_annotations) != len(sample_indices):
            raise ValueError("All input lists must have the same length")
        
        feedback_results = {
            'total_samples': len(sample_indices),
            'corrections_made': 0,
            'accuracy_by_category': {},
            'common_errors': [],
            'suggested_adaptations': {}
        }
        
        # Process each annotation pair
        for orig_pred, human_ann, sample_idx in zip(original_predictions, human_annotations, sample_indices):
            correction_info = self._analyze_correction(orig_pred, human_ann, sample_idx)
            
            if correction_info['correction_made']:
                feedback_results['corrections_made'] += 1
            
            # Store correction pattern
            self._store_correction_pattern(correction_info)
            
            # Update category performance
            self._update_category_performance(correction_info)
        
        # Analyze patterns and suggest adaptations
        feedback_results['accuracy_by_category'] = self._calculate_category_accuracies()
        feedback_results['common_errors'] = self._identify_common_errors()
        feedback_results['suggested_adaptations'] = self._suggest_parameter_adaptations()
        
        # Store feedback round
        self._store_feedback_round(feedback_results)
        
        # Apply adaptations if enabled
        if self.enable_parameter_adaptation:
            adaptations_applied = self._apply_parameter_adaptations(feedback_results['suggested_adaptations'])
            feedback_results['adaptations_applied'] = adaptations_applied
        
        logger.info(f"Processed feedback for {len(sample_indices)} samples, {feedback_results['corrections_made']} corrections made")
        return feedback_results
    
    def update_model_performance(self, 
                                model_name: str, 
                                accuracy: float, 
                                category_accuracies: Optional[Dict[str, float]] = None):
        """
        Update model performance metrics.
        
        Args:
            model_name: Name of the model
            accuracy: Overall accuracy score
            category_accuracies: Per-category accuracy scores
        """
        self.model_accuracy_history[model_name].append({
            'timestamp': datetime.now().isoformat(),
            'accuracy': accuracy,
            'category_accuracies': category_accuracies or {}
        })
        
        # Trim history if it gets too long
        if len(self.model_accuracy_history[model_name]) > self.feedback_memory:
            self.model_accuracy_history[model_name] = self.model_accuracy_history[model_name][-self.feedback_memory:]
        
        logger.debug(f"Updated performance for {model_name}: accuracy={accuracy:.3f}")
    
    def get_adaptation_suggestions(self) -> Dict[str, Any]:
        """
        Get current adaptation suggestions based on feedback history.
        
        Returns:
            Dictionary with suggested parameter adaptations
        """
        if not self.feedback_history:
            return {}
        
        suggestions = {
            'confidence_thresholds': self._suggest_confidence_threshold_changes(),
            'selection_strategy': self._suggest_selection_strategy_changes(),
            'priority_weights': self._suggest_priority_weight_changes(),
            'model_weights': self._suggest_model_weight_changes()
        }
        
        return suggestions
    
    def apply_feedback_to_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply learned adaptations to configuration.
        
        Args:
            config: Current configuration
            
        Returns:
            Updated configuration with adaptations applied
        """
        updated_config = copy.deepcopy(config)
        
        # Apply confidence threshold adaptations
        if 'confidence_thresholds' in self.adaptive_parameters:
            for category, threshold in self.adaptive_parameters['confidence_thresholds'].items():
                if 'models' in updated_config:
                    for model_config in updated_config['models'].values():
                        if isinstance(model_config, dict) and 'confidence_threshold' in model_config:
                            model_config['confidence_threshold'] = threshold
        
        # Apply selection weight adaptations
        if 'selection_weights' in self.adaptive_parameters:
            if 'sample_selection' in updated_config:
                updated_config['sample_selection'].update(self.adaptive_parameters['selection_weights'])
        
        # Apply priority weight adaptations
        if 'priority_weights' in self.adaptive_parameters:
            if 'priority_scoring' in updated_config:
                updated_config['priority_scoring'].update(self.adaptive_parameters['priority_weights'])
        
        logger.info("Applied feedback adaptations to configuration")
        return updated_config
    
    def get_feedback_statistics(self) -> Dict[str, Any]:
        """Get comprehensive feedback statistics."""
        if not self.feedback_history:
            return {}
        
        total_samples = sum(round_data['total_samples'] for round_data in self.feedback_history)
        total_corrections = sum(round_data['corrections_made'] for round_data in self.feedback_history)
        
        return {
            'feedback_rounds': len(self.feedback_history),
            'total_samples_reviewed': total_samples,
            'total_corrections_made': total_corrections,
            'overall_accuracy': 1.0 - (total_corrections / total_samples) if total_samples > 0 else 0.0,
            'category_performance': dict(self.category_performance),
            'adaptation_count': len(self.adaptation_history),
            'recent_performance_trend': self._calculate_performance_trend(),
            'most_problematic_categories': self._get_most_problematic_categories(),
            'adaptation_effectiveness': self._calculate_adaptation_effectiveness()
        }
    
    def export_feedback_data(self, filepath: str):
        """Export feedback data to file."""
        export_data = {
            'feedback_history': self.feedback_history,
            'correction_patterns': dict(self.correction_patterns),
            'category_performance': dict(self.category_performance),
            'adaptation_history': self.adaptation_history,
            'adaptive_parameters': self.adaptive_parameters,
            'model_accuracy_history': dict(self.model_accuracy_history),
            'config': self.feedback_config,
            'statistics': self.get_feedback_statistics()
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported feedback data to {filepath}")
    
    def _analyze_correction(self, 
                           original_prediction: Dict[str, Any], 
                           human_annotation: Dict[str, Any],
                           sample_idx: int) -> Dict[str, Any]:
        """Analyze a single prediction-correction pair."""
        correction_info = {
            'sample_idx': sample_idx,
            'correction_made': False,
            'error_type': None,
            'original_category': None,
            'corrected_category': None,
            'confidence_delta': 0.0,
            'bbox_adjustment': None
        }
        
        # Extract categories
        orig_category = self._extract_main_category(original_prediction)
        human_category = self._extract_main_category(human_annotation)
        
        correction_info['original_category'] = orig_category
        correction_info['corrected_category'] = human_category
        
        # Check if correction was made
        if orig_category != human_category:
            correction_info['correction_made'] = True
            correction_info['error_type'] = 'category_mismatch'
        
        # Check confidence differences
        orig_confidence = self._extract_main_confidence(original_prediction)
        human_confidence = self._extract_main_confidence(human_annotation)
        
        if orig_confidence is not None and human_confidence is not None:
            correction_info['confidence_delta'] = human_confidence - orig_confidence
        
        # Check bounding box adjustments (simplified)
        orig_bbox = self._extract_main_bbox(original_prediction)
        human_bbox = self._extract_main_bbox(human_annotation)
        
        if orig_bbox and human_bbox:
            bbox_iou = self._calculate_bbox_iou(orig_bbox, human_bbox)
            if bbox_iou < 0.8:  # Significant bbox adjustment
                correction_info['bbox_adjustment'] = bbox_iou
        
        return correction_info
    
    def _store_correction_pattern(self, correction_info: Dict[str, Any]):
        """Store correction pattern for analysis."""
        if correction_info['correction_made']:
            pattern_key = f"{correction_info['original_category']}->{correction_info['corrected_category']}"
            self.correction_patterns[pattern_key].append({
                'timestamp': datetime.now().isoformat(),
                'sample_idx': correction_info['sample_idx'],
                'confidence_delta': correction_info['confidence_delta'],
                'error_type': correction_info['error_type']
            })
    
    def _update_category_performance(self, correction_info: Dict[str, Any]):
        """Update per-category performance tracking."""
        category = correction_info['original_category']
        if category:
            self.category_performance[category]['total'] += 1
            if not correction_info['correction_made']:
                self.category_performance[category]['correct'] += 1
            
            # Update accuracy
            total = self.category_performance[category]['total']
            correct = self.category_performance[category]['correct']
            self.category_performance[category]['accuracy'] = correct / total if total > 0 else 0.0
    
    def _calculate_category_accuracies(self) -> Dict[str, float]:
        """Calculate current accuracy for each category."""
        return {
            category: perf['accuracy'] 
            for category, perf in self.category_performance.items()
        }
    
    def _identify_common_errors(self) -> List[Dict[str, Any]]:
        """Identify most common error patterns."""
        error_counts = Counter()
        
        for pattern, corrections in self.correction_patterns.items():
            error_counts[pattern] = len(corrections)
        
        # Return top 5 most common errors
        common_errors = []
        for pattern, count in error_counts.most_common(5):
            orig_cat, corrected_cat = pattern.split('->')
            common_errors.append({
                'pattern': pattern,
                'original_category': orig_cat,
                'corrected_category': corrected_cat,
                'frequency': count,
                'percentage': count / sum(error_counts.values()) * 100 if error_counts else 0
            })
        
        return common_errors
    
    def _suggest_parameter_adaptations(self) -> Dict[str, Any]:
        """Suggest parameter adaptations based on feedback patterns."""
        suggestions = {}
        
        # Confidence threshold suggestions
        confidence_suggestions = {}
        for category, perf in self.category_performance.items():
            if perf['total'] >= 5:  # Enough samples to be meaningful
                if perf['accuracy'] < 0.7:  # Poor performance
                    # Suggest lowering confidence threshold
                    current_threshold = 0.5  # Default assumption
                    suggested_threshold = max(0.1, current_threshold - 0.1)
                    confidence_suggestions[category] = suggested_threshold
                elif perf['accuracy'] > 0.95:  # Very good performance
                    # Suggest raising confidence threshold
                    current_threshold = 0.5
                    suggested_threshold = min(0.9, current_threshold + 0.1)
                    confidence_suggestions[category] = suggested_threshold
        
        if confidence_suggestions:
            suggestions['confidence_thresholds'] = confidence_suggestions
        
        # Selection strategy suggestions
        if self._should_adjust_selection_strategy():
            suggestions['selection_strategy'] = self._get_selection_strategy_suggestion()
        
        return suggestions
    
    def _apply_parameter_adaptations(self, suggestions: Dict[str, Any]) -> List[str]:
        """Apply suggested parameter adaptations."""
        applied_adaptations = []
        
        # Apply confidence threshold changes
        if 'confidence_thresholds' in suggestions:
            for category, threshold in suggestions['confidence_thresholds'].items():
                self.adaptive_parameters['confidence_thresholds'][category] = threshold
                applied_adaptations.append(f"Adjusted confidence threshold for {category} to {threshold:.2f}")
        
        # Apply selection strategy changes
        if 'selection_strategy' in suggestions:
            strategy = suggestions['selection_strategy']
            self.adaptive_parameters['selection_weights']['strategy'] = strategy
            applied_adaptations.append(f"Changed selection strategy to {strategy}")
        
        # Record adaptation
        if applied_adaptations:
            adaptation_record = {
                'timestamp': datetime.now().isoformat(),
                'adaptations': applied_adaptations,
                'trigger': 'feedback_analysis'
            }
            self.adaptation_history.append(adaptation_record)
        
        return applied_adaptations
    
    def _store_feedback_round(self, feedback_results: Dict[str, Any]):
        """Store feedback round data."""
        round_data = {
            'timestamp': datetime.now().isoformat(),
            'total_samples': feedback_results['total_samples'],
            'corrections_made': feedback_results['corrections_made'],
            'accuracy': 1.0 - (feedback_results['corrections_made'] / feedback_results['total_samples']),
            'category_accuracies': feedback_results['accuracy_by_category'],
            'common_errors': feedback_results['common_errors']
        }
        
        self.feedback_history.append(round_data)
        
        # Trim history if too long
        if len(self.feedback_history) > self.feedback_memory:
            self.feedback_history = self.feedback_history[-self.feedback_memory:]
    
    def _extract_main_category(self, annotation: Dict[str, Any]) -> Optional[str]:
        """Extract main category from annotation."""
        if 'category' in annotation:
            return annotation['category']
        elif 'annotations' in annotation and annotation['annotations']:
            # Return highest confidence annotation category
            best_ann = max(annotation['annotations'], key=lambda x: x.get('confidence', 0))
            return best_ann.get('category')
        return None
    
    def _extract_main_confidence(self, annotation: Dict[str, Any]) -> Optional[float]:
        """Extract main confidence from annotation."""
        if 'confidence' in annotation:
            return annotation['confidence']
        elif 'annotations' in annotation and annotation['annotations']:
            # Return highest confidence
            return max(ann.get('confidence', 0) for ann in annotation['annotations'])
        return None
    
    def _extract_main_bbox(self, annotation: Dict[str, Any]) -> Optional[List[float]]:
        """Extract main bounding box from annotation."""
        if 'bbox' in annotation:
            return annotation['bbox']
        elif 'annotations' in annotation and annotation['annotations']:
            # Return bbox from highest confidence annotation
            best_ann = max(annotation['annotations'], key=lambda x: x.get('confidence', 0))
            return best_ann.get('bbox')
        return None
    
    def _calculate_bbox_iou(self, bbox1: List[float], bbox2: List[float]) -> float:
        """Calculate IoU between two bounding boxes."""
        x1, y1, w1, h1 = bbox1
        x2, y2, w2, h2 = bbox2
        
        # Calculate intersection
        left = max(x1, x2)
        top = max(y1, y2)
        right = min(x1 + w1, x2 + w2)
        bottom = min(y1 + h1, y2 + h2)
        
        if left >= right or top >= bottom:
            return 0.0
        
        intersection = (right - left) * (bottom - top)
        area1 = w1 * h1
        area2 = w2 * h2
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def _should_adjust_selection_strategy(self) -> bool:
        """Determine if selection strategy should be adjusted."""
        if len(self.feedback_history) < 3:
            return False
        
        # Check if accuracy is consistently declining
        recent_accuracies = [round_data['accuracy'] for round_data in self.feedback_history[-3:]]
        return all(recent_accuracies[i] <= recent_accuracies[i-1] for i in range(1, len(recent_accuracies)))
    
    def _get_selection_strategy_suggestion(self) -> str:
        """Get selection strategy suggestion based on performance patterns."""
        # Simple heuristic - could be made more sophisticated
        if self._has_category_imbalance():
            return 'balanced'
        elif self._has_high_uncertainty():
            return 'uncertainty'
        else:
            return 'uncertainty_diversity'
    
    def _has_category_imbalance(self) -> bool:
        """Check if there's significant category imbalance in performance."""
        accuracies = [perf['accuracy'] for perf in self.category_performance.values() if perf['total'] > 0]
        if len(accuracies) < 2:
            return False
        return (max(accuracies) - min(accuracies)) > 0.3
    
    def _has_high_uncertainty(self) -> bool:
        """Check if there's high overall uncertainty."""
        if not self.feedback_history:
            return False
        recent_accuracy = self.feedback_history[-1]['accuracy']
        return recent_accuracy < 0.7
    
    def _calculate_performance_trend(self) -> str:
        """Calculate recent performance trend."""
        if len(self.feedback_history) < 2:
            return 'insufficient_data'
        
        recent_accuracies = [round_data['accuracy'] for round_data in self.feedback_history[-3:]]
        
        if len(recent_accuracies) >= 2:
            if recent_accuracies[-1] > recent_accuracies[-2]:
                return 'improving'
            elif recent_accuracies[-1] < recent_accuracies[-2]:
                return 'declining'
            else:
                return 'stable'
        
        return 'stable'
    
    def _get_most_problematic_categories(self) -> List[Dict[str, Any]]:
        """Get categories with worst performance."""
        problematic = []
        
        for category, perf in self.category_performance.items():
            if perf['total'] >= 3:  # Minimum samples for meaningful assessment
                problematic.append({
                    'category': category,
                    'accuracy': perf['accuracy'],
                    'total_samples': perf['total'],
                    'error_rate': 1.0 - perf['accuracy']
                })
        
        # Sort by error rate (descending)
        problematic.sort(key=lambda x: x['error_rate'], reverse=True)
        return problematic[:5]  # Top 5 most problematic
    
    def _calculate_adaptation_effectiveness(self) -> Dict[str, Any]:
        """Calculate effectiveness of parameter adaptations."""
        if not self.adaptation_history:
            return {'effectiveness': 'no_adaptations'}
        
        # Simple effectiveness measure based on accuracy before/after adaptations
        effectiveness = {
            'total_adaptations': len(self.adaptation_history),
            'recent_effectiveness': 'unknown'
        }
        
        if len(self.feedback_history) >= 2:
            pre_adaptation_accuracy = np.mean([r['accuracy'] for r in self.feedback_history[:-1]])
            post_adaptation_accuracy = self.feedback_history[-1]['accuracy']
            
            if post_adaptation_accuracy > pre_adaptation_accuracy + 0.05:
                effectiveness['recent_effectiveness'] = 'positive'
            elif post_adaptation_accuracy < pre_adaptation_accuracy - 0.05:
                effectiveness['recent_effectiveness'] = 'negative'
            else:
                effectiveness['recent_effectiveness'] = 'neutral'
        
        return effectiveness
    
    def _suggest_confidence_threshold_changes(self) -> Dict[str, float]:
        """Suggest confidence threshold changes based on performance."""
        suggestions = {}
        
        for category, perf in self.category_performance.items():
            if perf['total'] >= 5:
                if perf['accuracy'] < 0.6:
                    suggestions[category] = 0.3  # Lower threshold for poor performers
                elif perf['accuracy'] > 0.9:
                    suggestions[category] = 0.7  # Higher threshold for good performers
        
        return suggestions
    
    def _suggest_selection_strategy_changes(self) -> str:
        """Suggest selection strategy changes."""
        if self._has_category_imbalance():
            return 'balanced'
        elif self._calculate_performance_trend() == 'declining':
            return 'diversity'
        else:
            return 'uncertainty_diversity'
    
    def _suggest_priority_weight_changes(self) -> Dict[str, float]:
        """Suggest priority weight changes."""
        suggestions = {}
        
        trend = self._calculate_performance_trend()
        if trend == 'declining':
            suggestions['uncertainty_weight'] = 0.8
            suggestions['diversity_weight'] = 0.2
        elif trend == 'improving':
            suggestions['uncertainty_weight'] = 0.6
            suggestions['diversity_weight'] = 0.4
        
        return suggestions
    
    def _suggest_model_weight_changes(self) -> Dict[str, float]:
        """Suggest model weight changes based on individual model performance."""
        suggestions = {}
        
        # This would require tracking individual model performance
        # For now, return empty suggestions
        return suggestions


def create_feedback_loop(config: Dict[str, Any]) -> FeedbackLoop:
    """Factory function to create feedback loop."""
    return FeedbackLoop(config)