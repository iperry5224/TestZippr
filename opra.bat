@echo off
REM SOPRA - SAE On-Premise Risk Assessment Launch Command
REM Launches the SAE On-Premise Security Assessment Tool

echo.
echo   ============================================================
echo   SOPRA - SAE On-Premise Risk Assessment
echo   Enterprise Infrastructure Security Assessment Tool
echo   ============================================================
echo.

cd /d "C:\Users\iperr\TestZippr"
set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
echo   Starting SOPRA on http://localhost:8080
echo.
python -m streamlit run sopra_setup.py --server.port 8080 --server.headless true %*
