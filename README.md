# 🎵 Moobot Music Queue Scraper

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/platform-windows-lightgrey.svg)]()

A Python script that monitors Moobot music queue pages for **any Twitch streamer** and collects song requests into beautiful, organized HTML pages with direct YouTube links.

## 🎯 **Configure for Any Streamer**

By default, this monitors **Pokimane's** queue, but you can easily change it:

### Method 1: Command Line (Recommended)
```bash
# Monitor a different streamer
python moobot_scraper.py --streamer xqc
python moobot_scraper.py --streamer pokimane
python moobot_scraper.py --streamer shroud

# Or use short form
python moobot_scraper.py -s ninja
```

### Method 2: Edit the File
Change line 31 in `moobot_scraper.py`:
```python
DEFAULT_STREAMER = "your_streamer_name_here"
```

## Features

- 🎵 **Automated Song Collection** - Scrapes song requests every minute
- 📅 **Date Organization** - Organizes songs by date with beautiful daily pages
- 🎨 **Beautiful HTML Pages** - Responsive design with Twitch-style purple theme
- 🔗 **YouTube Integration** - Automatically generates YouTube search links for every song with 🔍 Search buttons
- 📊 **Rich Metadata** - Captures duration, requester, play status, and timestamps
- 🛡️ **Robust & Reliable** - Advanced error handling, Unicode support, and stale element recovery
- 💾 **Persistent Storage** - JSON backup with full data preservation
- 🚦 **Graceful Shutdown** - Press Ctrl+C for safe, immediate shutdown with data saving
- 🌍 **Unicode Support** - Handles international characters (Korean, Japanese, etc.)

## Installation

### Prerequisites

1. **Python 3.7+** - Make sure Python is installed on your system
2. **Google Chrome** - The scraper uses Chrome WebDriver
3. **ChromeDriver** - Will be automatically downloaded by webdriver-manager

### Setup

1. **Clone or download this project** to your desired location

2. **Install Python dependencies:**
   ```bash
   cd H:\Development\Python\moobot_collect
   pip install -r requirements.txt
   ```

3. **Test the setup:**
   ```bash
   python test_scraper.py
   ```

## Usage

### Quick Test
Run a single scan to test if everything works:

**Option 1: Using batch file (recommended for Windows - handles Unicode properly):**
```bash
run_test.bat
```

**Option 2: Using Python directly:**
```bash
python test_scraper.py
```

### Continuous Monitoring
Run the scraper continuously (scans every minute):

**Option 1: Default streamer (Pokimane):**
```bash
run_scraper.bat
```

**Option 2: Any streamer (interactive):**
```bash
run_any_streamer.bat
```

**Option 3: Command line (specify streamer):**
```bash
python moobot_scraper.py --streamer xqc
```

**Option 4: Python directly (uses default):**
```bash
python moobot_scraper.py
```

The scraper will:
- Scan the Moobot page every minute
- Save songs to `output/songs_data.json`
- Generate HTML pages in `output/html/`
- Create logs in `output/scraper.log`

### Stopping the Scraper
The scraper includes a **graceful shutdown system**:

- **Press `Ctrl+C`** - Stops immediately and safely saves all data ⭐ **Recommended**
- **Press `Ctrl+Pause/Break`** (Windows) - Alternative method (Pause/Break key is near Print Screen)
- **Close terminal window** - Also triggers graceful shutdown
- **Automatic cleanup** - Ensures WebDriver is closed and data is preserved
- **No data loss** - All collected songs are saved before shutdown

**💡 Tip:** Just use `Ctrl+C` - it's the easiest and works on all systems!

You'll see a message like: `"Received SIGINT (Ctrl+C). Initiating graceful shutdown..."`

## Output Files

### Data Files
- `output/songs_data.json` - Raw song data in JSON format
- `output/scraper.log` - Detailed log file
- `output/page_screenshot.png` - Screenshot of the last scraped page (for debugging)
- `output/page_source.html` - HTML source of the last scraped page (for debugging)

### Generated HTML Pages
- `output/html/index.html` - Main index page listing all dates
- `output/html/songs_YYYY-MM-DD.html` - Individual pages for each date

## How It Works

The scraper uses multiple strategies to find songs on the Moobot page:

