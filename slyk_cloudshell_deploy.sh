#!/usr/bin/env bash
# ============================================================================
# SLyK-53 — One-Shot CloudShell Deployment Script
# ============================================================================
# Paste this ENTIRE script into AWS CloudShell and hit Enter.
# It will:
#   1. Verify your AWS identity and account
#   2. Install git if missing (CloudShell usually has it)
#   3. Clone the TestZippr repo
#   4. Create the S3 bucket (if it doesn't exist)
#   5. Set environment variables
#   6. Run the full SLyK-53 deployment
#   7. Verify all resources were created
#
# Target account: 656443597515 (nesdis-ncis-ospocsta-5006)
# To use a DIFFERENT account, change EXPECTED_ACCOUNT below (or unset it).
# ============================================================================

set -e

# ── Configuration ───────────────────────────────────────────────────────────
EXPECTED_ACCOUNT="656443597515"          # Set to "" to skip account check
REGION="us-east-1"
REPO_URL="https://github.com/iperry5224/TestZippr.git"
WORK_DIR="$HOME/slyk_deploy"
AGENT_MODEL="amazon.nova-pro-v1:0"
# ────────────────────────────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║   SLyK-53 — One-Shot CloudShell Deployment                     ║"
echo "║   SAE Lightweight Yaml Kit                                      ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── Step 1: Verify AWS Identity ─────────────────────────────────────────────
echo -e "${BLUE}[1/7] Verifying AWS identity...${NC}"

CALLER_IDENTITY=$(aws sts get-caller-identity --output json 2>&1)
if [ $? -ne 0 ]; then
    echo -e "${RED}  ✗ Cannot reach AWS. Are you in CloudShell?${NC}"
    echo "  $CALLER_IDENTITY"
    exit 1
fi

ACCOUNT_ID=$(echo "$CALLER_IDENTITY" | python3 -c "import sys,json; print(json.load(sys.stdin)['Account'])")
USER_ARN=$(echo "$CALLER_IDENTITY" | python3 -c "import sys,json; print(json.load(sys.stdin)['Arn'])")

echo -e "${GREEN}  ✓ Account:  $ACCOUNT_ID${NC}"
echo -e "${GREEN}  ✓ Identity: $USER_ARN${NC}"
echo -e "${GREEN}  ✓ Region:   $REGION${NC}"

if [ -n "$EXPECTED_ACCOUNT" ] && [ "$ACCOUNT_ID" != "$EXPECTED_ACCOUNT" ]; then
    echo -e "${RED}  ✗ Account mismatch! Expected $EXPECTED_ACCOUNT but got $ACCOUNT_ID${NC}"
    echo -e "${RED}    Make sure you're logged into the correct AWS account.${NC}"
    exit 1
fi

# Set the S3 bucket name based on actual account
S3_BUCKET="slyk-grcp-${ACCOUNT_ID}"
echo -e "${GREEN}  ✓ S3 Bucket: $S3_BUCKET${NC}"
echo ""

# ── Step 2: Install prerequisites ───────────────────────────────────────────
echo -e "${BLUE}[2/7] Checking prerequisites...${NC}"

if command -v git &> /dev/null; then
    echo -e "${GREEN}  ✓ git $(git --version | cut -d' ' -f3)${NC}"
else
    echo -e "${YELLOW}  ! git not found — installing...${NC}"
    sudo yum install -y git 2>/dev/null || sudo apt-get install -y git 2>/dev/null
fi

if command -v python3 &> /dev/null; then
    echo -e "${GREEN}  ✓ python3 $(python3 --version | cut -d' ' -f2)${NC}"
else
    echo -e "${RED}  ✗ python3 not found — this shouldn't happen in CloudShell${NC}"
    exit 1
fi

# Verify boto3 is available
python3 -c "import boto3" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}  ✓ boto3 available${NC}"
else
    echo -e "${YELLOW}  ! Installing boto3...${NC}"
    pip3 install boto3 --quiet
fi
echo ""

# ── Step 3: Clone the repo ──────────────────────────────────────────────────
echo -e "${BLUE}[3/7] Setting up workspace...${NC}"

# Clean up any previous deployment attempt
if [ -d "$WORK_DIR" ]; then
    echo -e "${YELLOW}  ! Removing previous workspace at $WORK_DIR${NC}"
    rm -rf "$WORK_DIR"
fi

mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

echo "  Cloning $REPO_URL ..."
git clone --depth 1 "$REPO_URL" 2>&1 | tail -5
if [ $? -ne 0 ]; then
    echo -e "${RED}  ✗ Failed to clone repo${NC}"
    exit 1
fi
echo -e "${GREEN}  ✓ Repo cloned${NC}"

# Debug: show what was cloned
echo "  Contents of $WORK_DIR:"
ls -la "$WORK_DIR"

# Navigate to the SLyK deploy folder
SLYK_DIR="$WORK_DIR/TestZippr/slyk_deploy_extract/slyk"

