#!/usr/bin/env python3
"""
Debug script to figure out how the YouTube links work on the Moobot page
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import json

def debug_youtube_links():
    """Investigate how YouTube links are handled on Moobot page."""
    
    # Set up Chrome with network logging
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Enable logging to capture network requests
    chrome_options.add_argument("--enable-logging")
    chrome_options.add_argument("--log-level=0")
    chrome_options.set_capability("goog:loggingPrefs", {"browser": "ALL", "performance": "ALL"})
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("🔍 Loading Moobot page...")
        driver.get("https://moo.bot/r/music#slimaera")
        time.sleep(5)
        
        print("📊 Looking for external link buttons...")
        buttons = driver.find_elements(By.CSS_SELECTOR, "button.button-type-link")
        print(f"Found {len(buttons)} external link buttons")
        
        if buttons:
            print("🔬 Analyzing first button...")
            button = buttons[0]
            
            # Get all attributes
            print("Button attributes:")
            attributes = driver.execute_script("""
                var button = arguments[0];
                var attrs = {};
                for (var i = 0; i < button.attributes.length; i++) {
                    var attr = button.attributes[i];
                    attrs[attr.name] = attr.value;
                }
                return attrs;
            """, button)
            for key, value in attributes.items():
                print(f"  {key}: {value}")
            
            # Get parent row info
            try:
                row = button.find_element(By.XPATH, "ancestor::tr[@data-id]")
                data_id = row.get_attribute("data-id")
                print(f"Row data-id: {data_id}")
                
                # Try to get song title from the row
                try:
                    title_element = row.find_element(By.CSS_SELECTOR, ".moobot-input-label-text-text")
                    song_title = title_element.text.strip()
                    print(f"Song title: {song_title}")
                except Exception as e:
                    print(f"Could not get song title: {e}")
                    
            except Exception as e:
                print(f"Could not get row info: {e}")
            
            # Try clicking the button and see what happens
            print("🖱️ Trying to click button...")
            original_windows = driver.window_handles
            
            try:
                # Click the button
                driver.execute_script("arguments[0].click();", button)
                time.sleep(3)
                
                # Check for new windows
                new_windows = driver.window_handles
                if len(new_windows) > len(original_windows):
                    print("✅ New window opened!")
                    new_window = [w for w in new_windows if w not in original_windows][0]
                    driver.switch_to.window(new_window)
                    
                    current_url = driver.current_url
                    print(f"New window URL: {current_url}")
                    
                    # Close the new window and go back
                    driver.close()
                    driver.switch_to.window(original_windows[0])
                    
                    if "youtube.com" in current_url or "youtu.be" in current_url:
                        print(f"🎯 Found direct YouTube URL: {current_url}")
                    else:
                        print(f"❌ Not a YouTube URL: {current_url}")
                        
                else:
                    print("❌ No new window opened")
                    
            except Exception as click_error:
                print(f"Click error: {click_error}")
                try:
                    driver.switch_to.window(original_windows[0])
                except:
                    pass
        
        # Look for history section with thumbnails
        print("🖼️ Checking history section for thumbnails...")
        try:
            history_images = driver.find_elements(By.CSS_SELECTOR, "#input-content-history img[src*='youtube.com']")
            print(f"Found {len(history_images)} YouTube thumbnails in history")
            
            for i, img in enumerate(history_images[:3]):
                img_src = img.get_attribute("src")
                print(f"  Thumbnail {i+1}: {img_src}")
                
                # Extract video ID
                import re
                video_id_match = re.search(r'/vi/([^/]+)/', img_src)
                if video_id_match:
                    video_id = video_id_match.group(1)
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    print(f"    Video URL: {video_url}")
                    
        except Exception as e:
            print(f"History section error: {e}")
        
        # Check browser logs
        print("📋 Checking browser logs...")
        try:
            logs = driver.get_log("browser")
            for log in logs[-10:]:  # Last 10 logs
                print(f"  {log['level']}: {log['message']}")
        except Exception as e:
            print(f"Could not get logs: {e}")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_youtube_links()