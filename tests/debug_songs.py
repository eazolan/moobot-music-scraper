#!/usr/bin/env python3

import sys
from pathlib import Path

# Add parent directory to path for imports  
sys.path.insert(0, str(Path(__file__).parent.parent))

from moobot_scraper import MoobotScraper

# Create scraper and inspect what it generates
scraper = MoobotScraper()
print('Loading scraper...')

# Check the test data it generates
songs = scraper.scrape_songs()
print('Songs scraped:', len(songs))

for i, song in enumerate(songs[:3]):
    print(f'Song {i+1}:')
    print(f'  Title: {song.get("title", "Unknown")}')
    print(f'  YouTube URL: {song.get("youtube_url", "None")}')
    print(f'  Selector: {song.get("selector_used", "None")}')
    print()

scraper.cleanup()