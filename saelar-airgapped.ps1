# SAELAR - Air-Gapped Mode Launch Script
# Runs SAELAR without any internet connectivity requirements
# Requires Ollama to be running locally

$SAELAR_PORT = 8501

function Start-SAELAR-Airgapped {
    Write-Host ""
    Write-Host "  ============================================================" -ForegroundColor Cyan
    Write-Host "  SAELAR - Security Architecture and Evaluation" -ForegroundColor Cyan
    Write-Host "  AIR-GAPPED MODE (No Internet Required)" -ForegroundColor Yellow
    Write-Host "  ============================================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Set air-gapped mode
    $env:SAELAR_AIRGAPPED = "true"
    
    # Check if Ollama is running
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction Stop
        Write-Host "  [OK] Ollama is running" -ForegroundColor Green
        
        # List available models
        $models = $response.models | ForEach-Object { $_.name }
        if ($models.Count -gt 0) {
            Write-Host "  [OK] Available models: $($models[0..2] -join ', ')" -ForegroundColor Green
        }
    } catch {
        Write-Host "  [ERROR] Ollama is not running!" -ForegroundColor Red
        Write-Host ""
        Write-Host "  To start Ollama:" -ForegroundColor Yellow
        Write-Host "    1. Open a new terminal" -ForegroundColor White
        Write-Host "    2. Run: ollama serve" -ForegroundColor White
        Write-Host "    3. Then run this script again" -ForegroundColor White
        Write-Host ""
        Write-Host "  To install Ollama: https://ollama.ai" -ForegroundColor Cyan
        Write-Host ""
        return
    }
    
    Write-Host "  [OK] Air-gapped mode enabled" -ForegroundColor Green
    Write-Host ""
    
    # Start SAELAR
    Set-Location "C:\Users\iperr\TestZippr"
    $env:STREAMLIT_BROWSER_GATHER_USAGE_STATS = "false"
    
    Write-Host "  Starting SAELAR on http://localhost:$SAELAR_PORT" -ForegroundColor White
    Write-Host ""
    
    python -m streamlit run nist_setup.py --server.port $SAELAR_PORT --server.headless true
}

# Aliases
Set-Alias -Name saelar-airgapped -Value Start-SAELAR-Airgapped

Write-Host "SAELAR Air-Gapped commands loaded:" -ForegroundColor Cyan
Write-Host "  saelar-airgapped  - Start SAELAR in air-gapped mode (Ollama)" -ForegroundColor White
Write-Host ""
Write-Host "Prerequisites:" -ForegroundColor Yellow
Write-Host "  1. Install Ollama: https://ollama.ai" -ForegroundColor White
Write-Host "  2. Run: ollama serve" -ForegroundColor White
Write-Host "  3. Pull a model: ollama pull llama3:8b" -ForegroundColor White
Write-Host ""

# Auto-start if script is run directly (not dot-sourced)
if ($MyInvocation.InvocationName -ne '.') {
    Start-SAELAR-Airgapped
}
