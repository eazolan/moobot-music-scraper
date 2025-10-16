"""YouTube link extraction strategy for finding songs via YouTube links."""

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from selenium.webdriver.common.by import By

from .extraction_strategy import ExtractionStrategy
from ..entities import ExtractionResult, ExtractionConfig, ElementSelector
from domains.music_queue.entities import SongRequest
from domains.music_queue.services import SongMatchingService

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver


class YouTubeLinkExtractionStrategy(ExtractionStrategy):
    """Strategy for extracting songs specifically from YouTube links.
    
    Focuses on finding and extracting information from direct YouTube links
    on the page, either as standalone links or embedded in other elements.
    """
    
    def __init__(self):
        super().__init__("youtube_link")
        self.song_matcher = SongMatchingService()
    
    def can_handle(self, selector: ElementSelector) -> bool:
        """Check if this strategy can handle YouTube link selectors."""
        return selector.is_youtube_link_selector
    
    def get_priority(self) -> int:
        """High priority for YouTube link extraction."""
        return 8
    
    def supports_robust_extraction(self) -> bool:
        """This strategy supports robust re-finding of elements."""
        return True
    
    def extract_songs(
        self,
        driver: "WebDriver",
        selector: ElementSelector,
        config: ExtractionConfig
    ) -> ExtractionResult:
        """Extract songs from YouTube links."""
        try:
            return self._extract_songs_from_links(driver, selector, config)
                
        except Exception as e:
            self.logger.error(f"Error in YouTube link extraction: {e}")
            return ExtractionResult.create_failure(
                error_message=str(e),
                strategy_used=self.name,
                selector_used=selector.selector
            )
    
    def _extract_songs_from_links(
        self,
        driver: "WebDriver",
        selector: ElementSelector,
        config: ExtractionConfig
    ) -> ExtractionResult:
        """Extract songs from YouTube links found on the page."""
        songs = []
        current_time = datetime.now()
        
        try:
            # Find YouTube links using the selector
            youtube_links = driver.find_elements(By.CSS_SELECTOR, selector.selector)
            element_count = len(youtube_links)
            
            for i, link in enumerate(youtube_links):
                try:
                    song_info = self._extract_from_youtube_link(
                        link, i, current_time, selector.selector, config
                    )
                    if song_info:
                        song_request = SongRequest.from_dict(song_info)
                        songs.append(song_request)
                        
                        # Apply limit if configured
                        if (config.max_songs_per_strategy and 
                            len(songs) >= config.max_songs_per_strategy):
                            break
                        
                except ValueError as e:
                    self.logger.warning(f"Invalid song data from YouTube link {i}: {e}")
                    continue
                except Exception as e:
                    self.logger.warning(f"Error extracting from YouTube link {i}: {e}")
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
    
    def _extract_from_youtube_link(
        self,
        link_element,
        index: int,
        current_time: datetime,
        selector_used: str,
        config: ExtractionConfig
    ) -> Optional[dict]:
        """Extract song info from a YouTube link element."""
        try:
            href = link_element.get_attribute("href")
            if not href or not ("youtube.com" in href or "youtu.be" in href):
                return None
            
            title = link_element.text.strip()
            
            # If link text is empty or just URL, try to get title from parent element
            if not title or href in title:
                try:
                    parent = link_element.find_element(By.XPATH, "..")
                    title = parent.text.strip()
                    # Remove the URL from the title if it's there
                    if href in title:
                        title = title.replace(href, "").strip()
                except:
                    title = "Unknown Song"
            
            # Clean title if configured
            if config.clean_titles:
                title = self.song_matcher.clean_song_title(title)
            
            # Apply filtering
            if len(title) < config.min_title_length:
                return None
                
            if len(title) > config.max_title_length:
                return None
                
            if config.skip_ui_text and self.song_matcher.is_ui_text(title):
                return None
            
            # Extract additional metadata from the link if available
            video_id = self._extract_video_id(href)
            metadata = {}
            if video_id:
                metadata["video_id"] = video_id
            
            return {
                "title": title,
                "youtube_url": href,
                "timestamp": current_time.isoformat(),
                "scraped_at": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "selector_used": selector_used,
                "element_index": index,
                "metadata": metadata
            }
            
        except Exception as e:
            self.logger.debug(f"Error extracting from YouTube link {index}: {e}")
            return None
    
    def _extract_video_id(self, youtube_url: str) -> Optional[str]:
        """Extract YouTube video ID from URL."""
        try:
            import re
            
            # Handle different YouTube URL formats
            patterns = [
                r'(?:youtube\.com/watch\?v=)([^&\n?#]+)',
                r'(?:youtu\.be/)([^&\n?#]+)',
                r'(?:youtube\.com/embed/)([^&\n?#]+)',
                r'(?:youtube\.com/v/)([^&\n?#]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, youtube_url)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error extracting video ID from {youtube_url}: {e}")
            return None
    
    def validate_config(self, config: ExtractionConfig) -> bool:
        """Validate configuration for YouTube link extraction."""
        # YouTube link strategy works best with URL extraction enabled
        if not config.extract_youtube_urls:
            self.logger.warning(
                "YouTube link extraction strategy works best with "
                "extract_youtube_urls=True"
            )
        
        return True