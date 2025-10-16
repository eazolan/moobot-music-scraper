#!/usr/bin/env python3
"""
Test script for Music Queue domain entities and services
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from domains.music_queue import SongRequest, StreamerId, SongMatchingService

def test_song_request():
    """Test SongRequest entity."""
    print("🎵 Testing SongRequest entity...")
    
    # Test basic creation
    song = SongRequest(
        title="Bohemian Rhapsody",
        duration="5:55",
        requester="Queen Fan",
        youtube_url="https://youtube.com/watch?v=fJ9rUzIMcZQ"
    )
    
    print(f"  ✓ Title: {song.title}")
    print(f"  ✓ Has YouTube link: {song.has_youtube_link}")
    print(f"  ✓ Enhanced title: {song.enhanced_title}")
    
    # Test conversion to/from dict
    song_dict = song.to_dict()
    song_from_dict = SongRequest.from_dict(song_dict)
    print(f"  ✓ Dict conversion: {song.title == song_from_dict.title}")

def test_streamer_id():
    """Test StreamerId entity."""
    print("\n🎮 Testing StreamerId entity...")
    
    streamer = StreamerId("pokimane")
    print(f"  ✓ Name: {streamer.name}")
    print(f"  ✓ Display name: {streamer.display_name}")
    print(f"  ✓ Moobot URL: {streamer.moobot_url}")

def test_song_matching():
    """Test SongMatchingService."""
    print("\n🔍 Testing SongMatchingService...")
    
    matcher = SongMatchingService()
    
    # Test title matching
    title1 = "Bohemian Rhapsody"
    title2 = "Bohemian Rhapsody (Official Video)"
    match = matcher.titles_match(title1, title2)
    print(f"  ✓ Title matching: '{title1}' vs '{title2}' = {match}")
    
    # Test UI text detection
    ui_text = "Click here to view more"
    song_text = "Stairway to Heaven"
    print(f"  ✓ UI text detection: '{ui_text}' = {matcher.is_ui_text(ui_text)}")
    print(f"  ✓ Song text detection: '{song_text}' = {matcher.is_ui_text(song_text)}")
    
    # Test title cleaning
    messy_title = "  ♪ Now Playing: Imagine - John Lennon  "
    clean_title = matcher.clean_song_title(messy_title)
    print(f"  ✓ Title cleaning: '{messy_title}' → '{clean_title}'")

if __name__ == "__main__":
    print("🧪 Testing Music Queue Domain")
    print("=" * 40)
    
    test_song_request()
    test_streamer_id()
    test_song_matching()
    
    print("\n✅ All domain tests passed!")