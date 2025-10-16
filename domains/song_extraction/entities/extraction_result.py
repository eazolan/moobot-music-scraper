"""ExtractionResult entity for song extraction domain."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

from domains.music_queue.entities import SongRequest


@dataclass
class ExtractionResult:
    """Result of a song extraction operation.
    
    Encapsulates the songs found, metadata about the extraction process,
    and any errors or warnings encountered.
    """
    
    songs: List[SongRequest]
    strategy_used: str
    timestamp: datetime
    selector_used: str
    element_count: int
    success: bool = True
    error_message: Optional[str] = None
    warnings: List[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize optional fields."""
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def song_count(self) -> int:
        """Number of songs extracted."""
        return len(self.songs)
    
    @property
    def has_songs(self) -> bool:
        """Whether any songs were extracted."""
        return len(self.songs) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Whether there are any warnings."""
        return len(self.warnings) > 0
    
    def add_warning(self, warning: str):
        """Add a warning message."""
        self.warnings.append(warning)
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata information."""
        self.metadata[key] = value
    
    @classmethod
    def create_success(
        cls,
        songs: List[SongRequest],
        strategy_used: str,
        selector_used: str,
        element_count: int,
        timestamp: Optional[datetime] = None
    ) -> "ExtractionResult":
        """Create a successful extraction result."""
        if timestamp is None:
            timestamp = datetime.now()
            
        return cls(
            songs=songs,
            strategy_used=strategy_used,
            timestamp=timestamp,
            selector_used=selector_used,
            element_count=element_count,
            success=True
        )
    
    @classmethod 
    def create_failure(
        cls,
        error_message: str,
        strategy_used: str,
        selector_used: str = "",
        element_count: int = 0,
        timestamp: Optional[datetime] = None
    ) -> "ExtractionResult":
        """Create a failed extraction result."""
        if timestamp is None:
            timestamp = datetime.now()
            
        return cls(
            songs=[],
            strategy_used=strategy_used,
            timestamp=timestamp,
            selector_used=selector_used,
            element_count=element_count,
            success=False,
            error_message=error_message
        )