#!/bin/bash
#===============================================================================
# SAE GRC Tools — Post-deployment hook
# Sets permissions, installs dependencies, and restarts all apps
#===============================================================================

GRC_HOME="/home/ec2-user/grc_tools"

echo "[CodeDeploy] Setting permissions..."
chown -R ec2-user:ec2-user "$GRC_HOME"

#----------------------------------------------------------------------
# For each app directory: install deps and restart if service exists
#----------------------------------------------------------------------
for app_dir in "$GRC_HOME"/*/; do
    app_name=$(basename "$app_dir")
    echo "[CodeDeploy] Processing: $app_name"

    # Make scripts executable
    chmod +x "$app_dir"/*.sh 2>/dev/null || true

    # Install/update dependencies if venv and requirements.txt exist
    if [ -f "$app_dir/venv/bin/activate" ] && [ -f "$app_dir/requirements.txt" ]; then
        echo "[CodeDeploy]   Updating dependencies for $app_name..."
        source "$app_dir/venv/bin/activate"
        pip install -q -r "$app_dir/requirements.txt" 2>/dev/null || true
        deactivate
    fi

    # Restart systemd service if it exists
    svc_name=$(echo "$app_name" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
    if systemctl is-enabled "$svc_name" 2>/dev/null; then
        echo "[CodeDeploy]   Restarting $svc_name service..."
        systemctl restart "$svc_name"
    fi
done

sleep 3

echo "[CodeDeploy] Deployment complete. Running services:"
systemctl list-units --type=service --state=running | grep -E "saelar|sopra|beekeeper" || echo "  (no GRC services registered yet)"
