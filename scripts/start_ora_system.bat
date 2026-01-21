@echo off
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%.."
set "ROOT_DIR=%CD%"
chcp 65001 >nul
title ORA Ecosystem Unified Launcher

echo ========================================================
echo 🚀 ORA System 統合起動 (Full Stack: 3333 & 3000)
echo 📂 ROOT: %ROOT_DIR%
echo ========================================================

:: --- [CLEANUP] ---
echo [0/10] 以前のプロセスをクリーンアップ中...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM ngrok.exe >nul 2>&1
echo ✅ クリーンアップ完了

:: --- [DB INIT] ---
echo [1/11] データベースを準備中 (Schema Check & Init)...
set PYTHONPATH=core/src
python scripts/fix_user_id_column.py
python scripts/init_core_db.py
echo ✅ DB 準備完了

:: 1. ORA Core API (Brain) - Port 8001
echo [2/11] ORA Core API (Port 8001) を起動中...
start "ORA-CoreAPI" cmd /k "cd /d "%ROOT_DIR%" && set PYTHONPATH=core/src && python -m ora_core.main"
echo ✅ Step 1 OK

:: 2. ORA Core Web Client (New Main) - Port 3000
echo [2/10] ORA Core Web Client (Port 3000) を起動中...
start "ORA-Web-Main" cmd /k "cd /d "%ROOT_DIR%\clients\web" && npm run dev"
echo ✅ Step 2 OK

:: 3. ORA Dashboard (Legacy/Discord Info) - Port 3333
echo [3/10] ORA Dashboard (Port 3333) を起動中...
start "ORA-Dashboard-Legacy" cmd /k "cd /d "%ROOT_DIR%\ora-ui" && npm run dev"
echo ✅ Step 3 OK

:: 4. Legacy Web API - Port 8000 (for Bot compatibility)
echo [4/10] Legacy API (Port 8000) を起動中...
start "ORA-WebAPI-Legacy" cmd /k "cd /d "%ROOT_DIR%" && set PYTHONPATH=. && L:\ORADiscordBOT_Env\Scripts\uvicorn.exe src.web.app:app --reload --host 0.0.0.0 --port 8000"
echo ✅ Step 4 OK

:: 5. Ngrok (Multi-Tunnel: 3000, 3333, 8001)
echo [5/11] Ngrok (Multi-Tunnel) を起動中...
start "ORA-Ngrok" cmd /k "cd /d "%ROOT_DIR%" && ngrok start --all --config ngrok.yml"
echo ✅ Step 5 OK

:: --- [START ENGINES] ---

:: 6. ComfyUI (FLUX)
echo [6/10] ComfyUI (FLUX) をチェック中...
if exist "L:\ComfyUI\main.py" (
    start "ORA-ComfyUI" cmd /k "cd /d L:\ComfyUI && L:\ORADiscordBOT_Env\Scripts\python.exe main.py --listen 127.0.0.1 --port 8188 --normalvram"
)
echo ✅ Step 6 OK

:: 7. Voice & Layer Engines
echo [7/10] Voice/Layer エンジンを起動中...
start "ORA-Engine-Voice" cmd /k "cd /d "%ROOT_DIR%" && L:\ORADiscordBOT_Env\Scripts\python.exe src\services\voice_server.py"
start "ORA-Engine-Layer" cmd /k "cd /d "%ROOT_DIR%" && L:\ORADiscordBOT_Env\Scripts\python.exe src\services\layer_server.py"
echo ✅ Step 7 OK

:: 8. Visual Engine
echo [8/10] Visual エンジンを起動中...
start "ORA-Engine-Visual" cmd /k "cd /d "%ROOT_DIR%" && L:\ORADiscordBOT_Env\Scripts\python.exe src\services\visual_server.py"
echo ✅ Step 8 OK

:: 9. Discord Bot (Skin)
echo [9/10] Discord Bot (Port ログ出力用) を起動中...
start "ORA-Core-Bot" cmd /k "cd /d "%ROOT_DIR%" && scripts\run_bot_loop.bat"
start "ORA-Worker-Bot" cmd /k "cd /d "%ROOT_DIR%" && scripts\run_worker_loop.bat"
echo ✅ 全てのコンポーネントが起動されました！

:: 10. Final Cleanup & URL Open
echo [10/10] ブラウザでダッシュボードを表示します...
timeout /t 5 >nul
start http://localhost:3000
start http://localhost:3333/dashboard
echo ========================================================
echo ✅ 全システム起動完了！
echo - Core Web (Main): http://localhost:3000
echo - Legacy Dash: http://localhost:3333/dashboard
echo - Core API: http://localhost:8001/docs
echo ========================================================
pause
