@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PYTHONUTF8=1"

echo [INFO] 使用 uv 启动 Qt 界面...
echo ========================================
echo.

uv run python desktop_qt_ui\main.py

pause
