"""Music Queue domain entities.

Core business entities representing song requests and streamer identity.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SongRequest:
    """Represents a song request in the music queue."""
    
    title: str
    duration: Optional[str] = None
    requester: Optional[str] = None
    status: Optional[str] = None
    youtube_url: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    scraped_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    selector_used: Optional[str] = None
    element_index: Optional[int] = None
    
    def __post_init__(self):
        """Validate song request data."""
        if not self.title or not self.title.strip():
            raise ValueError("Song title cannot be empty")
        
        # Clean the title
        self.title = self.title.strip()
    
    @property
    def has_youtube_link(self) -> bool:
        """Check if the song has a direct YouTube link."""
        return bool(self.youtube_url and 
                   ("youtube.com" in self.youtube_url or "youtu.be" in self.youtube_url))
    
    @property
    def enhanced_title(self) -> str:
        """Get title with metadata for display purposes."""
        enhanced = self.title
        if self.duration:
            enhanced += f" [{self.duration}]"
        if self.requester:
            enhanced += f" - {self.requester}"
        if self.status:
            enhanced += f" ({self.status})"
        return enhanced
    
    def to_dict(self) -> dict:
        """Convert to dictionary format (for backward compatibility)."""
        return {
            "title": self.title,
            "duration": self.duration,
            "requester": self.requester,
            "status": self.status,
            "youtube_url": self.youtube_url,
            "timestamp": self.timestamp.isoformat(),
            "scraped_at": self.scraped_at,
            "selector_used": self.selector_used,
            "element_index": self.element_index,
            "enhanced_title": self.enhanced_title
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SongRequest':
        """Create SongRequest from dictionary (for backward compatibility)."""
        # Handle timestamp conversion
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()
        
        return cls(
            title=data.get('title', ''),
            duration=data.get('duration'),
            requester=data.get('requester'),
            status=data.get('status'),
            youtube_url=data.get('youtube_url'),
            timestamp=timestamp,
            scraped_at=data.get('scraped_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            selector_used=data.get('selector_used'),
            element_index=data.get('element_index')
        )


@dataclass(frozen=True)
class StreamerId:
    """Value object representing a Twitch streamer identifier."""
    
    name: str
    
    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Streamer name cannot be empty")
    
    @property
    def normalized_name(self) -> str:
        """Get the normalized streamer name (lowercase, stripped)."""
        return self.name.strip().lower()
    
    @property
    def display_name(self) -> str:
        """Get the display-friendly streamer name."""
        return self.name.strip().title()
    
    @property
    def moobot_url(self) -> str:
        """Get the Moobot URL for this streamer."""
        return f"https://moo.bot/r/music#{self.name}"
    
    def __str__(self) -> str:
        return self.name