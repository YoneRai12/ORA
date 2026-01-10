@echo off
title RTX5090 Auto-Training System
echo Starting Training Manager...
echo You can minimize this window and play games.
echo To stop, close this window or run stop_training.bat
echo.
cd /d "%~dp0"
start cmd /k "python RTX5090-DebugSystem-main/phoenix_cli_manager.py"
exit
