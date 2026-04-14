#!/bin/bash
#===============================================================================
# SAE GRC Tools — S3 Deploy Agent
#===============================================================================
# Polls S3 for new deployment artifacts and auto-deploys to EC2.
# Runs as a systemd service — no CodeDeploy required.
#
# How it works:
#   1. Checks S3 for a deploy marker file (deploy_manifest.json)
#   2. Compares the version hash to the last deployed version
#   3. If new version detected: downloads, stops apps, deploys, restarts
#   4. Sleeps and polls again
#
# Usage:
#   sudo python3 s3_deploy_agent.sh   (or install as systemd service)
#===============================================================================

set -euo pipefail

S3_BUCKET="${S3_BUCKET_NAME:-saelarallpurpose}"
S3_PREFIX="deployments"
GRC_HOME="/home/ec2-user/grc_tools"
DEPLOY_STATE="/home/ec2-user/.grc_deploy_state"
BACKUP_DIR="/home/ec2-user/.grc_backups"
POLL_INTERVAL="${DEPLOY_POLL_INTERVAL:-60}"
LOG_TAG="[grc-deploy]"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"

mkdir -p "$DEPLOY_STATE" "$BACKUP_DIR" "$GRC_HOME"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $LOG_TAG $1"
}

get_s3_etag() {
    aws s3api head-object \
        --bucket "$S3_BUCKET" \
        --key "$S3_PREFIX/grc-tools-latest.zip" \
        --query 'ETag' \
        --output text \
        --region "$REGION" 2>/dev/null || echo "none"
}

get_last_deployed_etag() {
    cat "$DEPLOY_STATE/last_etag" 2>/dev/null || echo "none"
}

save_deployed_etag() {
    echo "$1" > "$DEPLOY_STATE/last_etag"
}

stop_services() {
    log "Stopping GRC services..."
    for svc in saelar sopra beekeeper; do
        systemctl stop "$svc" 2>/dev/null || true
    done
    pkill -f "streamlit run" 2>/dev/null || true
    sleep 2
}

start_services() {
    log "Starting GRC services..."
    for svc in saelar sopra beekeeper; do
        if systemctl is-enabled "$svc" 2>/dev/null; then
            systemctl start "$svc"
            log "  Started $svc"
        fi
    done
}

do_deploy() {
    local etag="$1"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local tmp_zip="/tmp/grc-deploy-${timestamp}.zip"

    log "New deployment detected (ETag: $etag)"

    # Download
    log "Downloading artifact from s3://$S3_BUCKET/$S3_PREFIX/grc-tools-latest.zip..."
    aws s3 cp "s3://$S3_BUCKET/$S3_PREFIX/grc-tools-latest.zip" "$tmp_zip" --region "$REGION"

    if [ ! -f "$tmp_zip" ]; then
        log "ERROR: Download failed"
        return 1
    fi

    # Stop services
    stop_services

    # Backup
    log "Backing up current state..."
    local backup_path="$BACKUP_DIR/$timestamp"
    mkdir -p "$backup_path"
    cp -r "$GRC_HOME" "$backup_path/" 2>/dev/null || true

    # Deploy
    log "Extracting new files to $GRC_HOME..."
    unzip -o "$tmp_zip" -d "$GRC_HOME"

    # Fix permissions
    chown -R ec2-user:ec2-user "$GRC_HOME"

    # Install/update deps for each app
    for app_dir in "$GRC_HOME"/*/; do
        app_name=$(basename "$app_dir")
        if [ -f "$app_dir/venv/bin/activate" ] && [ -f "$app_dir/requirements.txt" ]; then
            log "  Updating dependencies for $app_name..."
            source "$app_dir/venv/bin/activate"
            pip install -q -r "$app_dir/requirements.txt" 2>/dev/null || true
            deactivate
        fi
        chmod +x "$app_dir"/*.sh 2>/dev/null || true
    done

    # Start services
    start_services

    # Record successful deployment
    save_deployed_etag "$etag"
    echo "$timestamp | $etag" >> "$DEPLOY_STATE/deploy_history.log"

    # Cleanup
    rm -f "$tmp_zip"

    # Clean old backups (keep last 5)
    ls -dt "$BACKUP_DIR"/*/ 2>/dev/null | tail -n +6 | xargs rm -rf 2>/dev/null || true

    log "Deployment complete!"
}

# ---- Main loop ----
log "S3 Deploy Agent started"
log "  Bucket: $S3_BUCKET"
log "  Prefix: $S3_PREFIX"
log "  Target: $GRC_HOME"
log "  Poll interval: ${POLL_INTERVAL}s"

while true; do
    current_etag=$(get_s3_etag)
    last_etag=$(get_last_deployed_etag)

    if [ "$current_etag" != "none" ] && [ "$current_etag" != "$last_etag" ]; then
        do_deploy "$current_etag" || log "ERROR: Deployment failed, will retry next cycle"
    fi

    sleep "$POLL_INTERVAL"
done
