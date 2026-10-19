# PowerShell script to create a 1-Click Desktop Shortcut for the Calculation Engine
$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath('Desktop')
$ProjectPath = $PSScriptRoot

$ShortcutPath = Join-Path -Path $DesktopPath -ChildPath "Calculation Dashboard.lnk"
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)

# Point directly to powershell executing run.py or manage.py with bypass
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Normal -Command ""Set-Location '$ProjectPath'; python run.py; if (`$LASTEXITCODE -ne 0) { pause }"""
$Shortcut.WorkingDirectory = $ProjectPath
$Shortcut.Description = "Launch Calculation Engine & Dashboard"
$Shortcut.IconLocation = "shell32.dll,220" # Modern web / calculation icon
$Shortcut.Save()

Write-Host "=========================================================" -ForegroundColor Green
Write-Host "  Success! Desktop Shortcut created: 'Calculation Dashboard'" -ForegroundColor Green
Write-Host "  Location: $ShortcutPath" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Green
