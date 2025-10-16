"""Song Extraction Domain

This domain handles the extraction of songs from web pages using various
strategies and selectors. It provides a clean interface for different
extraction approaches while maintaining consistency in results.
"""

from .entities import ExtractionResult, ExtractionConfig, ElementSelector
from .services import ExtractionStrategy, ExtractionCoordinator

__all__ = [
    # Entities
    "ExtractionResult",
    "ExtractionConfig", 
    "ElementSelector",
    
    # Services
    "ExtractionStrategy",
    "ExtractionCoordinator"
]