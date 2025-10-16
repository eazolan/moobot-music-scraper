"""Table row extraction strategy for Moobot-specific table structures."""

import time
import re
import urllib.parse
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from selenium.webdriver.common.by import By

from .extraction_strategy import ExtractionStrategy
from ..entities import ExtractionResult, ExtractionConfig, ElementSelector
from domains.music_queue.entities import SongRequest
from domains.music_queue.services import SongMatchingService

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver


class TableRowExtractionStrategy(ExtractionStrategy):
    """Strategy for extracting songs from table rows in Moobot interface.
    
    Handles the complex Moobot table structure with song titles, metadata,
    and YouTube URL extraction through various methods.
    """
    
    def __init__(self):
        super().__init__("table_row")
        self.song_matcher = SongMatchingService()
    
    def can_handle(self, selector: ElementSelector) -> bool:
        """Check if this strategy can handle table row selectors."""
        return selector.is_table_row_selector
    
    def get_priority(self) -> int:
        """High priority for table row extraction."""
        return 10
    
    def supports_robust_extraction(self) -> bool:
        """This strategy supports robust re-finding of elements."""
        return True
    
    def extract_songs(
        self,
        driver: "WebDriver", 
        selector: ElementSelector,
        config: ExtractionConfig
    ) -> ExtractionResult:
        """Extract songs from table rows."""
        try:
            if config.use_robust_finding:
                return self._extract_songs_robust(driver, selector, config)
            else:
                return self._extract_songs_simple(driver, selector, config)
                
        except Exception as e:
            self.logger.error(f"Error in table row extraction: {e}")
            return ExtractionResult.create_failure(
                error_message=str(e),
                strategy_used=self.name,
                selector_used=selector.selector
            )
    
    def _extract_songs_simple(
        self,
        driver: "WebDriver",
        selector: ElementSelector, 
        config: ExtractionConfig
    ) -> ExtractionResult:
        """Extract songs using simple element finding."""
        songs = []
        current_time = datetime.now()
        
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector.selector)
            element_count = len(elements)
            
            for i, element in enumerate(elements):
                try:
                    song_info = self._extract_from_table_row(
                        element, i, current_time, config
                    )
                    if song_info:
                        song_request = SongRequest.from_dict(song_info)
                        songs.append(song_request)
                        
                except ValueError as e:
                    self.logger.warning(f"Invalid song data from row {i}: {e}")
                    continue
                except Exception as e:
                    self.logger.warning(f"Error extracting from row {i}: {e}")
                    continue
            
            return ExtractionResult.create_success(
                songs=songs,
                strategy_used=self.name,
                selector_used=selector.selector,
                element_count=element_count
            )
            
        except Exception as e:
            return ExtractionResult.create_failure(
                error_message=str(e),
                strategy_used=self.name,
                selector_used=selector.selector
            )
    
    def _extract_songs_robust(
        self,
        driver: "WebDriver",
        selector: ElementSelector,
        config: ExtractionConfig
    ) -> ExtractionResult:
        """Extract songs using robust re-finding approach."""
        songs = []
        current_time = datetime.now()
        
        try:
            # Re-find elements each time to avoid stale references
            elements = driver.find_elements(By.CSS_SELECTOR, selector.selector)
            element_count = len(elements)
            
            for i in range(element_count):
                try:
                    song_info = self._extract_from_table_row_robust(
                        driver, selector.selector, i, current_time, config
                    )
                    if song_info:
                        song_request = SongRequest.from_dict(song_info)
                        songs.append(song_request)
                        
                except ValueError as e:
                    self.logger.warning(f"Invalid song data from row {i}: {e}")
                    continue
                except Exception as e:
                    self.logger.debug(f"Error extracting from row {i}: {e}")
                    continue
            
            return ExtractionResult.create_success(
                songs=songs,
                strategy_used=self.name,
                selector_used=selector.selector,
                element_count=element_count
            )
            
        except Exception as e:
            return ExtractionResult.create_failure(
                error_message=str(e),
                strategy_used=self.name,
                selector_used=selector.selector
            )
    
    def _extract_from_table_row(
        self, 
        row_element,
        index: int,
        current_time: datetime,
        config: ExtractionConfig
    ) -> Optional[dict]:
        """Extract song info from a single table row element."""
        try:
            # Look for the song title in Moobot's specific structure
            song_title_element = row_element.find_element(
                By.CSS_SELECTOR, ".moobot-input-label-text-text"
            )
            if not song_title_element:
                return None
                
            title = song_title_element.text.strip()
            
            # Apply filtering
            if not title or len(title) < config.min_title_length:
                return None
            
            if config.skip_ui_text and self.song_matcher.is_ui_text(title):
                return None
            
            # Clean title if configured
            if config.clean_titles:
                title = self.song_matcher.clean_song_title(title)
            
            # Extract metadata
            duration = ""
            requester = ""
            status = ""
            
            if config.extract_metadata:
                try:
                    labels = row_element.find_elements(
                        By.CSS_SELECTOR, ".moobot-input-label-text-label"
                    )
                    for label in labels:
                        label_text = label.text.strip()
                        if ":" in label_text and len(label_text) < 10:
                            duration = label_text
                        elif "By " in label_text:
                            requester = label_text
                        elif any(status_word in label_text 
                               for status_word in ["Playing", "next", "minutes"]):
                            status = label_text
                except:
                    pass
            
            # Extract YouTube URL with optimization
            youtube_url = ""
            if config.extract_youtube_urls:
                # Check if we already have URL for this song (optimization)
                existing_urls = config.get_custom_attribute("existing_youtube_urls", {})
                title_lower = title.lower()
                
                if title_lower in existing_urls:
                    youtube_url = existing_urls[title_lower]
                    self.logger.debug(f"Reused existing YouTube URL for: {title}")
                else:
                    # Only extract if we don't already have it
                    youtube_url = self._extract_youtube_url_simple(
                        row_element, title, config
                    )
            
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
    
    def _extract_from_table_row_robust(
        self,
        driver: "WebDriver",
        selector: str,
        row_index: int,
        current_time: datetime,
        config: ExtractionConfig
    ) -> Optional[dict]:
        """Extract song info from table row using robust re-finding approach."""
        try:
            # Re-find the table rows
            rows = driver.find_elements(By.CSS_SELECTOR, selector)
            if row_index >= len(rows):
                return None
                
            row = rows[row_index]
            
            # Extract song title
            title = ""
            try:
                title_element = row.find_element(
                    By.CSS_SELECTOR, ".moobot-input-label-text-text"
                )
                title = title_element.text.strip()
            except:
                # Fallback to row text
                title = row.text.strip().split('\\n')[0] if row.text.strip() else ""
            
            if not title or len(title) < config.min_title_length:
                return None
            
            if config.skip_ui_text and self.song_matcher.is_ui_text(title):
                return None
                
            if config.clean_titles:
                title = self.song_matcher.clean_song_title(title)
            
            # Extract metadata
            duration = ""
            requester = ""
            status = ""
            
            if config.extract_metadata:
                try:
                    labels = row.find_elements(
                        By.CSS_SELECTOR, ".moobot-input-label-text-label"
                    )
                    for label in labels:
                        label_text = label.text.strip()
                        if ":" in label_text and len(label_text) < 10:
                            duration = label_text
                        elif label_text.startswith("By "):
                            requester = label_text
                        elif any(status_word in label_text 
                               for status_word in ["Playing", "next", "minutes"]):
                            status = label_text
                except:
                    pass
            
            # Extract YouTube URL using comprehensive approach with optimization
            youtube_url = ""
            if config.extract_youtube_urls:
                # Check if we already have URL for this song (optimization)
                existing_urls = config.get_custom_attribute("existing_youtube_urls", {})
                title_lower = title.lower()
                
                if title_lower in existing_urls:
                    youtube_url = existing_urls[title_lower]
                    self.logger.debug(f"Reused existing YouTube URL for: {title}")
                else:
                    # Only extract if we don't already have it
                    youtube_url = self._extract_youtube_url_comprehensive(
                        driver, row, title, config
                    )
            
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
    
    def _extract_youtube_url_simple(
        self, 
        row_element, 
        song_title: str, 
        config: ExtractionConfig
    ) -> str:
        """Simple YouTube URL extraction from table row."""
        try:
            if config.try_direct_links:
                link_button = row_element.find_element(
                    By.CSS_SELECTOR, "button.button-type-link"
                )
                if link_button:
                    data_url = link_button.get_attribute("data-url")
                    if data_url and ("youtube.com" in data_url or "youtu.be" in data_url):
                        return data_url
        except:
            pass
        
        # Fallback to search if configured
        if config.fallback_to_search:
            return self._search_youtube_url(song_title)
        
        return ""
    
    def _extract_youtube_url_comprehensive(
        self,
        driver: "WebDriver",
        row_element,
        song_title: str,
        config: ExtractionConfig
    ) -> str:
        """Comprehensive YouTube URL extraction with multiple methods."""
        
        # Method 1: Try direct links
        if config.try_direct_links:
            try:
                link_button = row_element.find_element(
                    By.CSS_SELECTOR, 
                    "button[class*='button-type-link'], a[href*='youtube']"
                )
                if link_button:
                    data_url = link_button.get_attribute("data-url")
                    href = link_button.get_attribute("href")
                    
                    if data_url and ("youtube.com" in data_url or "youtu.be" in data_url):
                        return data_url
                    elif href and ("youtube.com" in href or "youtu.be" in href):
                        return href
                    
                    # Try comprehensive extraction from button
                    if config.try_button_click or config.try_javascript_extraction:
                        url = self._extract_youtube_url_from_button(
                            driver, link_button, song_title, config
                        )
                        if url:
                            return url
                            
            except Exception as e:
                self.logger.debug(f"Direct link extraction failed: {e}")
        
        # Method 2: Try history thumbnails
        if config.try_history_thumbnails:
            url = self._extract_from_history_thumbnails(
                driver, song_title
            )
            if url:
                return url
        
        # Method 3: Fallback to search
        if config.fallback_to_search:
            return self._search_youtube_url(song_title)
        
        return ""
    
    def _extract_youtube_url_from_button(
        self,
        driver: "WebDriver", 
        button_element,
        song_title: str,
        config: ExtractionConfig
    ) -> str:
        """Extract YouTube URL from Moobot's external link buttons."""
        
        # Method 1: Try button click (if enabled and safe)
        if config.try_button_click:
            url = self._extract_via_button_click(driver, button_element, config)
            if url:
                return url
        
        # Method 2: Try JavaScript extraction
        if config.try_javascript_extraction:
            url = self._extract_via_javascript(driver, button_element)
            if url:
                return url
        
        # Fallback to search
        if config.fallback_to_search:
            return self._search_youtube_url(song_title)
        
        return ""
    
    def _extract_via_button_click(
        self,
        driver: "WebDriver",
        button_element,
        config: ExtractionConfig
    ) -> str:
        """Extract URL by clicking the button and capturing opened tab."""
        try:
            original_windows = driver.window_handles
            
            # Click the button to open YouTube
            driver.execute_script("arguments[0].click();", button_element)
            
            # Wait for new window
            time.sleep(2)
            
            new_windows = driver.window_handles
            if len(new_windows) > len(original_windows):
                new_window = [w for w in new_windows if w not in original_windows][0]
                driver.switch_to.window(new_window)
                
                # Minimal wait and audio control
                time.sleep(0.5)
                
                if config.mute_audio or config.pause_videos:
                    self._control_video_playback(driver, config)
                
                current_url = driver.current_url
                
                # Close new tab and return to original
                if config.close_new_tabs:
                    driver.close()
                    driver.switch_to.window(original_windows[0])
                
                if "youtube.com" in current_url or "youtu.be" in current_url:
                    self.logger.info(f"Found YouTube URL via button click: {current_url}")
                    return current_url
                    
        except Exception as e:
            self.logger.debug(f"Button click extraction failed: {e}")
            # Make sure we're back to original window
            try:
                driver.switch_to.window(driver.window_handles[0])
            except:
                pass
        
        return ""
    
    def _extract_via_javascript(
        self, 
        driver: "WebDriver",
        button_element
    ) -> str:
        """Extract URL using JavaScript to inspect button attributes."""
        try:
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
            
            result = driver.execute_script(js_code, button_element)
            
            # Check each possible URL source
            for key, value in result.items():
                if value and ("youtube.com" in str(value) or "youtu.be" in str(value)):
                    # Extract URL from the value
                    url_pattern = r'https?://(?:www\.)?(youtube\.com|youtu\.be)/[^\s"\'>\)]+'
                    urls = re.findall(url_pattern, str(value))
                    if urls:
                        found_url = f"https://{urls[0]}"
                        self.logger.debug(f"Found YouTube URL via {key}: {found_url}")
                        return found_url
                        
        except Exception as e:
            self.logger.debug(f"JavaScript extraction failed: {e}")
        
        return ""
    
    def _extract_from_history_thumbnails(
        self, 
        driver: "WebDriver",
        song_title: str
    ) -> str:
        """Extract YouTube URL from history section thumbnails."""
        try:
            history_rows = driver.find_elements(
                By.CSS_SELECTOR, "#input-content-history tbody tr"
            )
            for history_row in history_rows:
                try:
                    # Get song title from history row
                    history_title_element = history_row.find_element(
                        By.CSS_SELECTOR, ".moobot-input-label-text-text"
                    )
                    history_title = history_title_element.text.strip()
                    
                    # Check if this matches our song
                    if self.song_matcher.titles_match(song_title, history_title):
                        # Look for YouTube thumbnail
                        img_element = history_row.find_element(
                            By.CSS_SELECTOR, "img[src*='youtube.com']"
                        )
                        img_src = img_element.get_attribute("src")
                        
                        # Extract video ID from thumbnail URL
                        video_id_match = re.search(r'/vi/([^/]+)/', img_src)
                        if video_id_match:
                            video_id = video_id_match.group(1)
                            youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                            self.logger.info(
                                f"Found YouTube URL via history thumbnail: {youtube_url} "
                                f"for song: {song_title}"
                            )
                            return youtube_url
                            
                except Exception:
                    continue
                    
        except Exception as e:
            self.logger.debug(f"History thumbnail method failed: {e}")
        
        return ""
    
    def _control_video_playback(
        self,
        driver: "WebDriver", 
        config: ExtractionConfig
    ):
        """Control video playback to prevent audio."""
        try:
            js_code = """
            // Pause any YouTube videos that might be playing
            var videos = document.querySelectorAll('video');
            for (var i = 0; i < videos.length; i++) {
                if (arguments[0]) videos[i].pause();  // pause_videos
                if (arguments[1]) {  // mute_audio
                    videos[i].muted = true;
                    videos[i].volume = 0;
                }
            }
            """
            driver.execute_script(js_code, config.pause_videos, config.mute_audio)
        except:
            pass  # Ignore JavaScript errors
    
    def _search_youtube_url(self, song_title: str) -> str:
        """Generate a YouTube search URL for the song title."""
        try:
            search_query = song_title.strip()
            
            # Remove common suffixes that might not be in YouTube titles
            suffixes_to_remove = [
                ' (Official Video)', ' (Official Audio)', ' (Official)', 
                ' (Lyrics)', ' M/V'
            ]
            for suffix in suffixes_to_remove:
                if search_query.endswith(suffix):
                    search_query = search_query[:-len(suffix)].strip()
                    break
            
            encoded_query = urllib.parse.quote_plus(search_query)
            return f"https://www.youtube.com/results?search_query={encoded_query}"
            
        except Exception as e:
            self.logger.debug(f"Error generating YouTube search URL: {e}")
            return ""