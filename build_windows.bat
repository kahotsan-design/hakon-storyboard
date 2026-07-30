@echo off
chcp 65001 >nul 2>&1
REM ============================================================
REM  HAKON 桌面应用 - Windows 一键构建脚本
REM  
REM  使用方法：
REM    1. 安装 Python 3.11+ (勾选 Add to PATH)
REM    2. 双击运行此脚本
REM    3. 构建完成后，dist\HAKON\HAKON.exe 即可使用
REM ============================================================

echo ============================================================
echo   HAKON 桌面应用构建工具
echo ============================================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.11+
    echo 下载地址: https://www.python.org/downloads/
    echo 安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)

echo [1/4] 安装依赖包...
pip install -r requirements.txt
pip install pyinstaller
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

echo.
echo [2/4] 检查 .env 配置文件...
if not exist .env (
    echo [警告] 未找到 .env 文件！
    set /p APIKEY=请输入 DeepSeek API Key: 
    echo # DeepSeek API 配置 > .env
    echo DEEPSEEK_API_KEY=%APIKEY% >> .env
    echo. >> .env
    echo DEEPSEEK_MODEL=deepseek-chat >> .env
    echo .env 已创建
)

echo.
echo [3/4] 开始构建...
pyinstaller hakon_desktop.spec --noconfirm
if errorlevel 1 (
    echo [错误] 构建失败
    pause
    exit /b 1
)

echo.
echo [4/4] 构建完成！
echo ============================================================
echo   输出目录: dist\HAKON\
echo   主程序:   dist\HAKON\HAKON.exe
echo ============================================================
echo.
echo 双击 HAKON.exe 即可启动应用。
echo.
pause
