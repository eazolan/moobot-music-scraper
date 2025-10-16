# Domain-Driven Design Refactoring Plan

## Current State Analysis

The `MoobotScraper` class has **32 methods** spanning multiple domains. Here's the domain breakdown:

### Method Classification by Domain

**Music Queue Domain** (6 methods):
- `clean_song_title()` - Song title normalization
- `is_ui_text()` - Content validation
- `songs_match()` - Song comparison logic
- `update_songs_data()` - Queue state management
- `extract_from_table_row()` - Queue item parsing
- `extract_from_table_row_robust()` - Enhanced queue parsing

**Web Extraction Domain** (12 methods):
- `setup_webdriver()` - Browser configuration
- `scrape_songs()` - Main extraction orchestration
- `extract_song_info()` - Generic element extraction
- `extract_song_info_robust()` - Resilient extraction
- `extract_youtube_url_from_button()` - YouTube link extraction
- `extract_from_youtube_links()` - Link-based extraction
- `parse_text_for_songs()` - Fallback text parsing
- `verify_streamer_exists()` - Page validation
- `search_youtube_url()` - Search URL generation
- `cleanup()` - Browser cleanup

**Content Publishing Domain** (3 methods):
- `generate_html()` - HTML orchestration
- `create_html_page()` - Page generation
- `generate_index_page()` - Index creation

**Stream Monitoring Domain** (6 methods):
- `setup_signal_handlers()` - Graceful shutdown setup
- `signal_handler()` - Signal processing
- `run_scan()` - Single scan execution
- `run_forever()` - Continuous monitoring
- `safe_log()` - Unicode-safe logging

**Infrastructure** (5 methods):
- `setup_logging()` - Logging configuration
- `setup_directories()` - File system setup
- `load_existing_data()` - JSON loading
- `save_data()` - JSON persistence
- `__init__()` - System initialization

---

## Domain Models

### 1. Music Queue Domain

**Core Entity:**
```python
@dataclass
class SongRequest:
    title: str
    duration: Optional[str] = None
    requester: Optional[str] = None
    status: Optional[str] = None
    youtube_url: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    scraped_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
```

**Value Objects:**
```python
@dataclass(frozen=True)
class StreamerId:
    name: str
    
    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Streamer name cannot be empty")

@dataclass(frozen=True)
class QueuePosition:
    index: int
    status: str  # "playing", "next", "queued"
```

**Domain Services:**
```python
class SongMatchingService:
    def songs_match(self, song1: SongRequest, song2: SongRequest) -> bool
    def normalize_title(self, title: str) -> str
    def is_ui_text(self, text: str) -> bool

class QueueRepository:
    def save_daily_queue(self, date: date, songs: List[SongRequest])
    def load_daily_queue(self, date: date) -> List[SongRequest]
    def get_all_dates(self) -> List[date]
```

### 2. Web Extraction Domain

**Core Entity:**
```python
@dataclass
class ExtractionSession:
    streamer_id: StreamerId
    browser: WebDriver
    strategies: List[ExtractionStrategy]
    debug_artifacts: Dict[str, Any] = field(default_factory=dict)
```

**Value Objects:**
```python
@dataclass(frozen=True)
class ExtractionResult:
    songs: List[SongRequest]
    success: bool
    strategy_used: str
    debug_info: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class YouTubeUrl:
    url: str
    
    def __post_init__(self):
        if not ("youtube.com" in self.url or "youtu.be" in self.url):
            raise ValueError("Invalid YouTube URL")
```

**Domain Services:**
```python
class WebDriverManager:
    def setup_chrome_driver(self) -> WebDriver
    def cleanup_driver(self, driver: WebDriver)

class ExtractionStrategyFactory:
    def get_strategies(self) -> List[ExtractionStrategy]

class ExtractionStrategy(ABC):
    @abstractmethod
    def extract(self, session: ExtractionSession) -> ExtractionResult
```

### 3. Content Publishing Domain

**Core Entity:**
```python
@dataclass
class SongCollection:
    date: date
    songs: List[SongRequest]
    streamer_id: StreamerId
```

**Value Objects:**
```python
@dataclass(frozen=True)
class HtmlPage:
    content: str
    title: str
    file_path: Path

@dataclass(frozen=True)
class PublishingConfig:
    output_dir: Path
    template_style: str
    streamer_name: str
```

**Domain Services:**
```python
class HtmlGenerator:
    def generate_daily_page(self, collection: SongCollection) -> HtmlPage
    def generate_index_page(self, collections: List[SongCollection]) -> HtmlPage

class ContentPublisher:
    def publish_page(self, page: HtmlPage)
    def publish_all(self, collections: List[SongCollection])
```

