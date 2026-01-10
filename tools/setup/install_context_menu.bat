@echo off
chcp 65001 >nul
title ORA Context Menu Installer
echo 右クリックメニューに "Start ORA Bot" を追加しています...

set "KEY_NAME=HKCU\Software\Classes\Directory\Background\shell\ORABot"
set "CMD_PATH=%~dp0run_l.bat"

reg add "%KEY_NAME%" /ve /d "Start ORA Bot" /f
reg add "%KEY_NAME%" /v "Icon" /d "cmd.exe" /f
reg add "%KEY_NAME%\command" /ve /d "\"%CMD_PATH%\"" /f

echo.
echo ✅ コンテキストメニューを追加しました！
echo デスクトップやフォルダの背景で右クリックすると "Start ORA Bot" が表示されます。
echo (反映にはエクスプローラの再起動が必要な場合があります)
echo.
pause
