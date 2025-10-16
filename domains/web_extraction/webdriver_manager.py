"""WebDriver management for Web Extraction domain.

Handles WebDriver lifecycle, configuration, and browser automation setup.
"""

import time
from pathlib import Path
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from infrastructure.logging import UnicodeLogger
from .entities import ExtractionSession, StreamerValidationResult
from domains.music_queue.entities import StreamerId


class WebDriverManager:
    """Service for managing WebDriver lifecycle and configuration."""
    
    def __init__(self, logger: UnicodeLogger):
        self.logger = logger
        self._driver: Optional[WebDriver] = None
    
    def create_extraction_session(self, streamer_id: StreamerId) -> ExtractionSession:
        """Create a new extraction session with WebDriver."""
        if not self._driver:
            self._setup_webdriver()
        
        return ExtractionSession(
            streamer_id=streamer_id,
            browser=self._driver
        )
    
    def cleanup(self) -> None:
        """Clean up WebDriver resources."""
        if self._driver:
            try:
                self._driver.quit()
                self.logger.info("WebDriver closed")
                self._driver = None
            except Exception as e:
                self.logger.error(f"Error closing WebDriver: {e}")
    
    def _setup_webdriver(self) -> None:
        """Initialize Chrome WebDriver with appropriate options."""
        chrome_options = self._get_chrome_options()
        
        try:
            self._driver = webdriver.Chrome(options=chrome_options)
            
            # Remove webdriver property to reduce detection
            self._driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            
            # Set implicit wait timeout
            self._driver.implicitly_wait(10)
            
            self.logger.info("WebDriver initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            raise WebDriverSetupError(f"WebDriver initialization failed: {e}")
    
    def _get_chrome_options(self) -> Options:
        """Get Chrome options configured for web scraping."""
        chrome_options = Options()
        
        # Basic options for headless operation
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # User agent to appear as regular browser
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        
        # Anti-detection measures
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Audio muting (important for YouTube extraction)
        chrome_options.add_argument("--mute-audio")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        
        # Media preferences to block audio/video
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
        
        return chrome_options
    
    def load_page(self, session: ExtractionSession, wait_seconds: int = 5) -> None:
        """Load the Moobot page for the session's streamer."""
        try:
            self.logger.info(f"Loading Moobot page for {session.streamer_id.name}...")
            session.browser.get(session.moobot_url)
            
            # Wait for page to load
            time.sleep(wait_seconds)
            
            # Save debug artifacts
            session.save_debug_artifacts(Path("output"))
            
        except Exception as e:
            error_msg = f"Failed to load page {session.moobot_url}: {e}"
            self.logger.error(error_msg)
            raise PageLoadError(error_msg)
    
    def validate_streamer(self, session: ExtractionSession) -> StreamerValidationResult:
        """Validate that the streamer exists on Moobot."""
        try:
            page_text = session.browser.find_element(By.TAG_NAME, "body").text.strip()
            self.logger.debug(f"Page content for validation: {page_text[:200]}...")
            
            # Check for common "not found" patterns
            not_found_patterns = [
                f"{session.streamer_id.name} was not found",
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
                    self.logger.debug(f"Found not-found pattern: {pattern}")
                    
                    # Special case: "This page requires Javascript" is normal if not the only content
                    if pattern == "This page requires Javascript" and len(page_text.strip()) < 50:
                        return StreamerValidationResult.invalid_streamer(
                            session.streamer_id, 
                            "Page appears to be empty or JavaScript-only"
                        )
                    elif pattern != "This page requires Javascript":
                        return StreamerValidationResult.invalid_streamer(
                            session.streamer_id,
                            f"Streamer not found: {pattern}"
                        )
            
            # Additional check: if the page is suspiciously empty
            if len(page_text.strip()) < 20:
                self.logger.debug("Page seems too short/empty")
                return StreamerValidationResult.invalid_streamer(
                    session.streamer_id,
                    "Page content is too short or empty"
                )
            
            # If we get here, the streamer likely exists
            self.logger.info(f"Streamer '{session.streamer_id.name}' appears to exist on Moobot")
            return StreamerValidationResult.valid_streamer(
                session.streamer_id,
                ["page_content_valid", "no_error_patterns"]
            )
            
        except Exception as e:
            self.logger.warning(f"Error validating streamer existence: {e}")
            # If we can't verify, assume it exists and let the scraper continue
            return StreamerValidationResult.valid_streamer(
                session.streamer_id,
                ["validation_error_fallback"]
            )


class WebDriverSetupError(Exception):
    """Exception raised when WebDriver setup fails."""
    pass


class PageLoadError(Exception):
    """Exception raised when page loading fails."""
    pass