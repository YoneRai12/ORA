
$regPath = "HKCU:\Software\Classes\Directory\Background\shell\ORAServices"
$commandPath = "$regPath\command"
$scriptPath = "C:\Users\YoneRai12\Desktop\ORADiscordBOT-main3\start_services.bat"

# Create Keys
if (-not (Test-Path $regPath)) { New-Item -Path $regPath -Force | Out-Null }
if (-not (Test-Path $commandPath)) { New-Item -Path $commandPath -Force | Out-Null }

# Set Values
Set-ItemProperty -Path $regPath -Name "(Default)" -Value "Start ORA Services 🧠"
Set-ItemProperty -Path $regPath -Name "Icon" -Value "imageres.dll,108" # Chip icon
Set-ItemProperty -Path $commandPath -Name "(Default)" -Value "cmd.exe /c start /min `"`" `"$scriptPath`""

Write-Host "Context menu added: Start ORA Services 🧠"
