#!/usr/bin/env python3
"""
Quick test to verify audio is muted during YouTube extraction
"""

import sys
from pathlib import Path

# Add parent directory to path for imports  
sys.path.insert(0, str(Path(__file__).parent.parent))

from moobot_scraper import MoobotScraper

def test_silent_scraping():
    """Test that scraping is completely silent."""
    print("🔇 Testing silent scraping...")
    print("⚠️  Listen carefully - you should hear NO audio during this test")
    print("=" * 60)
    
    try:
        # Create scraper with slimaera (known to have active songs)
        import moobot_scraper
        original_streamer = moobot_scraper.STREAMER_NAME
        moobot_scraper.STREAMER_NAME = "slimaera"
        moobot_scraper.MOOBOT_URL = f"https://moo.bot/r/music#slimaera"
        
        scraper = MoobotScraper()
        
        print("🎵 Running quick scan with audio muting...")
        print("   (This should be completely silent)")
        
        # Run just the scraping part (not full scan to save time)
        songs = scraper.scrape_songs()
        
        youtube_songs = [s for s in songs if s.get('youtube_url')]
        
        print(f"✅ Scan completed silently!")
        print(f"📊 Found {len(songs)} total songs")
        print(f"▶️  Found {len(youtube_songs)} songs with YouTube URLs")
        
        # Show first few songs with YouTube URLs
        if youtube_songs:
            print(f"\n🎶 Songs with YouTube URLs:")
            for i, song in enumerate(youtube_songs[:3]):
                print(f"   {i+1}. {song['title']}")
                print(f"      🔗 {song['youtube_url']}")
        
        scraper.cleanup()
        
        # Restore original values
        moobot_scraper.STREAMER_NAME = original_streamer
        
        print(f"\n🔇 If you heard any audio during this test, the muting failed!")
        print(f"✅ If it was silent, the audio muting is working correctly.")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_silent_scraping()