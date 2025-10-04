"""
Configuration settings for Web Dashboard Backend
"""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings."""

    # App info
    app_name: str = "YOLO Dataset Builder - Web Dashboard"
    version: str = "0.1.0"
    debug: bool = True

    # Paths
    project_root: Path = Path(__file__).parent.parent.parent
    data_dir: Path = project_root / "data"
    images_dir: Path = data_dir / "raw"
    annotations_dir: Path = data_dir / "annotations"
    reviewed_dir: Path = data_dir / "reviewed"

    # API settings
    api_prefix: str = "/api"
    cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]

    # Database (SQLite for MVP)
    database_url: str = "sqlite:///./dashboard.db"

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100

    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings()


# Ensure directories exist
settings.images_dir.mkdir(parents=True, exist_ok=True)
settings.annotations_dir.mkdir(parents=True, exist_ok=True)
settings.reviewed_dir.mkdir(parents=True, exist_ok=True)
