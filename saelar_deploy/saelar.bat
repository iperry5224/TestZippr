@echo off
REM SAELAR - Security Architecture and Evaluation Launch Command
REM Launches the NIST 800-53 Rev 5 Assessment Tool

cd /d "C:\Users\iperr\TestZippr"
call "C:\Users\iperr\TestZippr\security-venv\Scripts\activate.bat"
streamlit run nist_setup.py --server.port 8484 %*
