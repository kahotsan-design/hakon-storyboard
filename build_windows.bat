@echo off
chcp 65001 >nul 2>&1

echo ============================================================
echo   HAKON Desktop App Builder
echo ============================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.11+ first.
    echo Download: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [1/4] Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo [2/4] Checking .env file...
if not exist .env (
    echo [WARNING] .env file not found.
    set /p APIKEY=Please enter your DeepSeek API Key: 
    echo # DeepSeek API config > .env
    echo DEEPSEEK_API_KEY=%APIKEY% >> .env
    echo. >> .env
    echo DEEPSEEK_MODEL=deepseek-chat >> .env
    echo .env created successfully
)

echo.
echo [3/4] Building...
python -m PyInstaller hakon_desktop.spec --noconfirm
if errorlevel 1 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo.
echo [4/4] Build complete!
echo ============================================================
echo   Output folder: dist\HAKON\
echo   Main program:  dist\HAKON\HAKON.exe
echo ============================================================
echo.
echo Double-click HAKON.exe to run the app.
echo.
pause
