#===============================================================================
#  AWS Security Assessment Environment Setup - Windows PowerShell Wrapper
#===============================================================================
#  This script runs the setup_environment.sh script in WSL
#
#  Usage: .\setup_environment.ps1
#===============================================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     AWS Security Assessment Environment Setup                         ║" -ForegroundColor Cyan
Write-Host "║     Windows PowerShell Wrapper                                        ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$WslPath = "/mnt/" + $ScriptDir.Replace("\", "/").Replace(":", "").ToLower()

Write-Host "[INFO] Script directory: $ScriptDir" -ForegroundColor Blue
Write-Host "[INFO] WSL path: $WslPath" -ForegroundColor Blue
Write-Host ""

# Check if WSL is available
Write-Host "[INFO] Checking WSL installation..." -ForegroundColor Blue
try {
    $wslCheck = wsl --status 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "WSL not properly configured"
    }
    Write-Host "[✓] WSL is available" -ForegroundColor Green
} catch {
    Write-Host "[✗] WSL is not installed or not properly configured" -ForegroundColor Red
    Write-Host ""
    Write-Host "To install WSL, run the following in an elevated PowerShell:" -ForegroundColor Yellow
    Write-Host "  wsl --install" -ForegroundColor White
    Write-Host ""
    Write-Host "After installation, restart your computer and run this script again." -ForegroundColor Yellow
    exit 1
}

# Check if setup script exists
$SetupScript = Join-Path $ScriptDir "setup_environment.sh"
if (-not (Test-Path $SetupScript)) {
    Write-Host "[✗] Setup script not found: $SetupScript" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting WSL setup..." -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
Write-Host ""

# Run the bash setup script in WSL
wsl bash -c "cd '$WslPath' && bash setup_environment.sh"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "[✓] Setup completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "To use the tools, open WSL and run:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  cd $WslPath" -ForegroundColor White
    Write-Host "  source activate_env.sh" -ForegroundColor White
    Write-Host ""
    Write-Host "Or use the launcher scripts:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  ./run_nist_controls.sh   # NIST 800-53 Assessment" -ForegroundColor White
    Write-Host "  ./run_pentest.sh         # Penetration Testing" -ForegroundColor White
    Write-Host "  ./run_assessment.sh      # Interactive Menu" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "[✗] Setup failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

