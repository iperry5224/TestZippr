#!/bin/bash
cd "$(dirname "$0")"

# IMDSv2: get token first (required when metadata requires auth)
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 60" --max-time 2 2>/dev/null)
PUBLIC_IP="localhost"
if [ -n "$TOKEN" ]; then
  PUBLIC_IP=$(curl -s --max-time 2 -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null)
fi
[[ ! "$PUBLIC_IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] && PUBLIC_IP="localhost"

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║   SAELAR - NIST 800-53 + 800-30 Risk Assessment                       ║"
echo "║   🔒 Powered by AWS Bedrock                                           ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Access: http://${PUBLIC_IP}:8443"
echo ""

streamlit run nist_setup.py \
    --server.port 8443 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.fileWatcherType none
