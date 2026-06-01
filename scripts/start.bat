@echo off
chcp 65001 >nul
title Prompt Rewrite System
cd /d "%~dp0.."

echo =====================================================
echo   Prompt Rewrite System  v0.2.1
echo   Smart Prompt Optimization
echo =====================================================
echo.
echo   Installing dependencies...
pip install -r requirements.txt -q
echo.
echo   Starting server...
echo.
python -X utf8 launch_ui.py

pause
