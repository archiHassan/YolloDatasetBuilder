"""
YOLO Dataset Builder - Automated dataset generation pipeline for YOLO models.

This package provides tools to automatically generate COCO-format datasets
from raw, unlabeled images using pre-trained AI models.
"""

__version__ = "0.1.0"
__author__ = "YOLO Dataset Builder Team"

from .pipeline import Pipeline
from .config import Config

__all__ = ["Pipeline", "Config"]