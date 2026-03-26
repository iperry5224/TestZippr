# Deploy BeeKeeper to EC2 (port 2323)
# Creates /opt/apps/beekeeper, copies files, starts Streamlit

$EC2_HOST = if ($env:BEEKEEPER_EC2_HOST) { $env:BEEKEEPER_EC2_HOST } else { "ubuntu@18.232.122.255" }
$KEY_PATH = "saelar-sopra-key.pem"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not [System.IO.Path]::IsPathRooted($KEY_PATH)) {
    $KEY_PATH = Join-Path $ScriptDir $KEY_PATH
}

Write-Host "Deploying BeeKeeper to EC2 (port 2323)..." -ForegroundColor Cyan

# 1. Ensure port 2323 is open in security group
Write-Host "`n1. Ensuring port 2323 is open..." -ForegroundColor Cyan
py "$ScriptDir\ensure_ec2_ports_open.py" 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "   (Port check skipped - add 2323 to security group manually if needed)" -ForegroundColor Yellow
}

# 2. Copy files to staging on EC2
Write-Host "`n2. Copying BeeKeeper files to EC2..." -ForegroundColor Cyan
$staging = "/tmp/beekeeper_update"
ssh -i $KEY_PATH -o StrictHostKeyChecking=no $EC2_HOST "mkdir -p $staging/container_xray/assets $staging/.streamlit"
scp -i $KEY_PATH -o StrictHostKeyChecking=no "$ScriptDir\container_xray_app.py" "${EC2_HOST}:${staging}/"
$configSrc = if (Test-Path "$ScriptDir\.streamlit\beekeeper_config.toml") { "$ScriptDir\.streamlit\beekeeper_config.toml" } else { "$ScriptDir\.streamlit\config.toml" }
if (Test-Path $configSrc) {
    scp -i $KEY_PATH -o StrictHostKeyChecking=no $configSrc "${EC2_HOST}:${staging}/.streamlit/config.toml"
}
scp -i $KEY_PATH -o StrictHostKeyChecking=no "$ScriptDir\container_xray\__init__.py" "${EC2_HOST}:${staging}/container_xray/"
scp -i $KEY_PATH -o StrictHostKeyChecking=no "$ScriptDir\container_xray\scanner.py" "${EC2_HOST}:${staging}/container_xray/"
scp -i $KEY_PATH -o StrictHostKeyChecking=no "$ScriptDir\container_xray\ai_engine.py" "${EC2_HOST}:${staging}/container_xray/"
scp -i $KEY_PATH -o StrictHostKeyChecking=no "$ScriptDir\container_xray\test_data.py" "${EC2_HOST}:${staging}/container_xray/"
scp -i $KEY_PATH -o StrictHostKeyChecking=no "$ScriptDir\container_xray\assets\beekeeper_logo.png" "${EC2_HOST}:${staging}/container_xray/assets/"
scp -i $KEY_PATH -o StrictHostKeyChecking=no "$ScriptDir\beekeeper.service" "${EC2_HOST}:${staging}/"

if ($LASTEXITCODE -ne 0) {
    Write-Host "SCP failed." -ForegroundColor Red
    exit 1
}

# 3. Deploy to /opt/apps/beekeeper, install systemd service, start
Write-Host "`n3. Deploying to /opt/apps/beekeeper and starting (port 2323)..." -ForegroundColor Cyan
$RemoteCmd = @"
sudo mkdir -p /opt/apps/beekeeper
sudo cp -f /tmp/beekeeper_update/container_xray_app.py /opt/apps/beekeeper/
sudo mkdir -p /opt/apps/beekeeper/.streamlit
sudo cp -f /tmp/beekeeper_update/.streamlit/config.toml /opt/apps/beekeeper/.streamlit/ 2>/dev/null || true
sudo mkdir -p /opt/apps/beekeeper/container_xray
sudo cp -f /tmp/beekeeper_update/container_xray/__init__.py /opt/apps/beekeeper/container_xray/
sudo cp -f /tmp/beekeeper_update/container_xray/scanner.py /opt/apps/beekeeper/container_xray/
sudo cp -f /tmp/beekeeper_update/container_xray/ai_engine.py /opt/apps/beekeeper/container_xray/
sudo cp -f /tmp/beekeeper_update/container_xray/test_data.py /opt/apps/beekeeper/container_xray/
sudo mkdir -p /opt/apps/beekeeper/container_xray/assets
sudo cp -f /tmp/beekeeper_update/container_xray/assets/beekeeper_logo.png /opt/apps/beekeeper/container_xray/assets/
if [ -d /tmp/beekeeper_update/.streamlit ]; then sudo mkdir -p /opt/apps/beekeeper/.streamlit && sudo cp -f /tmp/beekeeper_update/.streamlit/config.toml /opt/apps/beekeeper/.streamlit/; fi
sudo chown -R ubuntu:ubuntu /opt/apps/beekeeper

sudo cp -f /tmp/beekeeper_update/beekeeper.service /tmp/
sudo mv /tmp/beekeeper.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable beekeeper
sudo systemctl restart beekeeper
sleep 2
sudo systemctl is-active beekeeper
ss -tlnp | grep 2323 || echo '(check: sudo journalctl -u beekeeper -n 30)'
"@
$RemoteCmd = $RemoteCmd -replace "`r`n", "`n"
ssh -i $KEY_PATH -o StrictHostKeyChecking=no $EC2_HOST $RemoteCmd

Write-Host "`nDone. BeeKeeper is available at: http://18.232.122.255:2323" -ForegroundColor Green
Write-Host "  (Ensure port 2323 is open in your EC2 security group)" -ForegroundColor Gray
