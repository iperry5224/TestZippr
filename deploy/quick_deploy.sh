#!/bin/bash
#===============================================================================
# GRCP — Quick Deploy
#===============================================================================
# Manually package and push to S3 from CloudShell or any machine with AWS CLI.
# The EC2 deploy agent will pick it up automatically.
#
# Usage (from CloudShell):
#   cd /path/to/your/project
#   bash deploy/quick_deploy.sh
#===============================================================================

S3_BUCKET="${S3_BUCKET_NAME:-saelarallpurpose}"
S3_PREFIX="deployments"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║   GRCP — Quick Deploy to EC2                                  ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

echo "[1/3] Packaging..."
zip -r /tmp/grcp-latest.zip . \
    -x '.git/*' '__pycache__/*' '*.pyc' '.env*' '*.pem' '*.key' 'venv/*' '.venv/*'

echo "[2/3] Uploading to s3://$S3_BUCKET/$S3_PREFIX/grcp-latest.zip..."
aws s3 cp /tmp/grcp-latest.zip "s3://$S3_BUCKET/$S3_PREFIX/grcp-latest.zip" --region "$REGION"

echo "[3/3] Done!"
echo ""
echo "  The EC2 deploy agent will detect the new artifact within 60 seconds."
echo "  Monitor on EC2: sudo journalctl -u grcp-deploy-agent -f"
echo ""

rm -f /tmp/grcp-latest.zip
