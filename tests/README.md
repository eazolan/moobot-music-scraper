# Test Scripts

This directory contains test scripts and debugging utilities for the Moobot scraper.

## Available Tests

### Core Functionality Tests
- `test_scraper.py` - Main scraper functionality test with any streamer
- `test_music_queue_domain.py` - Music queue domain logic tests
- `test_content_publishing_domain.py` - Content publishing domain tests
- `test_html_generation.py` - Test HTML generation with sample data

### WebDriver & System Tests
- `diagnose_webdriver.py` - Diagnose WebDriver and Chrome compatibility issues
- `test_webdriver_setup.py` - Test WebDriver initialization and basic functionality
- `test_audio_muting.py` - Test that scraping runs completely silently

### Filtering & Data Quality Tests
- `test_filtering.py` - Test UI text filtering to ensure clean song data

### Debugging & Diagnostics
- `debug_songs.py` - Quick debug script to inspect scraped song data
- `debug_youtube_links.py` - Debug YouTube link extraction (legacy)

### Utility Tests
- `test_graceful_shutdown.py` - Test graceful shutdown behavior
- `test_force_html_generation.py` - Force HTML regeneration test

## Running Tests

Run individual tests from the project root:
```bash
# Core functionality
python tests/test_scraper.py --streamer slimaera
python tests/test_html_generation.py
python tests/test_filtering.py

# WebDriver diagnostics
python tests/diagnose_webdriver.py
python tests/test_webdriver_setup.py

# Debug specific issues
python tests/debug_songs.py
python tests/test_audio_muting.py
```

Or use the convenient batch file from the root:
```bash
run_test.bat  # Runs test_scraper.py with default streamer
```

## Test Categories

**🚀 Quick Tests** (run these first):
- `diagnose_webdriver.py` - Check if WebDriver works
- `test_filtering.py` - Verify filtering logic
- `test_html_generation.py` - Test HTML output

**🧪 Full Integration Tests** (slower but comprehensive):
- `test_scraper.py --streamer slimaera` - Full scraping test
- `test_webdriver_setup.py` - WebDriver initialization test

**🐛 Debug Tools** (when things go wrong):
- `debug_songs.py` - Inspect what's being scraped
- `test_audio_muting.py` - Check if scraping is silent
