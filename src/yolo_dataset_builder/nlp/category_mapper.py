"""
Custom category mapping support for flexible dataset annotation.
"""

import logging
from typing import Dict, List, Set, Optional, Tuple, Any, Union
import json
import yaml
from pathlib import Path
from collections import defaultdict, Counter
import re

logger = logging.getLogger(__name__)


class CategoryMapper:
    """Custom category mapping system for flexible annotation workflows."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize category mapper.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.mapping_config = config.get('category_mapping', {})
        
        # Mapping configuration
        self.default_category = self.mapping_config.get('default_category', 'unknown')
        self.case_sensitive = self.mapping_config.get('case_sensitive', False)
        self.allow_multiple_mappings = self.mapping_config.get('allow_multiple_mappings', False)
        self.confidence_threshold = self.mapping_config.get('confidence_threshold', 0.5)
        
        # Mapping storage
        self.custom_mappings = {}  # {source: target}
        self.rule_based_mappings = []  # List of mapping rules
        self.pattern_mappings = {}  # {regex_pattern: target}
        self.conditional_mappings = {}  # {condition: mapping}
        
        # Statistics
        self.mapping_stats = Counter()
        self.unmapped_categories = set()
        
        # Load built-in mappings
        self._load_builtin_mappings()
        
        logger.info("Initialized custom category mapper")
    
    def add_custom_mapping(self, source: str, target: str, confidence: float = 1.0):
        """
        Add custom mapping from source to target category.
        
        Args:
            source: Source category name
            target: Target category name  
            confidence: Mapping confidence (0.0 to 1.0)
        """
        if not self.case_sensitive:
            source = source.lower()
        
        if self.allow_multiple_mappings:
            if source not in self.custom_mappings:
                self.custom_mappings[source] = []
            self.custom_mappings[source].append({'target': target, 'confidence': confidence})
        else:
            self.custom_mappings[source] = {'target': target, 'confidence': confidence}
        
        logger.debug(f"Added custom mapping: '{source}' -> '{target}' (confidence: {confidence})")
    
    def add_pattern_mapping(self, pattern: str, target: str, confidence: float = 1.0):
        """
        Add regex pattern-based mapping.
        
        Args:
            pattern: Regex pattern to match
            target: Target category name
            confidence: Mapping confidence
        """
        try:
            compiled_pattern = re.compile(pattern, re.IGNORECASE if not self.case_sensitive else 0)
            self.pattern_mappings[compiled_pattern] = {'target': target, 'confidence': confidence}
            logger.debug(f"Added pattern mapping: '{pattern}' -> '{target}'")
        except re.error as e:
            logger.error(f"Invalid regex pattern '{pattern}': {e}")
    
    def add_rule_mapping(self, rule: Dict[str, Any]):
        """
        Add rule-based mapping.
        
        Args:
            rule: Rule dictionary with conditions and actions
        """
        required_fields = ['condition', 'action']
        if not all(field in rule for field in required_fields):
            logger.error(f"Rule missing required fields: {required_fields}")
            return
        
        self.rule_based_mappings.append(rule)
        logger.debug(f"Added rule mapping: {rule}")
    
    def map_category(self, category: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Map a category using all available mapping strategies.
        
        Args:
            category: Category to map
            metadata: Additional metadata for rule-based mapping
            
        Returns:
            Dictionary with mapping result
        """
        if not category:
            return self._create_mapping_result(self.default_category, 0.0, 'empty_input')
        
        original_category = category
        if not self.case_sensitive:
            category = category.lower()
        
        # Strategy 1: Direct custom mappings
        result = self._apply_custom_mappings(category)
        if result['confidence'] >= self.confidence_threshold:
            self.mapping_stats[result['method']] += 1
            return result
        
        # Strategy 2: Pattern-based mappings
        result = self._apply_pattern_mappings(category)
        if result['confidence'] >= self.confidence_threshold:
            self.mapping_stats[result['method']] += 1
            return result
        
        # Strategy 3: Rule-based mappings
        result = self._apply_rule_mappings(category, metadata)
        if result['confidence'] >= self.confidence_threshold:
            self.mapping_stats[result['method']] += 1
            return result
        
        # Strategy 4: Built-in category mappings
        result = self._apply_builtin_mappings(category)
        if result['confidence'] >= self.confidence_threshold:
            self.mapping_stats[result['method']] += 1
            return result
        
        # No mapping found - use default
        self.unmapped_categories.add(original_category)
        result = self._create_mapping_result(self.default_category, 0.0, 'no_mapping')
        self.mapping_stats['no_mapping'] += 1
        
        logger.debug(f"No mapping found for '{original_category}', using default: '{self.default_category}'")
        return result
    
    def map_categories(self, categories: List[str], metadata_list: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Map multiple categories.
        
        Args:
            categories: List of categories to map
            metadata_list: Optional list of metadata for each category
            
        Returns:
            List of mapping results
        """
        if metadata_list is None:
            metadata_list = [None] * len(categories)
        
        results = []
        for category, metadata in zip(categories, metadata_list):
            result = self.map_category(category, metadata)
            results.append(result)
        
        return results
    
    def load_mappings_from_file(self, filepath: str):
        """
        Load mappings from configuration file (JSON or YAML).
        
        Args:
            filepath: Path to mapping configuration file
        """
        try:
            filepath = Path(filepath)
            
            with open(filepath, 'r') as f:
                if filepath.suffix.lower() in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            
            # Load custom mappings
            if 'custom_mappings' in data:
                for source, target_info in data['custom_mappings'].items():
                    if isinstance(target_info, str):
                        self.add_custom_mapping(source, target_info)
                    else:
                        self.add_custom_mapping(source, target_info['target'], target_info.get('confidence', 1.0))
            
            # Load pattern mappings
            if 'pattern_mappings' in data:
                for pattern, target_info in data['pattern_mappings'].items():
                    if isinstance(target_info, str):
                        self.add_pattern_mapping(pattern, target_info)
                    else:
                        self.add_pattern_mapping(pattern, target_info['target'], target_info.get('confidence', 1.0))
            
            # Load rule mappings
            if 'rule_mappings' in data:
                for rule in data['rule_mappings']:
                    self.add_rule_mapping(rule)
            
            logger.info(f"Loaded mappings from {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to load mappings from {filepath}: {e}")
    
    def save_mappings_to_file(self, filepath: str):
        """
        Save current mappings to configuration file.
        
        Args:
            filepath: Path to save mapping configuration
        """
        try:
            # Prepare data for export
            export_data = {
                'custom_mappings': self.custom_mappings,
                'pattern_mappings': {pattern.pattern: mapping for pattern, mapping in self.pattern_mappings.items()},
                'rule_mappings': self.rule_based_mappings,
                'config': self.mapping_config,
                'statistics': {
                    'mapping_stats': dict(self.mapping_stats),
                    'unmapped_categories': list(self.unmapped_categories)
                }
            }
            
            filepath = Path(filepath)
            
            with open(filepath, 'w') as f:
                if filepath.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(export_data, f, indent=2)
                else:
                    json.dump(export_data, f, indent=2)
            
            logger.info(f"Saved mappings to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save mappings to {filepath}: {e}")
    
    def get_mapping_statistics(self) -> Dict[str, Any]:
        """Get statistics about mapping usage and performance."""
        total_mappings = sum(self.mapping_stats.values())
        
        return {
            'total_mappings_applied': total_mappings,
            'mapping_method_counts': dict(self.mapping_stats),
            'mapping_method_percentages': {
                method: (count / total_mappings * 100) if total_mappings > 0 else 0
                for method, count in self.mapping_stats.items()
            },
            'custom_mappings_count': len(self.custom_mappings),
            'pattern_mappings_count': len(self.pattern_mappings),
            'rule_mappings_count': len(self.rule_based_mappings),
            'unmapped_categories_count': len(self.unmapped_categories),
            'unmapped_categories': list(self.unmapped_categories)
        }
    
    def suggest_mappings(self, unmapped_categories: List[str], available_targets: List[str]) -> Dict[str, List[Tuple[str, float]]]:
        """
        Suggest mappings for unmapped categories.
        
        Args:
            unmapped_categories: Categories that need mapping
            available_targets: Available target categories
            
        Returns:
            Dictionary with suggestions for each unmapped category
        """
        suggestions = {}
        
        for category in unmapped_categories:
            category_suggestions = []
            
            # Use fuzzy matching for suggestions
            try:
                from fuzzywuzzy import fuzz
                for target in available_targets:
                    similarity = fuzz.ratio(category.lower(), target.lower()) / 100.0
                    if similarity > 0.6:  # Threshold for suggestions
                        category_suggestions.append((target, similarity))
            except ImportError:
                # Fall back to simple substring matching
                for target in available_targets:
                    if category.lower() in target.lower() or target.lower() in category.lower():
                        similarity = len(set(category.lower()) & set(target.lower())) / len(set(category.lower()) | set(target.lower()))
                        category_suggestions.append((target, similarity))
            
            # Sort by similarity
            category_suggestions.sort(key=lambda x: x[1], reverse=True)
            suggestions[category] = category_suggestions[:5]  # Top 5 suggestions
        
        return suggestions
    
    def validate_mappings(self) -> Dict[str, List[str]]:
        """Validate current mappings and return issues."""
        issues = defaultdict(list)
        
        # Check for circular mappings
        for source, target_info in self.custom_mappings.items():
            if isinstance(target_info, dict):
                target = target_info['target']
            else:
                target = target_info
            
            if target in self.custom_mappings:
                issues['circular_mappings'].append(f"{source} -> {target}")
        
        # Check for invalid regex patterns
        for pattern in self.pattern_mappings.keys():
            try:
                re.compile(pattern.pattern)
            except re.error:
                issues['invalid_patterns'].append(pattern.pattern)
        
        # Check for missing rule fields
        for i, rule in enumerate(self.rule_based_mappings):
            required_fields = ['condition', 'action']
            missing_fields = [field for field in required_fields if field not in rule]
            if missing_fields:
                issues['invalid_rules'].append(f"Rule {i}: missing {missing_fields}")
        
        return dict(issues)
    
    def _apply_custom_mappings(self, category: str) -> Dict[str, Any]:
        """Apply direct custom mappings."""
        if category in self.custom_mappings:
            mapping = self.custom_mappings[category]
            
            if isinstance(mapping, dict):
                return self._create_mapping_result(mapping['target'], mapping['confidence'], 'custom_mapping')
            elif isinstance(mapping, list):
                # Multiple mappings - return highest confidence
                best_mapping = max(mapping, key=lambda x: x['confidence'])
                return self._create_mapping_result(best_mapping['target'], best_mapping['confidence'], 'custom_mapping')
        
        return self._create_mapping_result(None, 0.0, 'no_match')
    
    def _apply_pattern_mappings(self, category: str) -> Dict[str, Any]:
        """Apply regex pattern-based mappings."""
        for pattern, mapping in self.pattern_mappings.items():
            if pattern.search(category):
                return self._create_mapping_result(mapping['target'], mapping['confidence'], 'pattern_mapping')
        
        return self._create_mapping_result(None, 0.0, 'no_match')
    
    def _apply_rule_mappings(self, category: str, metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply rule-based mappings."""
        for rule in self.rule_based_mappings:
            if self._evaluate_rule_condition(rule['condition'], category, metadata):
                action = rule['action']
                confidence = rule.get('confidence', 0.8)
                
                if isinstance(action, str):
                    return self._create_mapping_result(action, confidence, 'rule_mapping')
                elif isinstance(action, dict) and 'target' in action:
                    return self._create_mapping_result(action['target'], confidence, 'rule_mapping')
        
        return self._create_mapping_result(None, 0.0, 'no_match')
    
    def _apply_builtin_mappings(self, category: str) -> Dict[str, Any]:
        """Apply built-in category mappings."""
        # Simple built-in mappings for common cases
        builtin_map = {
            'automobile': 'car',
            'motorbike': 'motorcycle',
            'cellphone': 'cell phone',
            'mobile': 'cell phone',
            'tv': 'tv',
            'laptop': 'laptop',
            'notebook': 'laptop'
        }
        
        if category in builtin_map:
            return self._create_mapping_result(builtin_map[category], 0.9, 'builtin_mapping')
        
        return self._create_mapping_result(None, 0.0, 'no_match')
    
    def _evaluate_rule_condition(self, condition: Dict[str, Any], category: str, metadata: Optional[Dict[str, Any]]) -> bool:
        """Evaluate rule condition."""
        try:
            condition_type = condition.get('type', 'exact')
            
            if condition_type == 'exact':
                return category == condition.get('value', '')
            
            elif condition_type == 'contains':
                return condition.get('value', '') in category
            
            elif condition_type == 'starts_with':
                return category.startswith(condition.get('value', ''))
            
            elif condition_type == 'ends_with':
                return category.endswith(condition.get('value', ''))
            
            elif condition_type == 'regex':
                pattern = condition.get('pattern', '')
                return bool(re.search(pattern, category, re.IGNORECASE if not self.case_sensitive else 0))
            
            elif condition_type == 'metadata' and metadata:
                field = condition.get('field', '')
                value = condition.get('value', '')
                return metadata.get(field) == value
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating rule condition: {e}")
            return False
    
    def _create_mapping_result(self, target: Optional[str], confidence: float, method: str) -> Dict[str, Any]:
        """Create standardized mapping result."""
        return {
            'target': target,
            'confidence': confidence,
            'method': method,
            'mapped': target is not None
        }
    
    def _load_builtin_mappings(self):
        """Load built-in mappings for common scenarios."""
        # Vehicle mappings
        self.add_custom_mapping('automobile', 'car', 1.0)
        self.add_custom_mapping('vehicle', 'car', 0.8)
        self.add_custom_mapping('motorbike', 'motorcycle', 1.0)
        self.add_custom_mapping('bike', 'bicycle', 0.9)
        
        # Electronics mappings
        self.add_custom_mapping('cellphone', 'cell phone', 1.0)
        self.add_custom_mapping('mobile', 'cell phone', 1.0)
        self.add_custom_mapping('smartphone', 'cell phone', 1.0)
        self.add_custom_mapping('television', 'tv', 1.0)
        self.add_custom_mapping('notebook', 'laptop', 1.0)
        self.add_custom_mapping('computer', 'laptop', 0.8)
        
        # Animal mappings
        self.add_custom_mapping('canine', 'dog', 1.0)
        self.add_custom_mapping('puppy', 'dog', 1.0)
        self.add_custom_mapping('feline', 'cat', 1.0)
        self.add_custom_mapping('kitten', 'cat', 1.0)
        
        # Add pattern mappings for plurals
        self.add_pattern_mapping(r'(\w+)s$', lambda m: m.group(1), 0.8)  # Simple plural removal
        
        logger.debug("Loaded built-in category mappings")


def create_category_mapper(config: Dict[str, Any]) -> CategoryMapper:
    """Factory function to create category mapper."""
    return CategoryMapper(config)