#!/usr/bin/env bash
# SLyK-53 — CloudShell environment for tenant: nesdis-ncis-ospocsta-5006
# AWS account ID: 656443597515
#
# Usage in CloudShell (from the directory that contains deploy_slyk.py):
#   source ./CLOUDSHELL_ENV_ospocsta_656443597515.sh
#   python3 deploy_slyk.py
#
# Optional: override any value before sourcing, e.g.
#   export S3_BUCKET_NAME=my-unique-bucket-name
#   source ./CLOUDSHELL_ENV_ospocsta_656443597515.sh

export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
export S3_BUCKET_NAME="${S3_BUCKET_NAME:-slyk-grcp-656443597515}"
export SLYK_EXPECT_ACCOUNT_ID="${SLYK_EXPECT_ACCOUNT_ID:-656443597515}"
export SLYK_AGENT_MODEL="${SLYK_AGENT_MODEL:-amazon.nova-pro-v1:0}"

echo "SLyK env: region=$AWS_DEFAULT_REGION account=$SLYK_EXPECT_ACCOUNT_ID bucket=$S3_BUCKET_NAME model=$SLYK_AGENT_MODEL"
echo "Create bucket once if it does not exist, e.g.:"
echo "  aws s3 mb s3://\${S3_BUCKET_NAME} --region \${AWS_DEFAULT_REGION}"
echo "Or from full TestZippr repo: python3 create_slyk_s3_bucket.py --bucket \${S3_BUCKET_NAME} --region \${AWS_DEFAULT_REGION}"
