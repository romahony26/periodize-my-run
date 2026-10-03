@echo off
rem Double-click to remove Periodize My Run. Your data is kept.
rem To delete your data too:  powershell -ExecutionPolicy Bypass -File uninstall.ps1 -Data
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0uninstall.ps1"
echo.
pause
