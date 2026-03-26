#!/bin/bash
# SOPSAEL - Start SAELAR + SOPRA containers on EC2
# Uses --network host so containers inherit instance IAM credentials (Bedrock)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOPSAEL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SOPSAEL_DIR"

# Stop and remove existing containers
sudo docker stop sopsael-saelar sopsael-sopra 2>/dev/null || true
sudo docker rm sopsael-saelar sopsael-sopra 2>/dev/null || true

# Run with host network - containers inherit EC2 instance IAM role (Bedrock access)
# No -p needed: app binds directly to host ports 8443 and 5224
sudo docker run -d \
  --name sopsael-saelar \
  --restart unless-stopped \
  --network host \
  -e AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}" \
  -e AWS_REGION="${AWS_REGION:-us-east-1}" \
  sopsael-saelar

sudo docker run -d \
  --name sopsael-sopra \
  --restart unless-stopped \
  --network host \
  -e AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}" \
  -e AWS_REGION="${AWS_REGION:-us-east-1}" \
  sopsael-sopra

echo "Containers started. SAELAR:8443 SOPRA:5224"
sudo docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
