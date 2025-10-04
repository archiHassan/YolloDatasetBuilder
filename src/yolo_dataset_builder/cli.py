"""Command-line interface for YOLO Dataset Builder."""

import click
import json
import sys
from pathlib import Path
from typing import Optional

from .pipeline import Pipeline
from .config import Config


@click.group()
@click.version_option(version="0.1.0")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def main(ctx, verbose):
    """YOLO Dataset Builder - Automated dataset generation for YOLO training.
    
    Generate COCO-format datasets from raw images using pre-trained AI models.
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose


@main.command()
@click.argument('input_dir', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument('output_dir', type=click.Path(file_okay=False, dir_okay=True))
@click.option('--config', '-c', type=click.Path(exists=True), 
              help='Configuration file path')
@click.option('--max-images', '-m', type=int, 
              help='Maximum number of images to process')
@click.option('--dataset-name', '-n', default='generated_dataset',
              help='Name for the generated dataset')
@click.option('--save-report', '-r', type=click.Path(),
              help='Save pipeline report to file')
@click.pass_context
def run(ctx, input_dir, output_dir, config, max_images, dataset_name, save_report):
    """Run the complete pipeline to generate a COCO dataset.
    
    INPUT_DIR: Directory containing raw images
    OUTPUT_DIR: Directory to save the generated dataset
    """
    try:
        # Initialize pipeline
        pipeline = Pipeline(config)
        
        click.echo(f"🚀 Starting YOLO Dataset Builder")
        click.echo(f"📁 Input: {input_dir}")
        click.echo(f"📁 Output: {output_dir}")
        click.echo(f"📊 Dataset: {dataset_name}")
        
        if max_images:
            click.echo(f"🔢 Max images: {max_images}")
        
        # Run pipeline
        with click.progressbar(length=5, label='Processing') as bar:
            # This is a simplified progress bar
            # In practice, you'd integrate with the pipeline's progress tracking
            results = pipeline.run(
                input_dir=input_dir,
                output_dir=output_dir,
                max_images=max_images,
                dataset_name=dataset_name
            )
            bar.update(5)
        
        # Display results
        _display_results(results)
        
        # Save report if requested
        if save_report:
            with open(save_report, 'w') as f:
                json.dump(results, f, indent=2)
            click.echo(f"📄 Report saved to: {save_report}")
        
        click.echo("✅ Pipeline completed successfully!")
        
    except Exception as e:
        click.echo(f"❌ Pipeline failed: {e}", err=True)
        if ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument('input_dir', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument('output_dir', type=click.Path(file_okay=False, dir_okay=True))
@click.option('--config', '-c', type=click.Path(exists=True),
              help='Configuration file path')
@click.option('--max-images', '-m', type=int,
              help='Maximum number of images to process')
@click.pass_context
def preprocess(ctx, input_dir, output_dir, config, max_images):
    """Run only the image preprocessing step.
    
    INPUT_DIR: Directory containing raw images
    OUTPUT_DIR: Directory to save preprocessed images
    """
    try:
        pipeline = Pipeline(config)
        
        click.echo(f"🖼️  Preprocessing images from {input_dir}")
        
        results = pipeline.run_preprocessing_only(
            input_dir=input_dir,
            output_dir=output_dir,
            max_images=max_images
        )
        
        # Display preprocessing results
        stats = results['input_statistics']
        click.echo(f"📊 Processing Summary:")
        click.echo(f"   • Input images: {stats['total_input_images']}")
        click.echo(f"   • Corrupted removed: {stats['corrupted_removed']}")
        click.echo(f"   • Size filtered: {stats['size_filtered']}")
        click.echo(f"   • Duplicates removed: {stats['duplicates_removed']}")
        click.echo(f"   • Final processed: {stats['final_processed']}")
        
        click.echo("✅ Preprocessing completed!")
        
    except Exception as e:
        click.echo(f"❌ Preprocessing failed: {e}", err=True)
        if ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument('image_dir', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument('output_file', type=click.Path())
@click.option('--config', '-c', type=click.Path(exists=True),
              help='Configuration file path')
@click.pass_context
def annotate(ctx, image_dir, output_file, config):
    """Run only the annotation step on preprocessed images.
    
    IMAGE_DIR: Directory containing preprocessed images
    OUTPUT_FILE: File to save annotation results
    """
    try:
        pipeline = Pipeline(config)
        
        click.echo(f"🏷️  Generating annotations for images in {image_dir}")
        
        results = pipeline.run_annotation_only(
            image_dir=image_dir,
            output_file=output_file
        )
        
        annotation_results = results['annotation_results']
        successful = len([r for r in annotation_results if r['success']])
        total_detections = sum(len(r['detections']) for r in annotation_results if r['success'])
        
        click.echo(f"📊 Annotation Summary:")
        click.echo(f"   • Images processed: {successful}")
        click.echo(f"   • Total detections: {total_detections}")
        click.echo(f"   • Average per image: {total_detections/successful:.1f}" if successful > 0 else "   • Average per image: 0.0")
        
        click.echo("✅ Annotation completed!")
        
    except Exception as e:
        click.echo(f"❌ Annotation failed: {e}", err=True)
        if ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.option('--output', '-o', type=click.Path(), default='config.yaml',
              help='Output configuration file path')
def init_config(output):
    """Generate a default configuration file."""
    try:
        # Load default config
        config = Config()
        
        # Save to specified output
        config.save(output)
        
        click.echo(f"📝 Default configuration saved to: {output}")
        click.echo("Edit this file to customize pipeline settings.")
        
    except Exception as e:
        click.echo(f"❌ Failed to create config: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument('config_file', type=click.Path(exists=True))
def validate_config(config_file):
    """Validate a configuration file."""
    try:
        config = Config(config_file)
        config.validate()
        
        click.echo(f"✅ Configuration file is valid: {config_file}")
        
        # Display key settings
        click.echo("📋 Key Settings:")
        click.echo(f"   • Project: {config.get('project.name')}")
        click.echo(f"   • YOLO model: {config.get('models.yolo.model_name')}")
        click.echo(f"   • SAM model: {config.get('models.sam.model_type')}")
        click.echo(f"   • Export format: {config.get('export.format')}")
        
    except Exception as e:
        click.echo(f"❌ Configuration validation failed: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument('annotation_file', type=click.Path(exists=True))
def validate_coco(annotation_file):
    """Validate a COCO format annotation file."""
    try:
        from .export.coco_exporter import COCOExporter
        
        # Create exporter for validation
        exporter = COCOExporter({})
        
        # Validate file
        results = exporter.validate_coco_format(annotation_file)
        
        if results['valid']:
            click.echo(f"✅ COCO file is valid: {annotation_file}")
            click.echo(f"📊 Summary:")
            click.echo(f"   • Images: {results['image_count']}")
            click.echo(f"   • Annotations: {results['annotation_count']}")
            click.echo(f"   • Categories: {results['category_count']}")
        else:
            click.echo(f"❌ COCO file validation failed: {annotation_file}")
            for error in results['errors']:
                click.echo(f"   • {error}")
            sys.exit(1)
        
    except Exception as e:
        click.echo(f"❌ Validation failed: {e}", err=True)
        sys.exit(1)


@main.command()
def info():
    """Display system information and requirements."""
    click.echo("🔧 YOLO Dataset Builder - System Information")
    click.echo()
    
    # Check Python version
    import sys
    click.echo(f"🐍 Python: {sys.version}")
    
    # Check key dependencies
    dependencies = [
        ('torch', 'PyTorch'),
        ('ultralytics', 'YOLOv8'),
        ('cv2', 'OpenCV'),
        ('PIL', 'Pillow'),
        ('numpy', 'NumPy'),
        ('pandas', 'Pandas'),
        ('yaml', 'PyYAML')
    ]
    
    click.echo("\n📦 Dependencies:")
    for module, name in dependencies:
        try:
            __import__(module)
            click.echo(f"   ✅ {name}")
        except ImportError:
            click.echo(f"   ❌ {name} (not installed)")
    
    # Check GPU availability
    try:
        import torch
        if torch.cuda.is_available():
            click.echo(f"\n🚀 GPU: {torch.cuda.get_device_name()}")
            click.echo(f"   CUDA version: {torch.version.cuda}")
        else:
            click.echo("\n💻 GPU: Not available (CPU mode)")
    except ImportError:
        click.echo("\n💻 GPU: Cannot check (PyTorch not installed)")
    
    # Check SAM availability
    try:
        import segment_anything
        click.echo("\n🎯 SAM: Available")
    except ImportError:
        click.echo("\n⚠️  SAM: Not installed (optional)")
        click.echo("   Install with: pip install git+https://github.com/facebookresearch/segment-anything.git")


def _display_results(results: dict) -> None:
    """Display pipeline results in a user-friendly format.
    
    Args:
        results: Pipeline results dictionary
    """
    click.echo("\n📊 Pipeline Results:")
    
    # Overall statistics
    overall = results['overall_statistics']
    click.echo(f"   • Success rate: {overall['overall_success_rate']:.1f}%")
    click.echo(f"   • Images retained: {overall['images_retained']}")
    click.echo(f"   • Total annotations: {overall['total_annotations_exported']}")
    click.echo(f"   • Avg annotations/image: {overall['average_annotations_per_image']:.1f}")
    
    # Processing time
    duration = results['pipeline_info']['total_duration_formatted']
    click.echo(f"   • Processing time: {duration}")
    
    # Dataset splits
    if 'splits' in results['export_summary']:
        click.echo("\n📁 Dataset Splits:")
        splits = results['export_summary']['splits']
        for split_name, split_info in splits.items():
            click.echo(f"   • {split_name}: {split_info['image_count']} images, "
                      f"{split_info['annotation_count']} annotations")
    
    # Output location
    output_dir = results['export_summary']['output_directory']
    click.echo(f"\n📁 Output directory: {output_dir}")


if __name__ == '__main__':
    main()