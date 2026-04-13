#!/bin/bash
#===============================================================================
# SAE GRC Tools — Pre-deployment hook
# Stops any running apps and backs up current state
#===============================================================================

GRC_HOME="/home/ec2-user/grc_tools"
BACKUP_DIR="/home/ec2-user/.grc_backups/$(date +%Y%m%d_%H%M%S)"

echo "[CodeDeploy] Stopping running services..."

# Stop known GRC tool services
for svc in saelar sopra beekeeper; do
    systemctl stop "$svc" 2>/dev/null || true
done

# Catch any manually started Streamlit apps
pkill -f "streamlit run" 2>/dev/null || true
sleep 2

# Back up current state
echo "[CodeDeploy] Backing up ${GRC_HOME}..."
mkdir -p "$BACKUP_DIR"
if [ -d "$GRC_HOME" ]; then
    cp -r "$GRC_HOME" "$BACKUP_DIR/" 2>/dev/null || true
    echo "[CodeDeploy] Backup saved to $BACKUP_DIR"
fi

echo "[CodeDeploy] Ready for install"
