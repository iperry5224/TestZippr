# SOPRA - SAE On-Premise Risk Assessment Launcher
# PowerShell Profile Commands

$SOPRA_PORT = 8080
$SOPRA_FILE = "sopra_setup.py"

function Start-SOPRA {
    param(
        [switch]$NoNgrok
    )
    
    Write-Host ""
    Write-Host "  ============================================================" -ForegroundColor Cyan
    Write-Host "  SOPRA - SAE On-Premise Risk Assessment" -ForegroundColor Cyan
    Write-Host "  Enterprise Infrastructure Security Assessment Tool" -ForegroundColor White
    Write-Host "  ============================================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Stop any existing instances
    Write-Host "  Stopping any existing SOPRA instances..." -ForegroundColor Yellow
    Stop-SOPRA -Quiet
    Start-Sleep -Seconds 1
    
    # Start Streamlit
    Write-Host "  Starting SOPRA..." -ForegroundColor Green
    $env:STREAMLIT_SERVER_PORT = $SOPRA_PORT
    Start-Process -FilePath "streamlit" -ArgumentList "run", $SOPRA_FILE, "--server.port=$SOPRA_PORT", "--server.address=localhost" -WindowStyle Hidden
    Start-Sleep -Seconds 3
    
    Write-Host "  SOPRA started" -ForegroundColor Green
    Write-Host "    Local URL: http://localhost:$SOPRA_PORT" -ForegroundColor White
    
    if (-not $NoNgrok) {
        Write-Host ""
        Write-Host "  Starting ngrok tunnel for SOPRA..." -ForegroundColor Green
        Start-Process -FilePath "ngrok" -ArgumentList "http", $SOPRA_PORT -WindowStyle Hidden
        Start-Sleep -Seconds 3
        
        try {
            $ngrokApi = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -ErrorAction Stop
            $publicUrl = $ngrokApi.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1 -ExpandProperty public_url
            if ($publicUrl) {
                Write-Host "  ngrok started" -ForegroundColor Green
                Write-Host "    Public URL: $publicUrl" -ForegroundColor Magenta
            }
        } catch {
            Write-Host "  ngrok may still be starting..." -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
    Write-Host "  ============================================================" -ForegroundColor Cyan
    Write-Host "  Commands: killsopra | sopra -nongrok" -ForegroundColor White
    Write-Host "  ============================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Stop-SOPRA {
    param([switch]$Quiet)
    
    if (-not $Quiet) {
        Write-Host "  Stopping SOPRA..." -ForegroundColor Yellow
    }
    
    # Kill Streamlit processes running SOPRA
    Get-Process -Name "streamlit" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
        $_.MainWindowTitle -like "*opra*" -or $_.CommandLine -like "*opra*"
    } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    if (-not $Quiet) {
        Write-Host "  SOPRA stopped" -ForegroundColor Green
    }
}

# Aliases
Set-Alias -Name sopra -Value Start-SOPRA
Set-Alias -Name killsopra -Value Stop-SOPRA

Write-Host "SOPRA commands loaded:" -ForegroundColor Cyan
Write-Host "  sopra           - Start SOPRA + ngrok" -ForegroundColor White
Write-Host "  sopra -nongrok  - Start SOPRA only (no ngrok)" -ForegroundColor White
Write-Host "  killsopra       - Stop SOPRA" -ForegroundColor White
