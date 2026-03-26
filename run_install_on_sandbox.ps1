# Run install_saelar_ec2.sh on SAELAR sandbox EC2
# Edit EC2_HOST and KEY_PATH below to match your setup

$EC2_HOST = "ec2-user@<YOUR_SANDBOX_IP_OR_DNS>"   # e.g. ec2-user@ec2-xx-xx-xx-xx.compute-1.amazonaws.com
$KEY_PATH = "saelar-sopra-key.pem"                  # Path to your .pem key (relative or absolute)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Copying install_saelar_ec2.sh to sandbox..." -ForegroundColor Cyan
scp -i $KEY_PATH "$ScriptDir\install_saelar_ec2.sh" "${EC2_HOST}:~/install_saelar_ec2.sh"

Write-Host "`nOn the sandbox, run:" -ForegroundColor Yellow
Write-Host "  cd ~" 
Write-Host "  # (or cd to the dir with nist_setup.py if SAELAR is in a subdir)"
Write-Host "  chmod +x install_saelar_ec2.sh"
Write-Host "  ./install_saelar_ec2.sh"
Write-Host "`nConnecting via SSH..." -ForegroundColor Cyan
ssh -i $KEY_PATH $EC2_HOST
