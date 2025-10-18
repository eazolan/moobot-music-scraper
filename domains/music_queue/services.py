"""Music Queue domain services.

Business logic services for song matching, queue management,
and data repository operations.
"""

import re
from datetime import date
from pathlib import Path
from typing import List, Dict, Set
from infrastructure.filesystem import FileSystemManager, FileOperationError
from infrastructure.logging import UnicodeLogger
from .entities import SongRequest, StreamerId


class SongMatchingService:
    """Service for comparing and matching song titles."""
    
    def __init__(self):
        pass
    
    def songs_match(self, song1: SongRequest, song2: SongRequest) -> bool:
        """Check if two song requests likely refer to the same song."""
        return self.titles_match(song1.title, song2.title)
    
    def titles_match(self, title1: str, title2: str) -> bool:
        """Check if two song titles likely refer to the same song."""
        try:
            norm1 = self.normalize_title(title1)
            norm2 = self.normalize_title(title2)
            
            # Exact match
            if norm1 == norm2:
                return True
            
            # Check if one is contained in the other (for cases like \"Song\" vs \"Song (Official Video)\")
            if norm1 in norm2 or norm2 in norm1:
                # Make sure it's not too short to avoid false positives
                if len(min(norm1, norm2)) > 10:
                    return True
            
            # Check similarity by word overlap
            words1 = set(norm1.split())
            words2 = set(norm2.split())
            
            if len(words1) > 0 and len(words2) > 0:
                overlap = len(words1.intersection(words2))
                total_words = len(words1.union(words2))
                similarity = overlap / total_words
                
                # If more than 70% of words match, consider it the same song
                if similarity > 0.7:
                    return True
            
            return False
            
        except Exception:
            # On any error, assume they don't match
            return False
    
    def normalize_title(self, title: str) -> str:
        """Normalize a song title for comparison."""
        if not title:
            return ""
        
        # Convert to lowercase
        title = title.lower().strip()
        
        # Remove common suffixes and prefixes
        suffixes = [
            ' (official video)', ' (official audio)', ' (official)', 
            ' (lyrics)', ' m/v', ' | lyrics'
        ]
        for suffix in suffixes:
            if title.endswith(suffix):
                title = title[:-len(suffix)].strip()
                break
        
        # Remove extra whitespace and special characters
        title = re.sub(r'[^a-z0-9\\s]', ' ', title)
        title = ' '.join(title.split())
        return title
    
    def clean_song_title(self, title: str) -> str:
        """Clean and normalize song titles for display."""
        if not title:
            return ""
        
        # Remove extra whitespace
        title = " ".join(title.split())
        
        # Remove common prefixes/suffixes
        prefixes_to_remove = ["Now Playing:", "Current:", "Playing:", "♪", "♫", "🎵", "🎶"]
        for prefix in prefixes_to_remove:
            if title.startswith(prefix):
                title = title[len(prefix):].strip()
        
        return title
    
    def is_ui_text(self, text: str) -> bool:
        """Check if text looks like UI elements rather than song titles."""
        if not text or len(text) > 100:
            return True
            
        text_lower = text.lower().strip()
        
        # Common UI text patterns
        ui_indicators = [
            "click", "button", "menu", "login", "sign", "register",
            "home", "about", "contact", "help", "settings", "profile",
            "search", "filter", "sort", "view", "show", "hide",
            "next", "previous", "back", "forward", "submit", "cancel",
            "song requests", "moobot", "refresh", "queue", "loading", "error",
            "song queue", "song history", "requested by", "played", "ago",
            "by ", "duration:", "status:", "page ", "page"
        ]
        
        # Check for UI patterns
        if any(indicator in text_lower for indicator in ui_indicators):
            return True
        
        # Check for pagination patterns (page 1, page 2, etc.)
        if re.match(r'^page\s*\d+$', text_lower):
            return True
        
        # Check for navigation patterns ("1", "2", "3" when they're just numbers)
        if re.match(r'^\d+$', text_lower) and len(text_lower) <= 3:
            return True
        
        # Check for search-related UI text
        search_ui_patterns = [
            'search youtube', 'youtube search', 'search', 'youtube'
        ]
        if text_lower in search_ui_patterns:
            return True
        
        # Check for time patterns (like "04:17", "03:41")
        if re.match(r'^\d{1,2}:\d{2}$', text.strip()):
            return True
        
        # Check for metadata patterns (like "By username X hours ago")
        if re.match(r'^(by|requested by|played)\s+\w+.*\d+\s+(hour|minute|second)s?\s+ago$', text_lower):
            return True
            
        # Check if it's mostly numbers or very short
        if len(text.strip()) < 5 and not re.search(r'[a-zA-Z]', text):
            return True
        
        # Check for common single words that aren't songs
        single_word_ui = ["refresh", "loading", "error", "menu", "home", "back"]
        if text_lower in single_word_ui:
            return True
            
        return False


