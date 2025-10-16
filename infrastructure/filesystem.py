"""Filesystem infrastructure for Moobot scraper.

Handles directory creation, JSON data persistence, and file operations
with proper Unicode support.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional


class FileSystemManager:
    """Manages file system operations for the scraper."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
    
    def setup_directories(self) -> None:
        """Create necessary directories."""
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / "html").mkdir(exist_ok=True)
    
    def load_json_data(self, file_path: Path) -> Dict[str, List[Dict]]:
        """Load JSON data from file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Dictionary containing loaded data, empty dict if file doesn't exist or fails to load
        """
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                # Note: We can't log here since this is infrastructure
                # The caller should handle logging
                raise FileOperationError(f"Could not load existing data: {e}")
        return {}
    
    def save_json_data(self, data: Dict[str, Any], file_path: Path) -> None:
        """Save data to JSON file.
        
        Args:
            data: Data to save
            file_path: Path to save the file
            
        Raises:
            FileOperationError: If saving fails
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise FileOperationError(f"Failed to save data: {e}")
    
    def write_text_file(self, content: str, file_path: Path) -> None:
        """Write text content to file.
        
        Args:
            content: Text content to write
            file_path: Path to save the file
            
        Raises:
            FileOperationError: If writing fails
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise FileOperationError(f"Failed to write text file {file_path}: {e}")
    
    def read_text_file(self, file_path: Path) -> str:
        """Read text content from file.
        
        Args:
            file_path: Path to read from
            
        Returns:
            File content as string
            
        Raises:
            FileOperationError: If reading fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise FileOperationError(f"Failed to read text file {file_path}: {e}")


class FileOperationError(Exception):
    """Exception raised when file operations fail."""
    pass


# Convenience functions for backward compatibility
def setup_directories(output_dir: Path) -> None:
    """Create necessary directories."""
    fs_manager = FileSystemManager(output_dir)
    fs_manager.setup_directories()


def load_existing_data(data_file: Path) -> Dict[str, List[Dict]]:
    """Load existing songs data from JSON file."""
    fs_manager = FileSystemManager(data_file.parent)
    try:
        return fs_manager.load_json_data(data_file)
    except FileOperationError:
        # Return empty dict on error for backward compatibility
        return {}


def save_data(data: Dict[str, Any], data_file: Path) -> None:
    """Save songs data to JSON file."""
    fs_manager = FileSystemManager(data_file.parent)
    fs_manager.save_json_data(data, data_file)