# If TestZippr folder doesn't exist, maybe it cloned directly
if [ ! -d "$WORK_DIR/TestZippr" ]; then
    # Check if slyk_deploy_extract exists directly (repo cloned without wrapper)
    if [ -d "$WORK_DIR/slyk_deploy_extract/slyk" ]; then
        SLYK_DIR="$WORK_DIR/slyk_deploy_extract/slyk"
        echo -e "${YELLOW}  ! Repo cloned without TestZippr wrapper — adjusting path${NC}"
    fi
fi

if [ ! -d "$SLYK_DIR" ]; then
    echo -e "${RED}  ✗ SLyK folder not found at $SLYK_DIR${NC}"
    echo "  Searching for slyk folder..."
    find "$WORK_DIR" -type d -name "slyk" 2>/dev/null | head -5
    exit 1
fi
cd "$SLYK_DIR"
echo -e "${GREEN}  ✓ Working directory: $(pwd)${NC}"
echo ""

# ── Step 4: Create S3 bucket ────────────────────────────────────────────────
echo -e "${BLUE}[4/7] Setting up S3 bucket...${NC}"

# Check if bucket already exists
if aws s3api head-bucket --bucket "$S3_BUCKET" 2>/dev/null; then
    echo -e "${GREEN}  ✓ Bucket $S3_BUCKET already exists${NC}"
else
    echo "  Creating bucket $S3_BUCKET in $REGION..."
    if [ "$REGION" = "us-east-1" ]; then
        aws s3api create-bucket --bucket "$S3_BUCKET" --region "$REGION"
    else
        aws s3api create-bucket --bucket "$S3_BUCKET" --region "$REGION" \
            --create-bucket-configuration LocationConstraint="$REGION"
    fi

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}  ✓ Bucket created${NC}"
    else
        echo -e "${RED}  ✗ Failed to create bucket. Name may be taken — try a different one.${NC}"
        echo -e "${YELLOW}    To use a custom name, set S3_BUCKET_NAME before running:${NC}"
        echo -e "${YELLOW}    export S3_BUCKET_NAME=your-unique-bucket-name${NC}"
        exit 1
    fi

    # Enable default encryption
    aws s3api put-bucket-encryption --bucket "$S3_BUCKET" \
        --server-side-encryption-configuration \
        '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
    echo -e "${GREEN}  ✓ Default encryption enabled${NC}"

    # Block public access
    aws s3api put-public-access-block --bucket "$S3_BUCKET" \
        --public-access-block-configuration \
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
    echo -e "${GREEN}  ✓ Public access blocked${NC}"

    # Enable versioning
    aws s3api put-bucket-versioning --bucket "$S3_BUCKET" \
        --versioning-configuration Status=Enabled
    echo -e "${GREEN}  ✓ Versioning enabled${NC}"
fi
echo ""

# ── Step 5: Set environment variables ────────────────────────────────────────
echo -e "${BLUE}[5/7] Configuring environment...${NC}"

export AWS_DEFAULT_REGION="$REGION"
export S3_BUCKET_NAME="$S3_BUCKET"
export SLYK_EXPECT_ACCOUNT_ID="$ACCOUNT_ID"
export SLYK_AGENT_MODEL="$AGENT_MODEL"

echo -e "${GREEN}  ✓ AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION${NC}"
echo -e "${GREEN}  ✓ S3_BUCKET_NAME=$S3_BUCKET_NAME${NC}"
echo -e "${GREEN}  ✓ SLYK_EXPECT_ACCOUNT_ID=$SLYK_EXPECT_ACCOUNT_ID${NC}"
echo -e "${GREEN}  ✓ SLYK_AGENT_MODEL=$SLYK_AGENT_MODEL${NC}"
echo ""

# ── Step 6: Deploy SLyK-53 ──────────────────────────────────────────────────
echo -e "${BLUE}[6/7] Deploying SLyK-53...${NC}"
echo ""

python3 deploy_slyk.py

DEPLOY_EXIT=$?
echo ""

if [ $DEPLOY_EXIT -ne 0 ]; then
    echo -e "${RED}  ✗ Deployment script exited with code $DEPLOY_EXIT${NC}"
    echo -e "${YELLOW}    Check the output above for errors.${NC}"
    exit 1
fi

# ── Step 7: Verify deployment ────────────────────────────────────────────────
echo -e "${BLUE}[7/7] Verifying deployment...${NC}"
echo ""

python3 - <<'VERIFY_SCRIPT'
import json
import boto3
from botocore.exceptions import ClientError
import os

region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
account = os.environ.get("SLYK_EXPECT_ACCOUNT_ID", "")
bucket = os.environ.get("S3_BUCKET_NAME", "")

GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
CYAN = "\033[0;36m"
NC = "\033[0m"

results = {"pass": 0, "fail": 0, "warn": 0}

