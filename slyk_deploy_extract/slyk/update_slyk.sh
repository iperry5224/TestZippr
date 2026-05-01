#!/bin/bash
#
# SLyK-53 One-Shot Update Script
# ================================
# Run this in AWS CloudShell to update/deploy SLyK-53
#
# Usage:
#   curl -s https://raw.githubusercontent.com/iperry5224/TestZippr/main/slyk_deploy_extract/slyk/update_slyk.sh | bash
#
# Or if you have the repo cloned:
#   bash update_slyk.sh
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║   SLyK-53 — One-Shot Update Script                                    ║"
echo "║   Run this in AWS CloudShell                                          ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Step 1: Clean up space
echo -e "${BLUE}[1/6]${NC} Cleaning up CloudShell storage..."
cd ~
rm -rf TestZippr .cache .local .npm 2>/dev/null || true
echo -e "${GREEN}  ✓${NC} Storage cleaned"

# Step 2: Check disk space
echo -e "${BLUE}[2/6]${NC} Checking disk space..."
AVAIL=$(df -m /home/cloudshell-user | tail -1 | awk '{print $4}')
if [ "$AVAIL" -lt 100 ]; then
    echo -e "${RED}  ✗${NC} Only ${AVAIL}MB available. Need at least 100MB."
    echo "    Try: rm -rf ~/* ~/.cache ~/.local ~/.npm"
    exit 1
fi
echo -e "${GREEN}  ✓${NC} ${AVAIL}MB available"

# Step 3: Clone repo
echo -e "${BLUE}[3/6]${NC} Cloning repository..."
git clone https://github.com/iperry5224/TestZippr.git
cd TestZippr/slyk_deploy_extract/slyk
echo -e "${GREEN}  ✓${NC} Repository cloned"

# Step 4: Deploy notifications (SNS + EventBridge)
echo -e "${BLUE}[4/6]${NC} Setting up email notifications..."
python3 deploy_notifications.py
echo -e "${GREEN}  ✓${NC} Notifications configured"

# Step 5: Deploy New_SLyK-53 variant
echo -e "${BLUE}[5/6]${NC} Deploying New_SLyK-53 agent..."
export SLYK_VARIANT=new
python3 deploy_slyk.py
echo -e "${GREEN}  ✓${NC} New_SLyK-53 deployed"

# Step 6: Also update original SLyK-53 (optional)
echo -e "${BLUE}[6/6]${NC} Updating original SLyK-53 agent..."
unset SLYK_VARIANT
python3 deploy_slyk.py
echo -e "${GREEN}  ✓${NC} Original SLyK-53 updated"

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════════╗"
echo -e "║                    SLyK-53 UPDATE COMPLETE!                           ║"
echo -e "╚═══════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Deployed Agents:${NC}"
echo "  • SLyK-53-Security-Assistant     (original)"
echo "  • New_SLyK-53-Security-Assistant (new controls)"
echo ""
echo -e "${CYAN}Email Notifications:${NC}"
echo "  • Topic: slyk-new-security-alerts"
echo "  • Email: ira.perry@noaa.gov"
echo ""
echo -e "${YELLOW}IMPORTANT:${NC} Check your email and confirm the SNS subscription!"
echo ""
echo -e "${CYAN}Test in AWS Console:${NC}"
echo "  1. Go to: Amazon Bedrock → Agents"
echo "  2. Select: New_SLyK-53-Security-Assistant"
echo "  3. Click: Test"
echo "  4. Try:   'Assess my AC-2 compliance'"
echo ""
