#!/usr/bin/env python3
"""
Test script for the Moobot scraper
Runs a single scan to test if everything is working properly
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from moobot_scraper import MoobotScraper
import logging

def test_single_scan():
    """Test a single scan without scheduling."""
    print("🎵 Testing Moobot Scraper...")
    print("=" * 50)
    
    # Set up logging to see what's happening
    logging.basicConfig(level=logging.INFO)
    
    scraper = MoobotScraper()
    
    try:
        print("\n🔍 Running a single scan...")
        scraper.run_scan()
        
        print(f"\n📊 Results:")
        total_days = len(scraper.songs_data)
        total_songs = sum(len(songs) for songs in scraper.songs_data.values())
        
        print(f"   - Days with data: {total_days}")
        print(f"   - Total songs collected: {total_songs}")
        
        if total_songs > 0:
            print(f"\n🎶 Sample songs:")
            for date_str, songs in scraper.songs_data.items():
                print(f"   {date_str}:")
                for i, song in enumerate(songs[:3]):  # Show first 3 songs
                    youtube_indicator = " ▶️" if song.get('youtube_url') else ""
                    print(f"     {i+1}. {song['title']}{youtube_indicator}")
                if len(songs) > 3:
                    print(f"     ... and {len(songs) - 3} more songs")
        
        print(f"\n📁 Files created:")
        print(f"   - Data: output/songs_data.json")
        print(f"   - Logs: output/scraper.log") 
        print(f"   - HTML: output/html/index.html")
        print(f"   - Debug: output/page_screenshot.png, output/page_source.html")
        
        print(f"\n✅ Test completed successfully!")
        print(f"   Open 'output/html/index.html' in your browser to see the results.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logging.error(f"Test error: {e}")
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    test_single_scan()