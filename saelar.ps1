# SAELAR - Security Architecture and Evaluation Launch Command
# Launches the NIST 800-53 Rev 5 Assessment Tool

param(
    [switch]$https,
    [string]$port = "8443"
)

$ErrorActionPreference = "Stop"

# Change to project directory
Set-Location "C:\Users\iperr\TestZippr"

# Activate virtual environment
& "C:\Users\iperr\TestZippr\security-venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "  ╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║                                                           ║" -ForegroundColor Cyan
Write-Host "  ║   🛡️  SAELAR - Real-Time Risk Transparency & Remediation  ║" -ForegroundColor Cyan
Write-Host "  ║       NIST 800-53 Rev 5 Security Assessment Tool          ║" -ForegroundColor Cyan
Write-Host "  ║                                                           ║" -ForegroundColor Cyan
Write-Host "  ╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

if ($https) {
    Write-Host "  Starting with HTTPS enabled..." -ForegroundColor Green
    Write-Host "  URL: https://localhost:$port" -ForegroundColor Yellow
    Write-Host ""
    streamlit run nist_setup.py --server.port $port --server.sslCertFile=ssl_certs/streamlit.crt --server.sslKeyFile=ssl_certs/streamlit.key
} else {
    Write-Host "  Starting SAELAR..." -ForegroundColor Green
    Write-Host "  URL: http://localhost:$port" -ForegroundColor Yellow
    Write-Host ""
    streamlit run nist_setup.py --server.port $port
}
