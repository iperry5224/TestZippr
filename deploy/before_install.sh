#!/bin/bash
#===============================================================================
# GRCP — Pre-deployment hook
# Stops any running apps and backs up current state
#===============================================================================

GRCP_HOME="/home/ec2-user/grcp"
BACKUP_DIR="/home/ec2-user/.grcp_backups/$(date +%Y%m%d_%H%M%S)"

echo "[CodeDeploy] Stopping running services..."

# Stop known GRCP services
for svc in grcp-saelar grcp-sopra grcp-beekeeper saelar sopra beekeeper; do
    systemctl stop "$svc" 2>/dev/null || true
done

# Catch any manually started Streamlit apps
pkill -f "streamlit run" 2>/dev/null || true
sleep 2

# Back up current state
echo "[CodeDeploy] Backing up ${GRCP_HOME}..."
mkdir -p "$BACKUP_DIR"
if [ -d "$GRCP_HOME" ]; then
    cp -r "$GRCP_HOME" "$BACKUP_DIR/" 2>/dev/null || true
    echo "[CodeDeploy] Backup saved to $BACKUP_DIR"
fi

echo "[CodeDeploy] Ready for install"
