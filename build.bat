@echo off
echo ========================================
echo  NewsHelper - Build Script
echo ========================================
echo.

echo [1/3] Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

echo [2/3] Building executable with PyInstaller...
pyinstaller --onefile --noconsole --name NewsHelper --icon=NONE --add-data "prompt.txt;." --add-data "config.json;." news_helper.py
if %errorlevel% neq 0 (
    echo ERROR: PyInstaller build failed
    pause
    exit /b 1
)
echo.

echo [3/3] Copying support files next to executable...
copy prompt.txt dist\prompt.txt >nul 2>&1
copy config.json dist\config.json >nul 2>&1
echo.

echo ========================================
echo  Build complete!
echo  Executable: dist\NewsHelper.exe
echo.
echo  To run: double-click dist\NewsHelper.exe
echo  It will appear in your system tray.
echo ========================================
pause
