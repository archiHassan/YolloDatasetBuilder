"""Image deduplication utilities using perceptual hashing."""

import hashlib
import imagehash
from PIL import Image
from pathlib import Path
from typing import List, Set, Dict, Tuple, Optional
import logging
from collections import defaultdict

from ..utils.image_utils import ImageUtils

logger = logging.getLogger(__name__)


class ImageDeduplicator:
    """Image deduplication using multiple hashing techniques."""
    
    def __init__(
        self,
        hash_algorithm: str = "phash",
        similarity_threshold: float = 0.9,
        hash_size: int = 8
    ):
        """Initialize deduplicator.
        
        Args:
            hash_algorithm: Hash algorithm ('md5', 'phash', 'ahash', 'dhash', 'whash')
            similarity_threshold: Similarity threshold for perceptual hashes (0-1)
            hash_size: Hash size for perceptual hashes
        """
        self.hash_algorithm = hash_algorithm.lower()
        self.similarity_threshold = similarity_threshold
        self.hash_size = hash_size
        
        # Validate algorithm
        valid_algorithms = {'md5', 'phash', 'ahash', 'dhash', 'whash'}
        if self.hash_algorithm not in valid_algorithms:
            raise ValueError(f"Invalid hash algorithm. Must be one of: {valid_algorithms}")
    
    def calculate_hash(self, image_path: str) -> Optional[str]:
        """Calculate hash for an image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Hash string or None if failed
        """
        try:
            if self.hash_algorithm == 'md5':
                return self._calculate_md5_hash(image_path)
            else:
                return self._calculate_perceptual_hash(image_path)
                
        except Exception as e:
            logger.error(f"Error calculating hash for {image_path}: {e}")
            return None
    
    def _calculate_md5_hash(self, image_path: str) -> str:
        """Calculate MD5 hash of file contents."""
        hash_md5 = hashlib.md5()
        with open(image_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _calculate_perceptual_hash(self, image_path: str) -> str:
        """Calculate perceptual hash using imagehash library."""
        with Image.open(image_path) as img:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            if self.hash_algorithm == 'phash':
                hash_obj = imagehash.phash(img, hash_size=self.hash_size)
            elif self.hash_algorithm == 'ahash':
                hash_obj = imagehash.average_hash(img, hash_size=self.hash_size)
            elif self.hash_algorithm == 'dhash':
                hash_obj = imagehash.dhash(img, hash_size=self.hash_size)
            elif self.hash_algorithm == 'whash':
                hash_obj = imagehash.whash(img, hash_size=self.hash_size)
            
            return str(hash_obj)
    
    def find_duplicates(self, image_paths: List[str]) -> Dict[str, List[str]]:
        """Find duplicate images in a list of paths.
        
        Args:
            image_paths: List of image paths to check
            
        Returns:
            Dictionary mapping representative image to list of duplicates
        """
        if self.hash_algorithm == 'md5':
            return self._find_exact_duplicates(image_paths)
        else:
            return self._find_similar_duplicates(image_paths)
    
    def _find_exact_duplicates(self, image_paths: List[str]) -> Dict[str, List[str]]:
        """Find exact duplicates using MD5 hash."""
        hash_to_paths = defaultdict(list)
        
        for image_path in image_paths:
            image_hash = self.calculate_hash(image_path)
            if image_hash:
                hash_to_paths[image_hash].append(image_path)
        
        # Return groups with more than one image
        duplicates = {}
        for image_hash, paths in hash_to_paths.items():
            if len(paths) > 1:
                # Use first path as representative
                representative = paths[0]
                duplicates[representative] = paths[1:]
        
        return duplicates
    
    def _find_similar_duplicates(self, image_paths: List[str]) -> Dict[str, List[str]]:
        """Find similar duplicates using perceptual hashing."""
        image_hashes = {}
        
        # Calculate hashes for all images
        for image_path in image_paths:
            image_hash = self.calculate_hash(image_path)
            if image_hash:
                image_hashes[image_path] = imagehash.hex_to_hash(image_hash)
        
        # Find similar images
        processed = set()
        duplicates = {}
        
        for path1, hash1 in image_hashes.items():
            if path1 in processed:
                continue
            
            similar_images = []
            
            for path2, hash2 in image_hashes.items():
                if path1 != path2 and path2 not in processed:
                    # Calculate similarity (lower distance = more similar)
                    distance = hash1 - hash2
                    max_distance = self.hash_size * self.hash_size
                    similarity = 1.0 - (distance / max_distance)
                    
                    if similarity >= self.similarity_threshold:
                        similar_images.append(path2)
                        processed.add(path2)
            
            if similar_images:
                duplicates[path1] = similar_images
            
            processed.add(path1)
        
        return duplicates
    
    def remove_duplicates(
        self,
        image_paths: List[str],
        keep_best_quality: bool = True
    ) -> Tuple[List[str], Dict[str, List[str]]]:
        """Remove duplicate images from list.
        
        Args:
            image_paths: List of image paths
            keep_best_quality: Whether to keep highest quality image in each group
            
        Returns:
            Tuple of (unique_images, removed_duplicates)
        """
        duplicates = self.find_duplicates(image_paths)
        removed = {}
        unique_images = []
        
        # Track which images to remove
        images_to_remove = set()
        for representative, duplicate_list in duplicates.items():
            if keep_best_quality:
                # Find best quality image in the group
                all_images = [representative] + duplicate_list
                best_image = self._select_best_quality(all_images)
                
                # Remove all others
                for img in all_images:
                    if img != best_image:
                        images_to_remove.add(img)
                
                removed[best_image] = [img for img in all_images if img != best_image]
            else:
                # Keep representative, remove duplicates
                images_to_remove.update(duplicate_list)
                removed[representative] = duplicate_list
        
        # Create list of unique images
        for image_path in image_paths:
            if image_path not in images_to_remove:
                unique_images.append(image_path)
        
        logger.info(f"Removed {len(image_paths) - len(unique_images)} duplicate images")
        return unique_images, removed
    
    def _select_best_quality(self, image_paths: List[str]) -> str:
        """Select the best quality image from a list.
        
        Args:
            image_paths: List of image paths
            
        Returns:
            Path to best quality image
        """
        best_image = image_paths[0]
        best_score = 0
        
        for image_path in image_paths:
            try:
                info = ImageUtils.get_image_info(image_path)
                if info:
                    # Score based on resolution and file size
                    resolution_score = info['width'] * info['height']
                    size_score = info['size_bytes'] / 1000  # Convert to KB
                    
                    # Weighted score (favor resolution over file size)
                    score = resolution_score * 0.7 + size_score * 0.3
                    
                    if score > best_score:
                        best_score = score
                        best_image = image_path
                        
            except Exception as e:
                logger.warning(f"Error evaluating image quality for {image_path}: {e}")
        
        return best_image
    
    def generate_deduplication_report(
        self,
        original_count: int,
        unique_count: int,
        removed_duplicates: Dict[str, List[str]]
    ) -> Dict:
        """Generate deduplication report.
        
        Args:
            original_count: Original number of images
            unique_count: Number of unique images after deduplication
            removed_duplicates: Dictionary of removed duplicates
            
        Returns:
            Report dictionary
        """
        removed_count = original_count - unique_count
        
        report = {
            'original_count': original_count,
            'unique_count': unique_count,
            'removed_count': removed_count,
            'duplicate_groups': len(removed_duplicates),
            'reduction_percentage': (removed_count / original_count) * 100 if original_count > 0 else 0,
            'algorithm': self.hash_algorithm,
            'similarity_threshold': self.similarity_threshold,
            'removed_images': removed_duplicates
        }
        
        return report