# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a **Python web scraper** that monitors Twitch streamers' music queues on Moobot and generates organized HTML pages with YouTube links. The scraper uses **Selenium WebDriver** to handle JavaScript-heavy pages and includes robust error handling, Unicode support, graceful shutdown mechanisms, and **intelligent YouTube URL optimization**.

**Target platform**: Windows (PowerShell)
**Language**: Python 3.7+
**Main dependencies**: Selenium, schedule
**Architecture**: Domain-Driven Design with separated concerns

## Common Development Commands

### Setup and Installation
```powershell
# Install dependencies
pip install -r requirements.txt

# Alternative: Use provided batch script
.\install.bat
```

### Testing
```powershell
# Run all key tests (recommended)
python tests/run_all_tests.py

# Quick diagnostic tests
python tests/diagnose_webdriver.py      # Check WebDriver compatibility
python tests/test_filtering.py          # Test UI filtering logic
python tests/test_html_generation.py    # Test HTML output

# Full integration tests  
python tests/test_scraper.py --streamer slimaera
.\run_test.bat                         # Batch script (Unicode-safe)

# Debug and troubleshooting
python tests/debug_songs.py            # Inspect scraped data
python tests/test_audio_muting.py       # Verify silent operation
python tests/test_webdriver_setup.py    # WebDriver diagnostics

# Legacy tests
.\test_invalid.bat                     # Invalid streamer detection
python tests/test_graceful_shutdown.py  # Graceful shutdown test
```

### Running the Scraper
```powershell
# Run with default streamer (Pokimane)
python moobot_scraper.py

# Run with specific streamer
python moobot_scraper.py --streamer xqc
python moobot_scraper.py -s shroud

# Use batch scripts (recommended for Windows Unicode support)
.\run_scraper.bat                    # Default streamer
.\run_any_streamer.bat              # Interactive streamer selection
```

### Development and Debugging
```powershell
# Check if output files exist
Get-ChildItem output\

# View generated HTML
Start-Process output\html\index.html

# Check logs
Get-Content output\scraper.log -Tail 50

# Debug specific components
python tests/debug_songs.py         # Inspect what songs are being scraped
python tests/debug_youtube_links.py # Analyze YouTube link extraction (legacy)
python tests/diagnose_webdriver.py  # WebDriver compatibility check

# Test HTML generation without scraping
python tests/test_html_generation.py

# Test filtering logic
python tests/test_filtering.py
```

## Architecture Overview

### Core Components

**MoobotScraper Class** (`moobot_scraper.py`)
- Main orchestrator using domain services for extraction and publishing
- Manages WebDriver lifecycle with optimized timeout handling
- Implements **YouTube URL optimization** to avoid redundant extraction
- Uses ExtractionCoordinator for multi-strategy song discovery

**Data Flow**:
1. **URL Construction** → `https://moo.bot/r/music#{streamer}`
2. **Page Load** → Selenium WebDriver with Chrome (headless, muted)
3. **Optimization Check** → Load existing songs to skip redundant YouTube extraction
4. **Multi-Strategy Extraction** → Coordinated extraction using multiple strategies
5. **Data Processing** → Clean, deduplicate, filter UI text, add metadata
6. **Persistence** → JSON storage via QueueRepository + HTML via ContentPublisher
7. **Scheduling** → Continuous monitoring every 60 seconds

### Key Technical Patterns

**Multiple Extraction Strategies**:
- ExtractionCoordinator manages TableRow, YouTubeLink, GeneralElement, and TextParsing strategies
- CSS selector targeting with priority-based selection
- YouTube URL extraction with **intelligent optimization** (skips existing URLs)
- Comprehensive UI text filtering to eliminate non-song elements
- Audio-muted operation for completely silent YouTube extraction

**Robust Error Handling**:
- WebDriver initialization with retry logic and timeout controls
- Stale element recovery (re-finding elements)
- Unicode encoding safety with fallback ASCII conversion
- Network timeout handling with retry mechanisms
- Force-quit WebDriver cleanup to prevent hanging processes

**Smart Optimization**:
- **YouTube URL reuse**: Existing songs skip redundant URL extraction
- **UI text filtering**: Advanced patterns to filter out non-song elements
- **Fast extraction config**: Reduced timeouts and limits for better performance
- **Silent operation**: Complete audio muting during all WebDriver operations

**Data Persistence Strategy**:
- Date-based organization via QueueRepository domain service
- Incremental updates to avoid data loss
- HTML generation via ContentPublisher with templating
- Debug artifacts (screenshots, page source) for troubleshooting

### File Structure Logic

```
output/
├── songs_data.json          # Master data store (date → songs[])
├── scraper.log             # Detailed operation logs
├── page_screenshot.png     # Visual debugging artifact
├── page_source.html        # Raw HTML debugging artifact
└── html/
    ├── index.html          # Master index with date navigation
    └── songs_YYYY-MM-DD.html # Daily song pages
```

## Development Guidelines

