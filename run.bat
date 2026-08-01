@echo off
echo Starting CyberShield Ghana (Development Mode)...
echo ==============================
echo.
title CyberShield Ghana - Cyber Incident Reporting App
cd /d "%~dp0"

REM Prefer the project virtual environment (it has all dependencies)
set "PY_CMD=python"
if exist ".venv\Scripts\python.exe" set "PY_CMD=.venv\Scripts\python.exe"

echo Launching application...
echo.
echo The app will open at http://127.0.0.1:5000
echo Press Ctrl+C to stop the server
echo.
"%PY_CMD%" app.py