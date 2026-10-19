# Calculation Specification Engine & AI Agent - PowerShell Launcher
$ErrorActionPreference = "Continue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Starting Calculation Engine & AI Agent" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Detect Python executable (.venv, venv, etc.)
$candidates = @(
    "$ScriptDir\.venv\Scripts\python.exe",
    "$ScriptDir\venv\Scripts\python.exe",
    "$ScriptDir\env\Scripts\python.exe",
    "$ScriptDir\..\.venv\Scripts\python.exe",
    "$ScriptDir\..\venv\Scripts\python.exe"
)

$pyExe = $null
foreach ($c in $candidates) {
    if (Test-Path $c) {
        $pyExe = $c
        break
    }
}

if (-not $pyExe) {
    $pyExe = "python"
}

Write-Host "[INFO] Using Python: $pyExe" -ForegroundColor Green

# 2. Free port 8005 if already held by another process
$p = Get-NetTCPConnection -LocalPort 8005 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($p) {
    Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
    Write-Host "[INFO] Cleared previous process on port 8005" -ForegroundColor Yellow
}

# 3. Apply database migrations
Write-Host "[INFO] Verifying database tables..." -ForegroundColor Gray
& $pyExe manage.py migrate --noinput

# 4. Open browser in 2 seconds
Start-Job -ScriptBlock {
    Start-Sleep -Seconds 2
    Start-Process "http://127.0.0.1:8005/"
} | Out-Null

# 5. Start Django development server
Write-Host ""
Write-Host "===================================================" -ForegroundColor Green
Write-Host "  Server is live!" -ForegroundColor Green
Write-Host "  - Local Browser:  http://127.0.0.1:8005/" -ForegroundColor White
Write-Host "  - Network Access: http://0.0.0.0:8005/" -ForegroundColor White
Write-Host "===================================================" -ForegroundColor Green
Write-Host "[INFO] Press Ctrl + C to stop the server.`n"

& $pyExe manage.py runserver 0.0.0.0:8005
