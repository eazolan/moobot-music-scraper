"""ExtractionConfig entity for configuring song extraction."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class ExtractionConfig:
    """Configuration for song extraction operations.
    
    Defines parameters and settings for how extraction strategies
    should behave when extracting songs from web elements.
    """
    
    # Filtering options
    min_title_length: int = 3
    max_title_length: int = 200
    skip_ui_text: bool = True
    skip_empty_elements: bool = True
    
    # Processing options
    clean_titles: bool = True
    extract_youtube_urls: bool = True
    extract_metadata: bool = True
    
    # Retry and robustness options
    use_robust_finding: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # YouTube URL extraction options
    try_direct_links: bool = True
    try_button_click: bool = True
    try_history_thumbnails: bool = True
    try_javascript_extraction: bool = True
    fallback_to_search: bool = True
    
    # Audio control (for YouTube extraction)
    mute_audio: bool = True
    pause_videos: bool = True
    close_new_tabs: bool = True
    
    # Limits and performance
    max_songs_per_strategy: Optional[int] = None
    timeout_seconds: float = 30.0
    
    # Custom attributes for specific strategies
    custom_attributes: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize optional fields."""
        if self.custom_attributes is None:
            self.custom_attributes = {}
    
    def get_custom_attribute(self, key: str, default: Any = None) -> Any:
        """Get a custom attribute value."""
        return self.custom_attributes.get(key, default)
    
    def set_custom_attribute(self, key: str, value: Any):
        """Set a custom attribute value."""
        self.custom_attributes[key] = value
    
    @classmethod
    def create_default(cls) -> "ExtractionConfig":
        """Create a default extraction configuration."""
        return cls()
    
    @classmethod
    def create_fast(cls) -> "ExtractionConfig":
        """Create a fast extraction configuration (less thorough)."""
        return cls(
            try_button_click=False,
            try_history_thumbnails=False,
            try_javascript_extraction=False,
            max_retries=1,
            timeout_seconds=10.0
        )
    
    @classmethod
    def create_thorough(cls) -> "ExtractionConfig":
        """Create a thorough extraction configuration (more complete)."""
        return cls(
            try_direct_links=True,
            try_button_click=True,
            try_history_thumbnails=True,
            try_javascript_extraction=True,
            fallback_to_search=True,
            max_retries=5,
            timeout_seconds=60.0,
            extract_metadata=True
        )
    
    @classmethod
    def create_silent(cls) -> "ExtractionConfig":
        """Create a silent extraction configuration (no audio)."""
        return cls(
            try_button_click=False,  # Avoid opening tabs that might play audio
            mute_audio=True,
            pause_videos=True,
            close_new_tabs=True
        )