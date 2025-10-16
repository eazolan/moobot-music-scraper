#!/usr/bin/env python3
"""
Test HTML generation with sample songs that have YouTube URLs
"""

import sys
from pathlib import Path
from datetime import datetime, date

# Add parent directory to path for imports  
sys.path.insert(0, str(Path(__file__).parent.parent))

from domains.music_queue.entities import SongRequest, StreamerId
from domains.content_publishing.entities import SongCollection, PublishingConfig
from domains.content_publishing.services import ContentPublisher
from infrastructure.logging import setup_logging

def create_sample_songs():
    """Create sample songs with YouTube URLs for testing."""
    current_time = datetime.now()
    
    songs = [
        SongRequest(
            title="Bohemian Rhapsody - Queen",
            youtube_url="https://www.youtube.com/watch?v=fJ9rUzIMcZQ",
            duration="5:55",
            requester="TestUser1",
            status="Playing",
            scraped_at=current_time.strftime("%Y-%m-%d %H:%M:%S")
        ),
        SongRequest(
            title="The Beatles - Here Comes The Sun",
            youtube_url="https://www.youtube.com/watch?v=KQetemT1sWc",
            duration="3:05", 
            requester="TestUser2",
            status="Queued",
            scraped_at=current_time.strftime("%Y-%m-%d %H:%M:%S")
        ),
        SongRequest(
            title="Imagine Dragons - Thunder",
            # No YouTube URL - should generate search link
            duration="3:07",
            requester="TestUser3", 
            status="Queued",
            scraped_at=current_time.strftime("%Y-%m-%d %H:%M:%S")
        ),
        SongRequest(
            title="Song Requests",  # This should be filtered out as UI text
            scraped_at=current_time.strftime("%Y-%m-%d %H:%M:%S")
        )
    ]
    
    return songs

def test_html_generation():
    """Test HTML generation with sample data."""
    print("🧪 Testing HTML generation with YouTube URLs...")
    
    # Create sample data
    songs = create_sample_songs()
    streamer_id = StreamerId("TestStreamer")
    collection_date = date.today()
    
    # Create song collection
    collection = SongCollection(
        date=collection_date,
        songs=songs,
        streamer_id=streamer_id
    )
    
    print(f"📋 Created collection with {collection.song_count} songs")
    
    # Set up publishing  
    output_dir = Path("../test_output").resolve()
    publishing_config = PublishingConfig(
        output_dir=output_dir,
        streamer_name="TestStreamer"
    )
    
    # Create logger
    log_file = output_dir / "test.log"
    logger = setup_logging(log_file, output_dir)
    
    # Create publisher
    publisher = ContentPublisher(publishing_config, logger)
    
    # Publish HTML
    result = publisher.publish_all([collection])
    
    if result.success:
        print(f"✅ HTML generation successful!")
        print(f"📄 Generated {result.total_pages} pages")
        for page in result.pages_generated:
            print(f"   - {page.file_name} ({page.content_length} characters)")
            
        print(f"\n🌐 Open test_output/html/index.html in your browser to see results")
        
        # Show sample of generated content
        daily_page = result.pages_generated[0] if result.pages_generated else None
        if daily_page:
            print(f"\n📝 Sample HTML content preview:")
            content_lines = daily_page.content.split('\n')
            for i, line in enumerate(content_lines[150:170]):  # Show song list section
                if 'song-item' in line or 'youtube-link' in line:
                    print(f"   {line.strip()}")
    else:
        print(f"❌ HTML generation failed:")
        for error in result.errors:
            print(f"   - {error}")

if __name__ == "__main__":
    test_html_generation()