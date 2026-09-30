@echo off
title Stop Application Server
cd /d "%~dp0"

echo ===================================================
echo   Stopping Application Server on Port 8005
echo ===================================================
echo.

powershell -Command "$p = Get-NetTCPConnection -LocalPort 8005 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique; if ($p) { Stop-Process -Id $p -Force; Write-Host '[SUCCESS] Stopped process' $p } else { Write-Host '[INFO] No server was running on port 8005.' }"

echo.
timeout /t 2 >nul
exit
