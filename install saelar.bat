@echo off
REM Run:  "install saelar"   (from this folder, or add this folder to PATH)
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_saelar.ps1" %*
if "%1"=="" pause
