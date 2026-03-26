#!/bin/bash
#===============================================================================
#  SAELAR EC2 Installation Script (Sandbox Edition)
#===============================================================================
#  Streamlined installation for dedicated EC2 sandbox environments
#  No virtual environment - installs directly to system Python
#
#  Usage: 
#    chmod +x install_saelar_ec2.sh
#    ./install_saelar_ec2.sh
#
#  Version: 3.0 (February 2026)
#===============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${SAELAR_PORT:-8080}"

# Banner
echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║   SAELAR - EC2 Sandbox Installation                                   ║"
echo "║   🔒 AWS Bedrock Integration - All Data Stays Within AWS              ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

#-------------------------------------------------------------------------------
# Step 1: Find and extract SAELAR package
#-------------------------------------------------------------------------------
echo -e "${BLUE}[1/4]${NC} Looking for SAELAR package..."

ZIP_FILE=$(ls -t SAELAR*.zip 2>/dev/null | head -1)
if [ -z "$ZIP_FILE" ]; then
    ZIP_FILE=$(ls -t saelar*.zip 2>/dev/null | head -1)
fi

if [ -n "$ZIP_FILE" ] && [ -f "$ZIP_FILE" ]; then
    echo -e "${GREEN}[✓]${NC} Found: ${ZIP_FILE}"
    echo "    Extracting..."
    unzip -o "$ZIP_FILE"
    echo -e "${GREEN}[✓]${NC} Extracted"
else
    echo -e "${YELLOW}[!]${NC} No zip file found - assuming files already extracted"
fi

#-------------------------------------------------------------------------------
# Step 2: Install Python packages directly
#-------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[2/4]${NC} Installing Python dependencies..."

# Upgrade pip first
pip3 install --upgrade pip

# Install all required packages
pip3 install \
    boto3>=1.34.0 \
    streamlit>=1.29.0 \
    pandas>=2.0.0 \
    numpy>=1.24.0 \
    python-docx>=0.8.11 \
    openpyxl>=3.1.0 \
    XlsxWriter>=3.1.0 \
    plotly>=5.18.0 \
    python-dateutil>=2.8.0 \
    requests>=2.31.0 \
    rich>=13.0.0 \
    tabulate>=0.9.0

echo -e "${GREEN}[✓]${NC} Dependencies installed"

#-------------------------------------------------------------------------------
# Step 3: Verify Bedrock access
#-------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[3/4]${NC} Checking AWS Bedrock access..."

# Get region from EC2 metadata
if curl -s --max-time 2 http://169.254.169.254/latest/meta-data/placement/region &>/dev/null; then
    REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/region)
    export AWS_DEFAULT_REGION=$REGION
    echo -e "${GREEN}[✓]${NC} Region: ${REGION}"
fi

# Quick Bedrock check
python3 -c "
import boto3
try:
    bedrock = boto3.client('bedrock')
    models = bedrock.list_foundation_models(byOutputModality='TEXT')
    count = len(models.get('modelSummaries', []))
    print(f'\033[92m[✓]\033[0m Bedrock access OK - {count} models available')
except Exception as e:
    print(f'\033[93m[!]\033[0m Bedrock: {str(e)[:60]}')
    print('    Chad AI will show guidance if models unavailable')
" 2>/dev/null || echo -e "${YELLOW}[!]${NC} Bedrock check skipped"

#-------------------------------------------------------------------------------
# Step 4: Create simple launch script
#-------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[4/4]${NC} Creating launch script..."

cat > start_saelar.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"

# Get public IP
PUBLIC_IP=$(curl -s --max-time 2 http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║   SAELAR - NIST 800-53 + 800-30 Risk Assessment                       ║"
echo "║   🔒 Powered by AWS Bedrock                                           ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Access: http://${PUBLIC_IP}:8080"
echo ""

streamlit run nist_setup.py \
    --server.port 8080 \
    --server.address 0.0.0.0 \
    --server.headless true
EOF
chmod +x start_saelar.sh

echo -e "${GREEN}[✓]${NC} Created start_saelar.sh"

#-------------------------------------------------------------------------------
# Done!
#-------------------------------------------------------------------------------
PUBLIC_IP=$(curl -s --max-time 2 http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "<your-ip>")

echo ""
echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                    INSTALLATION COMPLETE!                              ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo "To start SAELAR:"
echo "  ./start_saelar.sh"
echo ""
echo "Access URL: http://${PUBLIC_IP}:8080"
echo ""
echo "Make sure security group allows TCP port 8080!"
echo ""

# Ask to start
read -p "Start SAELAR now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./start_saelar.sh
fi
