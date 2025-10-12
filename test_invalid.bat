@echo off
echo Testing Invalid Streamer Detection
echo ===================================
echo.

REM Set UTF-8 encoding for console output
chcp 65001 > nul

REM Set Python environment variables for better Unicode support
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8

echo This will test if the scraper properly detects invalid streamers.
echo Testing with: slfdgagff (should fail)
echo.

python moobot_scraper.py --streamer slfdgagff

echo.
echo Test completed. If you saw an error about streamer not found, it's working correctly!
echo.
pause