@echo off
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%.."
set "ROOT_DIR=%CD%"
chcp 65001 >nul
title ORA Ecosystem Control Panel

echo ========================================================
echo 🚀 ORA Ecosystem 起動シーケンス開始
echo 📂 ROOT: %ROOT_DIR%
echo ========================================================

:: --- [CLEANUP] ---
echo [0/8] 以前の残骸を掃除中...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM ngrok.exe >nul 2>&1
echo ✅ 掃除成功

:: --- [START SERVICES] ---

:: 1. Web API
echo [1/8] API サーバーを起動中...
start "ORA-WebAPI" cmd /k "cd /d "%ROOT_DIR%" && set PYTHONPATH=. && L:\ORADiscordBOT_Env\Scripts\uvicorn.exe src.web.app:app --reload --host 0.0.0.0 --port 8000"
echo ✅ Step 1 OK

:: 2. Ngrok
echo [2/8] Ngrok トンネルを起動中...
:: --host-header=rewrite を追加して Next.js デフォルトのホストチェックを回避
start "ORA-Ngrok" cmd /k "cd /d "%ROOT_DIR%" && ngrok http --host-header=rewrite 3333"
echo ✅ Step 2 OK

:: 3. UI
echo [3/8] ダッシュボード UI を起動中...
start "ORA-Dashboard" cmd /k "cd /d "%ROOT_DIR%\ora-ui" && npm run dev"
echo ✅ Step 3 OK

timeout /t 3 >nul

:: 4. ComfyUI
echo [4/8] ComfyUI (FLUX) をチェック中...
if exist "L:\ComfyUI\main.py" (
    echo    >> L:ドメインのComfyUIを起動します
    start "ORA-ComfyUI" cmd /k "cd /d L:\ComfyUI && L:\ORADiscordBOT_Env\Scripts\python.exe main.py --listen 127.0.0.1 --port 8188 --normalvram"
) else (
    echo    -- 見つかりませんでした（スキップ）
)
echo ✅ Step 4 OK

:: 5. Voice
echo [5/8] 音声合成エンジンを起動中...
start "ORA-Engine-Voice" cmd /k "cd /d "%ROOT_DIR%" && L:\ORADiscordBOT_Env\Scripts\python.exe src\services\voice_server.py"
echo ✅ Step 5 OK

:: 6. Layer
echo [6/8] 思考レイヤーエンジンを起動中...
start "ORA-Engine-Layer" cmd /k "cd /d "%ROOT_DIR%" && L:\ORADiscordBOT_Env\Scripts\python.exe src\services\layer_server.py"
echo ✅ Step 6 OK

:: 7. Visual
echo [7/8] 画像解析（Vision）エンジンを起動中...
start "ORA-Engine-Visual" cmd /k "cd /d "%ROOT_DIR%" && L:\ORADiscordBOT_Env\Scripts\python.exe src\services\visual_server.py"
echo ✅ Step 7 OK

:: 8. Bot & Worker
echo [8/8] Bot コアプロセスを起動中...
start "ORA-Core-Bot" cmd /k "cd /d "%ROOT_DIR%" && scripts\run_bot_loop.bat"
start "ORA-Worker-Bot" cmd /k "cd /d "%ROOT_DIR%" && scripts\run_worker_loop.bat"
echo ✅ 全ての命令が送信されました！

:: --- [FINALIZE] ---
echo.
echo ========================================================
echo ✅ 起動シーケンス完了！
echo 全てのウィンドウが正常に立ち上がりましたか？
echo この画面に「✅ Step 8 OK」まで出ていれば送信済みです。
echo ========================================================
start http://localhost:3333/dashboard
pause
