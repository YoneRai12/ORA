@echo off
chcp 65001 >nul
title ORA Bot (L: Drive - GPU)
cd /d "%~dp0"
:start
cls
echo 🚀 ORA Bot を起動しています (L: Drive Environment - GPU Upgrade)
echo ========================================================
echo GPUの状態を確認中...
echo 前回のプロセスを終了しています...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1

echo ORA Web API を起動中...
start "ORA Web API" cmd /k "L:\ORADiscordBOT_Env\Scripts\uvicorn.exe src.web.app:app --reload --host 0.0.0.0 --port 8000"

echo Ngrok Tunnel と Dashboard を起動中...
start "Ngrok" cmd /k "ngrok http 3333"
timeout /t 3 >nul

echo ORA Vision UI を起動中...
start "ORA Vision UI" cmd /k "cd ora-ui && npm run dev"
timeout /t 10 >nul
start http://localhost:3333/dashboard

echo ComfyUI (FLUX.2 Engine) を起動中...
start "ComfyUI" cmd /k "cd /d L:\ComfyUI && L:\ORADiscordBOT_Env\Scripts\python.exe main.py --listen 127.0.0.1 --port 8188 --normalvram --disable-cuda-malloc --enable-cors-header * --force-fp16"
timeout /t 5 /nobreak >nul
start http://localhost:8188

echo 補助サービス (Voice/Layer) を起動中...
start "Voice Engine (Port 8002)" cmd /k "L:\ORADiscordBOT_Env\Scripts\python.exe src/services/voice_server.py"
start "Layer Service (Port 8003)" cmd /k "L:\ORADiscordBOT_Env\Scripts\python.exe src/services/layer_server.py"

echo Bot本体を起動中...
start "ORA Bot" cmd /k "scripts\run_bot_loop.bat"
start "ORA Worker Bot" cmd /k "scripts\run_worker_loop.bat"

echo ========================================================
echo ✅ 全てのサービスが正常に起動しました！
echo (このウィンドウは最小化しても大丈夫です)
echo.
echo [1] ORA Web API
echo [2] ORA Vision UI
echo [3] Stable Diffusion WebUI
echo [4] ORA Bot
echo.
echo サービスを停止して再起動するには何かキーを押してください...
echo ========================================================
pause
echo.
echo ========================================================
echo ⚠️ サービス停止準備完了。再起動しますか？
echo (完全に終了する場合はこのウィンドウを閉じてください)
echo 何かキーを押すと再起動します...
pause
goto start
