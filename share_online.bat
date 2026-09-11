@echo off
title InstaTranscribe Hindi - Public Online Access
echo =========================================================
echo    Starting InstaTranscribe Hindi Public Online Tunnel
echo =========================================================
cd /d "%~dp0"

echo [1/2] Checking if local server is running...
powershell -Command "if (!(Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue)) { Start-Process -FilePath '.\.venv\Scripts\python.exe' -ArgumentList 'run.py' -WindowStyle Minimized; Start-Sleep -Seconds 3 }"

echo [2/2] Starting Cloudflare Public HTTPS Tunnel...
echo.
echo =====================================================================
echo  Look for the URL ending with '.trycloudflare.com' below.
echo  Share that link with ANYONE in the world to access your website!
echo =====================================================================
echo.

cloudflared.exe tunnel --url http://127.0.0.1:8000
pause