def check(name, passed, detail=""):
    if passed:
        print(f"{GREEN}  ✓ {name}{NC}" + (f" — {detail}" if detail else ""))
        results["pass"] += 1
    else:
        print(f"{RED}  ✗ {name}{NC}" + (f" — {detail}" if detail else ""))
        results["fail"] += 1

def warn(name, detail=""):
    print(f"{YELLOW}  ! {name}{NC}" + (f" — {detail}" if detail else ""))
    results["warn"] += 1

print(f"{CYAN}── IAM Roles ──{NC}")
iam = boto3.client("iam")
for role_name in ["SLyK-Lambda-Role", "SLyK-Agent-Role"]:
    try:
        r = iam.get_role(RoleName=role_name)
        check(role_name, True, r["Role"]["Arn"])
    except ClientError:
        check(role_name, False, "not found")

print(f"\n{CYAN}── Lambda Functions ──{NC}")
lam = boto3.client("lambda", region_name=region)
for func_name in ["slyk-assess", "slyk-remediate", "slyk-harden"]:
    try:
        f = lam.get_function(FunctionName=func_name)
        runtime = f["Configuration"]["Runtime"]
        state = f["Configuration"].get("State", "Unknown")
        check(func_name, True, f"runtime={runtime} state={state}")
    except ClientError:
        check(func_name, False, "not found")

print(f"\n{CYAN}── Bedrock Agent ──{NC}")
bedrock = boto3.client("bedrock-agent", region_name=region)
agent_id = None
try:
    agents = bedrock.list_agents(maxResults=50)
    for a in agents.get("agentSummaries", []):
        if a["agentName"] == "SLyK-53-Security-Assistant":
            agent_id = a["agentId"]
            status = a.get("agentStatus", "Unknown")
            check("SLyK-53-Security-Assistant", True, f"id={agent_id} status={status}")
            break
    if not agent_id:
        check("SLyK-53-Security-Assistant", False, "agent not found")
except ClientError as e:
    check("SLyK-53-Security-Assistant", False, str(e))

if agent_id:
    # Check action groups
    try:
        ags = bedrock.list_agent_action_groups(agentId=agent_id, agentVersion="DRAFT")
        ag_names = [a["actionGroupName"] for a in ags.get("actionGroupSummaries", [])]
        for expected in ["ASSESS", "REMEDIATE", "HARDEN"]:
            check(f"Action Group: {expected}", expected in ag_names,
                  "attached" if expected in ag_names else "missing")
    except ClientError as e:
        warn("Action groups check failed", str(e))

    # Check aliases
    try:
        aliases = bedrock.list_agent_aliases(agentId=agent_id)
        alias_names = [a["agentAliasName"] for a in aliases.get("agentAliasSummaries", [])]
        check("Agent alias: production", "production" in alias_names,
              "ready" if "production" in alias_names else "missing")
    except ClientError as e:
        warn("Alias check failed", str(e))

    # Check foundation model
    try:
        agent_detail = bedrock.get_agent(agentId=agent_id)["agent"]
        model = agent_detail.get("foundationModel", "unknown")
        check("Foundation model", True, model)
    except ClientError as e:
        warn("Model check failed", str(e))

print(f"\n{CYAN}── S3 Bucket ──{NC}")
if bucket:
    s3 = boto3.client("s3", region_name=region)
    try:
        s3.head_bucket(Bucket=bucket)
        check(f"Bucket: {bucket}", True, "accessible")
    except ClientError:
        check(f"Bucket: {bucket}", False, "not accessible")

    # Check for config file
    try:
        s3.head_object(Bucket=bucket, Key="slyk/slyk_config.json")
        check("Config uploaded to S3", True)
    except ClientError:
        warn("Config not found in S3", "slyk/slyk_config.json")

# Summary
print(f"\n{CYAN}── Summary ──{NC}")
total = results["pass"] + results["fail"] + results["warn"]
print(f"  Passed:   {results['pass']}/{total}")
print(f"  Failed:   {results['fail']}/{total}")
print(f"  Warnings: {results['warn']}/{total}")

if results["fail"] == 0:
    print(f"\n{GREEN}  ✓ SLyK-53 deployment verified successfully!{NC}")
    print(f"\n{CYAN}  Next steps:{NC}")
    print(f"    1. Go to AWS Console > Amazon Bedrock > Agents")
    print(f"    2. Select 'SLyK-53-Security-Assistant'")
    print(f"    3. Click 'Test' in the right panel")
    print(f"    4. Try: 'Assess my NIST 800-53 compliance'")
    print(f"    5. Try: 'Harden all my S3 buckets'")
    print(f"    6. Try: 'Generate remediation for AC-2'")
else:
    print(f"\n{RED}  Some checks failed — review the output above.{NC}")
VERIFY_SCRIPT

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  SLyK-53 CloudShell deployment complete.${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════════${NC}"
