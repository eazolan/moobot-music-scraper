"""Base extraction strategy interface for song extraction domain."""

from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING
import logging

from ..entities import ExtractionResult, ExtractionConfig, ElementSelector

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver


class ExtractionStrategy(ABC):
    """Abstract base class for song extraction strategies.
    
    Defines the contract that all extraction strategy implementations
    must follow, ensuring consistent behavior across different
    extraction approaches.
    """
    
    def __init__(self, name: str, logger: Optional[logging.Logger] = None):
        """Initialize the extraction strategy.
        
        Args:
            name: Unique name for this strategy
            logger: Logger instance for this strategy
        """
        self.name = name
        self.logger = logger or logging.getLogger(f"extraction.{name}")
    
    @abstractmethod
    def can_handle(self, selector: ElementSelector) -> bool:
        """Check if this strategy can handle the given selector.
        
        Args:
            selector: Element selector to evaluate
            
        Returns:
            True if this strategy can handle the selector
        """
        pass
    
    @abstractmethod
    def extract_songs(
        self, 
        driver: "WebDriver",
        selector: ElementSelector, 
        config: ExtractionConfig
    ) -> ExtractionResult:
        """Extract songs using this strategy.
        
        Args:
            driver: Selenium WebDriver instance
            selector: Element selector for finding elements
            config: Configuration for extraction behavior
            
        Returns:
            ExtractionResult with found songs and metadata
        """
        pass
    
    @property
    def strategy_name(self) -> str:
        """Get the name of this strategy."""
        return self.name
    
    def get_priority(self) -> int:
        """Get the priority of this strategy (higher = more preferred).
        
        Returns:
            Priority value (default: 1)
        """
        return 1
    
    def supports_robust_extraction(self) -> bool:
        """Check if this strategy supports robust extraction.
        
        Returns:
            True if robust extraction is supported
        """
        return False
    
    def validate_config(self, config: ExtractionConfig) -> bool:
        """Validate that the configuration is compatible with this strategy.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if configuration is valid
        """
        return True
    
    def __str__(self) -> str:
        """String representation of the strategy."""
        return f"{self.__class__.__name__}({self.name})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the strategy."""
        return self.__str__()