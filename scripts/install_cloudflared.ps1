$ToolsDir = "tools\cloudflare"
if (!(Test-Path $ToolsDir)) { New-Item -ItemType Directory -Path $ToolsDir }

$Url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
$Dest = "$ToolsDir\cloudflared.exe"

echo "Downloading cloudflared..."
Invoke-WebRequest -Uri $Url -OutFile $Dest
echo "Done."