class QueueRepository:
    """Repository for managing song queue data persistence."""
    
    def __init__(self, data_file: Path, logger: UnicodeLogger):
        self.data_file = data_file
        self.logger = logger
        self.fs_manager = FileSystemManager(data_file.parent)
        self._songs_data = self._load_data()
    
    def _load_data(self) -> Dict[str, List[Dict]]:
        """Load existing songs data from storage."""
        try:
            return self.fs_manager.load_json_data(self.data_file)
        except FileOperationError as e:
            self.logger.warning(f"Could not load existing data: {e}")
            return {}
    
    def save_daily_queue(self, queue_date: date, songs: List[SongRequest]) -> None:
        """Save songs for a specific date."""
        date_str = queue_date.isoformat()
        
        # Convert SongRequest objects to dictionaries for storage
        song_dicts = [song.to_dict() for song in songs]
        self._songs_data[date_str] = song_dicts
        
        try:
            self.fs_manager.save_json_data(self._songs_data, self.data_file)
            self.logger.info(f"Saved {len(songs)} songs for {date_str}")
        except FileOperationError as e:
            self.logger.error(f"Failed to save songs data: {e}")
    
    def load_daily_queue(self, queue_date: date) -> List[SongRequest]:
        """Load songs for a specific date."""
        date_str = queue_date.isoformat()
        
        if date_str not in self._songs_data:
            return []
        
        # Convert dictionaries back to SongRequest objects
        song_dicts = self._songs_data[date_str]
        return [SongRequest.from_dict(song_dict) for song_dict in song_dicts]
    
    def get_all_dates(self) -> List[date]:
        """Get all dates that have song data."""
        dates = []
        for date_str in self._songs_data.keys():
            try:
                dates.append(date.fromisoformat(date_str))
            except ValueError:
                # Skip invalid date strings
                continue
        return sorted(dates)
    
    def add_new_songs(self, new_songs: List[SongRequest], queue_date: date = None) -> int:
        """Add new songs to the queue, avoiding duplicates.
        
        Args:
            new_songs: List of new songs to add
            queue_date: Date to add songs for (defaults to today)
            
        Returns:
            Number of new songs actually added
        """
        if queue_date is None:
            queue_date = date.today()
        
        # Load existing songs for this date
        existing_songs = self.load_daily_queue(queue_date)
        existing_titles = {song.title.lower() for song in existing_songs}
        
        # Filter out duplicates
        songs_to_add = []
        for song in new_songs:
            if song.title.lower() not in existing_titles:
                songs_to_add.append(song)
                existing_titles.add(song.title.lower())
        
        if songs_to_add:
            # Add to existing songs and save
            all_songs = existing_songs + songs_to_add
            self.save_daily_queue(queue_date, all_songs)
            self.logger.info(f"Added {len(songs_to_add)} new songs for {queue_date}")
        
        return len(songs_to_add)
    
    def get_total_song_count(self) -> int:
        """Get total number of songs across all dates."""
        total = 0
        for songs_list in self._songs_data.values():
            total += len(songs_list)
        return total
    
    def get_all_songs_data(self) -> Dict[str, List[Dict]]:
        """Get all songs data in dictionary format (for backward compatibility)."""
        return self._songs_data.copy()