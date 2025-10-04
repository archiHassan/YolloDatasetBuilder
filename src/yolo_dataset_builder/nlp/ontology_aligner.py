"""
Ontology alignment system for mapping between different category schemes.
"""

import logging
from typing import Dict, List, Set, Optional, Tuple, Any, Union
import json
from pathlib import Path
from collections import defaultdict
import networkx as nx

logger = logging.getLogger(__name__)


class OntologyAligner:
    """System for aligning and mapping between different category ontologies."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ontology aligner.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.ontology_config = config.get('ontology', {})
        
        # Alignment settings
        self.similarity_threshold = self.ontology_config.get('similarity_threshold', 0.7)
        self.use_hierarchy = self.ontology_config.get('use_hierarchy', True)
        self.exact_match_priority = self.ontology_config.get('exact_match_priority', True)
        
        # Ontology storage
        self.source_ontologies = {}  # {name: ontology}
        self.target_ontology = None
        self.alignment_mappings = {}  # {source_ontology: {source_concept: target_concept}}
        
        # Graph for hierarchical reasoning
        self.ontology_graph = nx.DiGraph()
        
        # Built-in ontologies
        self._load_builtin_ontologies()
        
        logger.info("Initialized ontology alignment system")
    
    def load_ontology(self, name: str, ontology: Dict[str, Any], is_target: bool = False):
        """
        Load an ontology into the system.
        
        Args:
            name: Name identifier for the ontology
            ontology: Ontology structure
            is_target: Whether this is the target ontology for alignment
        """
        if is_target:
            self.target_ontology = ontology
            logger.info(f"Loaded target ontology: {name}")
        else:
            self.source_ontologies[name] = ontology
            logger.info(f"Loaded source ontology: {name}")
        
        # Add to graph for hierarchical reasoning
        self._add_to_graph(name, ontology)
    
    def load_coco_ontology(self):
        """Load COCO dataset ontology as target."""
        coco_ontology = {
            'name': 'COCO',
            'version': '2017',
            'categories': {
                'person': {'id': 1, 'supercategory': 'person'},
                'bicycle': {'id': 2, 'supercategory': 'vehicle'},
                'car': {'id': 3, 'supercategory': 'vehicle'},
                'motorcycle': {'id': 4, 'supercategory': 'vehicle'},
                'airplane': {'id': 5, 'supercategory': 'vehicle'},
                'bus': {'id': 6, 'supercategory': 'vehicle'},
                'train': {'id': 7, 'supercategory': 'vehicle'},
                'truck': {'id': 8, 'supercategory': 'vehicle'},
                'boat': {'id': 9, 'supercategory': 'vehicle'},
                'traffic light': {'id': 10, 'supercategory': 'outdoor'},
                'fire hydrant': {'id': 11, 'supercategory': 'outdoor'},
                'stop sign': {'id': 12, 'supercategory': 'outdoor'},
                'parking meter': {'id': 13, 'supercategory': 'outdoor'},
                'bench': {'id': 14, 'supercategory': 'outdoor'},
                'bird': {'id': 15, 'supercategory': 'animal'},
                'cat': {'id': 16, 'supercategory': 'animal'},
                'dog': {'id': 17, 'supercategory': 'animal'},
                'horse': {'id': 18, 'supercategory': 'animal'},
                'sheep': {'id': 19, 'supercategory': 'animal'},
                'cow': {'id': 20, 'supercategory': 'animal'},
                'elephant': {'id': 21, 'supercategory': 'animal'},
                'bear': {'id': 22, 'supercategory': 'animal'},
                'zebra': {'id': 23, 'supercategory': 'animal'},
                'giraffe': {'id': 24, 'supercategory': 'animal'},
                'backpack': {'id': 25, 'supercategory': 'accessory'},
                'umbrella': {'id': 26, 'supercategory': 'accessory'},
                'handbag': {'id': 27, 'supercategory': 'accessory'},
                'tie': {'id': 28, 'supercategory': 'accessory'},
                'suitcase': {'id': 29, 'supercategory': 'accessory'},
                'frisbee': {'id': 30, 'supercategory': 'sports'},
                'skis': {'id': 31, 'supercategory': 'sports'},
                'snowboard': {'id': 32, 'supercategory': 'sports'},
                'sports ball': {'id': 33, 'supercategory': 'sports'},
                'kite': {'id': 34, 'supercategory': 'sports'},
                'baseball bat': {'id': 35, 'supercategory': 'sports'},
                'baseball glove': {'id': 36, 'supercategory': 'sports'},
                'skateboard': {'id': 37, 'supercategory': 'sports'},
                'surfboard': {'id': 38, 'supercategory': 'sports'},
                'tennis racket': {'id': 39, 'supercategory': 'sports'},
                'bottle': {'id': 40, 'supercategory': 'kitchen'},
                'wine glass': {'id': 41, 'supercategory': 'kitchen'},
                'cup': {'id': 42, 'supercategory': 'kitchen'},
                'fork': {'id': 43, 'supercategory': 'kitchen'},
                'knife': {'id': 44, 'supercategory': 'kitchen'},
                'spoon': {'id': 45, 'supercategory': 'kitchen'},
                'bowl': {'id': 46, 'supercategory': 'kitchen'},
                'banana': {'id': 47, 'supercategory': 'food'},
                'apple': {'id': 48, 'supercategory': 'food'},
                'sandwich': {'id': 49, 'supercategory': 'food'},
                'orange': {'id': 50, 'supercategory': 'food'},
                'broccoli': {'id': 51, 'supercategory': 'food'},
                'carrot': {'id': 52, 'supercategory': 'food'},
                'hot dog': {'id': 53, 'supercategory': 'food'},
                'pizza': {'id': 54, 'supercategory': 'food'},
                'donut': {'id': 55, 'supercategory': 'food'},
                'cake': {'id': 56, 'supercategory': 'food'},
                'chair': {'id': 57, 'supercategory': 'furniture'},
                'couch': {'id': 58, 'supercategory': 'furniture'},
                'potted plant': {'id': 59, 'supercategory': 'furniture'},
                'bed': {'id': 60, 'supercategory': 'furniture'},
                'dining table': {'id': 61, 'supercategory': 'furniture'},
                'toilet': {'id': 62, 'supercategory': 'furniture'},
                'tv': {'id': 63, 'supercategory': 'electronic'},
                'laptop': {'id': 64, 'supercategory': 'electronic'},
                'mouse': {'id': 65, 'supercategory': 'electronic'},
                'remote': {'id': 66, 'supercategory': 'electronic'},
                'keyboard': {'id': 67, 'supercategory': 'electronic'},
                'cell phone': {'id': 68, 'supercategory': 'electronic'},
                'microwave': {'id': 69, 'supercategory': 'appliance'},
                'oven': {'id': 70, 'supercategory': 'appliance'},
                'toaster': {'id': 71, 'supercategory': 'appliance'},
                'sink': {'id': 72, 'supercategory': 'appliance'},
                'refrigerator': {'id': 73, 'supercategory': 'appliance'},
                'book': {'id': 74, 'supercategory': 'indoor'},
                'clock': {'id': 75, 'supercategory': 'indoor'},
                'vase': {'id': 76, 'supercategory': 'indoor'},
                'scissors': {'id': 77, 'supercategory': 'indoor'},
                'teddy bear': {'id': 78, 'supercategory': 'indoor'},
                'hair drier': {'id': 79, 'supercategory': 'indoor'},
                'toothbrush': {'id': 80, 'supercategory': 'indoor'}
            }
        }
        
        self.load_ontology('COCO', coco_ontology, is_target=True)
    
    def align_ontologies(self, source_name: str) -> Dict[str, str]:
        """
        Align a source ontology to the target ontology.
        
        Args:
            source_name: Name of source ontology to align
            
        Returns:
            Dictionary mapping source concepts to target concepts
        """
        if source_name not in self.source_ontologies:
            raise ValueError(f"Source ontology '{source_name}' not found")
        
        if not self.target_ontology:
            raise ValueError("No target ontology loaded")
        
        source_ontology = self.source_ontologies[source_name]
        alignment = {}
        
        source_concepts = self._extract_concepts(source_ontology)
        target_concepts = self._extract_concepts(self.target_ontology)
        
        logger.info(f"Aligning {len(source_concepts)} source concepts to {len(target_concepts)} target concepts")
        
        for source_concept in source_concepts:
            target_concept = self._find_best_alignment(source_concept, target_concepts, source_name)
            if target_concept:
                alignment[source_concept] = target_concept
                logger.debug(f"Aligned '{source_concept}' -> '{target_concept}'")
            else:
                logger.debug(f"No alignment found for '{source_concept}'")
        
        # Store alignment
        self.alignment_mappings[source_name] = alignment
        
        logger.info(f"Created {len(alignment)} alignments for {source_name}")
        return alignment
    
    def map_category(self, category: str, source_ontology: str = None) -> Optional[str]:
        """
        Map a category using existing alignments.
        
        Args:
            category: Category to map
            source_ontology: Source ontology name (if None, try all)
            
        Returns:
            Mapped category or None if no mapping found
        """
        if source_ontology:
            if source_ontology in self.alignment_mappings:
                return self.alignment_mappings[source_ontology].get(category)
        else:
            # Try all source ontologies
            for ont_name, mappings in self.alignment_mappings.items():
                if category in mappings:
                    return mappings[category]
        
        return None
    
    def get_hierarchy_path(self, concept: str, ontology_name: str = None) -> List[str]:
        """
        Get hierarchical path for a concept.
        
        Args:
            concept: Concept to get path for
            ontology_name: Ontology name (uses target if None)
            
        Returns:
            List representing path from root to concept
        """
        try:
            if ontology_name:
                node = f"{ontology_name}:{concept}"
            else:
                node = concept
            
            # Find path to root
            paths = []
            for root in [n for n in self.ontology_graph.nodes() if self.ontology_graph.in_degree(n) == 0]:
                try:
                    path = nx.shortest_path(self.ontology_graph, root, node)
                    paths.append(path)
                except nx.NetworkXNoPath:
                    continue
            
            # Return shortest path
            if paths:
                return min(paths, key=len)
            else:
                return [concept]
                
        except Exception as e:
            logger.error(f"Error getting hierarchy path: {e}")
            return [concept]
    
    def find_common_ancestor(self, concept1: str, concept2: str) -> Optional[str]:
        """Find common ancestor of two concepts in hierarchy."""
        try:
            path1 = self.get_hierarchy_path(concept1)
            path2 = self.get_hierarchy_path(concept2)
            
            # Find common prefix
            common_path = []
            for c1, c2 in zip(path1, path2):
                if c1 == c2:
                    common_path.append(c1)
                else:
                    break
            
            return common_path[-1] if common_path else None
            
        except Exception as e:
            logger.error(f"Error finding common ancestor: {e}")
            return None
    
    def export_alignments(self, filepath: str):
        """Export alignment mappings to file."""
        export_data = {
            'alignments': self.alignment_mappings,
            'target_ontology': self.target_ontology,
            'source_ontologies': list(self.source_ontologies.keys()),
            'config': self.ontology_config
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported alignments to {filepath}")
    
    def import_alignments(self, filepath: str):
        """Import alignment mappings from file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.alignment_mappings.update(data.get('alignments', {}))
            if 'target_ontology' in data:
                self.target_ontology = data['target_ontology']
            
            logger.info(f"Imported alignments from {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to import alignments: {e}")
    
    def _extract_concepts(self, ontology: Dict[str, Any]) -> List[str]:
        """Extract concept names from ontology."""
        if 'categories' in ontology:
            return list(ontology['categories'].keys())
        elif 'concepts' in ontology:
            return list(ontology['concepts'].keys())
        else:
            # Try to infer structure
            for key, value in ontology.items():
                if isinstance(value, dict) and len(value) > 5:  # Likely concepts
                    return list(value.keys())
            return []
    
    def _find_best_alignment(self, source_concept: str, target_concepts: List[str], source_name: str) -> Optional[str]:
        """Find best alignment for a source concept."""
        candidates = []
        
        # 1. Exact match (case insensitive)
        for target in target_concepts:
            if source_concept.lower() == target.lower():
                candidates.append((target, 1.0))
        
        if candidates and self.exact_match_priority:
            return candidates[0][0]
        
        # 2. Substring matching
        for target in target_concepts:
            if source_concept.lower() in target.lower() or target.lower() in source_concept.lower():
                similarity = len(set(source_concept.lower()) & set(target.lower())) / len(set(source_concept.lower()) | set(target.lower()))
                candidates.append((target, similarity * 0.9))  # Slightly lower than exact
        
        # 3. Word-based similarity
        source_words = set(source_concept.lower().split())
        for target in target_concepts:
            target_words = set(target.lower().split())
            if source_words & target_words:  # Common words
                jaccard = len(source_words & target_words) / len(source_words | target_words)
                if jaccard >= self.similarity_threshold:
                    candidates.append((target, jaccard * 0.8))
        
        # 4. Hierarchical reasoning
        if self.use_hierarchy:
            hierarchical_match = self._find_hierarchical_match(source_concept, target_concepts, source_name)
            if hierarchical_match:
                candidates.append((hierarchical_match, 0.7))
        
        # 5. Character-based similarity (edit distance)
        try:
            from fuzzywuzzy import fuzz
            for target in target_concepts:
                ratio = fuzz.ratio(source_concept.lower(), target.lower()) / 100.0
                if ratio >= self.similarity_threshold:
                    candidates.append((target, ratio * 0.6))
        except ImportError:
            pass
        
        # Return best candidate
        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]
        
        return None
    
    def _find_hierarchical_match(self, source_concept: str, target_concepts: List[str], source_name: str) -> Optional[str]:
        """Find match using hierarchical reasoning."""
        # This is a simplified version - in practice, you'd use more sophisticated reasoning
        source_path = self.get_hierarchy_path(source_concept, source_name)
        
        for target in target_concepts:
            target_path = self.get_hierarchy_path(target)
            
            # Check if they share common ancestors
            common_ancestor = self.find_common_ancestor(source_concept, target)
            if common_ancestor and common_ancestor != source_concept and common_ancestor != target:
                return target
        
        return None
    
    def _add_to_graph(self, name: str, ontology: Dict[str, Any]):
        """Add ontology to graph for hierarchical reasoning."""
        try:
            categories = ontology.get('categories', {})
            
            for concept, details in categories.items():
                node_id = f"{name}:{concept}"
                self.ontology_graph.add_node(node_id, **details)
                
                # Add hierarchy edges
                if 'supercategory' in details:
                    parent_id = f"{name}:{details['supercategory']}"
                    self.ontology_graph.add_edge(parent_id, node_id)
        
        except Exception as e:
            logger.error(f"Error adding ontology to graph: {e}")
    
    def _load_builtin_ontologies(self):
        """Load built-in ontologies for common cases."""
        # ImageNet-style ontology
        imagenet_ontology = {
            'name': 'ImageNet-subset',
            'categories': {
                'dog': {'supercategory': 'animal'},
                'cat': {'supercategory': 'animal'},
                'bird': {'supercategory': 'animal'},
                'horse': {'supercategory': 'animal'},
                'car': {'supercategory': 'vehicle'},
                'truck': {'supercategory': 'vehicle'},
                'airplane': {'supercategory': 'vehicle'},
                'bottle': {'supercategory': 'object'},
                'chair': {'supercategory': 'furniture'},
                'table': {'supercategory': 'furniture'}
            }
        }
        
        self.load_ontology('ImageNet', imagenet_ontology)


def create_ontology_aligner(config: Dict[str, Any]) -> OntologyAligner:
    """Factory function to create ontology aligner."""
    return OntologyAligner(config)