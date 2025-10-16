"""Web Extraction domain entities.

Core entities for web scraping sessions, extraction results, 
and related value objects.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from selenium.webdriver.remote.webdriver import WebDriver
from domains.music_queue.entities import SongRequest, StreamerId


@dataclass
class ExtractionSession:
    """Represents a web extraction session with browser and context."""
    
    streamer_id: StreamerId
    browser: WebDriver
    debug_artifacts: Dict[str, Any] = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate extraction session data."""
        if not self.streamer_id:
            raise ValueError("StreamerId is required")
        
        if not self.browser:
            raise ValueError("WebDriver browser is required")
    
    @property
    def moobot_url(self) -> str:
        """Get the Moobot URL for this session's streamer."""
        return self.streamer_id.moobot_url
    
    @property
    def session_duration(self) -> float:
        """Get session duration in seconds."""
        return (datetime.now() - self.start_time).total_seconds()
    
    def add_debug_artifact(self, name: str, data: Any) -> None:
        """Add debug artifact to the session."""
        self.debug_artifacts[name] = data
    
    def save_debug_artifacts(self, output_dir: Path) -> None:
        """Save debug artifacts to files."""
        try:
            # Save screenshot
            screenshot_path = output_dir / "page_screenshot.png"
            self.browser.save_screenshot(str(screenshot_path))
            self.add_debug_artifact("screenshot_path", str(screenshot_path))
            
            # Save page source
            source_path = output_dir / "page_source.html"
            with open(source_path, 'w', encoding='utf-8') as f:
                f.write(self.browser.page_source)
            self.add_debug_artifact("source_path", str(source_path))
            
        except Exception as e:
            self.add_debug_artifact("debug_save_error", str(e))


@dataclass(frozen=True)
class ExtractionResult:
    """Result of a web extraction operation."""
    
    songs: List[SongRequest]
    success: bool
    strategy_used: str
    debug_info: Dict[str, Any] = field(default_factory=dict)
    extraction_time: datetime = field(default_factory=datetime.now)
    
    @property
    def song_count(self) -> int:
        """Get the number of songs extracted."""
        return len(self.songs)
    
    @property
    def has_songs(self) -> bool:
        """Check if any songs were extracted."""
        return self.song_count > 0
    
    @property
    def youtube_song_count(self) -> int:
        """Get count of songs with YouTube links."""
        return sum(1 for song in self.songs if song.has_youtube_link)
    
    @classmethod
    def success_result(cls, songs: List[SongRequest], strategy_used: str, 
                      debug_info: Dict[str, Any] = None) -> 'ExtractionResult':
        """Create a successful extraction result."""
        return cls(
            songs=songs,
            success=True,
            strategy_used=strategy_used,
            debug_info=debug_info or {}
        )
    
    @classmethod
    def failure_result(cls, strategy_used: str, error_message: str) -> 'ExtractionResult':
        """Create a failed extraction result."""
        return cls(
            songs=[],
            success=False,
            strategy_used=strategy_used,
            debug_info={"error": error_message}
        )


@dataclass(frozen=True)
class YouTubeUrl:
    """Value object representing a YouTube URL with validation."""
    
    url: str
    
    def __post_init__(self):
        """Validate YouTube URL."""
        if not self.url:
            raise ValueError("YouTube URL cannot be empty")
            
        if not ("youtube.com" in self.url or "youtu.be" in self.url):
            raise ValueError(f"Invalid YouTube URL: {self.url}")
    
    @property
    def is_direct_video(self) -> bool:
        """Check if this is a direct video link."""
        return "youtube.com/watch" in self.url or "youtu.be/" in self.url
    
    @property
    def is_search_url(self) -> bool:
        """Check if this is a search URL."""
        return "youtube.com/results" in self.url
    
    @property
    def video_id(self) -> Optional[str]:
        """Extract video ID if this is a direct video link."""
        if not self.is_direct_video:
            return None
            
        try:
            if "youtu.be/" in self.url:
                return self.url.split("youtu.be/")[1].split("?")[0]
            elif "watch?v=" in self.url:
                return self.url.split("watch?v=")[1].split("&")[0]
        except (IndexError, AttributeError):
            pass
            
        return None
    
    def __str__(self) -> str:
        return self.url


@dataclass
class StreamerValidationResult:
    """Result of streamer existence validation."""
    
    exists: bool
    streamer_id: StreamerId
    error_message: Optional[str] = None
    page_indicators: List[str] = field(default_factory=list)
    
    @classmethod
    def valid_streamer(cls, streamer_id: StreamerId, 
                      indicators: List[str] = None) -> 'StreamerValidationResult':
        """Create result for valid streamer."""
        return cls(
            exists=True,
            streamer_id=streamer_id,
            page_indicators=indicators or []
        )
    
    @classmethod
    def invalid_streamer(cls, streamer_id: StreamerId, 
                        error_message: str) -> 'StreamerValidationResult':
        """Create result for invalid streamer."""
        return cls(
            exists=False,
            streamer_id=streamer_id,
            error_message=error_message
        )


@dataclass
class ExtractionConfig:
    """Configuration for web extraction operations."""
    
    page_load_timeout: int = 15
    element_wait_timeout: int = 10
    scan_strategies: List[str] = field(default_factory=lambda: [
        "table_strategy", "youtube_strategy", "text_strategy"
    ])
    max_songs_per_strategy: int = 50
    debug_enabled: bool = True
    
    def __post_init__(self):
        """Validate configuration."""
        if self.page_load_timeout <= 0:
            raise ValueError("Page load timeout must be positive")
            
        if self.element_wait_timeout <= 0:
            raise ValueError("Element wait timeout must be positive")
            
        if not self.scan_strategies:
            raise ValueError("At least one scan strategy must be configured")