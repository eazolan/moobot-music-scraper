#!/usr/bin/env python3
"""
Diagnostic script to check what's on page 2 of the history
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

STREAMER_NAME = "slimaera"
MOOBOT_URL = f"https://moo.bot/r/music#{STREAMER_NAME}"

def main():
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
        
        print("Navigating to history page 1...")
        first_page_buttons = driver.find_elements(
            By.CSS_SELECTOR,
            "#input-content-history .moobot-nav-pagination li[data-index='1']"
        )
        
        if first_page_buttons:
            driver.execute_script("arguments[0].click();", first_page_buttons[0])
            time.sleep(2)
            print("✓ Clicked page 1 button")
        
        # Check what pages are available
        all_pages = driver.find_elements(
            By.CSS_SELECTOR,
            "#input-content-history .moobot-nav-pagination li[data-index]"
        )
        
        page_numbers = []
        for elem in all_pages:
            idx = elem.get_attribute("data-index")
            if idx and idx.isdigit():
                page_numbers.append(idx)
        
        print(f"Available page indices after clicking page 1: {sorted(set(page_numbers))}")
        
        # Now navigate to page 2
        print("\nNavigating to history page 2...")
        page2_buttons = driver.find_elements(
            By.CSS_SELECTOR,
            "#input-content-history .moobot-nav-pagination li[data-index='2']"
        )
        
        if not page2_buttons:
            print("❌ Page 2 button not found!")
            print("\nPagination HTML:")
            pagination_html = driver.find_element(
                By.CSS_SELECTOR,
                "#input-content-history .moobot-nav-pagination"
            ).get_attribute("outerHTML")
            print(pagination_html[:500])
        else:
            # Find non-navigation element
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
            print("✓ Clicked page 2 button")
            
            # Extract songs from page 2
            print("\nSongs on page 2:")
            rows = driver.find_elements(
                By.CSS_SELECTOR,
                "#input-content-history tbody tr"
            )
            
            print(f"Found {len(rows)} rows on page 2\n")
            
            for i, row in enumerate(rows[:10], 1):  # Show first 10
                try:
                    text = row.text
                    # Also get the data-id attribute
                    row_data_id = row.get_attribute("data-id")
                    print(f"Row {i} (data-id={row_data_id}):")
                    print(f"  Text: {text[:200]}")
                    print()
                except Exception as e:
                    print(f"Row {i}: Error - {e}")
            
            # Save page source
            with open("output/page2_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("Saved page source to output/page2_source.html")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
