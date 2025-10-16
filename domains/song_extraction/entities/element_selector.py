"""ElementSelector entity for defining web element selection."""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


class SelectorType(Enum):
    """Types of CSS selectors for element selection."""
    CSS = "css"
    XPATH = "xpath"
    TAG_NAME = "tag_name" 
    CLASS_NAME = "class_name"
    ID = "id"


@dataclass
class ElementSelector:
    """Defines how to select web elements for song extraction.
    
    Encapsulates the selector string, type, and associated metadata
    for finding elements on a web page.
    """
    
    selector: str
    selector_type: SelectorType = SelectorType.CSS
    description: Optional[str] = None
    priority: int = 1  # Higher numbers = higher priority
    is_fallback: bool = False
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize optional fields."""
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def is_table_row_selector(self) -> bool:
        """Check if this selector targets table rows."""
        return "tr" in self.selector.lower()
    
    @property
    def is_youtube_link_selector(self) -> bool:
        """Check if this selector targets YouTube links."""
        return any(keyword in self.selector.lower() 
                  for keyword in ["youtube", "youtu.be", "href*="])
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        return self.metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any):
        """Set metadata value."""
        self.metadata[key] = value
    
    @classmethod
    def create_table_row(cls, priority: int = 10) -> "ElementSelector":
        """Create selector for Moobot table rows."""
        return cls(
            selector="tr",
            selector_type=SelectorType.CSS,
            description="Moobot song queue table rows",
            priority=priority
        )
    
    @classmethod
    def create_youtube_links(cls, priority: int = 8) -> "ElementSelector":
        """Create selector for YouTube links."""
        return cls(
            selector="a[href*='youtube.com'], a[href*='youtu.be']",
            selector_type=SelectorType.CSS,
            description="Direct YouTube links",
            priority=priority
        )
    
    @classmethod
    def create_song_titles(cls, priority: int = 5) -> "ElementSelector":
        """Create selector for song title elements."""
        return cls(
            selector=".moobot-input-label-text-text, .song-title, .title",
            selector_type=SelectorType.CSS,
            description="Song title elements",
            priority=priority
        )
    
    @classmethod
    def create_generic_links(cls, priority: int = 3) -> "ElementSelector":
        """Create selector for generic links."""
        return cls(
            selector="a",
            selector_type=SelectorType.CSS,
            description="All link elements",
            priority=priority,
            is_fallback=True
        )
    
    @classmethod
    def create_text_elements(cls, priority: int = 1) -> "ElementSelector":
        """Create selector for text elements (fallback)."""
        return cls(
            selector="div, span, p, li",
            selector_type=SelectorType.CSS, 
            description="Text-containing elements",
            priority=priority,
            is_fallback=True
        )
    
    @classmethod
    def create_custom(
        cls, 
        selector: str, 
        selector_type: SelectorType = SelectorType.CSS,
        description: Optional[str] = None,
        priority: int = 5
    ) -> "ElementSelector":
        """Create a custom selector."""
        return cls(
            selector=selector,
            selector_type=selector_type,
            description=description or f"Custom {selector_type.value} selector",
            priority=priority
        )