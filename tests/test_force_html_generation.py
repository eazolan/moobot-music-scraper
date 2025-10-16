#!/usr/bin/env python3
"""
Test script to force HTML generation using the main scraper
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from moobot_scraper import MoobotScraper

def test_html_generation():
    """Test HTML generation from main scraper."""
    print("🎨 Testing HTML generation from main scraper...")
    
    scraper = MoobotScraper()
    
    try:
        print("📊 Current data:")
        print(f"  - Days with data: {len(scraper.songs_data)}")
        total_songs = sum(len(songs) for songs in scraper.songs_data.values())
        print(f"  - Total songs: {total_songs}")
        
        print("\n🌐 Generating HTML...")
        scraper.generate_html()
        print("✅ HTML generation completed!")
        
        # Check if HTML files exist
        from pathlib import Path
        index_file = Path("output/html/index.html")
        print(f"  - Index file exists: {index_file.exists()}")
        
        if index_file.exists():
            size = index_file.stat().st_size
            print(f"  - Index file size: {size} bytes")
        
    except Exception as e:
        print(f"❌ HTML generation failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    test_html_generation()