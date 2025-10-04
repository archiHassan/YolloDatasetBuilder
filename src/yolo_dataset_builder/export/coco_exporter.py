"""COCO format dataset exporter for YOLO Dataset Builder."""

import json
import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import logging
import numpy as np

from ..utils.file_utils import FileUtils
from ..utils.image_utils import ImageUtils

logger = logging.getLogger(__name__)


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy types."""
    
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


class COCOExporter:
    """Exporter for COCO format datasets."""
    
    def __init__(self, config: Dict):
        """Initialize COCO exporter.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.export_config = config.get('export', {})
        self.coco_config = self.export_config.get('coco', {})
        
        # Export settings
        self.include_segmentation = self.coco_config.get('include_segmentation', True)
        self.include_keypoints = self.coco_config.get('include_keypoints', False)
        
        # Dataset split ratios
        split_config = self.export_config.get('split_ratios', {})
        self.train_ratio = split_config.get('train', 0.7)
        self.val_ratio = split_config.get('val', 0.2)
        self.test_ratio = split_config.get('test', 0.1)
        
        # Validate split ratios
        total_ratio = self.train_ratio + self.val_ratio + self.test_ratio
        if not (0.99 <= total_ratio <= 1.01):
            logger.warning(f"Split ratios sum to {total_ratio}, adjusting...")
            # Normalize ratios
            self.train_ratio /= total_ratio
            self.val_ratio /= total_ratio
            self.test_ratio /= total_ratio
        
        # Statistics
        self.stats = {
            'total_images': 0,
            'total_annotations': 0,
            'train_images': 0,
            'val_images': 0,
            'test_images': 0,
            'categories': 0
        }
    
    def export_dataset(
        self,
        annotation_results: List[Dict],
        output_dir: str,
        dataset_name: str = "yolo_generated_dataset"
    ) -> Dict:
        """Export annotation results to COCO format dataset.
        
        Args:
            annotation_results: List of annotation results from the pipeline
            output_dir: Output directory for the dataset
            dataset_name: Name of the dataset
            
        Returns:
            Export results and statistics
        """
        logger.info(f"Exporting dataset to COCO format: {dataset_name}")
        
        # Create output directories
        output_path = Path(output_dir)
        self._create_output_structure(output_path)
        
        # Filter successful annotations
        valid_results = [
            result for result in annotation_results 
            if result.get('success', False) and result.get('detections')
        ]
        
        if not valid_results:
            logger.error("No valid annotation results found for export")
            return {'success': False, 'error': 'No valid annotations'}
        
        # Extract categories from all detections
        categories = self._extract_categories(valid_results)
        
        # Split dataset
        train_results, val_results, test_results = self._split_dataset(valid_results)
        
        # Create COCO annotations for each split
        export_results = {}
        
        # Export training set
        if train_results:
            train_coco = self._create_coco_annotation(
                train_results, categories, dataset_name, "train"
            )
            train_path = output_path / "annotations" / "train.json"
            self._save_annotation_file(train_coco, train_path)
            export_results['train'] = {
                'annotation_file': str(train_path),
                'image_count': len(train_results),
                'annotation_count': sum(len(r['detections']) for r in train_results)
            }
            self.stats['train_images'] = len(train_results)
        
        # Export validation set
        if val_results:
            val_coco = self._create_coco_annotation(
                val_results, categories, dataset_name, "val"
            )
            val_path = output_path / "annotations" / "val.json"
            self._save_annotation_file(val_coco, val_path)
            export_results['val'] = {
                'annotation_file': str(val_path),
                'image_count': len(val_results),
                'annotation_count': sum(len(r['detections']) for r in val_results)
            }
            self.stats['val_images'] = len(val_results)
        
        # Export test set
        if test_results:
            test_coco = self._create_coco_annotation(
                test_results, categories, dataset_name, "test"
            )
            test_path = output_path / "annotations" / "test.json"
            self._save_annotation_file(test_coco, test_path)
            export_results['test'] = {
                'annotation_file': str(test_path),
                'image_count': len(test_results),
                'annotation_count': sum(len(r['detections']) for r in test_results)
            }
            self.stats['test_images'] = len(test_results)
        
        # Copy images to appropriate directories
        self._organize_images(train_results, val_results, test_results, output_path)
        
        # Update statistics
        self.stats['total_images'] = len(valid_results)
        self.stats['total_annotations'] = sum(
            len(r['detections']) for r in valid_results
        )
        self.stats['categories'] = len(categories)
        
        # Create dataset info file
        dataset_info = self._create_dataset_info(
            dataset_name, categories, export_results
        )
        info_path = output_path / "dataset_info.json"
        self._save_annotation_file(dataset_info, info_path)
        
        logger.info("Dataset export completed successfully")
        
        return {
            'success': True,
            'dataset_name': dataset_name,
            'output_directory': str(output_path),
            'splits': export_results,
            'statistics': self.stats.copy(),
            'dataset_info_file': str(info_path)
        }
    
    def _create_output_structure(self, output_path: Path) -> None:
        """Create output directory structure.
        
        Args:
            output_path: Base output directory
        """
        # Create directories
        (output_path / "images" / "train").mkdir(parents=True, exist_ok=True)
        (output_path / "images" / "val").mkdir(parents=True, exist_ok=True)
        (output_path / "images" / "test").mkdir(parents=True, exist_ok=True)
        (output_path / "annotations").mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"Created output directory structure at {output_path}")
    
    def _extract_categories(self, annotation_results: List[Dict]) -> List[Dict]:
        """Extract unique categories from annotation results.
        
        Args:
            annotation_results: List of annotation results
            
        Returns:
            List of category dictionaries
        """
        category_map = {}
        
        for result in annotation_results:
            for detection in result.get('detections', []):
                class_id = detection.get('class_id', 0)
                class_name = detection.get('class_name', f'class_{class_id}')
                
                if class_id not in category_map:
                    category_map[class_id] = {
                        'id': class_id,
                        'name': class_name,
                        'supercategory': 'object'  # Default supercategory
                    }
        
        # Sort by ID for consistency
        categories = sorted(category_map.values(), key=lambda x: x['id'])
        
        logger.info(f"Extracted {len(categories)} categories")
        return categories
    
    def _split_dataset(
        self,
        annotation_results: List[Dict]
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Split dataset into train/val/test sets.
        
        Args:
            annotation_results: List of annotation results
            
        Returns:
            Tuple of (train_results, val_results, test_results)
        """
        total_count = len(annotation_results)
        
        # Calculate split indices
        train_end = int(total_count * self.train_ratio)
        val_end = train_end + int(total_count * self.val_ratio)
        
        # Split the data
        train_results = annotation_results[:train_end]
        val_results = annotation_results[train_end:val_end]
        test_results = annotation_results[val_end:]
        
        logger.info(
            f"Dataset split: {len(train_results)} train, "
            f"{len(val_results)} val, {len(test_results)} test"
        )
        
        return train_results, val_results, test_results
    
    def _create_coco_annotation(
        self,
        annotation_results: List[Dict],
        categories: List[Dict],
        dataset_name: str,
        split_name: str
    ) -> Dict:
        """Create COCO format annotation dictionary.
        
        Args:
            annotation_results: List of annotation results for this split
            categories: List of category dictionaries
            dataset_name: Name of the dataset
            split_name: Name of the split (train/val/test)
            
        Returns:
            COCO format annotation dictionary
        """
        # COCO annotation structure
        coco_data = {
            'info': self._create_info_dict(dataset_name, split_name),
            'licenses': self._create_licenses_dict(),
            'images': [],
            'annotations': [],
            'categories': categories
        }
        
        annotation_id = 1
        
        for image_id, result in enumerate(annotation_results, 1):
            # Add image info
            image_info = self._create_image_info(result, image_id)
            coco_data['images'].append(image_info)
            
            # Add annotations for this image
            for detection in result.get('detections', []):
                annotation = self._create_annotation(
                    detection, image_id, annotation_id
                )
                coco_data['annotations'].append(annotation)
                annotation_id += 1
        
        return coco_data
    
    def _create_info_dict(self, dataset_name: str, split_name: str) -> Dict:
        """Create info dictionary for COCO format.
        
        Args:
            dataset_name: Name of the dataset
            split_name: Name of the split
            
        Returns:
            Info dictionary
        """
        return {
            'description': f'{dataset_name} - {split_name} split',
            'url': 'https://github.com/your-repo/yolo-dataset-builder',
            'version': '1.0',
            'year': datetime.datetime.now().year,
            'contributor': 'YOLO Dataset Builder',
            'date_created': datetime.datetime.now().isoformat()
        }
    
    def _create_licenses_dict(self) -> List[Dict]:
        """Create licenses list for COCO format.
        
        Returns:
            List of license dictionaries
        """
        return [
            {
                'id': 1,
                'name': 'Generated Dataset License',
                'url': 'https://creativecommons.org/licenses/by/4.0/'
            }
        ]
    
    def _create_image_info(self, result: Dict, image_id: int) -> Dict:
        """Create image info dictionary.
        
        Args:
            result: Annotation result
            image_id: Image ID
            
        Returns:
            Image info dictionary
        """
        image_path = result.get('image_path', '')
        image_shape = result.get('image_shape', [0, 0, 0])
        
        height, width = image_shape[:2] if len(image_shape) >= 2 else [0, 0]
        
        # Get filename from path
        filename = Path(image_path).name if image_path else f'image_{image_id}.jpg'
        
        return {
            'id': image_id,
            'width': width,
            'height': height,
            'file_name': filename,
            'license': 1,
            'flickr_url': '',
            'coco_url': '',
            'date_captured': datetime.datetime.now().isoformat()
        }
    
    def _create_annotation(
        self,
        detection: Dict,
        image_id: int,
        annotation_id: int
    ) -> Dict:
        """Create annotation dictionary from detection.
        
        Args:
            detection: Detection dictionary
            image_id: Image ID
            annotation_id: Annotation ID
            
        Returns:
            COCO annotation dictionary
        """
        bbox = detection.get('bbox', [0, 0, 0, 0])  # [x, y, width, height]
        area = detection.get('area', bbox[2] * bbox[3])
        
        annotation = {
            'id': annotation_id,
            'image_id': image_id,
            'category_id': detection.get('class_id', 0),
            'bbox': bbox,
            'area': area,
            'iscrowd': 0
        }
        
        # Add segmentation if available and enabled
        if self.include_segmentation and 'segmentation' in detection:
            if 'segmentation_rle' in detection:
                # Use RLE format
                annotation['segmentation'] = detection['segmentation_rle']
            else:
                # Convert binary mask to polygon (simplified)
                annotation['segmentation'] = self._mask_to_polygon(
                    detection['segmentation']
                )
        else:
            # Default empty segmentation
            annotation['segmentation'] = []
        
        # Add keypoints if enabled (placeholder for future implementation)
        if self.include_keypoints:
            annotation['keypoints'] = []
            annotation['num_keypoints'] = 0
        
        return annotation
    
    def _mask_to_polygon(self, mask) -> List[List[float]]:
        """Convert binary mask to polygon format (simplified implementation).
        
        Args:
            mask: Binary mask
            
        Returns:
            List of polygon coordinates
        """
        # This is a placeholder implementation
        # In practice, you'd use cv2.findContours or similar
        return []
    
    def _organize_images(
        self,
        train_results: List[Dict],
        val_results: List[Dict],
        test_results: List[Dict],
        output_path: Path
    ) -> None:
        """Copy images to appropriate split directories.
        
        Args:
            train_results: Training set results
            val_results: Validation set results
            test_results: Test set results
            output_path: Base output directory
        """
        logger.info("Organizing images into split directories...")
        
        # Copy training images
        for i, result in enumerate(train_results, 1):
            self._copy_image_to_split(result, output_path / "images" / "train", i)
        
        # Copy validation images
        for i, result in enumerate(val_results, 1):
            self._copy_image_to_split(result, output_path / "images" / "val", i)
        
        # Copy test images
        for i, result in enumerate(test_results, 1):
            self._copy_image_to_split(result, output_path / "images" / "test", i)
        
        logger.info("Image organization completed")
    
    def _copy_image_to_split(
        self,
        result: Dict,
        split_dir: Path,
        image_number: int
    ) -> None:
        """Copy image to split directory.
        
        Args:
            result: Annotation result
            split_dir: Split directory path
            image_number: Image number for naming
        """
        image_path = result.get('image_path', '')
        if not image_path or not Path(image_path).exists():
            logger.warning(f"Image not found: {image_path}")
            return
        
        # Generate new filename
        original_path = Path(image_path)
        new_filename = f"image_{image_number:05d}{original_path.suffix}"
        destination = split_dir / new_filename
        
        # Copy file
        try:
            FileUtils.copy_file(image_path, str(destination))
            logger.debug(f"Copied {image_path} -> {destination}")
        except Exception as e:
            logger.error(f"Failed to copy image {image_path}: {e}")
    
    def _create_dataset_info(
        self,
        dataset_name: str,
        categories: List[Dict],
        export_results: Dict
    ) -> Dict:
        """Create dataset information summary.
        
        Args:
            dataset_name: Name of the dataset
            categories: List of categories
            export_results: Export results
            
        Returns:
            Dataset info dictionary
        """
        return {
            'dataset_name': dataset_name,
            'creation_date': datetime.datetime.now().isoformat(),
            'generator': 'YOLO Dataset Builder',
            'version': '1.0',
            'statistics': self.stats.copy(),
            'categories': categories,
            'splits': export_results,
            'format': 'COCO',
            'configuration': {
                'include_segmentation': self.include_segmentation,
                'include_keypoints': self.include_keypoints,
                'split_ratios': {
                    'train': self.train_ratio,
                    'val': self.val_ratio,
                    'test': self.test_ratio
                }
            }
        }
    
    def _save_annotation_file(self, data: Dict, file_path: Path) -> None:
        """Save annotation data to JSON file.
        
        Args:
            data: Data to save
            file_path: Output file path
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, cls=NumpyEncoder)
            
            logger.debug(f"Saved annotation file: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save annotation file {file_path}: {e}")
            raise
    
    def validate_coco_format(self, annotation_file: str) -> Dict:
        """Validate COCO format annotation file.
        
        Args:
            annotation_file: Path to annotation file
            
        Returns:
            Validation results
        """
        try:
            with open(annotation_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check required fields
            required_fields = ['info', 'images', 'annotations', 'categories']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                return {
                    'valid': False,
                    'errors': [f'Missing required field: {field}' for field in missing_fields]
                }
            
            # Validate structure
            errors = []
            
            # Check images
            if not isinstance(data['images'], list):
                errors.append('Images field must be a list')
            
            # Check annotations
            if not isinstance(data['annotations'], list):
                errors.append('Annotations field must be a list')
            
            # Check categories
            if not isinstance(data['categories'], list):
                errors.append('Categories field must be a list')
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'image_count': len(data['images']),
                'annotation_count': len(data['annotations']),
                'category_count': len(data['categories'])
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f'Failed to load annotation file: {e}']
            }
    
    def get_export_statistics(self) -> Dict:
        """Get export statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'export_settings': {
                'include_segmentation': self.include_segmentation,
                'include_keypoints': self.include_keypoints,
                'split_ratios': {
                    'train': self.train_ratio,
                    'val': self.val_ratio,
                    'test': self.test_ratio
                }
            },
            'statistics': self.stats.copy()
        }