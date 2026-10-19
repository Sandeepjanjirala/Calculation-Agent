@echo off
setlocal enabledelayedexpansion
title Calculation Specification Engine and AI Agent
cd /d "%~dp0"

echo ===================================================
echo   Starting Calculation Engine and AI Agent
echo ===================================================
echo.

:: 1. Auto-detect Python executable (.venv, venv, env, etc.)
set "PY_EXE="

if exist ".venv\Scripts\python.exe" (
    set "PY_EXE=%~dp0.venv\Scripts\python.exe"
    echo [INFO] Detected virtual environment: .venv
) else if exist "venv\Scripts\python.exe" (
    set "PY_EXE=%~dp0venv\Scripts\python.exe"
    echo [INFO] Detected virtual environment: venv
) else if exist "env\Scripts\python.exe" (
    set "PY_EXE=%~dp0env\Scripts\python.exe"
    echo [INFO] Detected virtual environment: env
) else if exist "..\.venv\Scripts\python.exe" (
    set "PY_EXE=%~dp0..\.venv\Scripts\python.exe"
    echo [INFO] Detected parent virtual environment: ..\.venv
) else if exist "..\venv\Scripts\python.exe" (
    set "PY_EXE=%~dp0..\venv\Scripts\python.exe"
    echo [INFO] Detected parent virtual environment: ..\venv
) else (
    set "PY_EXE=python"
    echo [INFO] Using system Python...
)

echo [INFO] Python Path: "!PY_EXE!"
echo.

:: 2. Free port 8005 if already held by an old background process
echo [INFO] Checking port 8005...
powershell -NoProfile -Command "$p = Get-NetTCPConnection -LocalPort 8005 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique; if ($p) { Stop-Process -Id $p -Force; Write-Host '[INFO] Cleared previous process on port 8005.' }" >nul 2>&1

:: 3. Run database migrations automatically to ensure all tables exist
echo [INFO] Verifying database tables...
"!PY_EXE!" manage.py migrate --noinput

:: 4. Launch default browser in 2 seconds
start "" powershell -NoProfile -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:8005/'"

:: 5. Start Django Server on 0.0.0.0:8005
echo.
echo ===================================================
echo   Server is running successfully!
echo   - Local PC URL:    http://127.0.0.1:8005/
echo   - Network Access:  http://0.0.0.0:8005/
echo ===================================================
echo [NOTE] Keep this window open while using the application.
echo.

"!PY_EXE!" manage.py runserver 0.0.0.0:8005

if errorlevel 1 (
    echo.
    echo ===================================================
    echo   [ERROR] Server stopped unexpectedly.
    echo ===================================================
    echo Please check the error message above.
    pause
)
