#!/usr/bin/env python3
"""
Diagnostic script to see exactly what gets extracted from page 2
"""

import time
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Add the parent directory to path to import from domains
sys.path.insert(0, str(Path(__file__).parent))

from infrastructure.logging import setup_logging
from domains.song_extraction import ExtractionCoordinator, ExtractionConfig, ElementSelector

STREAMER_NAME = "slimaera"
MOOBOT_URL = f"https://moo.bot/r/music#{STREAMER_NAME}"

def main():
    # Setup logging
    logger = setup_logging(Path("output/diagnostic.log"), Path("output"))
    
    # Setup Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print(f"Loading {MOOBOT_URL}...")
        driver.get(MOOBOT_URL)
        time.sleep(3)
        
        # Navigate to page 1
        print("Navigating to history page 1...")
        first_page_buttons = driver.find_elements(
            By.CSS_SELECTOR,
            "#input-content-history .moobot-nav-pagination li[data-index='1']"
        )
        
        if first_page_buttons:
            driver.execute_script("arguments[0].click();", first_page_buttons[0])
            time.sleep(2)
        
        # Navigate to page 2
        print("Navigating to history page 2...")
        page2_buttons = driver.find_elements(
            By.CSS_SELECTOR,
            "#input-content-history .moobot-nav-pagination li[data-index='2']"
        )
        
        if page2_buttons:
            clickable = None
            for elem in page2_buttons:
                style = elem.get_attribute("style") or ""
                if "61px" not in style and "132px" not in style:
                    clickable = elem
                    break
            if not clickable:
                clickable = page2_buttons[0]
            
            driver.execute_script("arguments[0].click();", clickable)
            time.sleep(2)
            print("✓ On page 2\n")
        
        # Now extract using the actual extraction logic
        print("=" * 60)
        print("EXTRACTION TEST")
        print("=" * 60)
        
        coordinator = ExtractionCoordinator(logger)
        config = ExtractionConfig.create_fast()
        config.extract_youtube_urls = True
        config.try_button_click = True
        config.use_robust_finding = True
        config.skip_ui_text = True
        config.min_title_length = 5
        config.clean_titles = True
        
        history_selectors = [
            ElementSelector.create_custom(
                "#input-content-history tbody tr",
                description="History table rows",
                priority=10
            )
        ]
        
        existing_songs_with_urls = {}
        
        result = coordinator.extract_songs_optimized(
            driver, history_selectors, config, existing_songs_with_urls
        )
        
        print(f"\nExtraction result:")
        print(f"  Success: {result.success}")
        print(f"  Songs found: {len(result.songs)}")
        print(f"  Strategy used: {result.strategy_used}")
        print()
        
        for i, song in enumerate(result.songs, 1):
            print(f"Song {i}:")
            print(f"  Title: {song.title}")
            print(f"  Duration: {song.duration}")
            print(f"  Requester: {song.requester}")
            print(f"  YouTube URL: {song.youtube_url}")
            print()
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
