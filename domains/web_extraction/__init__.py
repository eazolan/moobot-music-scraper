"""Web Extraction domain.

Handles web scraping, browser automation, and data extraction
from dynamic web pages using multiple strategies.
"""

from .entities import ExtractionSession, ExtractionResult, YouTubeUrl
from .webdriver_manager import WebDriverManager
from .extractor import SongExtractor

__all__ = [
    'ExtractionSession',
    'ExtractionResult', 
    'YouTubeUrl',
    'WebDriverManager',
    'SongExtractor'
]