### 4. Stream Monitoring Domain

**Core Entity:**
```python
@dataclass
class MonitoringSession:
    streamer_id: StreamerId
    scan_interval: int
    shutdown_requested: bool = False
    start_time: datetime = field(default_factory=datetime.now)
```

**Value Objects:**
```python
@dataclass(frozen=True)
class ScanResult:
    songs_found: int
    success: bool
    timestamp: datetime
    error_message: Optional[str] = None

@dataclass(frozen=True)
class MonitoringConfig:
    scan_interval_seconds: int
    max_retries: int
    graceful_shutdown_timeout: int
```

**Domain Services:**
```python
class GracefulShutdownHandler:
    def setup_signal_handlers(self, callback: Callable)
    def request_shutdown(self)

class ScanScheduler:
    def schedule_scans(self, interval: int, callback: Callable)
    def run_until_shutdown(self, shutdown_flag: Callable[[], bool])
```

---

## Domain Interfaces & Contracts

### Cross-Domain Interfaces

```python
# Music Queue → Content Publishing
class QueueDataProvider(Protocol):
    def get_collections_for_publishing(self) -> List[SongCollection]

# Web Extraction → Music Queue
class SongExtractor(Protocol):
    def extract_songs(self, streamer_id: StreamerId) -> List[SongRequest]

# Stream Monitoring → All Domains
class ScanOrchestrator(Protocol):
    def perform_scan(self) -> ScanResult
```

### External Dependencies

```python
# Infrastructure abstractions
class Logger(Protocol):
    def info(self, message: str): ...
    def warning(self, message: str): ...
    def error(self, message: str): ...

class FileSystem(Protocol):
    def write_file(self, path: Path, content: str): ...
    def read_file(self, path: Path) -> str: ...
    def create_directory(self, path: Path): ...

class WebDriver(Protocol):
    def get(self, url: str): ...
    def find_elements(self, by: By, selector: str) -> List[WebElement]: ...
    def quit(): ...
```

---

## Proposed File Structure

```
src/
├── domains/
│   ├── music_queue/
│   │   ├── __init__.py
│   │   ├── entities.py          # SongRequest, StreamerId
│   │   ├── services.py          # SongMatchingService, QueueRepository
│   │   └── repository.py        # JSON persistence implementation
│   │
│   ├── web_extraction/
│   │   ├── __init__.py
│   │   ├── entities.py          # ExtractionSession, ExtractionResult
│   │   ├── webdriver_manager.py # WebDriverManager
│   │   ├── strategies/
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # ExtractionStrategy ABC
│   │   │   ├── table_strategy.py    # Moobot table extraction
│   │   │   ├── youtube_strategy.py  # YouTube link extraction
│   │   │   └── text_strategy.py     # Text parsing fallback
│   │   └── extractor.py         # Main extractor orchestration
│   │
│   ├── content_publishing/
│   │   ├── __init__.py
│   │   ├── entities.py          # SongCollection, HtmlPage
│   │   ├── html_generator.py    # Template-based HTML generation
│   │   └── publisher.py         # File system publishing
│   │
│   └── stream_monitoring/
│       ├── __init__.py
│       ├── entities.py          # MonitoringSession, ScanResult
│       ├── shutdown_handler.py  # Signal handling
│       └── scheduler.py         # Scan scheduling
│
├── infrastructure/
│   ├── __init__.py
│   ├── logging.py               # Unicode-safe logging
│   ├── filesystem.py            # File operations
│   └── config.py                # Configuration management
│
├── application/
│   ├── __init__.py
│   ├── scan_orchestrator.py     # Coordinates all domains
│   └── cli.py                   # Command-line interface
│
└── main.py                      # Application entry point
```

---

## Migration Plan

### Phase 1: Extract Infrastructure (Safest Start)
**Goal**: Move generic utilities to infrastructure layer

**Steps**:
1. Create `infrastructure/` directory
2. Move `safe_log()` → `infrastructure/logging.py`
3. Move `setup_directories()`, `load_existing_data()`, `save_data()` → `infrastructure/filesystem.py`
4. Update imports in `MoobotScraper`

**Risk**: **Low** - These are utility functions with minimal dependencies

### Phase 2: Extract Music Queue Domain
**Goal**: Create the core business domain first

**Steps**:
1. Create `domains/music_queue/` structure
2. Define `SongRequest` entity based on current song dictionary structure
3. Move `clean_song_title()`, `is_ui_text()`, `songs_match()` → `services.py`
4. Move `update_songs_data()` → `repository.py`
5. Create `QueueRepository` interface and JSON implementation

