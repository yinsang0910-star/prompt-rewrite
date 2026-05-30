@echo off
chcp 65001 >nul
title Prompt Rewrite System
echo Starting Prompt Rewrite System...
echo.
start "" "%~dp0PromptRewrite.exe"
timeout /t 3 /nobreak >nul
start http://localhost:8000
echo.
echo Browser opened. Close this window to stop the server.
pause
