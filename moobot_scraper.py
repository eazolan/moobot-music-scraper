#!/usr/bin/env python3
"""
Moobot Music Queue Scraper - Refactored with Domain-Driven Design
Monitors Moobot music queue pages for any Twitch streamer
and generates local HTML pages organized by date.

To use for a different streamer, change the STREAMER_NAME below
or pass it as a command line argument.
"""

import time
import logging
import signal
import sys
import argparse
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional
import schedule

# Import infrastructure modules
from infrastructure.logging import setup_logging, UnicodeLogger
from infrastructure.filesystem import setup_directories

# Import domain modules
from domains.music_queue import SongRequest, StreamerId, SongMatchingService, QueueRepository
from domains.content_publishing import SongCollection, PublishingConfig, ContentPublisher
from domains.song_extraction import ExtractionCoordinator, ExtractionConfig, ElementSelector

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Configuration
DEFAULT_STREAMER = "pokimane"

def get_streamer_name():
    parser = argparse.ArgumentParser(description='Scrape Moobot music queue for a Twitch streamer')
    parser.add_argument('--streamer', '-s', 
                       default=DEFAULT_STREAMER,
                       help=f'Streamer name to monitor (default: {DEFAULT_STREAMER})')
    args, unknown = parser.parse_known_args()
    return args.streamer

STREAMER_NAME = get_streamer_name()

# Derived configuration
MOOBOT_URL = f"https://moo.bot/r/music#{STREAMER_NAME}"
OUTPUT_DIR = Path("output")
DATA_FILE = OUTPUT_DIR / "songs_data.json"
LOG_FILE = OUTPUT_DIR / "scraper.log"
SCAN_INTERVAL = 60  # seconds

