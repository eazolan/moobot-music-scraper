@echo off
echo Moobot Scraper - Any Streamer
echo ===============================

REM Set UTF-8 encoding for console output
chcp 65001 > nul

REM Set Python environment variables for better Unicode support
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8

echo.
set /p STREAMER_NAME="Enter streamer name (e.g., xqc, pokimane, shroud): "

if "%STREAMER_NAME%"=="" (
    echo Error: Please enter a streamer name
    pause
    exit /b 1
)

echo.
echo Starting scraper for %STREAMER_NAME%...
echo Monitoring: https://moo.bot/r/music#%STREAMER_NAME%
echo Press Ctrl+C to stop gracefully.
echo.

python moobot_scraper.py --streamer %STREAMER_NAME%

pause