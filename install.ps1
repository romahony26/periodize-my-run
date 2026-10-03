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
# None on this computer: download a private copy into the app's own folder (from python-build-standalone, checked against the
# SHA-256 in runtime.lock). Nothing is installed system-wide.
if (Test-Path "$Dir\.python\python.exe") { $Py = """$Dir\.python\python.exe""" }
if (-not $Py) {
    $Line = Get-Content "$Dir\runtime.lock" | Where-Object { $_ -match " x86_64-pc-windows-msvc " } | Select-Object -First 1
    if (-not $Line -or $env:PROCESSOR_ARCHITECTURE -ne "AMD64") { Write-Host "Python 3.12 or later is needed: install it from https://www.python.org/downloads/ and tick 'Add python.exe to PATH', then run this again."; exit 1 }
    $Sum = $Line.Split(" ")[0]; $Url = $Line.Split(" ")[-1]
    Write-Host "Python 3.12 or later was not found. Downloading a private copy for this app (about 25 MB)..."
    $Tmp = "$Dir\.python.tar.gz"
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $Url -OutFile $Tmp -UseBasicParsing
    if ((Get-FileHash $Tmp -Algorithm SHA256).Hash.ToLower() -ne $Sum) { Remove-Item $Tmp -Force; Write-Host "The download did not match its published checksum, so it was not used. Nothing was installed."; exit 1 }
    if (Test-Path "$Dir\.python") { Remove-Item -Recurse -Force "$Dir\.python" }
    New-Item -ItemType Directory "$Dir\.python" | Out-Null
    & tar.exe -xzf $Tmp -C "$Dir\.python" --strip-components 1
    Remove-Item $Tmp -Force
    $Py = """$Dir\.python\python.exe"""
}

Write-Host "Creating Python environment..."
& cmd /c "$Py -m venv ""$Dir\.venv"""
if (-not (Test-Path "$Dir\.venv\Scripts\pythonw.exe")) { Write-Host "The Python environment could not be created."; exit 1 }
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
Write-Host "To remove it later: powershell -ExecutionPolicy Bypass -File .\uninstall.ps1 (your data is kept unless you add -Data)"
