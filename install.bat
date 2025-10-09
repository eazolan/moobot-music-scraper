@echo off
echo Installing Moobot Scraper Dependencies...
echo ==========================================

REM Check if Python is installed
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://python.org
    pause
    exit /b 1
)

echo Python version:
python --version

echo.
echo Installing required packages...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install packages
    echo Try running as Administrator or check your internet connection
    pause
    exit /b 1
)

echo.
echo ===============================================
echo Installation complete!
echo ===============================================
echo.
echo To test the scraper, run:
echo   python test_scraper.py
echo.
echo To start continuous monitoring, run:
echo   python moobot_scraper.py
echo.
pause