### When Modifying Extraction Logic
- Test against multiple streamers to ensure selectors work universally
- Always provide fallback mechanisms for critical data extraction
- Update both regular and "robust" extraction methods simultaneously
- Consider the impact of Moobot UI changes on CSS selectors

### Selenium Best Practices
- Use `execute_script()` for reliable element interactions
- Implement proper window switching for external links
- Always clean up WebDriver resources in finally blocks
- Mute audio during YouTube link extraction to prevent sound

### Unicode and Windows Compatibility
- All file operations use `encoding='utf-8'`
- Batch scripts set `PYTHONIOENCODING=utf-8` and `chcp 65001`
- Safe logging fallback for characters that can't be displayed
- Test with streamers who have international song titles

### Error Recovery Patterns
- **Stale elements**: Re-find elements instead of caching references
- **Network issues**: Implement retry logic with exponential backoff
- **JavaScript errors**: Gracefully handle missing YouTube links
- **Data corruption**: Validate JSON before writing, keep backups

## Configuration Notes

### Default Settings
- `DEFAULT_STREAMER = "pokimane"` (line 31 in moobot_scraper.py)
- `SCAN_INTERVAL = 60` seconds
- Chrome headless mode with audio muted
- Output directory: `./output/`

### Streamer Validation
The scraper validates streamer existence by checking for "not found" messages on the Moobot page. Invalid streamers will cause immediate termination with a descriptive error message.

### Chrome WebDriver Options
Critical settings for reliable operation:
- `--mute-audio`, `--disable-audio`, `--disable-audio-output` - Complete audio silence
- `--disable-blink-features=AutomationControlled` - Reduces detection
- `--headless` - Background operation
- `--no-sandbox`, `--disable-dev-shm-usage`, `--disable-gpu` - Stability
- Page load timeout: 30 seconds, Element wait timeout: 5 seconds
- Retry logic with force-quit cleanup to prevent hanging

## Domain-Driven Design Architecture (✅ Complete)

This codebase uses Domain-Driven Design principles with clean separation of concerns:

### ✅ Implemented Architecture:
```
infrastructure/          # Cross-cutting concerns
├── logging.py          # Unicode-safe logging with fallback
└── filesystem.py       # Safe file operations

domains/                # Business domains
├── music_queue/        # Core song queue logic
│   ├── entities.py     # SongRequest, StreamerId
│   └── services.py     # SongMatchingService, QueueRepository
├── content_publishing/  # HTML generation & publishing
│   ├── entities.py     # SongCollection, HtmlPage, PublishingConfig
│   └── services.py     # HtmlGenerator, ContentPublisher
└── song_extraction/    # Multi-strategy song extraction
    ├── entities/       # ExtractionResult, ExtractionConfig, ElementSelector
    └── services/       # ExtractionCoordinator, extraction strategies

tests/                  # All test scripts organized
├── test_*.py           # Domain and integration tests
├── debug_*.py          # Debugging utilities
├── diagnose_*.py       # Diagnostic tools
└── run_all_tests.py    # Test suite runner
```

### 🧪 Domain Testing:
Run domain-specific tests:
- `python tests/test_music_queue_domain.py` - Song entities and matching
- `python tests/test_content_publishing_domain.py` - HTML generation
- `python tests/test_force_html_generation.py` - Full publishing workflow
- `python tests/test_filtering.py` - UI text filtering logic
- `python tests/run_all_tests.py` - Complete test suite

## Troubleshooting Context

### Common Issues and Solutions

**WebDriver Hanging/Timeout Issues**:
- Run `python tests/diagnose_webdriver.py` to check WebDriver compatibility
- WebDriver has retry logic and force-quit mechanisms for reliability
- Chrome processes are automatically cleaned up to prevent conflicts

**Audio Playing During Scraping**:
- ✅ **Fixed**: Complete audio muting is now implemented
- All YouTube extraction is completely silent
- Test with `python tests/test_audio_muting.py`

**Too Many Non-Song Items in HTML**:
- ✅ **Fixed**: Advanced UI text filtering implemented
- Filters out timestamps, usernames, UI elements automatically
- Test filtering with `python tests/test_filtering.py`

**Slow Performance/Redundant YouTube Extraction**:
- ✅ **Fixed**: YouTube URL optimization implemented
- Existing songs skip redundant URL extraction
- Much faster execution and completely silent on repeat runs

**No Songs Found**: 
- Check `output/page_screenshot.png` and `page_source.html` for page structure changes
- Try different streamer: `python tests/test_scraper.py --streamer slimaera`
- Run `python tests/debug_songs.py` to inspect what's being scraped

**ChromeDriver Issues**: 
- Selenium Manager auto-downloads correct version (Selenium 4.36.0+)
- Run `python tests/diagnose_webdriver.py` for detailed diagnostics

**Unicode Issues**: 
- Use provided batch scripts which set proper encoding
- All logging has Unicode fallback safety

**Domain/Architecture Issues**:
- Run `python tests/run_all_tests.py` for comprehensive testing
- Test specific domains: `python tests/test_music_queue_domain.py`
- All tests are organized in `tests/` directory with proper imports
