#!/bin/bash
#===============================================================================
# Generate self-signed SSL certs on EC2 for SAELAR and SOPRA HTTPS
# Run this on EC2 (e.g. via enable_ec2_https.ps1)
#===============================================================================

set -e
CERT_DIR="/opt/apps/ssl_certs"
DAYS_VALID=3650

echo "Generating SSL certificates for HTTPS..."
sudo mkdir -p "$CERT_DIR"
sudo chown ubuntu:ubuntu "$CERT_DIR"
cd "$CERT_DIR"

# Use EC2 public IP or localhost for CN (self-signed works with both)
CN="localhost"
if command -v curl &>/dev/null; then
  TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 60" --max-time 2 2>/dev/null || true)
  if [ -n "$TOKEN" ]; then
    IP=$(curl -s --max-time 2 -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || true)
    [[ "$IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] && CN="$IP"
  fi
fi

openssl req -x509 -nodes -days $DAYS_VALID -newkey rsa:2048 \
  -keyout streamlit.key \
  -out streamlit.crt \
  -subj "/C=US/ST=State/L=City/O=SecurityAssessment/CN=$CN"

chmod 600 streamlit.key
chmod 644 streamlit.crt
echo "SSL certs created in $CERT_DIR"
