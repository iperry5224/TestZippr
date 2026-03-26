#!/bin/bash
#===============================================================================
# SOPRA — start Streamlit (after ./install_sopra.sh)
# Default port 8080; override with SOPRA_PORT=8180 ./start_sopra.sh
#===============================================================================

cd "$(dirname "$0")"

if [ ! -f "venv/bin/activate" ]; then
    echo "ERROR: venv not found. Run ./install_sopra.sh first."
    exit 1
fi

# shellcheck source=/dev/null
source "venv/bin/activate"

PORT="${SOPRA_PORT:-8080}"

TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
    -H "X-aws-ec2-metadata-token-ttl-seconds: 60" --max-time 2 2>/dev/null || true)
PUBLIC_IP="localhost"
if [ -n "$TOKEN" ]; then
    PUBLIC_IP=$(curl -s --max-time 2 -H "X-aws-ec2-metadata-token: $TOKEN" \
        http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || true)
fi
[[ ! "$PUBLIC_IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] && PUBLIC_IP="localhost"

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║   SOPRA - SAE On-Premise Risk Assessment                              ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "  URL:  http://${PUBLIC_IP}:${PORT}"
echo ""

exec streamlit run sopra_setup.py \
    --server.port "${PORT}" \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.fileWatcherType none
