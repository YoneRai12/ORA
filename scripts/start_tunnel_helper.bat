@echo off
:: %1: cloudflared.exe path
:: %2: service url
:: %3: log file path
set "EXE_PATH=%~1"
set "URL=%~2"
set "LOG_PATH=%~3"

title Tunnel: %URL%
echo ========================================================
echo [Tunnel] Cloudflare Tunnel: %URL%
echo [Log   ] %LOG_PATH%
echo ========================================================

if not exist "%EXE_PATH%" (
    echo [Error ] cloudflared.exe not found: %EXE_PATH%
    pause
    exit /b 1
)

echo [Status] Starting tunnel...
"%EXE_PATH%" tunnel --url %URL% > "%LOG_PATH%" 2>&1

echo.
echo [Status] Tunnel stopped.
echo Please check the log: %LOG_PATH%
pause
