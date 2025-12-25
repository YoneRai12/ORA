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
taskkill /F /FI "WINDOWTITLE eq ORA Web API" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq ORA Vision UI" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq ComfyUI" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Voice Engine*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Layer Service*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq ORA Bot" >nul 2>&1

echo.
echo ✅ Cleanup Complete.
echo 🚀 Starting ORA...
echo ========================================================
timeout /t 2 /nobreak >nul

call run_l.bat
