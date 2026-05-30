@echo off
chcp 65001 >nul
title Prompt Rewrite System

echo =====================================================
echo   Prompt Rewrite System  v0.2.0
echo   Smart Prompt Optimization
echo =====================================================
echo.

REM 检查打包版 EXE 是否存在
if exist "%~dp0..\dist\PromptRewrite.exe" (
    echo   🚀 发现打包版，启动中...
    start "" "%~dp0..\dist\PromptRewrite.exe"
    timeout /t 3 /nobreak >nul
    start http://localhost:8000
    echo   ✅ 浏览器已打开！关闭此窗口可退出。
    goto end
)

REM EXE 不存在，提示下载或使用 Python 版
echo   ⚠️ 未找到打包版程序 (PromptRewrite.exe)。
echo.
echo   ┌─────────────────────────────────────────────────────┐
echo   │  方式1（推荐·无需装 Python）：                         │
echo   │     去 Releases 下载最新版 PromptRewrite.exe         │
echo   │     https://github.com/yinsang0910-star/             │
echo   │       prompt-rewrite/releases                        │
echo   │                                                     │
echo   │  方式2（需已安装 Python）：                            │
echo   │     双击同目录下的 start.bat                          │
echo   └─────────────────────────────────────────────────────┘
echo.
echo   按任意键打开下载页面...
pause >nul
start https://github.com/yinsang0910-star/prompt-rewrite/releases
echo   页面已打开，下载 PromptRewrite.exe 后放到 dist\ 文件夹即可。

:end
pause
