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

:: 2. Launch browser automatically in 2 seconds
start "" powershell -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:8005/'"

:: 3. Start Django Server
echo [INFO] Server running on http://127.0.0.1:8005/
echo [INFO] Close this window to stop the server.
echo.
python manage.py runserver 8005
pause
