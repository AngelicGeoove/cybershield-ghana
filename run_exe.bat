@echo off
echo Starting CyberShield Ghana...
echo ==============================
echo.
title CyberShield Ghana - Cyber Incident Reporting App
cd /d "%~dp0"
echo Launching application...
echo.
echo The app will open at http://127.0.0.1:5000
echo Press Ctrl+C to stop the server
echo.

REM Use the built exe from dist\ if present, otherwise look in this folder
set "EXE=CyberShieldGhana.exe"
if exist "dist\CyberShieldGhana.exe" set "EXE=dist\CyberShieldGhana.exe"
"%EXE%"