"""
BLIP (Bootstrapping Language-Image Pre-training) Annotator for Image Captioning
Provides detailed image descriptions to enhance dataset annotations.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import torch
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


class BLIPAnnotator:
    """BLIP annotator for generating image captions and descriptions."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize BLIP annotator.
        
        Args:
            config: Configuration dictionary containing BLIP settings
        """
        self.config = config
        self.model = None
        self.processor = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_loaded = False
        
        # BLIP configuration
        self.model_name = config.get('model_name', 'Salesforce/blip-image-captioning-base')
        self.max_length = config.get('max_length', 50)
        self.num_beams = config.get('num_beams', 5)
        self.temperature = config.get('temperature', 1.0)
        self.min_confidence = config.get('min_confidence', 0.5)
        
        logger.info(f"Initialized BLIP annotator with model: {self.model_name}")
    
    def load_model(self) -> bool:
        """Load BLIP model and processor."""
        if self.model_loaded:
            return True
            
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration
            
            logger.info(f"Loading BLIP model: {self.model_name}")
            self.processor = BlipProcessor.from_pretrained(self.model_name)
            self.model = BlipForConditionalGeneration.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            
            self.model_loaded = True
            logger.info(f"BLIP model loaded successfully on {self.device}")
            return True
            
        except ImportError as e:
            logger.error(f"BLIP dependencies not available: {e}")
            logger.info("Install with: pip install transformers torch")
            return False
        except Exception as e:
            logger.error(f"Failed to load BLIP model: {e}")
            return False
    
    def generate_caption(self, image: Image.Image, prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate caption for an image.
        
        Args:
            image: PIL Image object
            prompt: Optional text prompt to guide caption generation
            
        Returns:
            Dictionary containing caption and metadata
        """
        if not self.load_model():
            return {
                'caption': '',
                'confidence': 0.0,
                'error': 'Model not available'
            }
        
        try:
            # Prepare inputs
            if prompt:
                inputs = self.processor(image, prompt, return_tensors="pt").to(self.device)
            else:
                inputs = self.processor(image, return_tensors="pt").to(self.device)
            
            # Generate caption
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=self.max_length,
                    num_beams=self.num_beams,
                    temperature=self.temperature,
                    do_sample=True if self.temperature > 1.0 else False,
                    pad_token_id=self.processor.tokenizer.eos_token_id
                )
            
            # Decode caption
            caption = self.processor.decode(outputs[0], skip_special_tokens=True)
            
            # Calculate confidence (simplified based on generation probability)
            confidence = self._calculate_confidence(outputs[0])
            
            return {
                'caption': caption,
                'confidence': float(confidence),
                'model': self.model_name,
                'prompt': prompt
            }
            
        except Exception as e:
            logger.error(f"Error generating caption: {e}")
            return {
                'caption': '',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def generate_detailed_description(self, image: Image.Image) -> Dict[str, Any]:
        """
        Generate detailed description with multiple prompts.
        
        Args:
            image: PIL Image object
            
        Returns:
            Dictionary containing multiple descriptions
        """
        prompts = [
            None,  # Unconditional caption
            "a photo of",
            "describe this image in detail:",
            "what objects are in this image?",
            "what is happening in this image?"
        ]
        
        descriptions = {}
        
        for i, prompt in enumerate(prompts):
            result = self.generate_caption(image, prompt)
            key = f"description_{i}" if prompt is None else f"prompt_{i}"
            descriptions[key] = result
        
        # Extract key objects and themes
        descriptions['summary'] = self._extract_summary(descriptions)
        
        return descriptions
    
    def annotate_image(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Annotate image with captions (compatible with ensemble interface).
        
        Args:
            image_path: Path to image file
            
        Returns:
            List of annotation dictionaries
        """
        try:
            image = Image.open(image_path).convert('RGB')
            
            # Generate main caption
            caption_result = self.generate_caption(image)
            
            if caption_result['confidence'] < self.min_confidence:
                logger.warning(f"Low confidence caption for {image_path}: {caption_result['confidence']}")
                return []
            
            # Create annotation in standard format
            annotation = {
                'bbox': [0, 0, image.width, image.height],  # Full image
                'category': 'image_caption',
                'confidence': caption_result['confidence'],
                'caption': caption_result['caption'],
                'source': 'blip',
                'metadata': {
                    'model': self.model_name,
                    'image_size': [image.width, image.height]
                }
            }
            
            return [annotation]
            
        except Exception as e:
            logger.error(f"Error annotating image {image_path}: {e}")
            return []
    
    def _calculate_confidence(self, output_ids: torch.Tensor) -> float:
        """Calculate confidence score for generated caption."""
        # Simplified confidence calculation
        # In practice, you might use generation probabilities
        return min(0.9, max(0.1, len(output_ids) / self.max_length))
    
    def _extract_summary(self, descriptions: Dict[str, Any]) -> Dict[str, Any]:
        """Extract summary information from multiple descriptions."""
        captions = []
        confidences = []
        
        for key, desc in descriptions.items():
            if isinstance(desc, dict) and 'caption' in desc:
                if desc['caption']:
                    captions.append(desc['caption'])
                    confidences.append(desc.get('confidence', 0.0))
        
        if not captions:
            return {'main_caption': '', 'confidence': 0.0, 'num_descriptions': 0}
        
        # Use highest confidence caption as main
        best_idx = np.argmax(confidences) if confidences else 0
        
        return {
            'main_caption': captions[best_idx],
            'confidence': confidences[best_idx] if confidences else 0.0,
            'num_descriptions': len(captions),
            'all_captions': captions
        }
    
    def enhance_annotations(self, annotations: List[Dict[str, Any]], image: Image.Image) -> List[Dict[str, Any]]:
        """
        Enhance existing annotations with BLIP-generated descriptions.
        
        Args:
            annotations: List of existing annotations
            image: PIL Image object
            
        Returns:
            Enhanced annotations with captions
        """
        # Generate overall image caption
        caption_result = self.generate_caption(image)
        
        # Add caption to each annotation's metadata
        for annotation in annotations:
            if 'metadata' not in annotation:
                annotation['metadata'] = {}
            annotation['metadata']['image_caption'] = caption_result['caption']
            annotation['metadata']['caption_confidence'] = caption_result['confidence']
        
        return annotations


def create_blip_annotator(config: Dict[str, Any]) -> BLIPAnnotator:
    """Factory function to create BLIP annotator."""
    return BLIPAnnotator(config)