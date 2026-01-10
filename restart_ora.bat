@echo off
chcp 65001 >nul
title ORA Restarter
cls
echo ♻️ Restarting ORA System...
echo ========================================================
echo 1. Stopping Python Services (Bot, API, ComfyUI, Layer, Voice)...
taskkill /F /IM python.exe >nul 2>&1

echo 2. Stopping Node.js (Vision UI)...
taskkill /F /IM node.exe >nul 2>&1

echo 3. Closing Command Windows...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-Process | Where-Object { $_.MainWindowTitle -like 'ORA Bot*' -or $_.MainWindowTitle -like 'ORA Worker Bot*' -or $_.MainWindowTitle -like 'ORA Web API*' -or $_.MainWindowTitle -like 'ORA Vision UI*' -or $_.MainWindowTitle -like 'ComfyUI*' -or $_.MainWindowTitle -like 'Voice Engine*' -or $_.MainWindowTitle -like 'Layer Service*' -or $_.MainWindowTitle -like 'Ngrok*' } | Stop-Process -Force"

echo.
echo ✅ Cleanup Complete.
echo 🚀 Starting ORA...
echo ========================================================
timeout /t 2 /nobreak >nul

call run_l.bat
