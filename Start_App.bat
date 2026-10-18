@echo off
title Calculation Specification Engine & AI Agent
cd /d "%~dp0"

echo ===================================================
echo   Starting Calculation Specification Engine & AI Agent
echo ===================================================
echo.

:: 1. Check for Virtual Environment
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating local virtual environment...
    call "venv\Scripts\activate.bat"
) else if exist "..\excel_agent\venv\Scripts\activate.bat" (
    echo [INFO] Activating excel_agent virtual environment...
    call "..\excel_agent\venv\Scripts\activate.bat"
) else (
    echo [INFO] Using system Python...
)

:: 2. Auto-apply database migrations
echo [INFO] Checking database migrations...
python manage.py migrate --noinput

:: 3. Launch browser automatically in 2 seconds
start "" powershell -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:8005/'"

:: 4. Start Django Server
echo.
echo [INFO] Server running on:
echo   - Local:   http://127.0.0.1:8005/
echo   - Network: http://0.0.0.0:8005/
echo [INFO] Keep this window open while using the application.
echo.
python manage.py runserver 0.0.0.0:8005
pause
