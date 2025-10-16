"""Extraction coordinator service that manages multiple extraction strategies."""

import logging
from typing import List, Dict, Optional, TYPE_CHECKING
from collections import defaultdict

from .extraction_strategy import ExtractionStrategy
from .table_row_extraction_strategy import TableRowExtractionStrategy
from .general_element_extraction_strategy import GeneralElementExtractionStrategy
from .youtube_link_extraction_strategy import YouTubeLinkExtractionStrategy
from .text_parsing_extraction_strategy import TextParsingExtractionStrategy

from ..entities import ExtractionResult, ExtractionConfig, ElementSelector
from domains.music_queue.entities import SongRequest
from domains.music_queue.services import SongMatchingService

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver


class ExtractionCoordinator:
    """Coordinates multiple extraction strategies to comprehensively extract songs.
    
    This service manages different extraction strategies, combines their results,
    handles deduplication, and provides a unified interface for song extraction.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the extraction coordinator.
        
        Args:
            logger: Logger instance for the coordinator
        """
        self.logger = logger or logging.getLogger("extraction.coordinator")
        self.song_matcher = SongMatchingService()
        
        # Initialize extraction strategies
        self.strategies: List[ExtractionStrategy] = [
            TableRowExtractionStrategy(),
            YouTubeLinkExtractionStrategy(), 
            GeneralElementExtractionStrategy(),
            TextParsingExtractionStrategy()
        ]
        
        # Sort strategies by priority (highest first)
        self.strategies.sort(key=lambda s: s.get_priority(), reverse=True)
        
        self.logger.info(f"Initialized {len(self.strategies)} extraction strategies")
    
    def extract_songs_comprehensive(
        self,
        driver: "WebDriver",
        selectors: List[ElementSelector],
        config: ExtractionConfig
    ) -> List[ExtractionResult]:
        """Extract songs using multiple strategies across multiple selectors.
        
        Args:
            driver: Selenium WebDriver instance
            selectors: List of element selectors to try
            config: Configuration for extraction behavior
            
        Returns:
            List of ExtractionResult objects from each strategy/selector combination
        """
        all_results = []
        
        # Sort selectors by priority (highest first)
        sorted_selectors = sorted(selectors, key=lambda s: s.priority, reverse=True)
        
        for selector in sorted_selectors:
            self.logger.debug(f"Processing selector: {selector.selector}")
            
            # Find strategies that can handle this selector
            compatible_strategies = [
                strategy for strategy in self.strategies
                if strategy.can_handle(selector) and strategy.validate_config(config)
            ]
            
            if not compatible_strategies:
                self.logger.warning(f"No strategies can handle selector: {selector.selector}")
                continue
            
            # Execute each compatible strategy
            for strategy in compatible_strategies:
                try:
                    result = strategy.extract_songs(driver, selector, config)
                    all_results.append(result)
                    
                    self.logger.info(
                        f"{strategy.name} found {result.song_count} songs "
                        f"with selector '{selector.selector}'"
                    )
                    
                except Exception as e:
                    self.logger.error(f"Strategy {strategy.name} failed: {e}")
                    # Create failure result for tracking
                    failure_result = ExtractionResult.create_failure(
                        error_message=str(e),
                        strategy_used=strategy.name,
                        selector_used=selector.selector
                    )
                    all_results.append(failure_result)
        
        return all_results
    
    def extract_songs_deduplicated(
        self,
        driver: "WebDriver",
        selectors: List[ElementSelector],
        config: ExtractionConfig
    ) -> ExtractionResult:
        """Extract songs with deduplication across all strategies.
        
        Args:
            driver: Selenium WebDriver instance
            selectors: List of element selectors to try
            config: Configuration for extraction behavior
            
        Returns:
            Single ExtractionResult with deduplicated songs from all strategies
        """
        # Get all results
        all_results = self.extract_songs_comprehensive(driver, selectors, config)
        
        # Combine and deduplicate songs
        combined_songs = self._combine_and_deduplicate_songs(all_results)
        
        # Create summary result
        total_elements = sum(result.element_count for result in all_results)
        strategies_used = list(set(result.strategy_used for result in all_results))
        selectors_used = list(set(result.selector_used for result in all_results))
        
        result = ExtractionResult.create_success(
            songs=combined_songs,
            strategy_used=f"coordinator({','.join(strategies_used)})",
            selector_used=f"multiple({','.join(selectors_used)})",
            element_count=total_elements
        )
        
        # Add metadata about the coordination process
        result.add_metadata("total_results", len(all_results))
        result.add_metadata("successful_results", len([r for r in all_results if r.success]))
        result.add_metadata("failed_results", len([r for r in all_results if not r.success]))
        result.add_metadata("strategies_used", strategies_used)
        result.add_metadata("selectors_used", selectors_used)
        result.add_metadata("deduplication_enabled", True)
        
        # Collect warnings from all results
        for individual_result in all_results:
            for warning in individual_result.warnings:
                result.add_warning(f"{individual_result.strategy_used}: {warning}")
        
        self.logger.info(
            f"Coordinator extracted {len(combined_songs)} unique songs "
            f"from {len(all_results)} strategy executions"
        )
        
        return result
    
    def extract_songs_optimized(
        self,
        driver: "WebDriver",
        selectors: List[ElementSelector],
        config: ExtractionConfig,
        existing_songs_with_urls: Dict[str, str] = None
    ) -> ExtractionResult:
        """Extract songs with optimization to skip YouTube extraction for existing songs.
        
        Args:
            driver: Selenium WebDriver instance
            selectors: List of element selectors to try
            config: Configuration for extraction behavior
            existing_songs_with_urls: Dict mapping song titles (lowercase) to YouTube URLs
            
        Returns:
            Single ExtractionResult with optimized extraction
        """
        if existing_songs_with_urls is None:
            existing_songs_with_urls = {}
        
        # Store existing URLs in config for strategies to use
        config.set_custom_attribute("existing_youtube_urls", existing_songs_with_urls)
        config.set_custom_attribute("skip_existing_urls", True)
        
        self.logger.info(f"Optimization: Found {len(existing_songs_with_urls)} existing songs with URLs")
        
        # Use the standard deduplicated extraction but with optimization context
        result = self.extract_songs_deduplicated(driver, selectors, config)
        
        # Count how many URLs were reused vs newly extracted
        urls_reused = 0
        urls_extracted = 0
        
        for song in result.songs:
            if song.youtube_url:
                title_lower = song.title.lower()
                if title_lower in existing_songs_with_urls and song.youtube_url == existing_songs_with_urls[title_lower]:
                    urls_reused += 1
                else:
                    urls_extracted += 1
        
        if urls_reused > 0:
            self.logger.info(f"Optimization results: {urls_reused} URLs reused, {urls_extracted} URLs newly extracted")
        
        return result
    
    def extract_songs_best_effort(
        self,
        driver: "WebDriver",
        selectors: List[ElementSelector],
        config: ExtractionConfig
    ) -> ExtractionResult:
        """Extract songs using best-effort approach.
        
        Tries strategies in priority order until sufficient songs are found
        or all strategies are exhausted.
        
        Args:
            driver: Selenium WebDriver instance
            selectors: List of element selectors to try
            config: Configuration for extraction behavior
            
        Returns:
            ExtractionResult from the best performing strategy
        """
        best_result = None
        min_songs = config.get_custom_attribute("min_songs_for_success", 1)
        
        # Sort selectors by priority (highest first)
        sorted_selectors = sorted(selectors, key=lambda s: s.priority, reverse=True)
        
        for selector in sorted_selectors:
            # Find strategies that can handle this selector
            compatible_strategies = [
                strategy for strategy in self.strategies
                if strategy.can_handle(selector) and strategy.validate_config(config)
            ]
            
            for strategy in compatible_strategies:
                try:
                    result = strategy.extract_songs(driver, selector, config)
                    
                    # Update best result if this one is better
                    if self._is_better_result(result, best_result):
                        best_result = result
                        
                        self.logger.info(
                            f"New best result: {strategy.name} found {result.song_count} songs"
                        )
                    
                    # Stop if we have enough songs
                    if result.success and result.song_count >= min_songs:
                        self.logger.info(f"Sufficient songs found, stopping search")
                        break
                        
                except Exception as e:
                    self.logger.error(f"Strategy {strategy.name} failed: {e}")
                    continue
            
            # Stop if we have a good result
            if best_result and best_result.success and best_result.song_count >= min_songs:
                break
        
        # Return best result or create failure if nothing worked
        if best_result is None:
            return ExtractionResult.create_failure(
                error_message="No extraction strategies produced results",
                strategy_used="coordinator",
                selector_used="multiple"
            )
        
        return best_result
    
    def _combine_and_deduplicate_songs(self, results: List[ExtractionResult]) -> List[SongRequest]:
        """Combine songs from multiple results and remove duplicates.
        
        Args:
            results: List of extraction results to combine
            
        Returns:
            List of unique SongRequest objects
        """
        all_songs = []
        seen_titles = set()
        
        # Collect all successful results
        successful_results = [result for result in results if result.success]
        
        # Sort by strategy priority (table rows first, then YouTube links, etc.)
        strategy_priority = {
            "table_row": 10,
            "youtube_link": 8,
            "general_element": 5,
            "text_parsing": 1
        }
        
        successful_results.sort(
            key=lambda r: strategy_priority.get(r.strategy_used, 0),
            reverse=True
        )
        
        for result in successful_results:
            for song in result.songs:
                # Use song matching service to check for duplicates
                is_duplicate = any(
                    self.song_matcher.songs_match(song, existing_song)
                    for existing_song in all_songs
                )
                
                if not is_duplicate:
                    all_songs.append(song)
                    seen_titles.add(song.title.lower())
                    
                    self.logger.debug(f"Added unique song: {song.title}")
                else:
                    self.logger.debug(f"Skipped duplicate song: {song.title}")
        
        return all_songs
    
    def _is_better_result(self, new_result: ExtractionResult, current_best: Optional[ExtractionResult]) -> bool:
        """Determine if a new result is better than the current best.
        
        Args:
            new_result: New extraction result to evaluate
            current_best: Current best result (may be None)
            
        Returns:
            True if new result is better
        """
        if current_best is None:
            return new_result.success
        
        if not current_best.success and new_result.success:
            return True
        
        if not new_result.success:
            return False
        
        # Both are successful, compare by song count and strategy priority
        if new_result.song_count > current_best.song_count:
            return True
        
        if new_result.song_count == current_best.song_count:
            # Same song count, prefer higher priority strategy
            strategy_priority = {
                "table_row": 10,
                "youtube_link": 8,
                "general_element": 5,
                "text_parsing": 1
            }
            
            new_priority = strategy_priority.get(new_result.strategy_used, 0)
            current_priority = strategy_priority.get(current_best.strategy_used, 0)
            
            return new_priority > current_priority
        
        return False
    
    def get_available_strategies(self) -> List[str]:
        """Get list of available strategy names."""
        return [strategy.name for strategy in self.strategies]
    
    def get_strategy_by_name(self, name: str) -> Optional[ExtractionStrategy]:
        """Get a specific strategy by name."""
        for strategy in self.strategies:
            if strategy.name == name:
                return strategy
        return None
    
    def create_default_selectors(self) -> List[ElementSelector]:
        """Create a default set of selectors for common use cases."""
        return [
            ElementSelector.create_table_row(priority=10),
            ElementSelector.create_youtube_links(priority=8),
            ElementSelector.create_song_titles(priority=5),
            ElementSelector.create_generic_links(priority=3),
            ElementSelector.create_text_elements(priority=1)
        ]