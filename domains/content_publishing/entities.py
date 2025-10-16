"""Content Publishing domain entities.

Core entities for HTML generation and content publishing.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict, Optional
from domains.music_queue.entities import SongRequest, StreamerId


@dataclass
class SongCollection:
    """Represents a collection of songs for a specific date and streamer."""
    
    date: date
    songs: List[SongRequest]
    streamer_id: StreamerId
    
    def __post_init__(self):
        """Validate the song collection."""
        if not self.songs:
            # Allow empty collections for dates with no songs
            pass
        
        if not isinstance(self.date, date):
            raise ValueError("Date must be a date object")
    
    @property
    def song_count(self) -> int:
        """Get the number of songs in this collection."""
        return len(self.songs)
    
    @property
    def formatted_date(self) -> str:
        """Get a human-readable formatted date."""
        try:
            return self.date.strftime("%B %d, %Y")
        except:
            return self.date.isoformat()
    
    @property
    def file_date(self) -> str:
        """Get the date formatted for file names."""
        return self.date.isoformat()
    
    @property
    def has_youtube_songs(self) -> int:
        """Get count of songs with YouTube links."""
        return sum(1 for song in self.songs if song.has_youtube_link)
    
    def get_songs_with_youtube(self) -> List[SongRequest]:
        """Get all songs that have YouTube links."""
        return [song for song in self.songs if song.has_youtube_link]
    
    def get_recent_songs(self, limit: int = 5) -> List[SongRequest]:
        """Get the most recent songs (by timestamp)."""
        sorted_songs = sorted(self.songs, key=lambda s: s.timestamp, reverse=True)
        return sorted_songs[:limit]


@dataclass(frozen=True)
class HtmlPage:
    """Represents a generated HTML page."""
    
    content: str
    title: str
    file_path: Path
    
    def __post_init__(self):
        """Validate HTML page data."""
        if not self.content or not self.content.strip():
            raise ValueError("HTML content cannot be empty")
        
        if not self.title or not self.title.strip():
            raise ValueError("Page title cannot be empty")
        
        if not self.file_path:
            raise ValueError("File path cannot be empty")
    
    @property
    def file_name(self) -> str:
        """Get the filename without path."""
        return self.file_path.name
    
    @property
    def content_length(self) -> int:
        """Get the length of the HTML content."""
        return len(self.content)


@dataclass(frozen=True)
class PublishingConfig:
    """Configuration for content publishing."""
    
    output_dir: Path
    streamer_name: str
    template_style: str = "twitch_purple"
    
    def __post_init__(self):
        """Validate publishing configuration."""
        if not self.output_dir:
            raise ValueError("Output directory cannot be empty")
        
        if not self.streamer_name or not self.streamer_name.strip():
            raise ValueError("Streamer name cannot be empty")
    
    @property
    def html_dir(self) -> Path:
        """Get the HTML output directory."""
        return self.output_dir / "html"
    
    @property
    def index_file_path(self) -> Path:
        """Get the path for the index HTML file."""
        return self.html_dir / "index.html"
    
    def get_daily_file_path(self, date: date) -> Path:
        """Get the path for a daily HTML file."""
        date_str = date.isoformat()
        return self.html_dir / f"songs_{date_str}.html"
    
    @property
    def display_streamer_name(self) -> str:
        """Get the streamer name formatted for display."""
        return self.streamer_name.strip().title()


@dataclass
class PublishingResult:
    """Result of a publishing operation."""
    
    success: bool
    pages_generated: List[HtmlPage] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    @property
    def total_pages(self) -> int:
        """Get the total number of pages generated."""
        return len(self.pages_generated)
    
    @property
    def has_errors(self) -> bool:
        """Check if there were any errors during publishing."""
        return len(self.errors) > 0
    
    def add_page(self, page: HtmlPage) -> None:
        """Add a successfully generated page."""
        self.pages_generated.append(page)
    
    def add_error(self, error: str) -> None:
        """Add an error that occurred during publishing."""
        self.errors.append(error)
        self.success = False