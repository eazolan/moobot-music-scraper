@echo off
echo Starting Moobot Scraper with Unicode support...
echo ================================================

REM Set UTF-8 encoding for console output
chcp 65001 > nul

REM Set Python environment variables for better Unicode support
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8

echo Console encoding set to UTF-8
echo Starting scraper for Pokimane (default)...
echo Monitoring: https://moo.bot/r/music#Pokimane
echo.
echo To monitor a different streamer, use: run_any_streamer.bat
echo Press Ctrl+C to stop gracefully.
echo.

python moobot_scraper.py --streamer pokimane

pause