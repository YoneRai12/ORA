@echo off
chcp 65001 >nul
title Register ORA Bot to System
echo [ORA] Adding 'ora' command to Windows Registry...

:: Check for Admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Please Run as Administrator.
    pause
    exit /b
)

:: Get Current Directory
set "CURRENT_DIR=%~dp0"
set "CURRENT_DIR=%CURRENT_DIR:~0,-1%"

:: Clean up old keys (Aggressive Cleanup)
echo [ORA] Cleaning up old inputs...
reg delete "HKCR\Directory\Background\shell\ORA" /f >nul 2>&1

:: Define Paths
set "LAUNCHER_PATH=%CURRENT_DIR%\..\..\scripts\run_l.bat"

:: 1. Root Menu (The Heading)
reg add "HKCR\Directory\Background\shell\ORA" /v "MUIVerb" /d "🚀 ORA : 次世代AIシステム" /f
reg add "HKCR\Directory\Background\shell\ORA" /v "SubCommands" /d "" /f
reg add "HKCR\Directory\Background\shell\ORA" /v "Icon" /d "%SystemRoot%\System32\shell32.dll,238" /f

:: 2. Sub-Items
reg add "HKCR\Directory\Background\shell\ORA\shell\01start" /v "MUIVerb" /d "🚀 ORAを起動する" /f
reg add "HKCR\Directory\Background\shell\ORA\shell\01start" /v "Icon" /d "%SystemRoot%\System32\shell32.dll,190" /f
reg add "HKCR\Directory\Background\shell\ORA\shell\01start\command" /ve /d "cmd /k \"\"%LAUNCHER_PATH%\"\"" /f

reg add "HKCR\Directory\Background\shell\ORA\shell\02dash" /v "MUIVerb" /d "🌐 ダッシュボードを開く" /f
reg add "HKCR\Directory\Background\shell\ORA\shell\02dash" /v "Icon" /d "%SystemRoot%\System32\shell32.dll,14" /f
reg add "HKCR\Directory\Background\shell\ORA\shell\02dash\command" /ve /d "cmd /c start http://localhost:3333/dashboard" /f

reg add "HKCR\Directory\Background\shell\ORA\shell\03stop" /v "MUIVerb" /d "⏹️ 全てのプロセスを停止" /f
reg add "HKCR\Directory\Background\shell\ORA\shell\03stop" /v "Icon" /d "%SystemRoot%\System32\shell32.dll,131" /f
reg add "HKCR\Directory\Background\shell\ORA\shell\03stop\command" /ve /d "cmd /c taskkill /F /IM python.exe /IM node.exe /T" /f

echo.
echo [SUCCESS] Context menu registry updated with UTF-8 support.
echo.
pause