1. **Selenium WebDriver** - Loads the JavaScript-heavy page properly
2. **Multiple Selectors** - Tries various CSS selectors to find song elements
3. **YouTube Link Detection** - Specifically looks for YouTube links
4. **Text Parsing** - Falls back to parsing visible text for song-like content
5. **Smart Filtering** - Filters out UI elements and duplicate entries

## Troubleshooting

### Chrome/ChromeDriver Issues
If you get ChromeDriver errors:
- Make sure Google Chrome is installed
- The webdriver-manager should automatically download the correct ChromeDriver
- Try updating Chrome to the latest version

### Invalid Streamer Name
If you get an error like "Streamer 'xyz' was not found on Moobot":
1. **Double-check the spelling** - Streamer names are case-sensitive
2. **Verify the streamer exists on Twitch** - Make sure it's a real Twitch channel
3. **Check if they use Moobot** - Not all streamers use Moobot for music queues
4. **Try the URL manually** - Visit `https://moo.bot/r/music#streamername` in your browser
5. **Test with a known streamer** - Try `pokimane`, `xqc`, or `shroud` to verify the scraper works
6. **Run the invalid streamer test** - Use `test_invalid.bat` to verify error detection works

### No Songs Found
If the scraper runs but finds no songs:
1. Check the debug files:
   - `output/page_screenshot.png` - Visual of what the scraper sees
   - `output/page_source.html` - Raw HTML of the page
2. The page structure might have changed - check the logs for details
3. Make sure the stream is actually active with songs in the queue
4. Verify the streamer has a music queue feature enabled on Moobot

### Unicode/Encoding Issues
If you see `UnicodeEncodeError` when logging songs with special characters (Korean, Japanese, etc.):
- **Recommended:** Use the provided batch files (`run_test.bat` or `run_scraper.bat`)
- **Alternative:** Set environment variables manually:
  ```bash
  set PYTHONIOENCODING=utf-8
  chcp 65001
  python moobot_scraper.py
  ```

### Permission Issues
If you get permission errors:
- Make sure you have write access to the project directory
- Try running as administrator (Windows) or with sudo (Mac/Linux)

## Configuration

You can modify these settings in `moobot_scraper.py`:

- `SCAN_INTERVAL` - How often to scan (default: 60 seconds)
- `MOOBOT_URL` - The URL to scrape (currently set to pokimane's queue)
- Chrome options in `setup_webdriver()` method

## File Structure

```
moobot_collect/
│
├── moobot_scraper.py         # Main scraper script
├── test_scraper.py           # Test script for single runs  
├── test_invalid_streamer.py  # Test for invalid streamer detection
├── requirements.txt          # Python dependencies
├── install.bat              # Install dependencies (Windows)
├── run_scraper.bat          # Run with default streamer (Windows)
├── run_any_streamer.bat     # Run with custom streamer (Windows)
├── run_test.bat             # Single test run (Windows)
├── test_invalid.bat         # Test invalid streamer detection (Windows)
├── README.md                # This file
│
└── output/               # Created when first run
    ├── songs_data.json   # Persistent song data
    ├── scraper.log       # Log file
    ├── page_screenshot.png
    ├── page_source.html
    └── html/            # Generated HTML pages
        ├── index.html   # Main page
        └── songs_*.html # Daily pages
```

## Contributing

Feel free to improve the scraper! Common areas for enhancement:
- Better song title cleaning/normalization
- Additional music platforms beyond YouTube
- Mobile-responsive HTML improvements
- Search and filter functionality

## 🌟 Output Examples

### Main Index Page
- 📊 **Clean overview** of all collected songs organized by date
- 📈 **Statistics** showing total days tracked and songs collected
- 🔗 **Quick navigation** to daily song pages
- 🎨 **Modern design** with Twitch-style purple theme

### Daily Song Pages
- 🎵 **Song titles** with rich metadata (duration, requester, status)
- ▶️ **Direct YouTube links** - "Watch on YouTube" buttons
- 🔍 **Search fallbacks** - "Search YouTube" for songs without direct links
- 📅 **Timestamps** showing when each song was collected
- 📱 **Responsive design** that works on mobile and desktop

## 🆘 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## ⚠️ Disclaimer

This project is for personal/educational use. Please respect the terms of service of the websites being scraped.

## 👤 Author

Created for monitoring Twitch music requests via Moobot integration.
