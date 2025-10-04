"""Configuration management for YOLO Dataset Builder."""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """Configuration manager for the YOLO dataset builder pipeline."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.
        
        Args:
            config_path: Path to configuration file. If None, uses default config.
        """
        self.config_path = config_path or self._get_default_config_path()
        self._config_data = self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        current_dir = Path(__file__).parent.parent.parent
        return str(current_dir / "configs" / "default.yaml")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing configuration file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation (e.g., 'models.yolo.confidence_threshold')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config_data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation
            value: Value to set
        """
        keys = key.split('.')
        config = self._config_data
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the final value
        config[keys[-1]] = value
    
    def save(self, output_path: Optional[str] = None) -> None:
        """Save configuration to file.
        
        Args:
            output_path: Path to save configuration. If None, overwrites current file.
        """
        save_path = output_path or self.config_path
        
        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(self._config_data, f, default_flow_style=False, indent=2)
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values.
        
        Args:
            updates: Dictionary of configuration updates
        """
        self._deep_update(self._config_data, updates)
    
    def _deep_update(self, base: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """Deep update dictionary values."""
        for key, value in updates.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def validate(self) -> bool:
        """Validate configuration settings.
        
        Returns:
            True if configuration is valid
        """
        required_keys = [
            'project.name',
            'input.image_dir',
            'models.yolo.model_name',
            'export.format'
        ]
        
        for key in required_keys:
            if self.get(key) is None:
                raise ValueError(f"Required configuration key missing: {key}")
        
        # Validate split ratios sum to 1.0
        split_ratios = self.get('export.split_ratios', {})
        if split_ratios:
            total = sum(split_ratios.values())
            if not (0.99 <= total <= 1.01):  # Allow small floating point errors
                raise ValueError(f"Split ratios must sum to 1.0, got {total}")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary."""
        return self._config_data.copy()
    
    def __str__(self) -> str:
        """String representation of configuration."""
        return yaml.safe_dump(self._config_data, default_flow_style=False, indent=2)