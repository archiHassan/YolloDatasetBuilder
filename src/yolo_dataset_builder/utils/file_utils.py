"""File operation utilities."""

import os
import shutil
from pathlib import Path
from typing import List, Set, Optional, Generator
import hashlib


class FileUtils:
    """Utility class for file operations."""
    
    @staticmethod
    def get_supported_images(
        directory: str, 
        extensions: Optional[Set[str]] = None
    ) -> List[Path]:
        """Get all supported image files from directory.
        
        Args:
            directory: Directory to search
            extensions: Set of supported extensions (with dots, e.g., {'.jpg', '.png'})
            
        Returns:
            List of image file paths
        """
        if extensions is None:
            extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        
        # Convert to lowercase for case-insensitive matching
        extensions = {ext.lower() for ext in extensions}
        
        directory_path = Path(directory)
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        image_files = []
        for file_path in directory_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                image_files.append(file_path)
        
        return sorted(image_files)
    
    @staticmethod
    def create_directory(path: str, exist_ok: bool = True) -> Path:
        """Create directory with all parent directories.
        
        Args:
            path: Directory path to create
            exist_ok: Don't raise error if directory exists
            
        Returns:
            Created directory path
        """
        directory = Path(path)
        directory.mkdir(parents=True, exist_ok=exist_ok)
        return directory
    
    @staticmethod
    def copy_file(src: str, dst: str, preserve_metadata: bool = True) -> None:
        """Copy file from source to destination.
        
        Args:
            src: Source file path
            dst: Destination file path
            preserve_metadata: Whether to preserve file metadata
        """
        src_path = Path(src)
        dst_path = Path(dst)
        
        # Create destination directory if it doesn't exist
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        if preserve_metadata:
            shutil.copy2(src_path, dst_path)
        else:
            shutil.copy(src_path, dst_path)
    
    @staticmethod
    def get_file_hash(file_path: str, algorithm: str = 'md5') -> str:
        """Calculate file hash.
        
        Args:
            file_path: Path to file
            algorithm: Hash algorithm ('md5', 'sha1', 'sha256')
            
        Returns:
            File hash as hexadecimal string
        """
        hash_func = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size in bytes.
        
        Args:
            file_path: Path to file
            
        Returns:
            File size in bytes
        """
        return Path(file_path).stat().st_size
    
    @staticmethod
    def clean_filename(filename: str) -> str:
        """Clean filename by removing invalid characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Cleaned filename
        """
        # Characters not allowed in filenames
        invalid_chars = '<>:"/\\|?*'
        
        cleaned = filename
        for char in invalid_chars:
            cleaned = cleaned.replace(char, '_')
        
        # Remove leading/trailing spaces and dots
        cleaned = cleaned.strip(' .')
        
        return cleaned
    
    @staticmethod
    def safe_remove(file_path: str) -> bool:
        """Safely remove file, handling errors gracefully.
        
        Args:
            file_path: Path to file to remove
            
        Returns:
            True if file was removed, False otherwise
        """
        try:
            Path(file_path).unlink()
            return True
        except (FileNotFoundError, PermissionError, OSError):
            return False
    
    @staticmethod
    def batch_rename_files(
        file_paths: List[str], 
        name_pattern: str = "image_{:05d}",
        preserve_extension: bool = True
    ) -> List[str]:
        """Batch rename files with sequential naming.
        
        Args:
            file_paths: List of file paths to rename
            name_pattern: Pattern for new names (should include format placeholder)
            preserve_extension: Whether to keep original file extensions
            
        Returns:
            List of new file paths
        """
        new_paths = []
        
        for i, file_path in enumerate(file_paths):
            path = Path(file_path)
            
            # Generate new name
            new_name = name_pattern.format(i + 1)
            
            if preserve_extension:
                new_name += path.suffix
            
            new_path = path.parent / new_name
            
            # Rename file
            path.rename(new_path)
            new_paths.append(str(new_path))
        
        return new_paths