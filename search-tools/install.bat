@echo off
REM Quick installer for search tools (Windows)

echo 📚 Installing Book Database Search Tools...
echo.

pip install -r requirements.txt

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Installation complete!
    echo.
    echo Quick start:
    echo   python search.py --help          # Show all commands
    echo   python search.py search "query"  # Search books
    echo   python search.py stats           # View statistics
    echo.
    echo For full documentation, see README.md
) else (
    echo.
    echo ❌ Installation failed. Please check the error messages above.
    exit /b 1
)
