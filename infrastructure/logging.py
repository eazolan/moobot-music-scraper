"""Logging infrastructure for Moobot scraper.

Provides Unicode-safe logging functionality with proper encoding support
for Windows environments and international characters.
"""

import logging
from pathlib import Path
from typing import Optional


class UnicodeLogger:
    """Logger with Unicode safety for international characters."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def safe_log(self, level: str, message: str) -> None:
        """Safely log messages that might contain Unicode characters."""
        try:
            if level == 'info':
                self.logger.info(message)
            elif level == 'warning':
                self.logger.warning(message)
            elif level == 'error':
                self.logger.error(message)
            elif level == 'debug':
                self.logger.debug(message)
        except UnicodeEncodeError:
            # Fallback: encode problematic characters
            safe_message = message.encode('ascii', errors='replace').decode('ascii')
            if level == 'info':
                self.logger.info(f"[Unicode characters replaced] {safe_message}")
            elif level == 'warning':
                self.logger.warning(f"[Unicode characters replaced] {safe_message}")
            elif level == 'error':
                self.logger.error(f"[Unicode characters replaced] {safe_message}")
            elif level == 'debug':
                self.logger.debug(f"[Unicode characters replaced] {safe_message}")
    
    def info(self, message: str) -> None:
        """Log info message safely."""
        self.safe_log('info', message)
    
    def warning(self, message: str) -> None:
        """Log warning message safely."""
        self.safe_log('warning', message)
    
    def error(self, message: str) -> None:
        """Log error message safely."""
        self.safe_log('error', message)
    
    def debug(self, message: str) -> None:
        """Log debug message safely."""
        self.safe_log('debug', message)


def setup_logging(log_file: Path, output_dir: Path) -> UnicodeLogger:
    """Set up logging configuration with Unicode support.
    
    Args:
        log_file: Path to the log file
        output_dir: Directory for log files
    
    Returns:
        UnicodeLogger instance
    """
    output_dir.mkdir(exist_ok=True)
    
    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Create handlers with proper encoding
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    # Console handler with proper encoding for Windows
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler]
    )
    
    logger = logging.getLogger(__name__)
    return UnicodeLogger(logger)