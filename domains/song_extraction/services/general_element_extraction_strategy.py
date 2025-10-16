"""General element extraction strategy for non-table web elements."""

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from selenium.webdriver.common.by import By

from .extraction_strategy import ExtractionStrategy
from ..entities import ExtractionResult, ExtractionConfig, ElementSelector
from domains.music_queue.entities import SongRequest
from domains.music_queue.services import SongMatchingService

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver


class GeneralElementExtractionStrategy(ExtractionStrategy):
    """Strategy for extracting songs from general web elements.
    
    Handles extraction from non-table elements like divs, spans, links, etc.
    This is used for general content areas and fallback scenarios.
    """
    
    def __init__(self):
        super().__init__("general_element")
        self.song_matcher = SongMatchingService()
    
    def can_handle(self, selector: ElementSelector) -> bool:
        """Check if this strategy can handle general element selectors."""
        # This strategy handles everything that's not specifically table rows or YouTube links
        return not selector.is_table_row_selector and not selector.is_youtube_link_selector
    
    def get_priority(self) -> int:
        """Medium priority for general element extraction."""
        return 5
    
    def supports_robust_extraction(self) -> bool:
        """This strategy supports robust re-finding of elements."""
        return True
    
    def extract_songs(
        self,
        driver: "WebDriver",
        selector: ElementSelector,
        config: ExtractionConfig
    ) -> ExtractionResult:
        """Extract songs from general web elements."""
        try:
            if config.use_robust_finding:
                return self._extract_songs_robust(driver, selector, config)
            else:
                return self._extract_songs_simple(driver, selector, config)
                
        except Exception as e:
            self.logger.error(f"Error in general element extraction: {e}")
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
                    song_info = self._extract_from_element(
                        element, i, current_time, selector.selector, config
                    )
                    if song_info:
                        song_request = SongRequest.from_dict(song_info)
                        songs.append(song_request)
                        
                        # Apply limit if configured
                        if (config.max_songs_per_strategy and 
                            len(songs) >= config.max_songs_per_strategy):
                            break
                        
                except ValueError as e:
                    self.logger.warning(f"Invalid song data from element {i}: {e}")
                    continue
                except Exception as e:
                    self.logger.warning(f"Error extracting from element {i}: {e}")
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
                    song_info = self._extract_from_element_robust(
                        driver, selector.selector, i, current_time, config
                    )
                    if song_info:
                        song_request = SongRequest.from_dict(song_info)
                        songs.append(song_request)
                        
                        # Apply limit if configured
                        if (config.max_songs_per_strategy and 
                            len(songs) >= config.max_songs_per_strategy):
                            break
                        
                except ValueError as e:
                    self.logger.warning(f"Invalid song data from element {i}: {e}")
                    continue
                except Exception as e:
                    self.logger.debug(f"Error extracting from element {i}: {e}")
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
    
    def _extract_from_element(
        self,
        element,
        index: int,
        current_time: datetime,
        selector_used: str,
        config: ExtractionConfig
    ) -> Optional[dict]:
        """Extract song info from a general web element."""
        try:
            # Get all text content
            element_text = element.text.strip()
            
            # Skip empty or very short elements
            if config.skip_empty_elements and len(element_text) < config.min_title_length:
                return None
            
            # Look for YouTube links within the element
            youtube_url = ""
            if config.extract_youtube_urls:
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
                    link_element = element.find_element(
                        By.XPATH, f".//a[@href='{youtube_url}']"
                    )
                    title = link_element.text.strip()
                except:
                    pass
            
            if not title:
                title = element_text
            
            # Clean up the title if configured
            if config.clean_titles:
                title = self.song_matcher.clean_song_title(title)
            
            # Apply filtering
            if len(title) < config.min_title_length:
                return None
                
            if len(title) > config.max_title_length:
                return None
                
            if config.skip_ui_text and self.song_matcher.is_ui_text(title):
                return None
            
            return {
                "title": title,
                "youtube_url": youtube_url,
                "timestamp": current_time.isoformat(),
                "scraped_at": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "selector_used": selector_used,
                "element_index": index
            }
            
        except Exception as e:
            self.logger.debug(f"Error extracting from element {index}: {e}")
            return None
    
    def _extract_from_element_robust(
        self,
        driver: "WebDriver",
        selector: str,
        element_index: int,
        current_time: datetime,
        config: ExtractionConfig
    ) -> Optional[dict]:
        """Extract song info from element using robust re-finding approach."""
        try:
            # Re-find the specific element by index each time
            current_elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if element_index >= len(current_elements):
                return None
                
            element = current_elements[element_index]
            
            # General extraction for other selectors
            element_text = element.text.strip()
            if config.skip_empty_elements and len(element_text) < config.min_title_length:
                return None
            
            # Look for YouTube links
            youtube_url = ""
            if config.extract_youtube_urls:
                try:
                    links = element.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        href = link.get_attribute("href")
                        if href and ("youtube.com" in href or "youtu.be" in href):
                            youtube_url = href
                            break
                except:
                    pass
            
            # Extract and clean title
            title = element_text
            if config.clean_titles:
                title = self.song_matcher.clean_song_title(title)
            
            # Apply filtering
            if len(title) < config.min_title_length:
                return None
                
            if len(title) > config.max_title_length:
                return None
                
            if config.skip_ui_text and self.song_matcher.is_ui_text(title):
                return None
            
            return {
                "title": title,
                "youtube_url": youtube_url,
                "timestamp": current_time.isoformat(),
                "scraped_at": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "selector_used": selector,
                "element_index": element_index
            }
            
        except Exception as e:
            self.logger.debug(f"Error extracting from element {element_index} with {selector}: {e}")
            return None