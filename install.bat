@echo off
echo ========================================
echo   MarketNews - Easy Installer
echo ========================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo.
    echo Please install Python 3.10+ from:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)
echo [OK] Python found
python --version

:: Check for Claude CLI
claude --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Claude Code CLI not found.
    echo The app needs Claude Code to search for news.
    echo Install it from: https://docs.anthropic.com/en/docs/claude-code/overview
    echo.
    echo You can still install dependencies now and set up Claude later.
    echo.
)
if %errorlevel% equ 0 (
    echo [OK] Claude Code CLI found
)

:: Install dependencies
echo.
echo [1/2] Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install dependencies.
    echo Try running: pip install pystray Pillow
    pause
    exit /b 1
)
echo [OK] Dependencies installed

:: Done
echo.
echo ========================================
echo   Installation complete!
echo ========================================
echo.
echo To start MarketNews:
echo   python news_helper.py
echo.
echo It will appear in your system tray and
echo auto-start with Windows from now on.
echo.

set /p START="Start MarketNews now? (Y/N): "
if /i "%START%"=="Y" (
    echo.
    echo Starting MarketNews...
    start "" pythonw news_helper.py
    echo.
    echo MarketNews is running in your system tray!
    echo Look for the chart icon in the bottom-right.
)

echo.
pause
