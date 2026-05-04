#!/bin/bash
#===============================================================================
# Install the GRCP S3 Deploy Agent as a systemd service
# Run once on the EC2: sudo bash install_deploy_agent.sh
#===============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_SCRIPT="$SCRIPT_DIR/s3_deploy_agent.sh"

echo "[1/3] Installing deploy agent script..."
cp "$AGENT_SCRIPT" /usr/local/bin/grcp-deploy-agent.sh
chmod +x /usr/local/bin/grcp-deploy-agent.sh

echo "[2/3] Creating systemd service..."
cat > /etc/systemd/system/grcp-deploy-agent.service << 'EOF'
[Unit]
Description=GRCP - S3 Deploy Agent
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
Environment=S3_BUCKET_NAME=saelarallpurpose
Environment=AWS_DEFAULT_REGION=us-east-1
Environment=DEPLOY_POLL_INTERVAL=60
ExecStart=/bin/bash /usr/local/bin/grcp-deploy-agent.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "[3/3] Enabling and starting service..."
systemctl daemon-reload
systemctl enable grcp-deploy-agent
systemctl start grcp-deploy-agent

echo ""
echo "✓ GRCP Deploy agent installed and running!"
echo ""
echo "  Check status:  sudo systemctl status grcp-deploy-agent"
echo "  View logs:     sudo journalctl -u grcp-deploy-agent -f"
echo ""
echo "  How it works:"
echo "    - Polls s3://saelarallpurpose/deployments/grcp-latest.zip every 60s"
echo "    - When a new version is detected, auto-deploys to /home/ec2-user/grcp/"
echo "    - Backs up current state before each deploy (keeps last 5)"
echo ""
