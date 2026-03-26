# Run SAELAR in browser via SSH tunnel to sandbox EC2
# Same config as run_install_on_sandbox.ps1 - edit to match your setup

$EC2_HOST = "ec2-user@<YOUR_SANDBOX_IP_OR_DNS>"   # e.g. ec2-user@10.40.25.221 (VPN) or ec2-xx-xx-xx.compute-1.amazonaws.com
$KEY_PATH = "saelar-sopra-key.pem"                  # Path to your .pem key
# Must match port in start_saelar.sh (install script uses 8080)
$LOCAL_PORT = 8080
$REMOTE_PORT = 8080

# Resolve key path if relative
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not [System.IO.Path]::IsPathRooted($KEY_PATH)) {
    $KEY_PATH = Join-Path $ScriptDir $KEY_PATH
}

if (-not (Test-Path $KEY_PATH)) {
    Write-Host "Key not found: $KEY_PATH" -ForegroundColor Red
    Write-Host "Edit KEY_PATH in this script."
    exit 1
}

if ($EC2_HOST -match "<YOUR_") {
    Write-Host "Edit EC2_HOST in this script with your sandbox IP or hostname." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "  SAELAR Sandbox - Browser Tunnel" -ForegroundColor Cyan
Write-Host "  Connecting to $EC2_HOST..." -ForegroundColor Gray
Write-Host ""

# Start SSH tunnel in a new window (must stay open while browsing)
$tunnelArgs = "-i", $KEY_PATH, "-L", "${LOCAL_PORT}:localhost:${REMOTE_PORT}", "-N", $EC2_HOST
Start-Process -FilePath "ssh" -ArgumentList $tunnelArgs -WindowStyle Normal

Start-Sleep -Seconds 2

# Open browser - same experience as local SAELAR
Write-Host "  Opening http://localhost:$LOCAL_PORT in your browser..." -ForegroundColor Green
Start-Process "http://localhost:$LOCAL_PORT"

Write-Host ""
Write-Host "  SAELAR is available at http://localhost:$LOCAL_PORT" -ForegroundColor Yellow
Write-Host "  Keep the SSH tunnel window open while using SAELAR." -ForegroundColor Gray
Write-Host "  To stop: close the tunnel window (or press Ctrl+C in it)." -ForegroundColor Gray
Write-Host ""
