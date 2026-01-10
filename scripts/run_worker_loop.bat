@echo off
chcp 65001 >nul
:loop
title ORA Worker Bot (自動再起動モード)
echo 🚀 ORA Worker プロセスを起動中...
L:\ORADiscordBOT_Env\Scripts\python.exe src/worker_bot.py
echo ⚠️ Workerプロセスが終了しました。5秒後に再起動します...
timeout /t 5
goto loop
