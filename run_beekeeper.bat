@echo off
REM BeeKeeper — Automated Container Security Platform
cd /d "%~dp0"
streamlit run container_xray_app.py %*
