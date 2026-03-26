# Servator - Run Command Center
# Usage: .\run_servator.ps1

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host ""
Write-Host "  Servator - AI Retail Security Platform" -ForegroundColor Cyan
Write-Host "  Starting Command Center..." -ForegroundColor White
Write-Host ""

& python -m streamlit run servator/app/dashboard.py --server.port 8501
