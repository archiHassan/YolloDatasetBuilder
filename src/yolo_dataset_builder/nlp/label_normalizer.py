"""
NLP-based label normalization for category mapping and standardization.
"""

import logging
from typing import Dict, List, Set, Optional, Tuple, Any
import re
from collections import defaultdict, Counter
import json

logger = logging.getLogger(__name__)


class LabelNormalizer:
    """NLP-based label normalizer for category standardization."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize label normalizer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.nlp_config = config.get('nlp', {})
        
        # Normalization settings
        self.case_sensitive = self.nlp_config.get('case_sensitive', False)
        self.remove_plurals = self.nlp_config.get('remove_plurals', True)
        self.expand_abbreviations = self.nlp_config.get('expand_abbreviations', True)
        self.similarity_threshold = self.nlp_config.get('similarity_threshold', 0.8)
        
        # Initialize components
        self.spacy_model = None
        self.stemmer = None
        self.lemmatizer = None
        
        # Built-in mappings
        self.synonym_mappings = self._load_synonym_mappings()
        self.abbreviation_mappings = self._load_abbreviation_mappings()
        self.category_hierarchy = self._load_category_hierarchy()
        
        # Runtime mappings
        self.learned_mappings = {}
        self.frequency_counter = Counter()
        
        logger.info("Initialized NLP-based label normalizer")
    
    def load_nlp_models(self) -> bool:
        """Load NLP models (spaCy, NLTK components)."""
        try:
            # Try to load spaCy model
            try:
                import spacy
                self.spacy_model = spacy.load("en_core_web_sm")
                logger.info("Loaded spaCy model: en_core_web_sm")
            except (ImportError, OSError) as e:
                logger.warning(f"spaCy model not available: {e}")
                logger.info("Install with: python -m spacy download en_core_web_sm")
            
            # Try to load NLTK components
            try:
                import nltk
                from nltk.stem import PorterStemmer, WordNetLemmatizer
                from nltk.corpus import wordnet
                
                # Download required NLTK data
                nltk.download('wordnet', quiet=True)
                nltk.download('omw-1.4', quiet=True)
                nltk.download('punkt', quiet=True)
                
                self.stemmer = PorterStemmer()
                self.lemmatizer = WordNetLemmatizer()
                logger.info("Loaded NLTK components")
                
            except ImportError as e:
                logger.warning(f"NLTK not available: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load NLP models: {e}")
            return False
    
    def normalize_label(self, label: str) -> str:
        """
        Normalize a single label using various NLP techniques.
        
        Args:
            label: Input label to normalize
            
        Returns:
            Normalized label
        """
        if not label or not isinstance(label, str):
            return ""
        
        original_label = label
        
        # Basic text cleaning
        label = self._clean_text(label)
        
        # Case normalization
        if not self.case_sensitive:
            label = label.lower()
        
        # Expand abbreviations
        if self.expand_abbreviations:
            label = self._expand_abbreviations(label)
        
        # Apply synonym mappings
        label = self._apply_synonym_mappings(label)
        
        # Remove plurals
        if self.remove_plurals:
            label = self._singularize(label)
        
        # Apply learned mappings
        if label in self.learned_mappings:
            label = self.learned_mappings[label]
        
        # Update frequency counter
        self.frequency_counter[label] += 1
        
        if label != original_label:
            logger.debug(f"Normalized '{original_label}' -> '{label}'")
        
        return label
    
    def normalize_labels(self, labels: List[str]) -> List[str]:
        """
        Normalize a list of labels.
        
        Args:
            labels: List of labels to normalize
            
        Returns:
            List of normalized labels
        """
        return [self.normalize_label(label) for label in labels]
    
    def find_similar_labels(self, target_label: str, candidate_labels: List[str]) -> List[Tuple[str, float]]:
        """
        Find similar labels using various similarity metrics.
        
        Args:
            target_label: Target label to find similarities for
            candidate_labels: List of candidate labels
            
        Returns:
            List of (label, similarity_score) tuples, sorted by similarity
        """
        similarities = []
        target_normalized = self.normalize_label(target_label)
        
        for candidate in candidate_labels:
            candidate_normalized = self.normalize_label(candidate)
            
            # Calculate various similarity metrics
            similarity = self._calculate_similarity(target_normalized, candidate_normalized)
            
            if similarity >= self.similarity_threshold:
                similarities.append((candidate, similarity))
        
        # Sort by similarity score (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities
    
    def build_category_mapping(self, detected_labels: List[str], target_categories: List[str]) -> Dict[str, str]:
        """
        Build mapping from detected labels to target categories.
        
        Args:
            detected_labels: Labels detected by models
            target_categories: Target category set
            
        Returns:
            Dictionary mapping detected labels to target categories
        """
        mapping = {}
        
        for detected_label in detected_labels:
            # Find best matching target category
            similar_categories = self.find_similar_labels(detected_label, target_categories)
            
            if similar_categories:
                best_match = similar_categories[0][0]
                mapping[detected_label] = best_match
                logger.debug(f"Mapped '{detected_label}' -> '{best_match}'")
            else:
                # Check category hierarchy
                hierarchical_match = self._find_hierarchical_match(detected_label, target_categories)
                if hierarchical_match:
                    mapping[detected_label] = hierarchical_match
                else:
                    # Keep original if no match found
                    mapping[detected_label] = detected_label
                    logger.debug(f"No mapping found for '{detected_label}', keeping original")
        
        return mapping
    
    def learn_from_corrections(self, original_label: str, corrected_label: str):
        """
        Learn from human corrections to improve future mappings.
        
        Args:
            original_label: Original detected label
            corrected_label: Human-corrected label
        """
        normalized_original = self.normalize_label(original_label)
        normalized_corrected = self.normalize_label(corrected_label)
        
        if normalized_original != normalized_corrected:
            self.learned_mappings[normalized_original] = normalized_corrected
            logger.info(f"Learned mapping: '{normalized_original}' -> '{normalized_corrected}'")
    
    def get_label_statistics(self) -> Dict[str, Any]:
        """Get statistics about label frequency and mappings."""
        return {
            'total_labels_processed': sum(self.frequency_counter.values()),
            'unique_labels': len(self.frequency_counter),
            'most_common_labels': self.frequency_counter.most_common(10),
            'learned_mappings_count': len(self.learned_mappings),
            'synonym_mappings_count': len(self.synonym_mappings),
            'abbreviation_mappings_count': len(self.abbreviation_mappings)
        }
    
    def export_mappings(self, filepath: str):
        """Export learned mappings to file."""
        mappings_data = {
            'learned_mappings': self.learned_mappings,
            'frequency_counter': dict(self.frequency_counter),
            'config': self.nlp_config
        }
        
        with open(filepath, 'w') as f:
            json.dump(mappings_data, f, indent=2)
        
        logger.info(f"Exported mappings to {filepath}")
    
    def import_mappings(self, filepath: str):
        """Import mappings from file."""
        try:
            with open(filepath, 'r') as f:
                mappings_data = json.load(f)
            
            self.learned_mappings.update(mappings_data.get('learned_mappings', {}))
            self.frequency_counter.update(mappings_data.get('frequency_counter', {}))
            
            logger.info(f"Imported mappings from {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to import mappings: {e}")
    
    def _clean_text(self, text: str) -> str:
        """Clean and preprocess text."""
        # Remove special characters and extra whitespace
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove common prefixes/suffixes
        text = re.sub(r'^(a |an |the )', '', text, flags=re.IGNORECASE)
        text = re.sub(r'( object| item| thing)$', '', text, flags=re.IGNORECASE)
        
        return text
    
    def _expand_abbreviations(self, text: str) -> str:
        """Expand known abbreviations."""
        words = text.split()
        expanded_words = []
        
        for word in words:
            expanded = self.abbreviation_mappings.get(word.lower(), word)
            expanded_words.append(expanded)
        
        return ' '.join(expanded_words)
    
    def _apply_synonym_mappings(self, text: str) -> str:
        """Apply synonym mappings."""
        return self.synonym_mappings.get(text.lower(), text)
    
    def _singularize(self, text: str) -> str:
        """Convert plural forms to singular."""
        if self.lemmatizer:
            words = text.split()
            singular_words = []
            for word in words:
                # Use NLTK lemmatizer
                singular = self.lemmatizer.lemmatize(word, 'n')  # noun lemmatization
                singular_words.append(singular)
            return ' '.join(singular_words)
        else:
            # Simple rule-based singularization
            if text.endswith('ies'):
                return text[:-3] + 'y'
            elif text.endswith('es') and len(text) > 3:
                return text[:-2]
            elif text.endswith('s') and len(text) > 2:
                return text[:-1]
            return text
    
    def _calculate_similarity(self, label1: str, label2: str) -> float:
        """Calculate similarity between two labels."""
        if label1 == label2:
            return 1.0
        
        # Try different similarity metrics
        scores = []
        
        # Jaccard similarity (word-based)
        words1 = set(label1.split())
        words2 = set(label2.split())
        if words1 or words2:
            jaccard = len(words1.intersection(words2)) / len(words1.union(words2))
            scores.append(jaccard)
        
        # Edit distance similarity
        try:
            from fuzzywuzzy import fuzz
            edit_sim = fuzz.ratio(label1, label2) / 100.0
            scores.append(edit_sim)
        except ImportError:
            # Simple character-based similarity
            common_chars = sum(1 for a, b in zip(label1, label2) if a == b)
            max_len = max(len(label1), len(label2))
            if max_len > 0:
                char_sim = common_chars / max_len
                scores.append(char_sim)
        
        # Return maximum similarity
        return max(scores) if scores else 0.0
    
    def _find_hierarchical_match(self, label: str, target_categories: List[str]) -> Optional[str]:
        """Find match using category hierarchy."""
        normalized_label = label.lower()
        
        # Check if label is a subcategory of any target category
        for category in target_categories:
            if category.lower() in self.category_hierarchy:
                subcategories = self.category_hierarchy[category.lower()]
                if normalized_label in subcategories:
                    return category
        
        return None
    
    def _load_synonym_mappings(self) -> Dict[str, str]:
        """Load built-in synonym mappings."""
        return {
            # Animals
            'dog': 'dog',
            'canine': 'dog',
            'puppy': 'dog',
            'cat': 'cat',
            'feline': 'cat',
            'kitten': 'cat',
            'horse': 'horse',
            'equine': 'horse',
            'pony': 'horse',
            
            # Vehicles
            'car': 'car',
            'automobile': 'car',
            'vehicle': 'car',
            'auto': 'car',
            'truck': 'truck',
            'lorry': 'truck',
            'van': 'truck',
            'bicycle': 'bicycle',
            'bike': 'bicycle',
            'motorbike': 'motorcycle',
            'motorcycle': 'motorcycle',
            
            # Food
            'food': 'food',
            'meal': 'food',
            'dish': 'food',
            'fruit': 'fruit',
            'vegetable': 'vegetable',
            'veggie': 'vegetable',
            
            # Common objects
            'cellphone': 'cell phone',
            'mobile': 'cell phone',
            'smartphone': 'cell phone',
            'laptop': 'laptop',
            'notebook': 'laptop',
            'computer': 'laptop',
            'tv': 'tv',
            'television': 'tv',
            'monitor': 'tv'
        }
    
    def _load_abbreviation_mappings(self) -> Dict[str, str]:
        """Load built-in abbreviation mappings."""
        return {
            'tv': 'television',
            'pc': 'computer',
            'car': 'automobile',
            'bike': 'bicycle',
            'phone': 'telephone',
            'pic': 'picture',
            'photo': 'photograph',
            'min': 'minute',
            'max': 'maximum',
            'avg': 'average',
            'std': 'standard',
            'prof': 'professional',
            'biz': 'business',
            'info': 'information',
            'tech': 'technology',
            'auto': 'automobile',
            'moto': 'motorcycle'
        }
    
    def _load_category_hierarchy(self) -> Dict[str, List[str]]:
        """Load category hierarchy for hierarchical matching."""
        return {
            'animal': ['dog', 'cat', 'horse', 'cow', 'sheep', 'pig', 'bird', 'fish'],
            'vehicle': ['car', 'truck', 'motorcycle', 'bicycle', 'bus', 'boat', 'airplane'],
            'food': ['fruit', 'vegetable', 'meat', 'bread', 'cake', 'sandwich', 'pizza'],
            'furniture': ['chair', 'table', 'sofa', 'bed', 'desk', 'cabinet', 'shelf'],
            'electronics': ['tv', 'computer', 'phone', 'camera', 'radio', 'speaker'],
            'clothing': ['shirt', 'pants', 'dress', 'shoes', 'hat', 'jacket', 'tie'],
            'sports': ['ball', 'racket', 'bat', 'glove', 'helmet', 'goal', 'net'],
            'tools': ['hammer', 'screwdriver', 'wrench', 'drill', 'saw', 'knife']
        }


def create_label_normalizer(config: Dict[str, Any]) -> LabelNormalizer:
    """Factory function to create label normalizer."""
    return LabelNormalizer(config)