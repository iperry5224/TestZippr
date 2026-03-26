# Deploy local SOPRA updates to EC2 (Verify All Evidence, etc.)
# Edit EC2_HOST and KEY_PATH to match your setup

# SAELAR-SOPRA-Server - public IP for direct access (no VPN)
# CRITICAL: Use ubuntu (not ec2-user) - Ubuntu AMI uses ubuntu user
$EC2_HOST = if ($env:SOPRA_EC2_HOST) { $env:SOPRA_EC2_HOST } else { "ubuntu@18.232.122.255" }
$KEY_PATH = if ($env:SOPRA_EC2_KEY) { $env:SOPRA_EC2_KEY } else { "saelar-sopra-key.pem" }

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not [System.IO.Path]::IsPathRooted($KEY_PATH)) {
    $KEY_PATH = Join-Path $ScriptDir $KEY_PATH
}

# Build update zip
Write-Host "Building sopra_ec2_update.zip..." -ForegroundColor Cyan
python "$ScriptDir\create_sopra_ec2_update.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to create zip." -ForegroundColor Red
    exit 1
}

$ZipPath = Join-Path $ScriptDir "sopra_ec2_update.zip"
if (-not (Test-Path $ZipPath)) {
    Write-Host "Zip not found." -ForegroundColor Red
    exit 1
}

if ($EC2_HOST -match "<YOUR_") {
    Write-Host "Edit EC2_HOST in this script with your sandbox IP or hostname." -ForegroundColor Red
    exit 1
}

# Copy to EC2
Write-Host "`nCopying to EC2..." -ForegroundColor Cyan
scp -i $KEY_PATH $ZipPath "${EC2_HOST}:~/sopra_ec2_update.zip"
if ($LASTEXITCODE -ne 0) {
    Write-Host "SCP failed." -ForegroundColor Red
    exit 1
}

# Deploy on EC2 (unzip, restart SOPRA in background)
# SOPRA runs on port 8180 - pkill matches streamlit running sopra_setup
Write-Host "`nDeploying on EC2 (unzip, restart SOPRA)..." -ForegroundColor Cyan
$RemoteCmd = @"
cd ~
pkill -f 'streamlit run sopra_setup' 2>/dev/null || true
sleep 1
unzip -o sopra_ec2_update.zip
chmod +x start_sopra.sh 2>/dev/null || true
echo 'Update applied. Starting SOPRA in background...'
nohup ./start_sopra.sh > /tmp/sopra.log 2>&1 &
sleep 2
echo 'SOPRA restarted on port 8180. Check ngrok URL or SSH tunnel.'
"@
ssh -i $KEY_PATH $EC2_HOST $RemoteCmd

Write-Host "`nDone. SOPRA updated on EC2 (port 8180)." -ForegroundColor Green
