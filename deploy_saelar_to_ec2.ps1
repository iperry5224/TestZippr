# Deploy local SAELAR updates to EC2 (Chad box, risk_score, start script)
# Edit EC2_HOST and KEY_PATH to match your setup

# Use ubuntu (not ec2-user) for Ubuntu AMI. Set SAELAR_EC2_HOST to override.
$EC2_HOST = if ($env:SAELAR_EC2_HOST) { $env:SAELAR_EC2_HOST } else { "ubuntu@18.232.122.255" }
$KEY_PATH = "saelar-sopra-key.pem"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not [System.IO.Path]::IsPathRooted($KEY_PATH)) {
    $KEY_PATH = Join-Path $ScriptDir $KEY_PATH
}

# Build update zip
Write-Host "Building saelar_ec2_update.zip..." -ForegroundColor Cyan
python "$ScriptDir\create_saelar_ec2_update.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to create zip." -ForegroundColor Red
    exit 1
}

$ZipPath = Join-Path $ScriptDir "saelar_ec2_update.zip"
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
scp -i $KEY_PATH $ZipPath "${EC2_HOST}:~/saelar_ec2_update.zip"
if ($LASTEXITCODE -ne 0) {
    Write-Host "SCP failed." -ForegroundColor Red
    exit 1
}

# Deploy on EC2: unzip, copy to /opt/apps (production path), restart systemd saelar service (port 8484 = ngrok)
Write-Host "`nDeploying on EC2 (copy to /opt/apps, restart saelar service)..." -ForegroundColor Cyan
$RemoteCmd = @"
cd ~
unzip -o -q saelar_ec2_update.zip -d /tmp/saelar_update
sudo cp -f /tmp/saelar_update/nist_setup.py /opt/apps/
[ -f /tmp/saelar_update/nist_dashboard.py ] && sudo cp -f /tmp/saelar_update/nist_dashboard.py /opt/apps/
[ -f /tmp/saelar_update/nist_pages.py ] && sudo cp -f /tmp/saelar_update/nist_pages.py /opt/apps/
[ -f /tmp/saelar_update/risk_score_app.py ] && sudo cp -f /tmp/saelar_update/risk_score_app.py /opt/apps/
[ -f /tmp/saelar_update/risk_score_calculator.py ] && sudo cp -f /tmp/saelar_update/risk_score_calculator.py /opt/apps/
sudo chown ubuntu:ubuntu /opt/apps/nist_setup.py /opt/apps/nist_dashboard.py /opt/apps/nist_pages.py /opt/apps/risk_score_app.py /opt/apps/risk_score_calculator.py 2>/dev/null || true
sudo systemctl restart saelar
sleep 2
echo 'SAELAR updated in /opt/apps and service restarted (port 8484). Check https://saelar.ngrok.dev'
"@
$RemoteCmd = $RemoteCmd -replace "`r`n", "`n"
ssh -i $KEY_PATH $EC2_HOST $RemoteCmd

Write-Host "`nDone." -ForegroundColor Green
