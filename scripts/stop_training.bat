@echo off
echo Stopping Training System...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq RTX5090 Auto-Training System*"
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Administrator: RTX5090 Auto-Training System*"
echo.
echo If training is still running, please close the 'RTX5090 Auto-Training System' window manually.
pause
