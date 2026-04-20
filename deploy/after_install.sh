#!/bin/bash
#===============================================================================
# GRCP — Post-deployment hook
# Sets permissions, installs dependencies, and restarts all apps
#===============================================================================

GRCP_HOME="/home/ec2-user/grcp"

echo "[CodeDeploy] Setting permissions..."
chown -R ec2-user:ec2-user "$GRCP_HOME"

#----------------------------------------------------------------------
# For each app directory: install deps and restart if service exists
#----------------------------------------------------------------------
for app_dir in "$GRCP_HOME"/*/; do
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
    svc_name="grcp-${app_name}"
    if systemctl is-enabled "$svc_name" 2>/dev/null; then
        echo "[CodeDeploy]   Restarting $svc_name service..."
        systemctl restart "$svc_name"
    fi
done

sleep 3

echo "[CodeDeploy] Deployment complete. Running services:"
systemctl list-units --type=service --state=running | grep -E "grcp-" || echo "  (no GRCP services registered yet)"
