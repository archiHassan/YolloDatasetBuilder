"""Main image preprocessing pipeline."""

import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
import logging
from tqdm import tqdm

from ..utils.image_utils import ImageUtils
from ..utils.file_utils import FileUtils
from ..utils.logger import ProgressLogger
from .deduplicator import ImageDeduplicator

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Main image processing pipeline for preprocessing raw images."""
    
    def __init__(self, config: Dict):
        """Initialize image processor with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.preprocessing_config = config.get('preprocessing', {})
        self.input_config = config.get('input', {})
        
        # Initialize deduplicator
        dedup_config = self.preprocessing_config.get('deduplication', {})
        self.deduplicator = ImageDeduplicator(
            hash_algorithm=dedup_config.get('hash_algorithm', 'phash'),
            similarity_threshold=dedup_config.get('similarity_threshold', 0.9)
        )
        
        # Processing statistics
        self.stats = {
            'total_input': 0,
            'corrupted_removed': 0,
            'size_filtered': 0,
            'duplicates_removed': 0,
            'final_count': 0
        }
    
    def process_images(
        self,
        input_dir: str,
        output_dir: str,
        max_images: Optional[int] = None
    ) -> Dict:
        """Process images through the complete preprocessing pipeline.
        
        Args:
            input_dir: Directory containing raw images
            output_dir: Directory to save processed images
            max_images: Maximum number of images to process (None for all)
            
        Returns:
            Processing results and statistics
        """
        logger.info("Starting image preprocessing pipeline")
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Discover images
        image_paths = self._discover_images(input_dir)
        if max_images:
            image_paths = image_paths[:max_images]
        
        self.stats['total_input'] = len(image_paths)
        logger.info(f"Found {len(image_paths)} images to process")
        
        if not image_paths:
            logger.warning("No images found to process")
            return self._generate_report()
        
        # Step 2: Filter corrupted images
        valid_images = self._filter_corrupted_images(image_paths)
        
        # Step 3: Filter by size constraints
        size_filtered = self._filter_by_size(valid_images)
        
        # Step 4: Remove duplicates
        unique_images, duplicate_info = self._remove_duplicates(size_filtered)
        
        # Step 5: Process and save images
        processed_images = self._process_and_save_images(unique_images, output_dir)
        
        self.stats['final_count'] = len(processed_images)
        
        # Generate report
        report = self._generate_report()
        report['duplicate_info'] = duplicate_info
        report['processed_images'] = processed_images
        
        logger.info("Image preprocessing completed")
        return report
    
    def _discover_images(self, input_dir: str) -> List[str]:
        """Discover all supported images in input directory.
        
        Args:
            input_dir: Input directory path
            
        Returns:
            List of image file paths
        """
        supported_formats = self.input_config.get('supported_formats', ['.jpg', '.jpeg', '.png'])
        supported_extensions = {ext.lower() for ext in supported_formats}
        
        try:
            image_paths = FileUtils.get_supported_images(input_dir, supported_extensions)
            return [str(path) for path in image_paths]
        except Exception as e:
            logger.error(f"Error discovering images in {input_dir}: {e}")
            return []
    
    def _filter_corrupted_images(self, image_paths: List[str]) -> List[str]:
        """Filter out corrupted images.
        
        Args:
            image_paths: List of image paths
            
        Returns:
            List of valid image paths
        """
        logger.info("Filtering corrupted images...")
        valid_images = []
        
        progress = ProgressLogger(logger, len(image_paths), log_interval=100)
        
        for image_path in image_paths:
            if not ImageUtils.is_corrupted(image_path):
                valid_images.append(image_path)
            else:
                self.stats['corrupted_removed'] += 1
                logger.debug(f"Removed corrupted image: {image_path}")
            
            progress.update(1, "Checking image integrity")
        
        progress.finish("Image integrity check completed")
        logger.info(f"Removed {self.stats['corrupted_removed']} corrupted images")
        return valid_images
    
    def _filter_by_size(self, image_paths: List[str]) -> List[str]:
        """Filter images by size constraints.
        
        Args:
            image_paths: List of image paths
            
        Returns:
            List of images that meet size criteria
        """
        quality_config = self.preprocessing_config.get('quality_filter', {})
        
        if not quality_config.get('enabled', True):
            return image_paths
        
        logger.info("Filtering images by size constraints...")
        
        min_resolution = quality_config.get('min_resolution', [224, 224])
        max_file_size = quality_config.get('max_file_size_mb', 50)
        
        initial_count = len(image_paths)
        filtered_images = ImageUtils.filter_by_size(
            image_paths,
            min_resolution=tuple(min_resolution),
            max_size_mb=max_file_size
        )
        
        removed_count = initial_count - len(filtered_images)
        self.stats['size_filtered'] = removed_count
        
        logger.info(f"Removed {removed_count} images due to size constraints")
        return filtered_images
    
    def _remove_duplicates(self, image_paths: List[str]) -> Tuple[List[str], Dict]:
        """Remove duplicate images.
        
        Args:
            image_paths: List of image paths
            
        Returns:
            Tuple of (unique_images, duplicate_info)
        """
        dedup_config = self.preprocessing_config.get('deduplication', {})
        
        if not dedup_config.get('enabled', True):
            return image_paths, {}
        
        logger.info("Removing duplicate images...")
        
        unique_images, removed_duplicates = self.deduplicator.remove_duplicates(
            image_paths,
            keep_best_quality=True
        )
        
        self.stats['duplicates_removed'] = len(image_paths) - len(unique_images)
        
        # Generate deduplication report
        duplicate_info = self.deduplicator.generate_deduplication_report(
            len(image_paths),
            len(unique_images),
            removed_duplicates
        )
        
        return unique_images, duplicate_info
    
    def _process_and_save_images(
        self,
        image_paths: List[str],
        output_dir: str
    ) -> List[Dict]:
        """Process and save images with resizing and normalization.
        
        Args:
            image_paths: List of image paths to process
            output_dir: Output directory
            
        Returns:
            List of processed image information
        """
        logger.info("Processing and saving images...")
        
        resize_config = self.preprocessing_config.get('resize', {})
        resize_enabled = resize_config.get('enabled', True)
        target_size = resize_config.get('target_size', [640, 640])
        maintain_aspect = resize_config.get('maintain_aspect_ratio', True)
        
        processed_images = []
        progress = ProgressLogger(logger, len(image_paths), log_interval=50)
        
        for i, image_path in enumerate(image_paths):
            try:
                # Load image
                image = ImageUtils.load_image(image_path)
                if image is None:
                    continue
                
                # Resize if enabled
                if resize_enabled:
                    image = ImageUtils.resize_image(
                        image,
                        target_size=tuple(target_size),
                        maintain_aspect_ratio=maintain_aspect
                    )
                
                # Generate output filename
                input_path = Path(image_path)
                output_filename = f"image_{i+1:05d}{input_path.suffix}"
                output_path = Path(output_dir) / output_filename
                
                # Save processed image
                success = ImageUtils.save_image(image, str(output_path))
                
                if success:
                    # Get image info
                    info = ImageUtils.get_image_info(str(output_path))
                    if info:
                        info['original_path'] = image_path
                        info['processed_path'] = str(output_path)
                        processed_images.append(info)
                
                progress.update(1, "Processing images")
                
            except Exception as e:
                logger.error(f"Error processing image {image_path}: {e}")
                continue
        
        progress.finish("Image processing completed")
        return processed_images
    
    def _generate_report(self) -> Dict:
        """Generate processing report.
        
        Returns:
            Report dictionary with statistics
        """
        report = {
            'input_statistics': {
                'total_input_images': self.stats['total_input'],
                'corrupted_removed': self.stats['corrupted_removed'],
                'size_filtered': self.stats['size_filtered'],
                'duplicates_removed': self.stats['duplicates_removed'],
                'final_processed': self.stats['final_count']
            },
            'processing_summary': {
                'success_rate': (self.stats['final_count'] / self.stats['total_input']) * 100 
                               if self.stats['total_input'] > 0 else 0,
                'total_removed': (self.stats['corrupted_removed'] + 
                                self.stats['size_filtered'] + 
                                self.stats['duplicates_removed'])
            },
            'configuration': {
                'deduplication_enabled': self.preprocessing_config.get('deduplication', {}).get('enabled', True),
                'resize_enabled': self.preprocessing_config.get('resize', {}).get('enabled', True),
                'quality_filter_enabled': self.preprocessing_config.get('quality_filter', {}).get('enabled', True)
            }
        }
        
        return report
    
    def validate_input_directory(self, input_dir: str) -> bool:
        """Validate input directory and check for images.
        
        Args:
            input_dir: Input directory path
            
        Returns:
            True if directory is valid and contains images
        """
        input_path = Path(input_dir)
        
        if not input_path.exists():
            logger.error(f"Input directory does not exist: {input_dir}")
            return False
        
        if not input_path.is_dir():
            logger.error(f"Input path is not a directory: {input_dir}")
            return False
        
        # Check for images
        images = self._discover_images(input_dir)
        if not images:
            logger.warning(f"No supported images found in directory: {input_dir}")
            return False
        
        logger.info(f"Found {len(images)} images in input directory")
        return True