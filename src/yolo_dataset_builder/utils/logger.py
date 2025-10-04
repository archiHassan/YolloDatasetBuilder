"""Logging utilities for YOLO Dataset Builder."""

import logging
import os
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "yolo_dataset_builder",
    level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True
) -> logging.Logger:
    """Set up logger with file and console handlers.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file. If None, logs only to console
        console_output: Whether to output logs to console
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Set level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


class ProgressLogger:
    """Logger for tracking progress with counters."""
    
    def __init__(self, logger: logging.Logger, total: int, log_interval: int = 100):
        """Initialize progress logger.
        
        Args:
            logger: Logger instance
            total: Total number of items to process
            log_interval: Log progress every N items
        """
        self.logger = logger
        self.total = total
        self.log_interval = log_interval
        self.processed = 0
    
    def update(self, count: int = 1, message: str = "Processing") -> None:
        """Update progress counter and log if needed.
        
        Args:
            count: Number of items processed
            message: Progress message
        """
        self.processed += count
        
        if self.processed % self.log_interval == 0 or self.processed == self.total:
            percentage = (self.processed / self.total) * 100
            self.logger.info(f"{message}: {self.processed}/{self.total} ({percentage:.1f}%)")
    
    def finish(self, message: str = "Completed") -> None:
        """Log completion message."""
        self.logger.info(f"{message}: {self.processed}/{self.total} (100.0%)")