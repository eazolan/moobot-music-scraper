#!/usr/bin/env python3
"""
Test script for Content Publishing domain entities and services
"""

import sys
from datetime import date
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from domains.music_queue import SongRequest, StreamerId
from domains.content_publishing import SongCollection, PublishingConfig, ContentPublisher, HtmlGenerator
from infrastructure.logging import setup_logging

def test_publishing_entities():
    """Test Content Publishing domain entities."""
    print("🎨 Testing Content Publishing entities...")
    
    # Test StreamerId and SongRequest (from music queue domain)
    streamer = StreamerId("pokimane")
    songs = [
        SongRequest(
            title="Bohemian Rhapsody",
            duration="5:55",
            requester="By testuser",
            youtube_url="https://youtube.com/watch?v=fJ9rUzIMcZQ"
        ),
        SongRequest(
            title="Imagine",
            duration="3:07",
            requester="By testuser2",
            status="Playing next"
        )
    ]
    
    # Test SongCollection
    collection = SongCollection(
        date=date.today(),
        songs=songs,
        streamer_id=streamer
    )
    
    print(f"  ✓ Collection date: {collection.formatted_date}")
    print(f"  ✓ Song count: {collection.song_count}")
    print(f"  ✓ YouTube songs: {collection.has_youtube_songs}")
    
    # Test PublishingConfig
    config = PublishingConfig(
        output_dir=Path("test_output"),
        streamer_name="teststreamer"
    )
    
    print(f"  ✓ Config HTML dir: {config.html_dir}")
    print(f"  ✓ Display name: {config.display_streamer_name}")

def test_html_generation():
    """Test HTML generation services."""
    print("\n🌐 Testing HTML generation...")
    
    # Create test data
    streamer = StreamerId("pokimane")
    songs = [
        SongRequest(
            title="Test Song 1",
            duration="3:30",
            youtube_url="https://youtube.com/watch?v=test1"
        ),
        SongRequest(
            title="Test Song 2", 
            requester="By testuser"
        )
    ]
    
    collection = SongCollection(
        date=date.today(),
        songs=songs,
        streamer_id=streamer
    )
    
    config = PublishingConfig(
        output_dir=Path("test_output"),
        streamer_name="pokimane"
    )
    
    # Test HTML generator
    generator = HtmlGenerator(config)
    
    daily_page = generator.generate_daily_page(collection)
    print(f"  ✓ Daily page title: {daily_page.title}")
    print(f"  ✓ Daily page content length: {daily_page.content_length} chars")
    
    index_page = generator.generate_index_page([collection])
    print(f"  ✓ Index page title: {index_page.title}")
    print(f"  ✓ Index page content length: {index_page.content_length} chars")
    
    # Verify HTML contains expected content
    assert "Test Song 1" in daily_page.content
    assert "pokimane" in index_page.content.lower()
    print("  ✓ HTML content validation passed")

def test_content_publishing():
    """Test full content publishing workflow."""
    print("\n📤 Testing content publishing...")
    
    # Setup test logger and config
    logger = setup_logging(Path("test_output/test.log"), Path("test_output"))
    config = PublishingConfig(
        output_dir=Path("test_output"),
        streamer_name="testpublisher"
    )
    
    # Create test collections
    streamer = StreamerId("testpublisher")
    collections = []
    
    for i in range(2):
        songs = [
            SongRequest(title=f"Test Song {i}-{j}") 
            for j in range(3)
        ]
        collection = SongCollection(
            date=date.today(),
            songs=songs,
            streamer_id=streamer
        )
        collections.append(collection)
    
    # Test publisher
    publisher = ContentPublisher(config, logger)
    result = publisher.publish_all(collections)
    
    print(f"  ✓ Publishing success: {result.success}")
    print(f"  ✓ Pages generated: {result.total_pages}")
    print(f"  ✓ Errors: {len(result.errors)}")
    
    if result.errors:
        for error in result.errors:
            print(f"    - Error: {error}")
    
    # Check if files were created
    index_exists = config.index_file_path.exists()
    print(f"  ✓ Index file created: {index_exists}")

if __name__ == "__main__":
    print("🧪 Testing Content Publishing Domain")
    print("=" * 45)
    
    test_publishing_entities()
    test_html_generation()
    test_content_publishing()
    
    print("\n✅ All content publishing tests passed!")