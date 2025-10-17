# Installation Guide

This project provides multiple installation options for different platforms and preferences.

## Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- Internet connection for downloading dependencies

## Installation Options

### Option 1: Cross-Platform Python Script (Recommended)

Works on both Windows and Linux:

```bash
python install.py
```

or

```bash
python3 install.py
```

### Option 2: Windows Batch File

For Windows users who prefer the original batch script:

```cmd
install.bat
```

### Option 3: Linux Shell Script

For Linux users who prefer shell scripts:

```bash
chmod +x install.sh
./install.sh
```

## What Gets Installed

All installation methods will:

1. Check for Python 3.7+ installation
2. Install the following Python packages:
   - `selenium>=4.15.0`
   - `schedule>=1.2.0` 
   - `webdriver-manager>=4.0.0`
3. Provide usage instructions

## After Installation

Once installation is complete, you can:

- Test the scraper: `python test_scraper.py`
- Start monitoring: `python moobot_scraper.py`

## Troubleshooting

### Python Not Found
- **Windows**: Install from [python.org](https://python.org) and ensure "Add to PATH" is checked
- **Linux**: Use your package manager (e.g., `sudo apt install python3 python3-pip`)

### Permission Errors
- **Windows**: Run Command Prompt as Administrator
- **Linux**: Use `sudo` or create a virtual environment

### Network Issues
- Check your internet connection
- If behind a corporate firewall, you may need to configure pip proxy settings

## Virtual Environment (Optional but Recommended)

For a cleaner installation, consider using a virtual environment:

```bash
# Create virtual environment
python -m venv moobot_env

# Activate it
# Windows:
moobot_env\Scripts\activate
# Linux:
source moobot_env/bin/activate

# Then run any of the install scripts
python install.py
```