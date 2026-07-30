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

echo [1/5] Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo [2/5] Checking .env file...
if not exist .env (
    echo [INFO] .env file not found. This is normal for first-time setup.
    echo Your API Key is needed to power the AI features.
    echo You can get one from: https://platform.deepseek.com/api_keys
    echo.
    set /p APIKEY=Please paste your DeepSeek API Key (sk-xxx): 
    echo # DeepSeek API config > .env
    echo DEEPSEEK_API_KEY=%APIKEY% >> .env
    echo. >> .env
    echo DEEPSEEK_MODEL=deepseek-chat >> .env
    echo .env created successfully
) else (
    echo .env found. Using existing config.
)

echo.
echo [3/5] Building executable...
python -m PyInstaller hakon_desktop.spec --noconfirm
if errorlevel 1 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo.
echo [4/5] Checking Inno Setup...
where iscc >nul 2>&1
if errorlevel 1 (
    if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
        set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    ) else (
        echo [WARNING] Inno Setup not found. Skipping installer creation.
        echo You can download Inno Setup from: https://jrsoftware.org/isdl.php
        echo.
        echo ============================================================
        echo   Build complete! (exe only, no installer)
        echo ============================================================
        echo   Output: dist\HAKON\HAKON.exe
        echo.
        echo To create a setup installer, install Inno Setup and run this script again.
        echo.
        pause
        exit /b 0
    )
) else (
    set "ISCC=iscc"
)

echo.
echo [5/5] Creating installer...
if not exist installer_output mkdir installer_output
"%ISCC%" hakon_installer.iss
if errorlevel 1 (
    echo [WARNING] Installer creation failed. You can still use dist\HAKON\HAKON.exe directly.
    echo.
    echo ============================================================
    echo   Build complete! (exe only, no installer)
    echo ============================================================
    echo   Output: dist\HAKON\HAKON.exe
    echo.
    pause
    exit /b 0
)

echo.
echo ============================================================
echo   Build complete!
echo ============================================================
echo   Installer:   installer_output\HAKON_Setup.exe
echo   Standalone:  dist\HAKON\HAKON.exe
echo ============================================================
echo.
echo Send HAKON_Setup.exe to your colleagues.
echo They double-click it, install, and HAKON icon appears on desktop.
echo.
pause
