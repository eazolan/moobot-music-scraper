@echo off
echo Testing Moobot Scraper with Unicode support...
echo ==============================================

REM Set UTF-8 encoding for console output
chcp 65001 > nul

REM Set Python environment variables for better Unicode support
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8

echo Console encoding set to UTF-8
echo Running test...
echo.

python tests/test_scraper.py

pause