**Risk**: **Medium** - Core data structure changes require careful testing

### Phase 3: Extract Content Publishing Domain
**Goal**: Separate HTML generation concerns

**Steps**:
1. Create `domains/content_publishing/` structure
2. Move `generate_html()`, `create_html_page()`, `generate_index_page()` → `html_generator.py`
3. Create `SongCollection` entity
4. Refactor HTML methods to use domain entities

**Risk**: **Low** - HTML generation is isolated with clear boundaries

### Phase 4: Extract Web Extraction Domain
**Goal**: Isolate the most complex scraping logic

**Steps**:
1. Create `domains/web_extraction/` structure
2. Move `setup_webdriver()`, `cleanup()` → `webdriver_manager.py`
3. Create strategy pattern for extraction:
   - `TableStrategy` ← `extract_from_table_row*()`
   - `YouTubeStrategy` ← `extract_youtube_url_from_button()`, `extract_from_youtube_links()`
   - `TextStrategy` ← `parse_text_for_songs()`
4. Move `scrape_songs()` → `extractor.py` as orchestrator

**Risk**: **High** - Most complex domain with many interdependencies

### Phase 5: Extract Stream Monitoring Domain
**Goal**: Separate scheduling and lifecycle concerns

**Steps**:
1. Create `domains/stream_monitoring/` structure
2. Move signal handling → `shutdown_handler.py`
3. Move `run_scan()`, `run_forever()` → `scheduler.py`
4. Create `MonitoringSession` entity

**Risk**: **Medium** - Threading and signal handling require careful testing

### Phase 6: Create Application Layer
**Goal**: Orchestrate all domains

**Steps**:
1. Create `application/scan_orchestrator.py`
2. Implement domain coordination logic
3. Create new `main.py` that uses orchestrator
4. Remove old `MoobotScraper` class

**Risk**: **Medium** - Integration point requiring thorough testing

---

## Testing Strategy

### Domain-Specific Tests
```python
# domains/music_queue/test_services.py
def test_song_matching_service():
    service = SongMatchingService()
    song1 = SongRequest(title="Bohemian Rhapsody")
    song2 = SongRequest(title="Bohemian Rhapsody (Official Video)")
    assert service.songs_match(song1, song2)

# domains/web_extraction/test_strategies.py
def test_table_extraction_strategy():
    strategy = TableStrategy()
    # Mock WebDriver and test extraction
```

### Integration Tests
```python
# tests/test_scan_orchestrator.py
def test_full_scan_cycle():
    orchestrator = ScanOrchestrator(
        extractor=mock_extractor,
        queue_repo=mock_repository,
        publisher=mock_publisher
    )
    result = orchestrator.perform_scan(StreamerId("test_streamer"))
    assert result.success
```

### Migration Validation
- Run existing test suite after each phase
- Compare JSON output before/after migration
- Validate HTML generation produces identical results
- Performance benchmarking (ensure no regression)

---

## Benefits After Refactoring

### For AI Analysis
1. **Targeted Problem Solving**: "YouTube extraction failing" → Look only at `web_extraction/strategies/youtube_strategy.py`
2. **Clear Dependencies**: Each domain's external dependencies are explicit via interfaces
3. **Focused Context**: Read ~200 lines instead of 1,470 lines when debugging specific issues
4. **Pattern Recognition**: Strategy pattern makes it easy to add new extraction methods

### For Human Developers
1. **Single Responsibility**: Each class has one reason to change
2. **Testability**: Mock interfaces make unit testing straightforward
3. **Extensibility**: Add new extraction strategies or publishers easily
4. **Maintainability**: Domain expertise stays within domain boundaries

### Operational Benefits
1. **Error Isolation**: Extraction failures don't break HTML generation
2. **Performance**: Can optimize individual domains independently
3. **Monitoring**: Domain-specific metrics and logging
4. **Deployment**: Could eventually deploy domains as separate services

---

## Timeline Estimate

- **Phase 1** (Infrastructure): 1-2 days
- **Phase 2** (Music Queue): 2-3 days  
- **Phase 3** (Content Publishing): 1-2 days
- **Phase 4** (Web Extraction): 3-4 days
- **Phase 5** (Stream Monitoring): 2-3 days
- **Phase 6** (Application Layer): 2-3 days

**Total**: 11-17 days with thorough testing and validation

Would you like me to start with Phase 1 (Infrastructure extraction) to demonstrate the approach?