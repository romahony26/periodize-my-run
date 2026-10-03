@echo off
rem Double-click to install Periodize My Run. It downloads what this computer lacks (Python if there is none, and the libraries).
rem Keep this folder where it is: the app runs from here.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
if errorlevel 1 (echo. ^& echo The install did not finish. ^& pause ^& exit /b 1)
start "" "http://localhost:8321"
echo.
pause
