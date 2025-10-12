#!/usr/bin/env python3
"""
Moobot Music Queue Scraper
Monitors Moobot music queue pages for any Twitch streamer
and generates local HTML pages organized by date.

To use for a different streamer, change the STREAMER_NAME below
or pass it as a command line argument.
"""

import time
import json
import logging
import signal
import sys
import argparse
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional
import schedule

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Configuration
# Default streamer (can be overridden by command line argument)
DEFAULT_STREAMER = "pokimane"

# Get streamer name from command line args or use default
def get_streamer_name():
    parser = argparse.ArgumentParser(description='Scrape Moobot music queue for a Twitch streamer')
    parser.add_argument('--streamer', '-s', 
                       default=DEFAULT_STREAMER,
                       help=f'Streamer name to monitor (default: {DEFAULT_STREAMER})')
    args, unknown = parser.parse_known_args()  # Allow unknown args for compatibility
    return args.streamer

STREAMER_NAME = get_streamer_name()

# Derived configuration (don't change these)
MOOBOT_URL = f"https://moo.bot/r/music#{STREAMER_NAME}"
OUTPUT_DIR = Path("output")
DATA_FILE = OUTPUT_DIR / "songs_data.json"
LOG_FILE = OUTPUT_DIR / "scraper.log"
SCAN_INTERVAL = 60  # seconds

