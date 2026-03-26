@echo off
REM SAELAR - Air-Gapped Mode Launch Command
REM Runs SAELAR without any internet connectivity requirements
REM Requires Ollama to be running locally

echo.
echo   ============================================================
echo   SAELAR - Security Architecture and Evaluation
echo   AIR-GAPPED MODE (No Internet Required)
echo   ============================================================
echo.

REM Set air-gapped mode environment variable
set SAELAR_AIRGAPPED=true

REM Check if Ollama is running
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo   [WARNING] Ollama is not running!
    echo.
    echo   To start Ollama:
    echo     1. Open a new terminal
    echo     2. Run: ollama serve
    echo     3. Then run this script again
    echo.
    echo   To install Ollama: https://ollama.ai
    echo.
    pause
    exit /b 1
)

echo   [OK] Ollama is running
echo   [OK] Air-gapped mode enabled
echo.

cd /d "C:\Users\iperr\TestZippr"
set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
echo   Starting SAELAR on http://localhost:8501
echo.
python -m streamlit run nist_setup.py --server.port 8501 --server.headless true %*
