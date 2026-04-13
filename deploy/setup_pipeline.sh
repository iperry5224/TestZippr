#!/bin/bash
#===============================================================================
# SAE GRC Tools — CodeDeploy Pipeline Setup
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
APP_NAME="sae-grc-deploy"
DG_NAME="sae-grc-ec2"
DC_NAME="sae-grc-config"
ROLE_NAME="saelar-role"
CODEDEPLOY_ROLE_NAME="SAE-CodeDeploy-Role"

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║   SAE GRC Tools — CodeDeploy Pipeline Setup                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

#----------------------------------------------------------------------
# Step 1: Add CodeDeploy agent to EC2
#----------------------------------------------------------------------
echo "[1/5] Installing CodeDeploy agent on EC2..."
echo ""
echo "  Run these commands on the EC2 (via Session Manager):"
echo ""
echo "    sudo bash"
echo "    yum install -y ruby wget 2>/dev/null || apt-get install -y ruby wget"
echo "    cd /tmp"
echo "    wget https://aws-codedeploy-${REGION}.s3.${REGION}.amazonaws.com/latest/install"
echo "    chmod +x install"
echo "    ./install auto"
echo "    systemctl enable codedeploy-agent"
echo "    systemctl start codedeploy-agent"
echo "    systemctl status codedeploy-agent"
echo ""
read -p "  Press Enter once the CodeDeploy agent is running on the EC2..."

#----------------------------------------------------------------------
# Step 2: Add CodeDeploy permissions to the EC2 IAM role
#----------------------------------------------------------------------
echo "[2/5] Adding CodeDeploy permissions to ${ROLE_NAME}..."

aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn arn:aws:iam::aws:policy/AmazonEC2RoleforAWSCodeDeploy 2>/dev/null \
    && echo "  ✓ AmazonEC2RoleforAWSCodeDeploy attached" \
    || echo "  ! Policy may already be attached"

#----------------------------------------------------------------------
# Step 3: Create CodeDeploy service role
#----------------------------------------------------------------------
echo "[3/5] Creating CodeDeploy service role..."

TRUST_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"Service": "codedeploy.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }
  ]
}'

aws iam create-role \
    --role-name "$CODEDEPLOY_ROLE_NAME" \
    --assume-role-policy-document "$TRUST_POLICY" \
    --description "CodeDeploy service role for SAE GRC deployments" 2>/dev/null \
    && echo "  ✓ Role created" \
    || echo "  ! Role may already exist"

aws iam attach-role-policy \
    --role-name "$CODEDEPLOY_ROLE_NAME" \
    --policy-arn arn:aws:iam::aws:policy/AWSCodeDeployRole 2>/dev/null \
    && echo "  ✓ AWSCodeDeployRole attached" \
    || echo "  ! Policy may already be attached"

echo "  Waiting 10s for IAM propagation..."
sleep 10

CODEDEPLOY_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${CODEDEPLOY_ROLE_NAME}"

#----------------------------------------------------------------------
# Step 4: Create CodeDeploy application and deployment group
#----------------------------------------------------------------------
echo "[4/5] Creating CodeDeploy application..."

aws deploy create-application \
    --application-name "$APP_NAME" \
    --compute-platform Server \
    --region "$REGION" 2>/dev/null \
    && echo "  ✓ Application '${APP_NAME}' created" \
    || echo "  ! Application may already exist"

echo "  Creating deployment group..."

aws deploy create-deployment-group \
    --application-name "$APP_NAME" \
    --deployment-group-name "$DG_NAME" \
    --deployment-config-name CodeDeployDefault.AllAtOnce \
    --ec2-tag-filters Key=Name,Value=GRC_Titan,Type=KEY_AND_VALUE \
    --service-role-arn "$CODEDEPLOY_ROLE_ARN" \
    --auto-rollback-configuration enabled=true,events=DEPLOYMENT_FAILURE \
    --region "$REGION" 2>/dev/null \
    && echo "  ✓ Deployment group '${DG_NAME}' created" \
    || echo "  ! Deployment group may already exist"

#----------------------------------------------------------------------
# Step 5: Show next steps
#----------------------------------------------------------------------
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    SETUP COMPLETE                              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "  CodeDeploy is ready. To deploy any project to GRC_Titan:"
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
echo "       --s3-location bucket=<artifact-bucket>,key=<artifact.zip>,bundleType=zip \\"
echo "       --region ${REGION}"
echo ""
echo "  Or add a Deploy stage to the existing ospo-csta pipeline:"
echo "     aws codepipeline update-pipeline --cli-input-json file://pipeline-update.json"
echo ""
