"""Main pipeline orchestrator for YOLO Dataset Builder."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import time

from .config import Config
from .preprocessing.image_processor import ImageProcessor
from .annotation.yolo_annotator import YOLOAnnotator
from .annotation.sam_annotator import SAMAnnotator
from .ensemble.confidence_filter import ConfidenceFilter
from .ensemble.multi_model_ensemble import MultiModelEnsemble
from .export.coco_exporter import COCOExporter
from .utils.logger import setup_logger, ProgressLogger

logger = logging.getLogger(__name__)


class Pipeline:
    """Main pipeline for automated dataset generation."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize pipeline with configuration.
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = Config(config_path)
        self.config.validate()
        
        # Setup logging
        logging_config = self.config.get('logging', {})
        self.logger = setup_logger(
            level=logging_config.get('level', 'INFO'),
            log_file=logging_config.get('log_file'),
            console_output=logging_config.get('console_output', True)
        )
        
        # Initialize pipeline components
        self.image_processor = ImageProcessor(self.config.to_dict())
        
        # Check if ensemble mode is enabled
        ensemble_config = self.config.get('ensemble', {})
        self.use_ensemble = ensemble_config.get('enabled', False)
        
        if self.use_ensemble:
            # Initialize ensemble system
            self.ensemble_annotator = MultiModelEnsemble(self.config.to_dict())
            self.yolo_annotator = None  # Managed by ensemble
            self.sam_annotator = None   # Managed by ensemble
            self.logger.info("Pipeline initialized in ensemble mode")
        else:
            # Initialize individual models (legacy Phase 1 mode)
            self.ensemble_annotator = None
            self.yolo_annotator = YOLOAnnotator(self.config.to_dict())
            self.sam_annotator = SAMAnnotator(self.config.to_dict())
            self.logger.info("Pipeline initialized in single-model mode")
        
        self.confidence_filter = ConfidenceFilter(self.config.to_dict())
        self.coco_exporter = COCOExporter(self.config.to_dict())
        
        # Pipeline statistics
        self.stats = {
            'start_time': None,
            'end_time': None,
            'total_duration': 0,
            'images_processed': 0,
            'annotations_generated': 0,
            'errors_encountered': 0
        }
    
    def run(
        self,
        input_dir: str,
        output_dir: str,
        max_images: Optional[int] = None,
        dataset_name: str = "generated_dataset"
    ) -> Dict[str, Any]:
        """Run the complete pipeline.
        
        Args:
            input_dir: Directory containing raw images
            output_dir: Output directory for processed dataset
            max_images: Maximum number of images to process
            dataset_name: Name for the generated dataset
            
        Returns:
            Pipeline results and statistics
        """
        self.stats['start_time'] = time.time()
        logger.info("Starting YOLO Dataset Builder pipeline")
        logger.info(f"Input directory: {input_dir}")
        logger.info(f"Output directory: {output_dir}")
        
        try:
            # Step 1: Validate inputs
            self._validate_inputs(input_dir, output_dir)
            
            # Step 2: Preprocess images
            logger.info("Step 1/5: Preprocessing images...")
            preprocessing_results = self.image_processor.process_images(
                input_dir, 
                str(Path(output_dir) / "processed_images"),
                max_images
            )
            
            if preprocessing_results['input_statistics']['final_processed'] == 0:
                raise ValueError("No images survived preprocessing")
            
            # Step 3: Load annotation models
            logger.info("Step 2/5: Loading annotation models...")
            self._load_annotation_models()
            
            # Step 4: Generate annotations
            logger.info("Step 3/5: Generating annotations...")
            annotation_results = self._generate_annotations(
                preprocessing_results['processed_images']
            )
            
            # Step 5: Filter annotations
            logger.info("Step 4/5: Filtering annotations...")
            filtered_results = self._filter_annotations(annotation_results)
            
            # Step 6: Export dataset
            logger.info("Step 5/5: Exporting COCO dataset...")
            export_results = self.coco_exporter.export_dataset(
                filtered_results,
                output_dir,
                dataset_name
            )
            
            # Finalize statistics
            self.stats['end_time'] = time.time()
            self.stats['total_duration'] = self.stats['end_time'] - self.stats['start_time']
            
            # Create final report
            final_results = self._create_final_report(
                preprocessing_results,
                annotation_results,
                filtered_results,
                export_results
            )
            
            logger.info("Pipeline completed successfully!")
            return final_results
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            self.stats['errors_encountered'] += 1
            raise
        
        finally:
            # Cleanup models to free memory
            self._cleanup_models()
    
    def _validate_inputs(self, input_dir: str, output_dir: str) -> None:
        """Validate input parameters.
        
        Args:
            input_dir: Input directory path
            output_dir: Output directory path
        """
        # Validate input directory
        if not self.image_processor.validate_input_directory(input_dir):
            raise ValueError(f"Invalid input directory: {input_dir}")
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory prepared: {output_dir}")
    
    def _load_annotation_models(self) -> None:
        """Load annotation models."""
        try:
            if self.use_ensemble:
                # Load ensemble models
                logger.info("Loading ensemble models...")
                self.ensemble_annotator.load_models()
                logger.info("Ensemble models loaded successfully")
            else:
                # Legacy single-model mode (Phase 1)
                # Load YOLO annotator
                self.yolo_annotator.load_model()
                logger.info("YOLO model loaded successfully")
                
                # Load SAM annotator (optional for Phase 1)
                try:
                    self.sam_annotator.load_model()
                    logger.info("SAM model loaded successfully")
                except Exception as e:
                    logger.warning(f"SAM model loading failed: {e}")
                    logger.info("Continuing with YOLO-only annotations")
                    self.sam_annotator = None
                
        except Exception as e:
            logger.error(f"Failed to load annotation models: {e}")
            raise RuntimeError(f"Model loading failed: {e}")
    
    def _generate_annotations(self, processed_images: List[Dict]) -> List[Dict]:
        """Generate annotations for processed images.
        
        Args:
            processed_images: List of processed image information
            
        Returns:
            List of annotation results
        """
        image_paths = [img['processed_path'] for img in processed_images]
        
        logger.info(f"Generating annotations for {len(image_paths)} images")
        
        if self.use_ensemble:
            # Use ensemble annotation (Phase 2)
            logger.info("Using ensemble annotation system...")
            annotation_results = []
            
            progress = ProgressLogger(logger, len(image_paths), log_interval=50)
            
            for image_path in image_paths:
                try:
                    # Get ensemble configuration
                    ensemble_config = self.config.get('ensemble', {})
                    clip_config = self.config.get('models', {}).get('clip', {})
                    
                    result = self.ensemble_annotator.annotate_image(
                        image_path,
                        use_sam_refinement=True,
                        use_clip_enhancement=clip_config.get('enabled', False)
                    )
                    annotation_results.append(result)
                    
                    progress.update(1, f"Ensemble annotation")
                    
                except Exception as e:
                    logger.error(f"Ensemble annotation failed for {image_path}: {e}")
                    # Create error result
                    error_result = {
                        'image_path': image_path,
                        'detections': [],
                        'detection_count': 0,
                        'success': False,
                        'error': str(e)
                    }
                    annotation_results.append(error_result)
            
            progress.finish("Ensemble annotation completed")
            
        else:
            # Legacy single-model mode (Phase 1)
            # Generate YOLO annotations
            yolo_results = self.yolo_annotator.annotate_batch(image_paths)
            
            # Enhance with SAM if available
            if self.sam_annotator:
                logger.info("Enhancing annotations with SAM segmentation...")
                enhanced_results = []
                
                progress = ProgressLogger(logger, len(yolo_results), log_interval=50)
                
                for yolo_result in yolo_results:
                    if yolo_result['success'] and yolo_result['detections']:
                        # Generate SAM masks for detected objects
                        bboxes = [det['bbox'] for det in yolo_result['detections']]
                        sam_result = self.sam_annotator.generate_masks_from_boxes(
                            yolo_result['image_path'],
                            bboxes
                        )
                        
                        # Combine YOLO and SAM results
                        enhanced_result = self.sam_annotator.combine_with_detections(
                            yolo_result,
                            sam_result
                        )
                        enhanced_results.append(enhanced_result)
                    else:
                        enhanced_results.append(yolo_result)
                    
                    progress.update(1, "Enhancing with SAM")
                
                progress.finish("SAM enhancement completed")
                annotation_results = enhanced_results
            else:
                annotation_results = yolo_results
        
        # Update statistics
        successful_annotations = [r for r in annotation_results if r['success']]
        self.stats['images_processed'] = len(successful_annotations)
        self.stats['annotations_generated'] = sum(
            len(r['detections']) for r in successful_annotations
        )
        
        logger.info(f"Generated annotations for {len(successful_annotations)} images")
        return annotation_results
    
    def _filter_annotations(self, annotation_results: List[Dict]) -> List[Dict]:
        """Filter annotations based on confidence and quality.
        
        Args:
            annotation_results: Raw annotation results
            
        Returns:
            Filtered annotation results
        """
        filtered_results = []
        
        for result in annotation_results:
            if not result['success'] or not result['detections']:
                continue
            
            # Apply confidence filtering
            filtered_detections = self.confidence_filter.filter_detections(
                result['detections'],
                result.get('image_shape')
            )
            
            # Update result with filtered detections
            filtered_result = result.copy()
            filtered_result['detections'] = filtered_detections
            filtered_result['filtered_detection_count'] = len(filtered_detections)
            
            # Only keep images with remaining detections
            if filtered_detections:
                filtered_results.append(filtered_result)
        
        logger.info(f"Retained {len(filtered_results)} images after filtering")
        return filtered_results
    
    def _create_final_report(
        self,
        preprocessing_results: Dict,
        annotation_results: List[Dict],
        filtered_results: List[Dict],
        export_results: Dict
    ) -> Dict:
        """Create comprehensive final report.
        
        Args:
            preprocessing_results: Image preprocessing results
            annotation_results: Raw annotation results
            filtered_results: Filtered annotation results
            export_results: Dataset export results
            
        Returns:
            Final report dictionary
        """
        # Calculate success rates
        total_input = preprocessing_results['input_statistics']['total_input_images']
        final_output = len(filtered_results)
        
        overall_success_rate = (final_output / total_input * 100) if total_input > 0 else 0
        
        report = {
            'pipeline_info': {
                'version': '1.0.0',
                'completion_time': self.stats['end_time'],
                'total_duration_seconds': self.stats['total_duration'],
                'total_duration_formatted': self._format_duration(self.stats['total_duration'])
            },
            'input_summary': {
                'input_directory': preprocessing_results.get('input_directory'),
                'total_input_images': total_input,
                'supported_formats': self.config.get('input.supported_formats')
            },
            'preprocessing_summary': preprocessing_results,
            'annotation_summary': {
                'total_images_annotated': len([r for r in annotation_results if r['success']]),
                'total_detections_generated': sum(
                    len(r['detections']) for r in annotation_results if r['success']
                ),
                'yolo_statistics': self.yolo_annotator.get_statistics() if self.yolo_annotator else {},
                'sam_statistics': self.sam_annotator.get_statistics() if self.sam_annotator else {}
            },
            'filtering_summary': self.confidence_filter.get_filtering_report(),
            'export_summary': export_results,
            'overall_statistics': {
                'overall_success_rate': overall_success_rate,
                'images_retained': final_output,
                'total_annotations_exported': sum(
                    len(r['detections']) for r in filtered_results
                ),
                'average_annotations_per_image': (
                    sum(len(r['detections']) for r in filtered_results) / len(filtered_results)
                ) if filtered_results else 0
            },
            'configuration_used': self.config.to_dict()
        }
        
        return report
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def _cleanup_models(self) -> None:
        """Cleanup loaded models to free memory."""
        if self.yolo_annotator:
            self.yolo_annotator.unload_model()
        
        if self.sam_annotator:
            self.sam_annotator.unload_model()
        
        logger.info("Models unloaded and memory cleaned up")
    
    def run_preprocessing_only(
        self,
        input_dir: str,
        output_dir: str,
        max_images: Optional[int] = None
    ) -> Dict:
        """Run only the preprocessing step.
        
        Args:
            input_dir: Input directory
            output_dir: Output directory
            max_images: Maximum images to process
            
        Returns:
            Preprocessing results
        """
        logger.info("Running preprocessing only...")
        
        self._validate_inputs(input_dir, output_dir)
        
        results = self.image_processor.process_images(
            input_dir,
            output_dir,
            max_images
        )
        
        logger.info("Preprocessing completed")
        return results
    
    def run_annotation_only(
        self,
        image_dir: str,
        output_file: str
    ) -> Dict:
        """Run only the annotation step on preprocessed images.
        
        Args:
            image_dir: Directory with preprocessed images
            output_file: Output file for annotations
            
        Returns:
            Annotation results
        """
        logger.info("Running annotation only...")
        
        # Discover images
        from .utils.file_utils import FileUtils
        image_paths = FileUtils.get_supported_images(image_dir)
        
        if not image_paths:
            raise ValueError(f"No images found in {image_dir}")
        
        # Load models and generate annotations
        self._load_annotation_models()
        
        # Create mock processed_images structure
        processed_images = [
            {'processed_path': str(path)} for path in image_paths
        ]
        
        annotation_results = self._generate_annotations(processed_images)
        
        # Save results
        import json
        with open(output_file, 'w') as f:
            json.dump(annotation_results, f, indent=2)
        
        self._cleanup_models()
        
        logger.info(f"Annotations saved to {output_file}")
        return {'annotation_results': annotation_results}
    
    def get_pipeline_status(self) -> Dict:
        """Get current pipeline status and statistics.
        
        Returns:
            Status dictionary
        """
        return {
            'statistics': self.stats.copy(),
            'configuration': self.config.to_dict(),
            'components_loaded': {
                'yolo_annotator': self.yolo_annotator is not None,
                'sam_annotator': self.sam_annotator is not None
            }
        }