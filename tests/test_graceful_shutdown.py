#!/usr/bin/env python3
"""
Test script to demonstrate graceful shutdown
Runs for 30 seconds then shows graceful shutdown
"""

import sys
from pathlib import Path
import time
import threading

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from moobot_scraper import MoobotScraper

def stop_scraper_after_delay(scraper, delay_seconds):
    """Stop the scraper after a delay to demonstrate graceful shutdown."""
    time.sleep(delay_seconds)
    print(f"\n⏰ {delay_seconds} seconds elapsed. Requesting graceful shutdown...")
    scraper.shutdown_requested = True

def test_graceful_shutdown():
    """Test the scraper with automatic graceful shutdown after 30 seconds."""
    print("🎵 Testing Moobot Scraper with Graceful Shutdown...")
    print("=" * 60)
    print("This will run for 30 seconds then demonstrate graceful shutdown.")
    print("You can also press Ctrl+C at any time for immediate graceful shutdown.")
    print("=" * 60)
    
    scraper = MoobotScraper()
    
    try:
        # Start a timer to stop the scraper after 30 seconds
        stop_timer = threading.Thread(target=stop_scraper_after_delay, args=(scraper, 30))
        stop_timer.daemon = True
        stop_timer.start()
        
        # Run the scraper
        scraper.run_forever()
        
        print(f"\n📊 Final Results:")
        total_days = len(scraper.songs_data)
        total_songs = sum(len(songs) for songs in scraper.songs_data.values())
        
        print(f"   - Days with data: {total_days}")
        print(f"   - Total songs collected: {total_songs}")
        
        if total_songs > 0:
            print(f"\n🎶 Recent songs:")
            for date_str, songs in list(scraper.songs_data.items())[-1:]:  # Show last date
                print(f"   {date_str}:")
                for i, song in enumerate(songs[-5:], 1):  # Show last 5 songs
                    youtube_indicator = " ▶️" if song.get('youtube_url') else ""
                    print(f"     {i}. {song['title']}{youtube_indicator}")
        
        print(f"\n✅ Graceful shutdown test completed successfully!")
        print(f"   Open 'output/html/index.html' to see all collected songs.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
    finally:
        # Ensure cleanup happens
        try:
            scraper.cleanup()
        except:
            pass

if __name__ == "__main__":
    test_graceful_shutdown()