# Enable HTTPS on EC2 for direct access (SAELAR + SOPRA)
# Uses nginx reverse proxy - Streamlit and ngrok stay unchanged
# Direct HTTPS: https://18.232.122.255:8443 (SAELAR), https://18.232.122.255:8444 (SOPRA)

$EC2_HOST = if ($env:SAELAR_EC2_HOST) { $env:SAELAR_EC2_HOST } else { "ubuntu@18.232.122.255" }
$KEY_PATH = "saelar-sopra-key.pem"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not [System.IO.Path]::IsPathRooted($KEY_PATH)) {
    $KEY_PATH = Join-Path $ScriptDir $KEY_PATH
}

if (-not (Test-Path $KEY_PATH)) {
    Write-Host "Error: $KEY_PATH not found" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Enable HTTPS on EC2 (direct access only) ===" -ForegroundColor Cyan
Write-Host "Target: $EC2_HOST" -ForegroundColor Gray
Write-Host "ngrok: unchanged`n" -ForegroundColor Gray

# 1. Copy and run SSL cert generation script
Write-Host "1. Generating SSL certificates on EC2..." -ForegroundColor Cyan
scp -i $KEY_PATH -o StrictHostKeyChecking=no "$ScriptDir\ec2_ssl_setup.sh" "${EC2_HOST}:/tmp/ec2_ssl_setup.sh"
if ($LASTEXITCODE -ne 0) {
    Write-Host "   SCP failed." -ForegroundColor Red
    exit 1
}
$cmd1 = "sed -i 's/\r$//' /tmp/ec2_ssl_setup.sh; chmod +x /tmp/ec2_ssl_setup.sh; bash /tmp/ec2_ssl_setup.sh"
ssh -i $KEY_PATH -o StrictHostKeyChecking=no $EC2_HOST $cmd1
if ($LASTEXITCODE -ne 0) {
    Write-Host "   SSL setup failed." -ForegroundColor Red
    exit 1
}
Write-Host "   Done.`n" -ForegroundColor Green

# 2. Deploy splash page and nginx config
Write-Host "2. Setting up splash page and nginx..." -ForegroundColor Cyan
scp -i $KEY_PATH -o StrictHostKeyChecking=no "$ScriptDir\ec2_splash.html" "${EC2_HOST}:/tmp/splash_index.html"
scp -i $KEY_PATH -o StrictHostKeyChecking=no "$ScriptDir\ec2_nginx_https.conf" "${EC2_HOST}:/tmp/saelar-sopra-https.conf"
$cmd2 = @"
sudo apt-get update -qq && sudo apt-get install -y -qq nginx 2>/dev/null || true
sudo mkdir -p /opt/apps/splash
sudo cp /tmp/splash_index.html /opt/apps/splash/index.html
sudo chown -R ubuntu:ubuntu /opt/apps/splash
sudo cp /tmp/saelar-sopra-https.conf /etc/nginx/sites-available/saelar-sopra-https
sudo ln -sf /etc/nginx/sites-available/saelar-sopra-https /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
sudo nginx -t 2>/dev/null && sudo systemctl reload nginx || sudo systemctl restart nginx
"@
$cmd2 = $cmd2 -replace "`r`n", "`n"
ssh -i $KEY_PATH -o StrictHostKeyChecking=no $EC2_HOST $cmd2
Write-Host "   Done.`n" -ForegroundColor Green

# 3. Ensure ports 8443, 8444 are open (optional - user may need to run ensure_ec2_ports_open.py)
Write-Host "3. Ensure ports 8443 and 8444 are open in EC2 security group." -ForegroundColor Cyan
py "$ScriptDir\ensure_ec2_ports_open.py" 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "   (Run ensure_ec2_ports_open.py or add 8443, 8444 manually)" -ForegroundColor Yellow
}

Write-Host "`n=== HTTPS enabled ===" -ForegroundColor Green
Write-Host ""
Write-Host "Splash page:" -ForegroundColor White
Write-Host "  http://18.232.122.255" -ForegroundColor Gray
Write-Host ""
Write-Host "Direct access (HTTPS, no ngrok in URL):" -ForegroundColor White
Write-Host "  SAELAR: https://18.232.122.255:8443" -ForegroundColor Gray
Write-Host "  SOPRA:  https://18.232.122.255:8444" -ForegroundColor Gray
Write-Host ""
Write-Host "ngrok (unchanged):" -ForegroundColor White
Write-Host "  https://saelar.ngrok.dev" -ForegroundColor Gray
Write-Host "  https://sopra.ngrok.dev" -ForegroundColor Gray
Write-Host ""
Write-Host "Note: Browser may show warning for self-signed cert - click Advanced > Proceed." -ForegroundColor Yellow
Write-Host ""
