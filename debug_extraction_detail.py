#!/usr/bin/env python3
"""Debug exactly what happens during extraction from page 2"""

import time
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from infrastructure.logging import setup_logging
from domains.music_queue import SongMatchingService

def main():
    logger = setup_logging(Path("output/extraction_debug.log"), Path("output"))
    song_matcher = SongMatchingService()
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("Loading page...")
        driver.get("https://moo.bot/r/music#slimaera")
        time.sleep(3)
        
        # Navigate to page 1 then page 2
        first_page = driver.find_elements(By.CSS_SELECTOR, "#input-content-history .moobot-nav-pagination li[data-index='1']")
        if first_page:
            driver.execute_script("arguments[0].click();", first_page[0])
            time.sleep(2)
        
        page2 = driver.find_elements(By.CSS_SELECTOR, "#input-content-history .moobot-nav-pagination li[data-index='2']")
        if page2:
            for elem in page2:
                style = elem.get_attribute("style") or ""
                if "61px" not in style and "132px" not in style:
                    driver.execute_script("arguments[0].click();", elem)
                    time.sleep(2)
                    break
        
        print("\n" + "="*70)
        print("EXTRACTION SIMULATION")
        print("="*70)
        
        rows = driver.find_elements(By.CSS_SELECTOR, "#input-content-history tbody tr")
        print(f"\nFound {len(rows)} rows on page 2\n")
        
        extracted_songs = []
        
        for i, row in enumerate(rows, 1):
            print(f"\n--- Processing Row {i} ---")
            
            try:
                # Extract title
                title_elem = row.find_element(By.CSS_SELECTOR, ".moobot-input-label-text-text")
                title = title_elem.text.strip()
                print(f"  Raw title: '{title}'")
                print(f"  Title length: {len(title)}")
                
                # Check filters
                min_length = 5
                if len(title) < min_length:
                    print(f"  ❌ FILTERED: Title too short (< {min_length})")
                    continue
                
                if song_matcher.is_ui_text(title):
                    print(f"  ❌ FILTERED: Detected as UI text")
                    continue
                
                # Clean title
                cleaned_title = song_matcher.clean_song_title(title)
                print(f"  Cleaned title: '{cleaned_title}'")
                
                # Check for duplicates in extracted_songs
                is_duplicate = False
                for existing in extracted_songs:
                    if existing['title'].lower() == cleaned_title.lower():
                        is_duplicate = True
                        print(f"  ❌ FILTERED: Duplicate of previously extracted song")
                        break
                
                if is_duplicate:
                    continue
                
                # Extract metadata
                labels = row.find_elements(By.CSS_SELECTOR, ".moobot-input-label-text-label")
                duration = ""
                requester = ""
                for label in labels:
                    text = label.text.strip()
                    if ":" in text and len(text) < 10:
                        duration = text
                    elif "By " in text or "Requested by" in text:
                        requester = text
                
                song_info = {
                    'title': cleaned_title,
                    'duration': duration,
                    'requester': requester
                }
                
                extracted_songs.append(song_info)
                print(f"  ✓ EXTRACTED: {cleaned_title}")
                
            except Exception as e:
                print(f"  ❌ ERROR: {e}")
        
        print(f"\n" + "="*70)
        print(f"EXTRACTION SUMMARY")
        print("="*70)
        print(f"Total rows: {len(rows)}")
        print(f"Songs extracted: {len(extracted_songs)}")
        print()
        
        for i, song in enumerate(extracted_songs, 1):
            print(f"{i}. {song['title']}")
            print(f"   Duration: {song['duration']}")
            print(f"   Requester: {song['requester']}")
            print()
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
