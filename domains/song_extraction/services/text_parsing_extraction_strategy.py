"""Text parsing extraction strategy for fallback song extraction from raw text."""

from datetime import datetime
from typing import List, Optional, Set, TYPE_CHECKING
from selenium.webdriver.common.by import By

from .extraction_strategy import ExtractionStrategy
from ..entities import ExtractionResult, ExtractionConfig, ElementSelector
from domains.music_queue.entities import SongRequest
from domains.music_queue.services import SongMatchingService

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver


class TextParsingExtractionStrategy(ExtractionStrategy):
    """Strategy for extracting songs from raw text content.
    
    This is a fallback strategy that attempts to parse song titles
    from page text when other extraction methods fail or are insufficient.
    """
    
    def __init__(self):
        super().__init__("text_parsing")
        self.song_matcher = SongMatchingService()
    
    def can_handle(self, selector: ElementSelector) -> bool:
        """This strategy can handle any selector as a fallback."""
        return selector.is_fallback or selector.priority <= 2
    
    def get_priority(self) -> int:
        """Lowest priority - this is a fallback strategy."""
        return 1
    
    def supports_robust_extraction(self) -> bool:
        """Text parsing doesn't need robust element finding."""
        return False
    
    def extract_songs(
        self,
        driver: "WebDriver",
        selector: ElementSelector,
        config: ExtractionConfig
    ) -> ExtractionResult:
        """Extract songs from page text content."""
        try:
            return self._extract_songs_from_text(driver, selector, config)
                
        except Exception as e:
            self.logger.error(f"Error in text parsing extraction: {e}")
            return ExtractionResult.create_failure(
                error_message=str(e),
                strategy_used=self.name,
                selector_used=selector.selector
            )
    
    def _extract_songs_from_text(
        self,
        driver: "WebDriver",
        selector: ElementSelector,
        config: ExtractionConfig
    ) -> ExtractionResult:
        """Extract songs by parsing text content."""
        songs = []
        current_time = datetime.now()
        
        try:
            # Get page text content
            if selector.selector == "body" or selector.selector == "*":
                # Get all page text
                page_text = driver.find_element(By.TAG_NAME, "body").text
            else:
                # Get text from specific elements
                elements = driver.find_elements(By.CSS_SELECTOR, selector.selector)
                page_text = "\n".join([elem.text for elem in elements if elem.text.strip()])
            
            element_count = 1  # We're processing the combined text as one unit
            
            # Parse songs from the text
            song_dicts = self._parse_text_for_songs(page_text, config, current_time)
            
            # Convert to SongRequest objects
            for song_dict in song_dicts:
                try:
                    song_request = SongRequest.from_dict(song_dict)
                    songs.append(song_request)
                    
                    # Apply limit if configured
                    if (config.max_songs_per_strategy and 
                        len(songs) >= config.max_songs_per_strategy):
                        break
                        
                except ValueError as e:
                    self.logger.warning(f"Invalid song data from text parsing: {e}")
                    continue
            
            result = ExtractionResult.create_success(
                songs=songs,
                strategy_used=self.name,
                selector_used=selector.selector,
                element_count=element_count
            )
            
            # Add metadata about text processing
            result.add_metadata("text_length", len(page_text))
            result.add_metadata("lines_processed", len(page_text.split('\n')))
            
            return result
            
        except Exception as e:
            return ExtractionResult.create_failure(
                error_message=str(e),
                strategy_used=self.name,
                selector_used=selector.selector
            )
    
    def _parse_text_for_songs(
        self, 
        text: str, 
        config: ExtractionConfig,
        current_time: datetime
    ) -> List[dict]:
        """Parse songs from page text content."""
        songs = []
        
        if not text or len(text.strip()) == 0:
            return songs
        
        lines = text.split('\n')
        seen_titles: Set[str] = set()
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            
            # Apply basic filtering
            if not self._is_potential_song_line(line, config):
                continue
            
            # Clean the line if configured
            if config.clean_titles:
                clean_line = self.song_matcher.clean_song_title(line)
            else:
                clean_line = line
            
            # Apply length and content filters
            if len(clean_line) < config.min_title_length:
                continue
                
            if len(clean_line) > config.max_title_length:
                continue
                
            if config.skip_ui_text and self.song_matcher.is_ui_text(clean_line):
                continue
            
            # Avoid duplicates
            clean_lower = clean_line.lower()
            if clean_lower in seen_titles:
                continue
            
            seen_titles.add(clean_lower)
            
            song_info = {
                "title": clean_line,
                "youtube_url": "",  # Text parsing doesn't extract URLs
                "timestamp": current_time.isoformat(),
                "scraped_at": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "selector_used": "text_parsing",
                "element_index": line_num,
                "metadata": {
                    "source_line": line_num + 1,
                    "original_text": line
                }
            }
            songs.append(song_info)
            
            # Limit results to prevent too many false positives
            if len(songs) >= 50:  # Reasonable default limit
                break
        
        return songs
    
    def _is_potential_song_line(self, line: str, config: ExtractionConfig) -> bool:
        """Check if a line of text might be a song title."""
        if not line or len(line.strip()) < config.min_title_length:
            return False
        
        # Skip lines that are clearly not songs
        skip_patterns = [
            # URLs and technical content
            lambda l: l.startswith(('http', 'www', 'ftp')),
            
            # UI elements and navigation
            lambda l: any(ui_word in l.lower() for ui_word in [
                'click', 'toggle', 'menu', 'button', 'login', 'sign up',
                'home', 'about', 'contact', 'help', 'settings'
            ]),
            
            # Very short lines (likely not song titles)
            lambda l: len(l.strip()) < 5,
            
            # Lines with lots of numbers/special chars (likely not songs)
            lambda l: sum(c.isdigit() or not c.isalnum() and c != ' ' for c in l) > len(l) // 2,
            
            # Common non-song phrases
            lambda l: l.lower().strip() in [
                'loading', 'please wait', 'error', 'not found', 
                'no results', 'empty', 'none', 'null'
            ],
            
            # Very repetitive content
            lambda l: len(set(l.lower().split())) < max(1, len(l.split()) // 3)
        ]
        
        return not any(pattern(line) for pattern in skip_patterns)
    
    def validate_config(self, config: ExtractionConfig) -> bool:
        """Validate configuration for text parsing extraction."""
        # Text parsing works better with stricter filtering
        if config.min_title_length < 5:
            self.logger.info(
                "Text parsing strategy works better with min_title_length >= 5"
            )
        
        if not config.skip_ui_text:
            self.logger.info(
                "Text parsing strategy works better with skip_ui_text=True"
            )
        
        return True