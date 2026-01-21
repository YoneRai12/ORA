@echo off
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
echo 🚀 ORA System (via Legacy Registry Link: start_vllm.bat)
echo Starting unified launcher...
call "scripts\start_ora_system.bat"