class MoobotScraper:
    def __init__(self):
        self.setup_logging()
        self.setup_directories()
        self.driver = None
        self.songs_data = self.load_existing_data()
        self.shutdown_requested = False
        self.setup_signal_handlers()
        
    def setup_logging(self):
        """Set up logging configuration."""
        OUTPUT_DIR.mkdir(exist_ok=True)
        
        # Create formatters
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Create handlers with proper encoding
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        # Console handler with proper encoding for Windows
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            handlers=[file_handler, console_handler]
        )
        
        self.logger = logging.getLogger(__name__)
        
    def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        if sys.platform == "win32":
            # On Windows, also handle CTRL_BREAK_EVENT
            try:
                signal.signal(signal.SIGBREAK, self.signal_handler)
            except AttributeError:
                pass  # SIGBREAK may not be available on all Windows versions
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        signal_names = {signal.SIGINT: "SIGINT (Ctrl+C)", signal.SIGTERM: "SIGTERM"}
        if sys.platform == "win32" and hasattr(signal, 'SIGBREAK'):
            signal_names[signal.SIGBREAK] = "SIGBREAK (Ctrl+Break)"
        
        signal_name = signal_names.get(signum, f"Signal {signum}")
        self.safe_log('info', f"Received {signal_name}. Initiating graceful shutdown...")
        self.shutdown_requested = True
        
    def safe_log(self, level, message):
        """Safely log messages that might contain Unicode characters."""
        try:
            if level == 'info':
                self.logger.info(message)
            elif level == 'warning':
                self.logger.warning(message)
            elif level == 'error':
                self.logger.error(message)
            elif level == 'debug':
                self.logger.debug(message)
        except UnicodeEncodeError:
            # Fallback: encode problematic characters
            safe_message = message.encode('ascii', errors='replace').decode('ascii')
            if level == 'info':
                self.logger.info(f"[Unicode characters replaced] {safe_message}")
            elif level == 'warning':
                self.logger.warning(f"[Unicode characters replaced] {safe_message}")
            elif level == 'error':
                self.logger.error(f"[Unicode characters replaced] {safe_message}")
            elif level == 'debug':
                self.logger.debug(f"[Unicode characters replaced] {safe_message}")
        
    def setup_directories(self):
        """Create necessary directories."""
        OUTPUT_DIR.mkdir(exist_ok=True)
        (OUTPUT_DIR / "html").mkdir(exist_ok=True)
        
    def setup_webdriver(self):
        """Initialize Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Mute audio to prevent hearing song previews when extracting YouTube URLs
        chrome_options.add_argument("--mute-audio")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        
        # Additional audio blocking preferences
        prefs = {
            "profile.default_content_setting_values": {
                "media_stream_mic": 2,
                "media_stream_camera": 2,
                "geolocation": 2,
                "notifications": 2,
                "media_stream": 2,
            },
            "profile.content_settings": {
                "exceptions": {
                    "media_stream": {
                        "https://www.youtube.com,*": {
                            "setting": 2
                        }
                    }
                }
            }
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.implicitly_wait(10)
            self.logger.info("WebDriver initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            raise
            
    def load_existing_data(self) -> Dict[str, List[Dict]]:
        """Load existing songs data from JSON file."""
        if DATA_FILE.exists():
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Could not load existing data: {e}")
        return {}
        
    def save_data(self):
        """Save songs data to JSON file."""
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.songs_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save data: {e}")
            
    def verify_streamer_exists(self) -> bool:
        """Check if the streamer exists on Moobot by looking for 'not found' messages."""
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.strip()
            self.safe_log('debug', f"Page content for verification: {page_text[:200]}...")
            
            # Check for common "not found" patterns
            not_found_patterns = [
                f"{STREAMER_NAME} was not found",
                "was not found",
                "not found",
                "404",
                "User not found",
                "Streamer not found",
                "This page requires Javascript"
            ]
            
            page_text_lower = page_text.lower()
            
            for pattern in not_found_patterns:
                if pattern.lower() in page_text_lower:
                    self.safe_log('debug', f"Found not-found pattern: {pattern}")
                    # Special case: "This page requires Javascript" is normal, but if that's ALL we see, it's suspicious
                    if pattern == "This page requires Javascript" and len(page_text.strip()) < 50:
                        return False
                    elif pattern != "This page requires Javascript":
                        return False
            
            # Additional check: if the page is suspiciously empty or only has basic content
            if len(page_text.strip()) < 20:
                self.safe_log('debug', "Page seems too short/empty")
                return False
                
            # If we get here, the streamer likely exists
            self.safe_log('info', f"Streamer '{STREAMER_NAME}' appears to exist on Moobot")
            return True
            
        except Exception as e:
            self.safe_log('warning', f"Error verifying streamer existence: {e}")
            # If we can't verify, assume it exists and let the scraper continue
            return True
    
    def scrape_songs(self) -> List[Dict]:
        """Scrape current songs from the Moobot page."""
        if not self.driver:
            self.setup_webdriver()
            
        try:
            self.logger.info("Loading Moobot page...")
            self.driver.get(MOOBOT_URL)
            
            # Wait for the page to load
            time.sleep(5)
            
            # Check if the streamer exists on Moobot
            if not self.verify_streamer_exists():
                error_msg = f"Streamer '{STREAMER_NAME}' was not found on Moobot. Please check the spelling and try again."
                self.safe_log('error', error_msg)
                print(f"\n❌ ERROR: {error_msg}")
                print(f"   URL attempted: {MOOBOT_URL}")
                print(f"   Make sure the streamer has a Moobot music queue configured.")
                print(f"   Try checking the URL manually in your browser.\n")
                return []
            
            # Take a screenshot for debugging
            self.driver.save_screenshot(OUTPUT_DIR / "page_screenshot.png")
            
            # Log the page source for debugging
            with open(OUTPUT_DIR / "page_source.html", 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            
            # Try multiple approaches to find song data
            songs = []
            
            # Approach 1: Look for Moobot-specific song queue
            selectors_to_try = [
                # Target the song queue table specifically
                "#input-content-queue tbody tr",
                "table.table-striped tbody tr",
                "tbody tr[data-id]",
                # Fallback to more generic selectors
                "tbody tr",
                "tr[data-id]",
                "tr",
                # Other potential selectors
                ".queue-item",
                ".song-item", 
                ".music-item",
                "[class*='song']",
                "[class*='music']"
            ]
            
            wait = WebDriverWait(self.driver, 15)
            
            for selector in selectors_to_try:
                try:
                    # Re-find elements each time to avoid stale references
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        self.logger.info(f"Found {len(elements)} elements with selector: {selector}")
                        
                        # Extract data immediately without storing element references
                        potential_songs = self.extract_song_info_robust(selector)
                        if potential_songs:
                            songs.extend(potential_songs)
                            self.logger.info(f"Extracted {len(potential_songs)} songs using {selector}")
                            break
                except Exception as e:
                    self.logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            # Approach 2: Look for YouTube links anywhere on the page
            if not songs:
                try:
                    youtube_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'youtube.com') or contains(@href, 'youtu.be')]")
                    if youtube_links:
                        self.logger.info(f"Found {len(youtube_links)} YouTube links")
                        songs = self.extract_from_youtube_links(youtube_links)
                except Exception as e:
                    self.logger.error(f"YouTube link extraction failed: {e}")
            
            # Approach 3: Parse visible text for song-like content
            if not songs:
                try:
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text
                    songs = self.parse_text_for_songs(page_text)
                    self.logger.info(f"Text parsing found {len(songs)} potential songs")
                except Exception as e:
                    self.logger.error(f"Text parsing failed: {e}")
            
            # Log what we found
            self.logger.info(f"Total songs extracted: {len(songs)}")
            
            return songs
            
        except Exception as e:
            self.logger.error(f"Error scraping songs: {e}")
            return []
            
    def extract_song_info(self, elements, selector) -> List[Dict]:
        """Extract song information from web elements."""
        songs = []
        current_time = datetime.now()
        
        for i, element in enumerate(elements):
            try:
                # Get all text content
                element_text = element.text.strip()
                
                # Skip empty or very short elements
                if len(element_text) < 3:
                    continue
                
                # Special handling for table rows (which contain the song queue)
                if selector == "tr":
                    song_info = self.extract_from_table_row(element, i, current_time)
                    if song_info:
                        songs.append(song_info)
                    continue
                
                # Look for YouTube links within the element
                youtube_url = ""
                try:
                    links = element.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        href = link.get_attribute("href")
                        if href and ("youtube.com" in href or "youtu.be" in href):
                            youtube_url = href
                            break
                except:
                    pass
                
                # Extract title - prefer link text if available, otherwise use element text
                title = ""
                if youtube_url:
                    try:
                        link_element = element.find_element(By.XPATH, f".//a[@href='{youtube_url}']")
                        title = link_element.text.strip()
                    except:
                        pass
                
                if not title:
                    title = element_text
                
                # Clean up the title
                title = self.clean_song_title(title)
                
                # Skip if title is still too short or looks like UI text
                if len(title) < 3 or self.is_ui_text(title):
                    continue
                
                song_info = {
                    "title": title,
                    "youtube_url": youtube_url,
                    "timestamp": current_time.isoformat(),
                    "scraped_at": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "selector_used": selector,
                    "element_index": i
                }
                
                songs.append(song_info)
                
            except Exception as e:
                self.logger.warning(f"Error extracting info from element {i}: {e}")
                continue
                
        return songs
    
    def extract_song_info_robust(self, selector: str) -> List[Dict]:
        """Extract song information robustly by re-finding elements each time."""
        songs = []
        current_time = datetime.now()
        
        try:
            # Re-find elements each time to avoid stale references
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            
            for i in range(len(elements)):
                try:
                    # Re-find the specific element by index each time
                    current_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if i >= len(current_elements):
                        continue
                        
                    element = current_elements[i]
                    
                    # Special handling for table rows (which contain the song queue)
                    if "tr" in selector:
                        song_info = self.extract_from_table_row_robust(selector, i, current_time)
                        if song_info:
                            songs.append(song_info)
                        continue
                    
                    # General extraction for other selectors
                    element_text = element.text.strip()
                    if len(element_text) < 3:
                        continue
                    
                    # Look for YouTube links
                    youtube_url = ""
                    try:
                        links = element.find_elements(By.TAG_NAME, "a")
                        for link in links:
                            href = link.get_attribute("href")
                            if href and ("youtube.com" in href or "youtu.be" in href):
                                youtube_url = href
                                break
                    except:
                        pass
                    
                    title = self.clean_song_title(element_text)
                    
                    if len(title) < 3 or self.is_ui_text(title):
                        continue
                    
                    song_info = {
                        "title": title,
                        "youtube_url": youtube_url,
                        "timestamp": current_time.isoformat(),
                        "scraped_at": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "selector_used": selector,
                        "element_index": i
                    }
                    
                    songs.append(song_info)
                    
                except Exception as e:
                    self.logger.debug(f"Error extracting from element {i} with {selector}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.warning(f"Error in robust extraction with {selector}: {e}")
            
        return songs
    
    def extract_from_table_row_robust(self, selector: str, row_index: int, current_time) -> Optional[Dict]:
        """Extract song info from table row using robust re-finding approach."""
        try:
            # Re-find the table rows
            rows = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if row_index >= len(rows):
                return None
                
            row = rows[row_index]
            
            # Extract song title
            title = ""
            try:
                title_element = row.find_element(By.CSS_SELECTOR, ".moobot-input-label-text-text")
                title = title_element.text.strip()
            except:
                # Fallback to row text
                title = row.text.strip().split('\n')[0] if row.text.strip() else ""
            
            if not title or len(title) < 3:
                return None
            
            # Extract metadata
            duration = ""
            requester = ""
            status = ""
            
            try:
                labels = row.find_elements(By.CSS_SELECTOR, ".moobot-input-label-text-label")
                for label in labels:
                    label_text = label.text.strip()
                    if ":" in label_text and len(label_text) < 10:  # Duration like 04:11
                        duration = label_text
                    elif label_text.startswith("By "):
                        requester = label_text
                    elif any(status_word in label_text for status_word in ["Playing", "next", "minutes"]):
                        status = label_text
            except:
                pass
            
            # Try to find YouTube link using multiple approaches
            youtube_url = ""
            try:
                # First, try to find the link button
                link_button = row.find_element(By.CSS_SELECTOR, "button[class*='button-type-link'], a[href*='youtube']")
                if link_button:
                    # Try getting data attributes
                    data_url = link_button.get_attribute("data-url")
                    href = link_button.get_attribute("href")
                    onclick = link_button.get_attribute("onclick")
                    
                    if data_url and ("youtube.com" in data_url or "youtu.be" in data_url):
                        youtube_url = data_url
                    elif href and ("youtube.com" in href or "youtu.be" in href):
                        youtube_url = href
                    else:
                        # Try to execute JavaScript to get the YouTube URL
                        try:
                            youtube_url = self.extract_youtube_url_from_button(link_button, title)
                        except Exception as js_error:
                            self.logger.debug(f"JavaScript extraction failed: {js_error}")
            except Exception as e:
                self.logger.debug(f"YouTube link extraction failed: {e}")
            
            return {
                "title": title,
                "duration": duration,
                "requester": requester,
                "status": status,
                "youtube_url": youtube_url,
                "timestamp": current_time.isoformat(),
                "scraped_at": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "selector_used": selector,
                "element_index": row_index
            }
            
        except Exception as e:
            self.logger.debug(f"Error extracting from table row {row_index}: {e}")
            return None
    
    def extract_youtube_url_from_button(self, button_element, song_title: str) -> str:
        """Extract YouTube URL from Moobot's external link buttons."""
        try:
            # Method 1: Try to click the button and capture the opened URL
            # First, store current window handles
            original_windows = self.driver.window_handles
            
            try:
                # Try to click the button (this should open YouTube in a new tab)
                self.driver.execute_script("arguments[0].click();", button_element)
                
                # Wait for new window to open (minimized to reduce audio)
                import time
                time.sleep(2)  # Reduced wait time to minimize audio
                
                # Check for new windows
                new_windows = self.driver.window_handles
                if len(new_windows) > len(original_windows):
                    # Switch to the new window
                    new_window = [w for w in new_windows if w not in original_windows][0]
                    self.driver.switch_to.window(new_window)
                    
                    # Minimal wait - just enough to get the URL
                    time.sleep(0.5)
                    
                    # Immediately pause any video that might be playing
                    try:
                        self.driver.execute_script("""
                            // Pause any YouTube videos that might be playing
                            var videos = document.querySelectorAll('video');
                            for (var i = 0; i < videos.length; i++) {
                                videos[i].pause();
                                videos[i].muted = true;
                                videos[i].volume = 0;
                            }
                        """)
                    except:
                        pass  # Ignore any JavaScript errors
                    
                    # Get the URL
                    current_url = self.driver.current_url
                    
                    # Close the new window and switch back
                    self.driver.close()
                    self.driver.switch_to.window(original_windows[0])
                    
                    # Check if it's a YouTube URL
                    if "youtube.com" in current_url or "youtu.be" in current_url:
                        self.logger.info(f"Found direct YouTube URL: {current_url}")
                        return current_url
                    else:
                        self.logger.debug(f"Button opened non-YouTube URL: {current_url}")
                    
            except Exception as click_error:
                self.logger.info(f"Button click method failed: {click_error}")
                # Make sure we're back to the original window
                try:
                    self.driver.switch_to.window(original_windows[0])
                except:
                    pass
            
            # Method 2: Try to extract from JavaScript event handlers
            try:
                # Look for data attributes or JavaScript events
                js_code = """
                var button = arguments[0];
                var result = {};
                
                // Check various attributes that might contain the URL
                result.dataUrl = button.getAttribute('data-url');
                result.dataHref = button.getAttribute('data-href');
                result.dataLink = button.getAttribute('data-link');
                result.onclick = button.onclick ? button.onclick.toString() : null;
                
                // Check parent elements for data
                var parent = button.parentElement;
                if (parent) {
                    result.parentDataUrl = parent.getAttribute('data-url');
                    result.parentDataHref = parent.getAttribute('data-href');
                }
                
                return result;
                """
                
                result = self.driver.execute_script(js_code, button_element)
                
                # Check each possible URL source
                for key, value in result.items():
                    if value and ("youtube.com" in str(value) or "youtu.be" in str(value)):
                        # Extract URL from the value
                        import re
                        url_pattern = r'https?://(?:www\.)?(youtube\.com|youtu\.be)/[^\s"\'>\)]+'
                        urls = re.findall(url_pattern, str(value))
                        if urls:
                            found_url = f"https://{urls[0]}"
                            self.logger.debug(f"Found YouTube URL via {key}: {found_url}")
                            return found_url
                            
            except Exception as js_error:
                self.logger.debug(f"JavaScript method failed: {js_error}")
            
            # Method 3: Try to inspect the network requests (advanced)
            try:
                # Get the row's data-id which might be used in API calls
                row = button_element.find_element(By.XPATH, "ancestor::tr[@data-id]")
                data_id = row.get_attribute("data-id")
                
                if data_id:
                    # Try to make an API call to get song info
                    api_url = f"https://moo.bot/api/song/{data_id}"
                    
                    # Use JavaScript to make the request
                    js_code = f"""
                    return fetch('{api_url}', {{
                        credentials: 'include',
                        headers: {{
                            'Accept': 'application/json'
                        }}
                    }})
                    .then(response => response.json())
                    .then(data => data)
                    .catch(error => null);
                    """
                    
                    # This is async, so we'd need a different approach
                    # For now, skip this method
                    
            except Exception as api_error:
                self.logger.debug(f"API method failed: {api_error}")
            
            # Method 4: Try to find video ID from history section thumbnails
            try:
                # Look for the song in the history section which has thumbnails
                history_rows = self.driver.find_elements(By.CSS_SELECTOR, "#input-content-history tbody tr")
                for history_row in history_rows:
                    try:
                        # Get song title from history row
                        history_title_element = history_row.find_element(By.CSS_SELECTOR, ".moobot-input-label-text-text")
                        history_title = history_title_element.text.strip()
                        
                        # Check if this matches our song (fuzzy match)
                        if self.songs_match(song_title, history_title):
                            # Look for YouTube thumbnail
                            img_element = history_row.find_element(By.CSS_SELECTOR, "img[src*='youtube.com']")
                            img_src = img_element.get_attribute("src")
                            
                            # Extract video ID from thumbnail URL
                            # Format: https://img.youtube.com/vi/VIDEO_ID/sddefault.jpg
                            import re
                            video_id_match = re.search(r'/vi/([^/]+)/', img_src)
                            if video_id_match:
                                video_id = video_id_match.group(1)
                                youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                                self.logger.info(f"Found direct YouTube URL via history thumbnail: {youtube_url} for song: {song_title}")
                                return youtube_url
                                
                    except Exception as row_error:
                        continue
                        
            except Exception as history_error:
                self.logger.debug(f"History thumbnail method failed: {history_error}")
            
            # Method 5: Fallback to search (only if no direct link found)
            self.logger.info(f"No direct YouTube link found for '{song_title}', using search fallback")
            return self.search_youtube_url(song_title)
            
        except Exception as e:
            self.logger.debug(f"Error extracting YouTube URL: {e}")
            # Fallback to search
            return self.search_youtube_url(song_title)
    
    def songs_match(self, title1: str, title2: str) -> bool:
        """Check if two song titles likely refer to the same song."""
        try:
            # Normalize both titles
            def normalize_title(title):
                import re
                # Convert to lowercase
                title = title.lower().strip()
                # Remove common suffixes and prefixes
                suffixes = [' (official video)', ' (official audio)', ' (official)', ' (lyrics)', ' m/v', ' | lyrics']
                for suffix in suffixes:
                    if title.endswith(suffix):
                        title = title[:-len(suffix)].strip()
                        break
                # Remove extra whitespace and special characters
                title = re.sub(r'[^a-z0-9\s]', ' ', title)
                title = ' '.join(title.split())
                return title
            
            norm1 = normalize_title(title1)
            norm2 = normalize_title(title2)
            
            # Exact match
            if norm1 == norm2:
                return True
            
            # Check if one is contained in the other (for cases like "Song" vs "Song (Official Video)")
            if norm1 in norm2 or norm2 in norm1:
                # Make sure it's not too short to avoid false positives
                if len(min(norm1, norm2)) > 10:
                    return True
            
            # Check similarity by word overlap
            words1 = set(norm1.split())
            words2 = set(norm2.split())
            
            if len(words1) > 0 and len(words2) > 0:
                overlap = len(words1.intersection(words2))
                total_words = len(words1.union(words2))
                similarity = overlap / total_words
                
                # If more than 70% of words match, consider it the same song
                if similarity > 0.7:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Error matching song titles: {e}")
            return False
    
    def search_youtube_url(self, song_title: str) -> str:
        """Generate a YouTube search URL for the song title."""
        try:
            import urllib.parse
            # Clean the title for searching
            search_query = song_title.strip()
            # Remove common suffixes that might not be in YouTube titles
            suffixes_to_remove = [' (Official Video)', ' (Official Audio)', ' (Official)', ' (Lyrics)', ' M/V']
            for suffix in suffixes_to_remove:
                if search_query.endswith(suffix):
                    search_query = search_query[:-len(suffix)].strip()
                    break
            
            encoded_query = urllib.parse.quote_plus(search_query)
            return f"https://www.youtube.com/results?search_query={encoded_query}"
        except Exception as e:
            self.logger.debug(f"Error generating YouTube search URL: {e}")
            return ""
    
    def extract_from_table_row(self, row_element, index, current_time) -> Optional[Dict]:
        """Extract song info specifically from Moobot table rows."""
        try:
            # Look for the song title in the specific structure
            song_title_element = row_element.find_element(By.CSS_SELECTOR, ".moobot-input-label-text-text")
            if not song_title_element:
                return None
                
            title = song_title_element.text.strip()
            
            # Skip if no meaningful title
            if not title or len(title) < 3:
                return None
            
            # Look for additional info (duration, requester, status)
            duration = ""
            requester = ""
            status = ""
            
            try:
                labels = row_element.find_elements(By.CSS_SELECTOR, ".moobot-input-label-text-label")
                for label in labels:
                    label_text = label.text.strip()
                    if ":" in label_text and len(label_text) < 10:  # Likely duration
                        duration = label_text
                    elif "By " in label_text:
                        requester = label_text
                    elif label_text in ["Playing now", "Playing next", "Playing in"]:
                        status = label_text
                    elif "Playing in" in label_text:
                        status = label_text
            except:
                pass
            
            # Try to find YouTube link by looking for external link buttons
            youtube_url = ""
            try:
                link_button = row_element.find_element(By.CSS_SELECTOR, "button.button-type-link")
                if link_button:
                    # The button should have a click handler that opens YouTube
                    # We'll try to construct the YouTube URL or find it in attributes
                    onclick = link_button.get_attribute("onclick")
                    data_url = link_button.get_attribute("data-url")
                    if data_url and ("youtube.com" in data_url or "youtu.be" in data_url):
                        youtube_url = data_url
            except:
                pass
            
            # Create enhanced title with metadata
            enhanced_title = title
            if duration:
                enhanced_title += f" [{duration}]"
            if requester:
                enhanced_title += f" - {requester}"
            if status:
                enhanced_title += f" ({status})"
            
            return {
                "title": title,
                "enhanced_title": enhanced_title,
                "duration": duration,
                "requester": requester,
                "status": status,
                "youtube_url": youtube_url,
                "timestamp": current_time.isoformat(),
                "scraped_at": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "selector_used": "tr",
                "element_index": index
            }
            
        except Exception as e:
            self.logger.debug(f"Error extracting from table row {index}: {e}")
            return None
    
    def extract_from_youtube_links(self, youtube_links) -> List[Dict]:
        """Extract songs from YouTube links found on the page."""
        songs = []
        current_time = datetime.now()
        
        for i, link in enumerate(youtube_links):
            try:
                href = link.get_attribute("href")
                title = link.text.strip()
                
                # If link text is empty or just URL, try to get title from parent element
                if not title or href in title:
                    try:
                        parent = link.find_element(By.XPATH, "..")
                        title = parent.text.strip()
                        # Remove the URL from the title if it's there
                        if href in title:
                            title = title.replace(href, "").strip()
                    except:
                        title = "Unknown Song"
                
                title = self.clean_song_title(title)
                
                if len(title) > 3 and not self.is_ui_text(title):
                    song_info = {
                        "title": title,
                        "youtube_url": href,
                        "timestamp": current_time.isoformat(),
                        "scraped_at": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "selector_used": "youtube_link",
                        "element_index": i
                    }
                    songs.append(song_info)
                    
            except Exception as e:
                self.logger.warning(f"Error extracting from YouTube link {i}: {e}")
                continue
                
        return songs
    
    def clean_song_title(self, title: str) -> str:
        """Clean and normalize song titles."""
        if not title:
            return ""
        
        # Remove extra whitespace
        title = " ".join(title.split())
        
        # Remove common prefixes/suffixes
        prefixes_to_remove = ["Now Playing:", "Current:", "Playing:", "♪", "♫", "🎵", "🎶"]
        for prefix in prefixes_to_remove:
            if title.startswith(prefix):
                title = title[len(prefix):].strip()
        
        return title
    
    def is_ui_text(self, text: str) -> bool:
        """Check if text looks like UI elements rather than song titles."""
        ui_indicators = [
            "click", "button", "menu", "login", "sign", "register",
            "home", "about", "contact", "help", "settings", "profile",
            "search", "filter", "sort", "view", "show", "hide",
            "next", "previous", "back", "forward", "submit", "cancel"
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in ui_indicators) or len(text) > 100
        
    def parse_text_for_songs(self, text: str) -> List[Dict]:
        """Fallback method to parse songs from page text."""
        songs = []
        current_time = datetime.now()
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            
            # Look for lines that might be songs
            if (len(line) > 5 and len(line) < 100 and 
                not line.startswith(('http', 'www', 'Click', 'Toggle', 'Menu')) and
                not self.is_ui_text(line)):
                
                song_info = {
                    "title": self.clean_song_title(line),
                    "youtube_url": "",
                    "timestamp": current_time.isoformat(),
                    "scraped_at": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "selector_used": "text_parsing",
                    "element_index": 0
                }
                songs.append(song_info)
                
        # Limit results and remove duplicates
        unique_songs = []
        seen_titles = set()
        
        for song in songs[:50]:  # Limit to reasonable number
            if song["title"] not in seen_titles:
                unique_songs.append(song)
                seen_titles.add(song["title"])
                
        return unique_songs
        
    def update_songs_data(self, new_songs: List[Dict]):
        """Update the songs data with new entries."""
        today = date.today().isoformat()
        
        if today not in self.songs_data:
            self.songs_data[today] = []
            
        # Add new songs, avoiding duplicates
        existing_titles = {song["title"].lower() for song in self.songs_data[today]}
        
        new_count = 0
        for song in new_songs:
            if song["title"].lower() not in existing_titles:
                self.songs_data[today].append(song)
                existing_titles.add(song["title"].lower())
                new_count += 1
                
        if new_count > 0:
            self.logger.info(f"Added {new_count} new songs for {today}")
            self.save_data()
            self.generate_html()
        else:
            self.logger.info("No new songs found")
            
    def generate_html(self):
        """Generate HTML pages for each date."""
        html_dir = OUTPUT_DIR / "html"
        
        for date_str, songs in self.songs_data.items():
            if not songs:
                continue
                
            html_content = self.create_html_page(date_str, songs)
            html_file = html_dir / f"songs_{date_str}.html"
            
            try:
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                self.logger.info(f"Generated HTML for {date_str}: {len(songs)} songs")
            except Exception as e:
                self.logger.error(f"Failed to write HTML file for {date_str}: {e}")
                
        # Generate index page
        self.generate_index_page()
        
    def create_html_page(self, date_str: str, songs: List[Dict]) -> str:
        """Create HTML content for a specific date."""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slimaera Songs - {date_str}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f0f2f5;
            line-height: 1.6;
        }}
        .header {{
            background: linear-gradient(135deg, #6441a5, #9146ff);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 20px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 2.5em;
        }}
        .header h2 {{
            margin: 0;
            font-weight: 300;
            font-size: 1.3em;
        }}
        .song-list {{
            background-color: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .song-item {{
            border-bottom: 1px solid #e1e8ed;
            padding: 20px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background-color 0.2s;
        }}
        .song-item:hover {{
            background-color: #f8f9fa;
            margin: 0 -20px;
            padding: 20px 20px;
            border-radius: 8px;
        }}
        .song-item:last-child {{
            border-bottom: none;
        }}
        .song-info {{
            flex-grow: 1;
        }}
        .song-title {{
            font-weight: 600;
            color: #1a202c;
            font-size: 1.1em;
            margin-bottom: 5px;
        }}
        .song-meta {{
            color: #718096;
            font-size: 0.9em;
        }}
        .song-time {{
            color: #666;
            font-size: 0.9em;
            margin-left: 10px;
        }}
        .youtube-link {{
            background-color: #ff0000;
            color: white;
            padding: 8px 16px;
            text-decoration: none;
            border-radius: 6px;
            margin-left: 15px;
            font-weight: 500;
            transition: background-color 0.2s;
        }}
        .youtube-link:hover {{
            background-color: #cc0000;
            text-decoration: none;
            color: white;
        }}
        .youtube-search {{
            background-color: #1976d2;
        }}
        .youtube-search:hover {{
            background-color: #1565c0;
        }}
        .song-actions {{
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 5px;
        }}
        .stats {{
            margin-bottom: 20px;
            padding: 15px 20px;
            background: linear-gradient(135deg, #e6f3ff, #f0f8ff);
            border-radius: 8px;
            border-left: 4px solid #6441a5;
        }}
        .stats strong {{
            color: #6441a5;
        }}
        .nav {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .nav a {{
            color: #6441a5;
            text-decoration: none;
            font-weight: 600;
            padding: 10px 20px;
            border: 2px solid #6441a5;
            border-radius: 6px;
            transition: all 0.2s;
        }}
        .nav a:hover {{
            background-color: #6441a5;
            color: white;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #718096;
            font-size: 0.9em;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div class="nav">
        <a href="index.html">← Back to All Dates</a>
    </div>
    
    <div class="header">
        <h1>🎵 {STREAMER_NAME.title()}'s Song Queue</h1>
        <h2>{date_str}</h2>
    </div>
    
    <div class="stats">
        <strong>Total Songs Collected:</strong> {len(songs)}
    </div>
    
    <div class="song-list">
"""
        
        for i, song in enumerate(songs, 1):
            youtube_link = ""
            youtube_icon = ""
            
            if song.get("youtube_url"):
                url = song["youtube_url"]
                if "youtube.com/results" in url:
                    # It's a search URL (fallback)
                    youtube_link = f'<a href="{url}" target="_blank" class="youtube-link youtube-search">🔍 Search YouTube</a>'
                    youtube_icon = " 🔍"
                elif "youtube.com/watch" in url or "youtu.be/" in url:
                    # Direct YouTube video link
                    youtube_link = f'<a href="{url}" target="_blank" class="youtube-link">▶️ Watch on YouTube</a>'
                    youtube_icon = " ▶️"
                else:
                    # Other YouTube link (channel, playlist, etc.)
                    youtube_link = f'<a href="{url}" target="_blank" class="youtube-link">🎵 Open YouTube</a>'
                    youtube_icon = " 🎵"
                
            # Use enhanced title if available, otherwise fall back to regular title
            display_title = song.get("enhanced_title", song["title"])
            
            # Build metadata string
            metadata_parts = [f"Collected at {song['scraped_at']}"]
            if song.get("duration"):
                metadata_parts.append(f"Duration: {song['duration']}")
            if song.get("requester"):
                metadata_parts.append(song['requester'])
            if song.get("status"):
                metadata_parts.append(f"Status: {song['status']}")
            
            metadata_string = " | ".join(metadata_parts)
                
            html += f"""
        <div class="song-item">
            <div class="song-info">
                <div class="song-title">#{i} {song["title"]}{youtube_icon}</div>
                <div class="song-meta">{metadata_string}</div>
            </div>
            <div class="song-actions">
                {youtube_link}
            </div>
        </div>"""
            
        html += """
    </div>
    
    <div class="footer">
        Generated by Moobot Scraper | Last updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
    </div>
</body>
</html>"""
        
        return html
        
    def generate_index_page(self):
        """Generate an index page listing all dates."""
        html_dir = OUTPUT_DIR / "html"
        
        total_songs = sum(len(songs) for songs in self.songs_data.values())
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slimaera Songs - Archive</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f0f2f5;
            line-height: 1.6;
        }}
        .header {{
            background: linear-gradient(135deg, #6441a5, #9146ff);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 10px 0 0 0;
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #6441a5;
        }}
        .stat-label {{
            color: #718096;
            margin-top: 5px;
        }}
        .date-list {{
            background-color: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .date-item {{
            border-bottom: 1px solid #e1e8ed;
            padding: 20px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background-color 0.2s;
        }}
        .date-item:hover {{
            background-color: #f8f9fa;
            margin: 0 -20px;
            padding: 20px;
            border-radius: 8px;
        }}
        .date-item:last-child {{
            border-bottom: none;
        }}
        .date-link {{
            color: #6441a5;
            text-decoration: none;
            font-weight: 600;
            font-size: 1.1em;
        }}
        .date-link:hover {{
            text-decoration: underline;
        }}
        .song-count {{
            background-color: #6441a5;
            color: white;
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 0.9em;
            font-weight: 500;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #718096;
            font-size: 0.9em;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎵 {STREAMER_NAME.title()}'s Song Queue Archive</h1>
        <p>Songs collected from Moobot stream requests</p>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">{len(self.songs_data)}</div>
            <div class="stat-label">Days Tracked</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{total_songs}</div>
            <div class="stat-label">Total Songs</div>
        </div>
    </div>
    
    <div class="date-list">
"""
        
        sorted_dates = sorted(self.songs_data.keys(), reverse=True)
        if not sorted_dates:
            html += """
        <div style="text-align: center; color: #718096; padding: 40px;">
            No songs collected yet. The scraper will start collecting songs once it runs.
        </div>"""
        
        for date_str in sorted_dates:
            song_count = len(self.songs_data[date_str])
            if song_count > 0:
                # Format the date nicely
                try:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%B %d, %Y")
                except:
                    formatted_date = date_str
                
                html += f"""
        <div class="date-item">
            <a href="songs_{date_str}.html" class="date-link">{formatted_date}</a>
            <span class="song-count">{song_count} songs</span>
        </div>"""
        
        html += """
    </div>
    
    <div class="footer">
        Generated by Moobot Scraper | Last updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
    </div>
</body>
</html>"""
        
        try:
            with open(html_dir / "index.html", 'w', encoding='utf-8') as f:
                f.write(html)
            self.logger.info("Generated index page")
        except Exception as e:
            self.logger.error(f"Failed to generate index page: {e}")
            
    def run_scan(self):
        """Run a single scan cycle."""
        try:
            self.logger.info("Starting scan...")
            songs = self.scrape_songs()
            
            if songs:
                self.logger.info(f"Found {len(songs)} songs")
                for song in songs[:5]:  # Log first few songs
                    self.safe_log('info', f"  - {song['title']} [{song.get('selector_used', 'unknown')}]")
                self.update_songs_data(songs)
            else:
                self.logger.warning("No songs found in this scan")
                
        except Exception as e:
            self.logger.error(f"Error during scan: {e}")
            
    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("WebDriver closed")
            except Exception as e:
                self.logger.error(f"Error closing WebDriver: {e}")
                
    def run_forever(self):
        """Run the scraper continuously."""
        self.logger.info("Starting Moobot scraper...")
        
        try:
            # Run initial scan
            if not self.shutdown_requested:
                self.run_scan()
            
            # Schedule regular scans
            schedule.every(1).minutes.do(self.run_scan)
            
            self.logger.info("Scheduler started. Scanning every minute.")
            self.logger.info("Press Ctrl+C to stop gracefully.")
            
            while not self.shutdown_requested:
                schedule.run_pending()
                time.sleep(1)
                
            self.logger.info("Shutdown requested. Saving data and cleaning up...")
                
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt. Shutting down gracefully...")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
        finally:
            # Ensure data is saved before cleanup
            try:
                self.save_data()
                self.generate_html()
                self.logger.info("Final data save completed.")
            except Exception as e:
                self.logger.error(f"Error during final save: {e}")
            self.cleanup()

def main():
    """Main entry point."""
    scraper = MoobotScraper()
    
    try:
        scraper.run_forever()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    main()