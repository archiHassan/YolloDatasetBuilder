"""CLIP annotation module for image classification and label enhancement."""

import torch
import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
import logging

from ..utils.image_utils import ImageUtils

logger = logging.getLogger(__name__)


class CLIPAnnotator:
    """CLIP-based image classification and label enhancement."""
    
    def __init__(self, config: Dict):
        """Initialize CLIP annotator.
        
        Args:
            config: Configuration dictionary containing CLIP settings
        """
        self.config = config
        self.model_config = config.get('models', {}).get('clip', {})
        
        # Model parameters
        self.model_name = self.model_config.get('model_name', 'openai/clip-vit-base-patch32')
        self.device = self._setup_device()
        
        # Label enhancement settings
        self.enhancement_categories = self.model_config.get('enhancement_categories', {
            'scene_type': [
                'indoor scene', 'outdoor scene', 'urban environment', 'natural landscape',
                'kitchen', 'bedroom', 'living room', 'office', 'restaurant', 'street'
            ],
            'lighting': [
                'bright lighting', 'dim lighting', 'natural sunlight', 'artificial lighting',
                'golden hour', 'blue hour', 'dramatic lighting', 'soft lighting'
            ],
            'style': [
                'photograph', 'painting', 'sketch', 'cartoon', 'digital art',
                'vintage style', 'modern style', 'artistic style'
            ],
            'quality': [
                'high quality', 'professional photo', 'amateur photo', 'blurry image',
                'sharp image', 'well composed', 'poor composition'
            ]
        })
        
        # Model components
        self.model = None
        self.processor = None
        self.tokenizer = None
        
        # Statistics
        self.stats = {
            'images_processed': 0,
            'classifications_made': 0,
            'labels_enhanced': 0
        }
    
    def _setup_device(self) -> str:
        """Setup computing device (CPU/CUDA).
        
        Returns:
            Device string
        """
        device_config = self.model_config.get('device', 'auto')
        
        if device_config == 'auto':
            if torch.cuda.is_available():
                device = 'cuda'
                logger.info(f"Using CUDA device: {torch.cuda.get_device_name()}")
            else:
                device = 'cpu'
                logger.info("Using CPU device")
        else:
            device = device_config
            logger.info(f"Using specified device: {device}")
        
        return device
    
    def load_model(self) -> None:
        """Load CLIP model and processor."""
        try:
            logger.info(f"Loading CLIP model: {self.model_name}")
            
            # Try to import transformers CLIP
            try:
                from transformers import CLIPProcessor, CLIPModel
                
                # Load processor and model
                self.processor = CLIPProcessor.from_pretrained(self.model_name)
                self.model = CLIPModel.from_pretrained(self.model_name)
                
            except ImportError:
                logger.warning("transformers not available, trying open_clip")
                
                # Fallback to open_clip
                try:
                    import open_clip
                    
                    model_name, pretrained = self.model_name.split('/')[-1], 'openai'
                    self.model, _, self.processor = open_clip.create_model_and_transforms(
                        model_name, pretrained=pretrained
                    )
                    self.tokenizer = open_clip.get_tokenizer(model_name)
                    
                except ImportError:
                    logger.error("Neither transformers nor open_clip available")
                    raise ImportError("CLIP model requires transformers or open_clip")
            
            # Move to device
            self.model.to(self.device)
            self.model.eval()
            
            logger.info("CLIP model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            raise RuntimeError(f"Could not load CLIP model: {e}")
    
    def classify_image(
        self,
        image_path: str,
        candidate_labels: Optional[List[str]] = None,
        return_probabilities: bool = True
    ) -> Dict:
        """Classify image using CLIP.
        
        Args:
            image_path: Path to image file
            candidate_labels: List of candidate labels (uses defaults if None)
            return_probabilities: Whether to return probability scores
            
        Returns:
            Dictionary containing classification results
        """
        if self.model is None:
            raise RuntimeError("CLIP model not loaded. Call load_model() first.")
        
        try:
            # Load image
            image = ImageUtils.load_image_pil(image_path)
            if image is None:
                return self._empty_classification_result(image_path, "Failed to load image")
            
            # Use default labels if none provided
            if candidate_labels is None:
                candidate_labels = self._get_default_labels()
            
            # Run classification
            classification_results = self._classify_with_labels(image, candidate_labels)
            
            # Update statistics
            self.stats['images_processed'] += 1
            self.stats['classifications_made'] += len(classification_results)
            
            # Create result dictionary
            result = {
                'image_path': image_path,
                'image_shape': [image.height, image.width, 3],
                'classifications': classification_results,
                'candidate_labels': candidate_labels,
                'success': True,
                'error': None
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error classifying image {image_path}: {e}")
            return self._empty_classification_result(image_path, str(e))
    
    def enhance_detection_labels(
        self,
        detections: List[Dict],
        image_path: str
    ) -> List[Dict]:
        """Enhance object detection labels using CLIP.
        
        Args:
            detections: List of detection dictionaries
            image_path: Path to source image
            
        Returns:
            Enhanced detections with CLIP-based label refinement
        """
        if self.model is None:
            logger.warning("CLIP model not loaded, returning original detections")
            return detections
        
        try:
            # Load full image
            full_image = ImageUtils.load_image_pil(image_path)
            if full_image is None:
                logger.warning(f"Could not load image {image_path} for label enhancement")
                return detections
            
            enhanced_detections = []
            
            for detection in detections:
                enhanced_detection = detection.copy()
                
                try:
                    # Extract object crop
                    bbox = detection['bbox']  # [x, y, width, height]
                    x, y, w, h = [int(coord) for coord in bbox]
                    
                    # Crop object from image
                    object_crop = full_image.crop((x, y, x + w, y + h))
                    
                    # Generate alternative labels for this object
                    current_label = detection['class_name']
                    alternative_labels = self._generate_alternative_labels(current_label)
                    
                    # Classify object crop with alternatives
                    crop_classification = self._classify_with_labels(object_crop, alternative_labels)
                    
                    # Add enhanced label information
                    enhanced_detection['clip_enhancement'] = {
                        'original_label': current_label,
                        'alternative_classifications': crop_classification,
                        'enhanced': True
                    }
                    
                    # Optionally update the main label if CLIP is very confident
                    best_alternative = max(crop_classification, key=lambda x: x['score'])
                    if best_alternative['score'] > 0.8 and best_alternative['score'] > detection['confidence']:
                        enhanced_detection['class_name_enhanced'] = best_alternative['label']
                        enhanced_detection['enhancement_confidence'] = best_alternative['score']
                    
                    self.stats['labels_enhanced'] += 1
                    
                except Exception as e:
                    logger.debug(f"Could not enhance detection: {e}")
                    enhanced_detection['clip_enhancement'] = {'enhanced': False, 'error': str(e)}
                
                enhanced_detections.append(enhanced_detection)
            
            return enhanced_detections
            
        except Exception as e:
            logger.error(f"Error enhancing detection labels: {e}")
            return detections
    
    def _classify_with_labels(self, image: Image.Image, labels: List[str]) -> List[Dict]:
        """Classify image with given labels.
        
        Args:
            image: PIL Image
            labels: List of candidate labels
            
        Returns:
            List of classification results
        """
        if hasattr(self.processor, 'tokenizer'):  # transformers CLIP
            return self._classify_transformers(image, labels)
        else:  # open_clip
            return self._classify_open_clip(image, labels)
    
    def _classify_transformers(self, image: Image.Image, labels: List[str]) -> List[Dict]:
        """Classify using transformers CLIP."""
        # Prepare inputs
        inputs = self.processor(
            text=labels,
            images=image,
            return_tensors="pt",
            padding=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Run inference
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # Get probabilities
        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=1)
        
        # Format results
        results = []
        for i, (label, prob) in enumerate(zip(labels, probs[0])):
            results.append({
                'label': label,
                'score': float(prob),
                'rank': i + 1
            })
        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Update ranks
        for i, result in enumerate(results):
            result['rank'] = i + 1
        
        return results
    
    def _classify_open_clip(self, image: Image.Image, labels: List[str]) -> List[Dict]:
        """Classify using open_clip."""
        # Preprocess image
        image_tensor = self.processor(image).unsqueeze(0).to(self.device)
        
        # Tokenize text
        text_tokens = self.tokenizer(labels).to(self.device)
        
        # Run inference
        with torch.no_grad():
            image_features = self.model.encode_image(image_tensor)
            text_features = self.model.encode_text(text_tokens)
            
            # Calculate similarities
            image_features /= image_features.norm(dim=-1, keepdim=True)
            text_features /= text_features.norm(dim=-1, keepdim=True)
            
            similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
        
        # Format results
        results = []
        for i, (label, sim) in enumerate(zip(labels, similarity[0])):
            results.append({
                'label': label,
                'score': float(sim),
                'rank': i + 1
            })
        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Update ranks
        for i, result in enumerate(results):
            result['rank'] = i + 1
        
        return results
    
    def _get_default_labels(self) -> List[str]:
        """Get default classification labels."""
        # Combine all enhancement categories
        all_labels = []
        for category_labels in self.enhancement_categories.values():
            all_labels.extend(category_labels)
        
        # Add common object labels
        common_objects = [
            'person', 'car', 'bicycle', 'dog', 'cat', 'bird', 'horse', 'sheep', 'cow',
            'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag',
            'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite',
            'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
            'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana',
            'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza',
            'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table',
            'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
            'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock',
            'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
        ]
        
        all_labels.extend(common_objects)
        return list(set(all_labels))  # Remove duplicates
    
    def _generate_alternative_labels(self, current_label: str) -> List[str]:
        """Generate alternative labels for a given object label.
        
        Args:
            current_label: Current object label
            
        Returns:
            List of alternative labels to test
        """
        alternatives = [current_label]  # Include original
        
        # Add similar/related terms
        label_synonyms = {
            'person': ['human', 'individual', 'man', 'woman', 'child', 'adult'],
            'car': ['vehicle', 'automobile', 'sedan', 'SUV', 'truck', 'van'],
            'dog': ['puppy', 'canine', 'pet dog', 'domestic dog'],
            'cat': ['kitten', 'feline', 'pet cat', 'domestic cat'],
            'bicycle': ['bike', 'cycle', 'mountain bike', 'road bike'],
            'chair': ['seat', 'office chair', 'dining chair', 'armchair'],
            'table': ['desk', 'dining table', 'coffee table', 'work table'],
            'bottle': ['water bottle', 'plastic bottle', 'glass bottle', 'drink bottle'],
            'cup': ['mug', 'coffee cup', 'tea cup', 'drinking cup'],
            'book': ['novel', 'textbook', 'magazine', 'publication'],
            'phone': ['smartphone', 'mobile phone', 'cell phone', 'telephone']
        }
        
        # Add synonyms if available
        if current_label.lower() in label_synonyms:
            alternatives.extend(label_synonyms[current_label.lower()])
        
        # Add generic descriptors
        alternatives.extend([
            f'{current_label} object',
            f'small {current_label}',
            f'large {current_label}',
            f'colorful {current_label}',
            f'modern {current_label}'
        ])
        
        return alternatives[:10]  # Limit to 10 alternatives
    
    def _empty_classification_result(self, image_path: str, error_message: str) -> Dict:
        """Create empty result for failed classification.
        
        Args:
            image_path: Path to image
            error_message: Error description
            
        Returns:
            Empty result dictionary
        """
        return {
            'image_path': image_path,
            'image_shape': None,
            'classifications': [],
            'candidate_labels': [],
            'success': False,
            'error': error_message
        }
    
    def get_statistics(self) -> Dict:
        """Get annotation statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'model_info': {
                'model_name': self.model_name,
                'device': self.device,
                'enhancement_categories': len(self.enhancement_categories)
            },
            'processing_stats': self.stats.copy()
        }
    
    def unload_model(self) -> None:
        """Unload model to free memory."""
        if self.model is not None:
            del self.model
            self.model = None
            
        if self.processor is not None:
            del self.processor
            self.processor = None
            
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
            
        # Clear CUDA cache if using GPU
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("CLIP model unloaded")