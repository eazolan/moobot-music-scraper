#!/usr/bin/env python3
"""Debug script to see exactly what each row contains"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def main():
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
        print("Navigating to page 1...")
        first_page = driver.find_elements(By.CSS_SELECTOR, "#input-content-history .moobot-nav-pagination li[data-index='1']")
        if first_page:
            driver.execute_script("arguments[0].click();", first_page[0])
            time.sleep(2)
        
        print("Navigating to page 2...")
        page2 = driver.find_elements(By.CSS_SELECTOR, "#input-content-history .moobot-nav-pagination li[data-index='2']")
        if page2:
            clickable = None
            for elem in page2:
                style = elem.get_attribute("style") or ""
                if "61px" not in style and "132px" not in style:
                    clickable = elem
                    break
            if clickable:
                driver.execute_script("arguments[0].click();", clickable)
                time.sleep(2)
        
        print("\n" + "="*70)
        print("DETAILED ROW ANALYSIS - Page 2")
        print("="*70)
        
        rows = driver.find_elements(By.CSS_SELECTOR, "#input-content-history tbody tr")
        print(f"\nTotal rows found: {len(rows)}\n")
        
        for i, row in enumerate(rows, 1):
            print(f"Row {i}:")
            print(f"  data-id: {row.get_attribute('data-id')}")
            
            # Try to find title element
            try:
                title_elem = row.find_element(By.CSS_SELECTOR, ".moobot-input-label-text-text")
                title = title_elem.text.strip()
                print(f"  Title: '{title}'")
                print(f"  Title length: {len(title)}")
            except Exception as e:
                print(f"  Title: ERROR - {e}")
            
            # Get all label elements
            try:
                labels = row.find_elements(By.CSS_SELECTOR, ".moobot-input-label-text-label")
                print(f"  Labels: {len(labels)} found")
                for j, label in enumerate(labels, 1):
                    print(f"    Label {j}: '{label.text}'")
            except Exception as e:
                print(f"  Labels: ERROR - {e}")
            
            # Full row text
            print(f"  Full row text (first 150 chars): {row.text[:150]}")
            print()
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
