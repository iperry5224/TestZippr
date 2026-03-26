#!/bin/bash
#===============================================================================
#  SOPRA EC2 Installation Script (Sandbox Edition)
#===============================================================================
#  Streamlined installation for dedicated EC2 sandbox environments
#  No virtual environment - installs directly to system Python
#
#  Usage: 
#    chmod +x install_sopra_ec2.sh
#    ./install_sopra_ec2.sh
#
#  Version: 1.0 (February 2026)
#===============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration - use 8180 to avoid conflict with SAELAR (8080) on same host
PORT="${SOPRA_PORT:-8180}"

# Banner
echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║   SOPRA - EC2 Sandbox Installation                                    ║"
echo "║   🛡️  Security Operations Platform for Risk Assessment                ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

#-------------------------------------------------------------------------------
# Step 1: Find and extract SOPRA package
#-------------------------------------------------------------------------------
echo -e "${BLUE}[1/4]${NC} Looking for SOPRA package..."

ZIP_FILE=$(ls -t SOPRA*.zip 2>/dev/null | head -1)
if [ -z "$ZIP_FILE" ]; then
    ZIP_FILE=$(ls -t sopra*.zip 2>/dev/null | head -1)
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
# Step 2: Install Python packages
#-------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[2/4]${NC} Installing Python dependencies..."

pip3 install --upgrade pip
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
# Step 3: Verify Bedrock access (optional for SOPRA)
#-------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[3/4]${NC} Checking AWS Bedrock access..."

TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 60" --max-time 2 2>/dev/null)
if [ -n "$TOKEN" ]; then
    REGION=$(curl -s --max-time 2 -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/region 2>/dev/null)
fi
[ -z "$REGION" ] && REGION=$(curl -s --max-time 2 http://169.254.169.254/latest/meta-data/placement/region 2>/dev/null)
if [ -n "$REGION" ]; then
    export AWS_DEFAULT_REGION=$REGION
    echo -e "${GREEN}[✓]${NC} Region: ${REGION}"
fi

python3 -c "
import boto3
try:
    bedrock = boto3.client('bedrock')
    models = bedrock.list_foundation_models(byOutputModality='TEXT')
    count = len(models.get('modelSummaries', []))
    print(f'\033[92m[✓]\033[0m Bedrock access OK - {count} models available')
except Exception as e:
    print(f'\033[93m[!]\033[0m Bedrock: {str(e)[:60]}')
" 2>/dev/null || echo -e "${YELLOW}[!]${NC} Bedrock check skipped"

#-------------------------------------------------------------------------------
# Step 4: Create launch script
#-------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[4/4]${NC} Creating launch script..."

# IMDSv2 for public IP
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 60" --max-time 2 2>/dev/null)
PUBLIC_IP="localhost"
if [ -n "$TOKEN" ]; then
  PUBLIC_IP=$(curl -s --max-time 2 -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null)
fi
[[ ! "$PUBLIC_IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] && PUBLIC_IP="localhost"

cat > start_sopra.sh << 'SCRIPT'
#!/bin/bash
cd "$(dirname "$0")"

TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 60" --max-time 2 2>/dev/null)
PUBLIC_IP="localhost"
if [ -n "$TOKEN" ]; then
  PUBLIC_IP=$(curl -s --max-time 2 -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null)
fi
[[ ! "$PUBLIC_IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] && PUBLIC_IP="localhost"

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║   SOPRA - Security Operations Platform for Risk Assessment            ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Access: http://${PUBLIC_IP}:PORT_PLACEHOLDER"
echo ""

streamlit run sopra_setup.py \
    --server.port PORT_PLACEHOLDER \
    --server.address 0.0.0.0 \
    --server.headless true
SCRIPT
sed -i "s/PORT_PLACEHOLDER/${PORT}/g" start_sopra.sh
chmod +x start_sopra.sh

echo -e "${GREEN}[✓]${NC} Created start_sopra.sh"

#-------------------------------------------------------------------------------
# Done!
#-------------------------------------------------------------------------------
echo ""
echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                    INSTALLATION COMPLETE!                              ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo "To start SOPRA:"
echo "  ./start_sopra.sh"
echo ""
echo "Access URL: http://${PUBLIC_IP}:${PORT}"
echo ""
echo "Make sure security group allows TCP port ${PORT}!"
echo ""

read -p "Start SOPRA now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./start_sopra.sh
fi
