"""Image processing utilities."""

import cv2
import numpy as np
from PIL import Image, ExifTags
from pathlib import Path
from typing import Tuple, Optional, List, Union
import logging

logger = logging.getLogger(__name__)


class ImageUtils:
    """Utility class for image operations."""
    
    @staticmethod
    def load_image(image_path: str) -> Optional[np.ndarray]:
        """Load image as numpy array.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Image as numpy array (BGR format) or None if failed
        """
        try:
            image = cv2.imread(str(image_path))
            if image is None:
                logger.warning(f"Failed to load image: {image_path}")
                return None
            return image
        except Exception as e:
            logger.error(f"Error loading image {image_path}: {e}")
            return None
    
    @staticmethod
    def load_image_pil(image_path: str) -> Optional[Image.Image]:
        """Load image using PIL.
        
        Args:
            image_path: Path to image file
            
        Returns:
            PIL Image object or None if failed
        """
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                return img.copy()
        except Exception as e:
            logger.error(f"Error loading image {image_path}: {e}")
            return None
    
    @staticmethod
    def get_image_info(image_path: str) -> Optional[dict]:
        """Get image information including dimensions, format, and EXIF data.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with image information or None if failed
        """
        try:
            with Image.open(image_path) as img:
                info = {
                    'path': str(image_path),
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'size_bytes': Path(image_path).stat().st_size
                }
                
                # Extract EXIF data if available
                exif_data = {}
                if hasattr(img, '_getexif'):
                    exif = img._getexif()
                    if exif:
                        for tag, value in exif.items():
                            tag_name = ExifTags.TAGS.get(tag, tag)
                            exif_data[tag_name] = value
                
                info['exif'] = exif_data
                return info
                
        except Exception as e:
            logger.error(f"Error getting image info for {image_path}: {e}")
            return None
    
    @staticmethod
    def is_corrupted(image_path: str) -> bool:
        """Check if image file is corrupted.
        
        Args:
            image_path: Path to image file
            
        Returns:
            True if image is corrupted, False otherwise
        """
        try:
            with Image.open(image_path) as img:
                img.verify()  # Verify image integrity
            return False
        except Exception:
            return True
    
    @staticmethod
    def resize_image(
        image: np.ndarray,
        target_size: Tuple[int, int],
        maintain_aspect_ratio: bool = True,
        padding_color: Tuple[int, int, int] = (114, 114, 114)
    ) -> np.ndarray:
        """Resize image to target size.
        
        Args:
            image: Input image as numpy array
            target_size: Target size as (width, height)
            maintain_aspect_ratio: Whether to maintain aspect ratio
            padding_color: Color for padding when maintaining aspect ratio
            
        Returns:
            Resized image
        """
        height, width = image.shape[:2]
        target_width, target_height = target_size
        
        if not maintain_aspect_ratio:
            return cv2.resize(image, (target_width, target_height))
        
        # Calculate scaling factor
        scale = min(target_width / width, target_height / height)
        
        # Calculate new dimensions
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        # Resize image
        resized = cv2.resize(image, (new_width, new_height))
        
        # Create padded image
        padded = np.full((target_height, target_width, 3), padding_color, dtype=np.uint8)
        
        # Calculate padding offsets
        y_offset = (target_height - new_height) // 2
        x_offset = (target_width - new_width) // 2
        
        # Place resized image in center
        padded[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized
        
        return padded
    
    @staticmethod
    def normalize_image(image: np.ndarray) -> np.ndarray:
        """Normalize image values to [0, 1] range.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Normalized image
        """
        return image.astype(np.float32) / 255.0
    
    @staticmethod
    def save_image(image: np.ndarray, output_path: str, quality: int = 95) -> bool:
        """Save image to file.
        
        Args:
            image: Image as numpy array
            output_path: Output file path
            quality: JPEG quality (0-100)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create output directory if needed
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Set quality for JPEG
            if output_path.lower().endswith(('.jpg', '.jpeg')):
                cv2.imwrite(output_path, image, [cv2.IMWRITE_JPEG_QUALITY, quality])
            else:
                cv2.imwrite(output_path, image)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving image to {output_path}: {e}")
            return False
    
    @staticmethod
    def calculate_aspect_ratio(width: int, height: int) -> float:
        """Calculate aspect ratio of image.
        
        Args:
            width: Image width
            height: Image height
            
        Returns:
            Aspect ratio (width / height)
        """
        return width / height if height > 0 else 0.0
    
    @staticmethod
    def filter_by_size(
        image_paths: List[str],
        min_resolution: Tuple[int, int] = (224, 224),
        max_size_mb: float = 50.0
    ) -> List[str]:
        """Filter images by size constraints.
        
        Args:
            image_paths: List of image paths
            min_resolution: Minimum resolution as (width, height)
            max_size_mb: Maximum file size in MB
            
        Returns:
            List of paths that meet size criteria
        """
        filtered_paths = []
        min_width, min_height = min_resolution
        max_size_bytes = max_size_mb * 1024 * 1024
        
        for image_path in image_paths:
            try:
                # Check file size
                file_size = Path(image_path).stat().st_size
                if file_size > max_size_bytes:
                    continue
                
                # Check image resolution
                with Image.open(image_path) as img:
                    if img.width >= min_width and img.height >= min_height:
                        filtered_paths.append(image_path)
                        
            except Exception as e:
                logger.warning(f"Skipping image {image_path}: {e}")
                continue
        
        return filtered_paths