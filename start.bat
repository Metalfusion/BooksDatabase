@echo off
REM Quick start script for Windows

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo ========================================
echo Kirja.fi Scraper
echo ========================================
echo.
echo Available commands:
echo   1. Run full scraper: python scraper.py
echo   2. Test scraper: python test_scraper.py
echo   3. View data: python utils.py
echo   4. Search books: python utils.py "search term"
echo.
echo ========================================
echo.

cmd /k