class MoobotScraper:
    def __init__(self):
        self.logger = setup_logging(LOG_FILE, OUTPUT_DIR)
        setup_directories(OUTPUT_DIR)
        self.driver = None
        
        # Initialize domain services
        self.song_matcher = SongMatchingService()
        self.queue_repository = QueueRepository(DATA_FILE, self.logger)
        self.songs_data = self.queue_repository.get_all_songs_data()  # Backward compatibility
        
        # Initialize extraction domain
        self.extraction_coordinator = ExtractionCoordinator(self.logger)
        # Use faster config to avoid long extraction times
        self.extraction_config = ExtractionConfig.create_fast()
        # But still extract YouTube URLs
        self.extraction_config.extract_youtube_urls = True
        self.extraction_config.try_button_click = True  # This was working well
        self.extraction_config.max_songs_per_strategy = 10  # Limit songs per strategy
        # Enable strong filtering
        self.extraction_config.skip_ui_text = True
        self.extraction_config.min_title_length = 5  # Require at least 5 characters
        self.extraction_config.clean_titles = True
        
        # Initialize publishing domain
        self.publishing_config = PublishingConfig(
            output_dir=OUTPUT_DIR,
            streamer_name=STREAMER_NAME
        )
        self.content_publisher = ContentPublisher(self.publishing_config, self.logger)
        
        self.shutdown_requested = False
        self.setup_signal_handlers()
        
    def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        if sys.platform == "win32":
            try:
                signal.signal(signal.SIGBREAK, self.signal_handler)
            except AttributeError:
                pass
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        signal_names = {signal.SIGINT: "SIGINT (Ctrl+C)", signal.SIGTERM: "SIGTERM"}
        if sys.platform == "win32" and hasattr(signal, 'SIGBREAK'):
            signal_names[signal.SIGBREAK] = "SIGBREAK (Ctrl+Break)"
        
        signal_name = signal_names.get(signum, f"Signal {signum}")
        self.logger.info(f"Received {signal_name}. Initiating graceful shutdown...")
        self.shutdown_requested = True
        
    def setup_webdriver(self):
        """Initialize Chrome WebDriver with appropriate options."""
        # Clean up any existing Chrome processes that might interfere
        self._cleanup_chrome_processes()
        
        chrome_options = Options()
        # Use minimal options that work (matching the diagnostic script)
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        # Ensure complete audio silence
        chrome_options.add_argument("--mute-audio")
        chrome_options.add_argument("--disable-audio")
        chrome_options.add_argument("--disable-audio-output")
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        try:
            from selenium.webdriver.chrome.service import Service
            
            # Let Selenium Manager handle ChromeDriver automatically
            # This should automatically download and manage the correct ChromeDriver version
            self.logger.info("Initializing ChromeDriver with Selenium Manager...")
            
            # Try multiple approaches with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if attempt == 0:
                        # First attempt: Use Selenium Manager (automatic driver management)
                        self.logger.info(f"Attempt {attempt + 1}: Using Selenium Manager...")
                        self.driver = webdriver.Chrome(options=chrome_options)
                    else:
                        # Subsequent attempts: Use explicit service
                        self.logger.info(f"Attempt {attempt + 1}: Using explicit service...")
                        service = Service()
                        self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    
                    # If we get here, initialization was successful
                    break
                    
                except Exception as e:
                    self.logger.warning(f"WebDriver attempt {attempt + 1} failed: {e}")
                    
                    if attempt < max_retries - 1:
                        # Clean up and wait before retry
                        self._cleanup_chrome_processes()
                        time.sleep(2)  # Wait 2 seconds before retry
                    else:
                        # Final attempt failed, re-raise the exception
                        raise e
            # Set shorter timeouts to prevent hanging
            self.driver.set_page_load_timeout(30)  # 30 second page load timeout
            self.driver.implicitly_wait(5)  # 5 second element wait timeout
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.logger.info("WebDriver initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize WebDriver: {e}"
            self.logger.error(error_msg)
            
            # Provide helpful troubleshooting information
            self.logger.error("\n=== WebDriver Troubleshooting ===")
            self.logger.error("Common causes of SessionNotCreatedException:")
            self.logger.error("1. Chrome and ChromeDriver version mismatch")
            self.logger.error("2. ChromeDriver not found in PATH")
            self.logger.error("3. Chrome browser not installed or accessible")
            self.logger.error("\nTroubleshooting steps:")
            self.logger.error("1. Check Chrome version: chrome://version/")
            self.logger.error("2. Download matching ChromeDriver from https://chromedriver.chromium.org/")
            self.logger.error("3. Ensure ChromeDriver is in PATH or same directory as script")
            self.logger.error("4. Try running: 'chromedriver --version' to test driver")
            self.logger.error("================================\n")
            raise
    
    def _cleanup_chrome_processes(self):
        """Clean up any hanging Chrome processes that might interfere with WebDriver."""
        try:
            import subprocess
            if sys.platform == "win32":
                # Kill any hanging Chrome processes on Windows
                subprocess.run(
                    ["taskkill", "/f", "/im", "chrome.exe"],
                    capture_output=True, timeout=5
                )
                subprocess.run(
                    ["taskkill", "/f", "/im", "chromedriver.exe"],
                    capture_output=True, timeout=5
                )
                self.logger.debug("Cleaned up existing Chrome processes")
        except Exception as e:
            self.logger.debug(f"Chrome process cleanup failed (this is usually fine): {e}")
            
    def verify_streamer_exists(self) -> bool:
        """Check if the streamer exists on Moobot."""
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.strip()
            
            not_found_patterns = [
                f"{STREAMER_NAME} was not found",
                "was not found",
                "not found",
                "404",
                "User not found",
                "Streamer not found"
            ]
            
            page_text_lower = page_text.lower()
            
            for pattern in not_found_patterns:
                if pattern.lower() in page_text_lower:
                    return False
            
            if len(page_text.strip()) < 20:
                return False
                
            self.logger.info(f"Streamer '{STREAMER_NAME}' appears to exist on Moobot")
            return True
            
        except Exception as e:
            self.logger.warning(f"Error verifying streamer existence: {e}")
            return True
    
    def _create_extraction_selectors(self) -> List[ElementSelector]:
        """Create Moobot-specific selectors with priorities."""
        return [
            # High priority: Moobot-specific song queue table
            ElementSelector.create_custom(
                "#input-content-queue tbody tr", 
                description="Moobot song queue table rows", 
                priority=10
            ),
            ElementSelector.create_custom(
                "table.table-striped tbody tr", 
                description="Striped table rows", 
                priority=9
            ),
            ElementSelector.create_custom(
                "tbody tr[data-id]", 
                description="Table rows with data-id", 
                priority=8
            ),
            # Medium priority: General table rows and YouTube links
            ElementSelector.create_table_row(priority=7),
            ElementSelector.create_youtube_links(priority=6),
            # Low priority: Fallback selectors
            ElementSelector.create_custom(
                ".queue-item, .song-item, .music-item", 
                description="Music item classes", 
                priority=4
            ),
            ElementSelector.create_custom(
                "[class*='song'], [class*='music']", 
                description="Elements with song/music in class", 
                priority=3
            ),
            ElementSelector.create_generic_links(priority=2),
            ElementSelector.create_text_elements(priority=1)
        ]
    
    def scrape_songs(self) -> List[Dict]:
        """Scrape current songs from the Moobot page using the extraction domain."""
        if not self.driver:
            self.setup_webdriver()
            
        try:
            self.logger.info("Loading Moobot page...")
            # Add explicit timeout handling for page load
            try:
                self.driver.get(MOOBOT_URL)
                # Wait for page to be ready
                WebDriverWait(self.driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                time.sleep(2)  # Reduced wait time
            except TimeoutException:
                self.logger.warning("Page load timeout - proceeding anyway")
            except Exception as e:
                self.logger.error(f"Error loading page: {e}")
                return []
            
            # Check if the streamer exists
            if not self.verify_streamer_exists():
                error_msg = f"Streamer '{STREAMER_NAME}' was not found on Moobot."
                self.logger.error(error_msg)
                print(f"\n❌ ERROR: {error_msg}")
                print(f"   URL attempted: {MOOBOT_URL}")
                return []
            
            # Save debugging info
            self.driver.save_screenshot(OUTPUT_DIR / "page_screenshot.png")
            with open(OUTPUT_DIR / "page_source.html", 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            
            # Load existing songs for today to avoid redundant YouTube extraction
            from datetime import date
            existing_songs_today = self.queue_repository.load_daily_queue(date.today())
            existing_songs_with_urls = {
                song.title.lower(): song.youtube_url 
                for song in existing_songs_today 
                if song.youtube_url
            }
            
            self.logger.info(f"Found {len(existing_songs_with_urls)} existing songs with YouTube URLs")
            
            # Use the extraction domain for comprehensive song extraction
            selectors = self._create_extraction_selectors()
            
            # Extract songs using the optimized approach
            extraction_result = self.extraction_coordinator.extract_songs_optimized(
                self.driver, selectors, self.extraction_config, existing_songs_with_urls
            )
            
            if extraction_result.success:
                self.logger.info(f"Extraction successful: {extraction_result.song_count} unique songs found")
                if extraction_result.has_warnings:
                    for warning in extraction_result.warnings:
                        self.logger.warning(f"Extraction warning: {warning}")
            else:
                self.logger.error(f"Extraction failed: {extraction_result.error_message}")
            
            # Convert SongRequest objects to dictionaries for backward compatibility
            songs = [song.to_dict() for song in extraction_result.songs]
            
            self.logger.info(f"Total songs extracted: {len(songs)}")
            
            return songs
            
        except Exception as e:
            self.logger.error(f"Error scraping songs: {e}")
            return []
    
    def update_songs_data(self, new_songs: List[Dict]):
        """Update the songs data with new entries."""
        # Convert dictionaries to SongRequest objects
        song_requests = []
        for song_dict in new_songs:
            try:
                song_request = SongRequest.from_dict(song_dict)
                song_requests.append(song_request)
            except ValueError as e:
                self.logger.warning(f"Skipping invalid song: {e}")
                continue
        
        # Add songs using domain repository
        new_count = self.queue_repository.add_new_songs(song_requests)
        
        if new_count > 0:
            # Update backward compatibility data
            self.songs_data = self.queue_repository.get_all_songs_data()
            self.generate_html()
        else:
            self.logger.info("No new songs found")
            
    def generate_html(self):
        """Generate HTML pages for each date using content publishing domain."""
        # Convert songs data to SongCollection objects
        collections = []
        streamer_id = StreamerId(STREAMER_NAME)
        
        for date_str, songs_dicts in self.songs_data.items():
            if not songs_dicts:
                continue
            
            try:
                # Parse date
                collection_date = date.fromisoformat(date_str)
                
                # Convert dictionaries to SongRequest objects
                songs = []
                for song_dict in songs_dicts:
                    try:
                        song = SongRequest.from_dict(song_dict)
                        songs.append(song)
                    except ValueError as e:
                        self.logger.warning(f"Skipping invalid song in {date_str}: {e}")
                        continue
                
                # Create SongCollection
                collection = SongCollection(
                    date=collection_date,
                    songs=songs,
                    streamer_id=streamer_id
                )
                collections.append(collection)
                
            except Exception as e:
                self.logger.error(f"Error creating collection for {date_str}: {e}")
                continue
        
        # Publish all collections using content publishing domain
        result = self.content_publisher.publish_all(collections)
        
        if result.has_errors:
            for error in result.errors:
                self.logger.error(f"Publishing error: {error}")
    
    def save_data(self):
        """Save songs data - now handled by repository."""
        pass  # Repository handles saving automatically
            
    def run_scan(self):
        """Run a single scan cycle."""
        try:
            self.logger.info("Starting scan...")
            songs = self.scrape_songs()
            
            if songs:
                self.logger.info(f"Found {len(songs)} songs")
                for song in songs[:5]:  # Log first few songs
                    self.logger.info(f"  - {song['title']} [{song.get('selector_used', 'unknown')}]")
                self.update_songs_data(songs)
            else:
                self.logger.warning("No songs found in this scan")
                
        except Exception as e:
            self.logger.error(f"Error during scan: {e}")
            
    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            try:
                # Force close WebDriver with timeout
                import threading
                import subprocess
                
                def force_quit():
                    try:
                        self.driver.quit()
                    except:
                        pass
                    
                    # Kill any remaining Chrome processes as backup
                    try:
                        if sys.platform == "win32":
                            subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], 
                                         capture_output=True, timeout=5)
                            subprocess.run(["taskkill", "/f", "/im", "chromedriver.exe"], 
                                         capture_output=True, timeout=5)
                    except:
                        pass
                
                # Run cleanup in thread with timeout
                cleanup_thread = threading.Thread(target=force_quit)
                cleanup_thread.start()
                cleanup_thread.join(timeout=5)  # 5 second timeout
                
                if cleanup_thread.is_alive():
                    self.logger.warning("WebDriver cleanup timed out")
                else:
                    self.logger.info("WebDriver closed")
                    
            except Exception as e:
                self.logger.error(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None
                
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
                
            self.logger.info("Shutdown requested. Cleaning up...")
                
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt. Shutting down gracefully...")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
        finally:
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