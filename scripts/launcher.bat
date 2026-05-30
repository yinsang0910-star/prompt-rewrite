@echo off
chcp 65001 >nul
title Prompt Rewrite System
echo Starting Prompt Rewrite System...
start "" "%~dp0..\dist\PromptRewrite.exe"
timeout /t 3 /nobreak >nul
start http://localhost:8000
echo Browser opened. Close this window to stop.
pause
