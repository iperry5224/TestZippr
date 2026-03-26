@echo off
REM Usage: run beekeeper
if /i "%~1"=="beekeeper" (
    cd /d "%~dp0"
    streamlit run container_xray_app.py
) else (
    echo Usage: run beekeeper
    echo   Launches BeeKeeper — Automated Container Security Platform
)
