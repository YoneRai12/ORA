@echo off
title ORA Launcher
echo ===================================================
echo   ORA System Launcher
echo ===================================================

echo Starting ORA Web UI (Next.js) on Port 3333...
start "ORA Web UI" cmd /k "cd ora-ui && npm run dev"

echo Starting ORA Discord Bot...
python main.py

pause
