"""Song Extraction Domain Entities

This module contains the core entities for the song extraction domain,
representing the fundamental concepts and data structures used in
extracting songs from web pages.
"""

from .extraction_result import ExtractionResult
from .extraction_config import ExtractionConfig
from .element_selector import ElementSelector

__all__ = [
    "ExtractionResult",
    "ExtractionConfig", 
    "ElementSelector"
]