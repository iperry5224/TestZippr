#!/bin/bash
#===============================================================================
# GRCP — CodeDeploy Pipeline Setup
#===============================================================================
# Run this ONCE in AWS CloudShell to set up auto-deployment from CodeCommit
# to the GRC_Titan EC2 instance.
#
# Usage: bash setup_pipeline.sh
#===============================================================================

set -e

REGION="us-east-1"
ACCOUNT_ID="656443597515"
EC2_INSTANCE="i-0f5ecc5cc369e85fe"
APP_NAME="grcp-deploy"
DG_NAME="grcp-ec2"
DC_NAME="grcp-config"

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║   GRCP — CodeDeploy Pipeline Setup                            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    SETUP COMPLETE                              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "  Directory structure on EC2:"
echo "     /home/ec2-user/grcp/"
echo "       ├── saelar/        ← SAELAR-53"
echo "       ├── sopra/         ← SOPRA"
echo "       ├── beekeeper/     ← BeeKeeper"
echo "       └── <your_app>/    ← any future tool"
echo ""
echo "  1. Make sure your repo has these files:"
echo "     - appspec.yml (deployment instructions)"
echo "     - deploy/before_install.sh"
echo "     - deploy/after_install.sh"
echo ""
echo "  2. Push to CodeCommit:"
echo "     git push origin main"
echo ""
echo "  3. Deploy manually (or add Deploy stage to pipeline):"
echo "     aws deploy create-deployment \\"
echo "       --application-name ${APP_NAME} \\"
echo "       --deployment-group-name ${DG_NAME} \\"
echo "       --s3-location bucket=saelarallpurpose,key=deployments/grcp-latest.zip,bundleType=zip \\"
echo "       --region ${REGION}"
echo ""
echo "  Or add a Deploy stage to the existing ospo-csta pipeline:"
echo "     aws codepipeline update-pipeline --cli-input-json file://pipeline-update.json"
echo ""
