#!/bin/bash
# Post-deployment: install dependencies and restart SAELAR
SAELAR_DIR="/home/ec2-user/saelar"

echo "[CodeDeploy] Setting permissions..."
chown -R ec2-user:ec2-user "$SAELAR_DIR"
chmod +x "$SAELAR_DIR/start_saelar.sh" 2>/dev/null || true

# Install/update dependencies if venv exists
if [ -f "$SAELAR_DIR/venv/bin/activate" ]; then
    echo "[CodeDeploy] Updating dependencies..."
    source "$SAELAR_DIR/venv/bin/activate"
    pip install -q -r "$SAELAR_DIR/requirements.txt" 2>/dev/null || true
    deactivate
fi

# Restart via systemd if service exists, otherwise start directly
if systemctl is-enabled saelar 2>/dev/null; then
    echo "[CodeDeploy] Restarting SAELAR via systemd..."
    systemctl restart saelar
else
    echo "[CodeDeploy] Starting SAELAR directly..."
    cd "$SAELAR_DIR"
    source venv/bin/activate
    nohup streamlit run nist_setup.py \
        --server.port 8484 \
        --server.address 0.0.0.0 \
        --server.headless true \
        --server.fileWatcherType none &
fi

sleep 3

# Verify
if pgrep -f "streamlit run nist_setup" > /dev/null; then
    echo "[CodeDeploy] SAELAR is running"
else
    echo "[CodeDeploy] WARNING: SAELAR may not have started"
fi
