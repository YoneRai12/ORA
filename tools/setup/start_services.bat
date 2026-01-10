@echo off
cd /d "%~dp0"
echo Starting ORA Services...

echo ============================
echo [1] Voice Engine (Aratako TTS) -> Port 8002
echo [2] Layer Service (Qwen-Layered) -> Port 8003
echo ============================

start "Voice Engine (Port 8002)" cmd /k "python src/services/voice_server.py"
start "Layer Service (Port 8003)" cmd /k "python src/services/layer_server.py"

echo Services launched! Main Bot can now be started.
pause

