# Periodize My Run uninstaller for Windows 10 and 11.
#
# Run from PowerShell in the Periodize My Run folder:
#     powershell -ExecutionPolicy Bypass -File .\uninstall.ps1          stop the app, stop it starting at sign-in, remove its Python environment. Your data is kept.
#     powershell -ExecutionPolicy Bypass -File .\uninstall.ps1 -Data    the same, and also delete your data, backups and the key to your stored Garmin login.
#
# It removes only what the installer made. The app's own folder (this one) is left for you to delete.
param([switch]$Data)
$ErrorActionPreference = "Stop"
$Dir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$Home_ = [Environment]::GetFolderPath("UserProfile")
$DataDir = if ($env:PERIODIZE_HOME) { $env:PERIODIZE_HOME } else { Join-Path $Home_ ".periodize-my-run" }
$KeyDir  = Join-Path $Home_ ".config\periodize-my-run"

$Task = "Periodize My Run"
if (Get-ScheduledTask -TaskName $Task -ErrorAction SilentlyContinue) {
    Stop-ScheduledTask -TaskName $Task -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $Task -Confirm:$false
    Write-Host "Stopped the app and removed it from sign-in."
} else {
    Write-Host "The app was not set to start at sign-in."
}
# the app itself, if it is still running from this folder's Python environment
Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' OR Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith("$Dir\.venv", [StringComparison]::OrdinalIgnoreCase) } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

foreach ($p in @("$Dir\.venv", "$Dir\.python")) { if (Test-Path $p) { Remove-Item -Recurse -Force $p } }
Write-Host "Removed the Python environment."

if ($Data) {
    Write-Host "This deletes your training data, backups and stored Garmin login for good:"
    Write-Host "  $DataDir"
    Write-Host "  $KeyDir"
    $answer = Read-Host "Type delete to go ahead"
    if ($answer -eq "delete") {
        foreach ($p in @($DataDir, $KeyDir)) { if (Test-Path $p) { Remove-Item -Recurse -Force $p } }
        Write-Host "Your data is deleted."
    } else {
        Write-Host "Nothing was deleted. Your data is still in $DataDir"
    }
} else {
    Write-Host "Your data is kept in $DataDir (add -Data to delete it too)."
}
Write-Host "To finish, delete this folder: $Dir"
Write-Host "If you installed it as an app in Edge or Chrome, remove that from the browser's Apps page."
