#!/bin/bash
# Stop SAELAR before deploying new files
echo "[CodeDeploy] Stopping SAELAR..."
systemctl stop saelar 2>/dev/null || pkill -f "streamlit run nist_setup.py" 2>/dev/null || true
sleep 2

# Back up current version
BACKUP_DIR="/home/ec2-user/.saelar_backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
if [ -f /home/ec2-user/saelar/nist_setup.py ]; then
    cp /home/ec2-user/saelar/*.py "$BACKUP_DIR/" 2>/dev/null || true
    echo "[CodeDeploy] Backup saved to $BACKUP_DIR"
fi

echo "[CodeDeploy] Ready for install"
