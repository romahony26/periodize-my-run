# Periodize My Run installer for Windows 10 and 11.
# Creates a Python environment, then starts Periodize My Run now and every time you sign in to Windows, for this computer only.
#
# Run from PowerShell in the Periodize My Run folder:
#     powershell -ExecutionPolicy Bypass -File .\install.ps1
#
# Then open http://localhost:8321. To have it as an app with its own icon, open that address in Edge or Chrome and choose
# "Install Periodize My Run" (Edge: ... > Apps; Chrome: the install icon in the address bar), then pin it to the taskbar or Start.
$ErrorActionPreference = "Stop"
$Dir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$Port = if ($env:PERIODIZE_PORT) { $env:PERIODIZE_PORT } else { "8321" }

# Python 3.12 or later, from python.org or the Microsoft Store ("py" is the launcher python.org installs).
$Py = $null
foreach ($c in @("py -3", "python")) {
    try {
        $v = & cmd /c "$c -c ""import sys; print(sys.version_info >= (3, 12))""" 2>$null
        if ($v -eq "True") { $Py = $c; break }
    } catch { }
}
if (-not $Py) { Write-Host "Python 3.12 or later is needed: install it from https://www.python.org/downloads/ and tick 'Add python.exe to PATH'."; exit 1 }

Write-Host "Creating Python environment..."
& cmd /c "$Py -m venv ""$Dir\.venv"""
& "$Dir\.venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
& "$Dir\.venv\Scripts\python.exe" -m pip install --quiet --require-hashes -r "$Dir\requirements.lock"   # exact versions, each checked against its published SHA-256

# Start at sign-in, hidden, for this user only. It listens on this computer only (127.0.0.1): no password or certificate is needed,
# and nothing on your network can reach it.
$Task = "Periodize My Run"
$Action  = New-ScheduledTaskAction -Execute "$Dir\.venv\Scripts\pythonw.exe" -Argument "`"$Dir\web.py`" --host 127.0.0.1 --port $Port" -WorkingDirectory $Dir
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Days 0) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Unregister-ScheduledTask -TaskName $Task -Confirm:$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "Periodize" -Confirm:$false -ErrorAction SilentlyContinue      # the task from before the rename
Register-ScheduledTask -TaskName $Task -Action $Action -Trigger $Trigger -Settings $Settings -Description "Periodize My Run training planner" | Out-Null
Start-ScheduledTask -TaskName $Task

Write-Host "Periodize My Run is running. Open http://localhost:$Port"
Write-Host "To have it as an app: open that address in Edge or Chrome and choose Install Periodize My Run, then pin it."
Write-Host "To stop it starting at sign-in: Unregister-ScheduledTask -TaskName Periodize My Run"
