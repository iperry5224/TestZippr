#!/bin/bash
#===============================================================================
#  AWS Security Assessment Environment Setup Script
#===============================================================================
#  This script sets up your WSL environment for running AWS security tools:
#    - NIST 800-53 Controls Assessment
#    - AWS Penetration Testing Toolkit
#
#  Usage: bash setup_environment.sh
#===============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║     AWS Security Assessment Environment Setup                         ║"
echo "║     NIST 800-53 Controls & Penetration Testing Toolkit               ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

#-------------------------------------------------------------------------------
# Configuration
#-------------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_NAME="security-venv"
VENV_PATH="${SCRIPT_DIR}/${VENV_NAME}"
REQUIREMENTS_FILE="${SCRIPT_DIR}/requirements.txt"

#-------------------------------------------------------------------------------
# Helper Functions
#-------------------------------------------------------------------------------
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

#-------------------------------------------------------------------------------
# Step 1: Check Prerequisites
#-------------------------------------------------------------------------------
echo ""
log_info "Step 1: Checking prerequisites..."

# Check if running in WSL
if grep -qi microsoft /proc/version 2>/dev/null || grep -qi wsl /proc/version 2>/dev/null; then
    log_success "Running in WSL environment"
else
    log_warning "Not running in WSL - script may still work on native Linux"
fi

# Check Python
if check_command python3; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    log_success "Python 3 found: ${PYTHON_VERSION}"
else
    log_error "Python 3 not found. Installing..."
    sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv
fi

# Check pip
if check_command pip3; then
    log_success "pip3 found"
else
    log_info "Installing pip..."
    sudo apt-get install -y python3-pip
fi

# Check venv module
if python3 -c "import venv" 2>/dev/null; then
    log_success "Python venv module available"
else
    log_info "Installing python3-venv..."
    sudo apt-get install -y python3-venv
fi

#-------------------------------------------------------------------------------
# Step 2: Create Virtual Environment
#-------------------------------------------------------------------------------
echo ""
log_info "Step 2: Setting up Python virtual environment..."

if [ -d "${VENV_PATH}" ]; then
    log_warning "Virtual environment already exists at ${VENV_PATH}"
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "${VENV_PATH}"
        python3 -m venv "${VENV_PATH}"
        log_success "Virtual environment recreated"
    else
        log_info "Using existing virtual environment"
    fi
else
    python3 -m venv "${VENV_PATH}"
    log_success "Virtual environment created at ${VENV_PATH}"
fi

# Activate virtual environment
source "${VENV_PATH}/bin/activate"
log_success "Virtual environment activated"

#-------------------------------------------------------------------------------
# Step 3: Create Requirements File
#-------------------------------------------------------------------------------
echo ""
log_info "Step 3: Creating requirements file..."

cat > "${REQUIREMENTS_FILE}" << 'EOF'
# AWS SDK
boto3>=1.34.0
botocore>=1.34.0

# Streamlit UI
streamlit>=1.29.0

# Data processing
pandas>=2.0.0

# Utilities
python-dateutil>=2.8.0

# Optional: For enhanced features
rich>=13.0.0
tabulate>=0.9.0
EOF

log_success "Requirements file created"

#-------------------------------------------------------------------------------
# Step 4: Install Python Dependencies
#-------------------------------------------------------------------------------
echo ""
log_info "Step 4: Installing Python dependencies..."

pip install --upgrade pip
pip install -r "${REQUIREMENTS_FILE}"

log_success "All Python dependencies installed"

#-------------------------------------------------------------------------------
# Step 5: Configure AWS Credentials
#-------------------------------------------------------------------------------
echo ""
log_info "Step 5: Configuring AWS credentials..."

AWS_DIR="${HOME}/.aws"
AWS_CREDENTIALS="${AWS_DIR}/credentials"
AWS_CONFIG="${AWS_DIR}/config"

# Create .aws directory if it doesn't exist
mkdir -p "${AWS_DIR}"
chmod 700 "${AWS_DIR}"

# Check if credentials already exist
if [ -f "${AWS_CREDENTIALS}" ]; then
    log_success "AWS credentials file found"
    
    # Test AWS connection
    if aws sts get-caller-identity &>/dev/null; then
        ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
        USER_ARN=$(aws sts get-caller-identity --query Arn --output text 2>/dev/null)
        log_success "AWS connection verified!"
        echo -e "         Account: ${GREEN}${ACCOUNT_ID}${NC}"
        echo -e "         Identity: ${GREEN}${USER_ARN}${NC}"
    else
        log_warning "AWS credentials exist but connection failed"
        log_info "Please verify your credentials are correct"
    fi
else
    log_warning "AWS credentials not configured"
    echo ""
    echo -e "${YELLOW}To configure AWS credentials, you have several options:${NC}"
    echo ""
    echo "  Option 1: Run AWS configure"
    echo "    $ aws configure"
    echo ""
    echo "  Option 2: Set environment variables"
    echo "    $ export AWS_ACCESS_KEY_ID='your-access-key'"
    echo "    $ export AWS_SECRET_ACCESS_KEY='your-secret-key'"
    echo "    $ export AWS_DEFAULT_REGION='us-east-1'"
    echo ""
    echo "  Option 3: Create credentials file manually"
    echo "    $ cat > ~/.aws/credentials << EOF"
    echo "    [default]"
    echo "    aws_access_key_id = YOUR_ACCESS_KEY"
    echo "    aws_secret_access_key = YOUR_SECRET_KEY"
    echo "    EOF"
    echo ""
    
    read -p "Would you like to configure AWS credentials now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        read -p "Enter AWS Access Key ID: " AWS_ACCESS_KEY_ID
        read -s -p "Enter AWS Secret Access Key: " AWS_SECRET_ACCESS_KEY
        echo ""
        read -p "Enter default region (e.g., us-east-1): " AWS_REGION
        
        # Create credentials file
        cat > "${AWS_CREDENTIALS}" << EOF
[default]
aws_access_key_id = ${AWS_ACCESS_KEY_ID}
aws_secret_access_key = ${AWS_SECRET_ACCESS_KEY}
EOF
        chmod 600 "${AWS_CREDENTIALS}"
        
        # Create config file
        cat > "${AWS_CONFIG}" << EOF
[default]
region = ${AWS_REGION}
output = json
EOF
        chmod 600 "${AWS_CONFIG}"
        
        log_success "AWS credentials configured"
        
        # Test connection
        if aws sts get-caller-identity &>/dev/null; then
            ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
            log_success "AWS connection verified! Account: ${ACCOUNT_ID}"
        else
            log_error "AWS connection failed. Please verify your credentials."
        fi
    fi
fi

#-------------------------------------------------------------------------------
# Step 6: Install AWS CLI (if not present)
#-------------------------------------------------------------------------------
echo ""
log_info "Step 6: Checking AWS CLI..."

if check_command aws; then
    AWS_CLI_VERSION=$(aws --version 2>&1 | cut -d' ' -f1 | cut -d'/' -f2)
    log_success "AWS CLI found: ${AWS_CLI_VERSION}"
else
    log_info "Installing AWS CLI..."
    
    # Install AWS CLI v2
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"
    unzip -q /tmp/awscliv2.zip -d /tmp
    sudo /tmp/aws/install
    rm -rf /tmp/aws /tmp/awscliv2.zip
    
    log_success "AWS CLI installed"
fi

#-------------------------------------------------------------------------------
# Step 7: Create Launcher Scripts
#-------------------------------------------------------------------------------
echo ""
log_info "Step 7: Creating launcher scripts..."

# Create launcher for NIST Controls App
cat > "${SCRIPT_DIR}/run_nist_controls.sh" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/security-venv/bin/activate"
echo "🛡️ Starting NIST 800-53 Controls Assessment..."
streamlit run "${SCRIPT_DIR}/nist_controls_app.py"
EOF
chmod +x "${SCRIPT_DIR}/run_nist_controls.sh"

# Create launcher for PenTest App
cat > "${SCRIPT_DIR}/run_pentest.sh" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/security-venv/bin/activate"
echo "🔓 Starting AWS Penetration Testing Toolkit..."
streamlit run "${SCRIPT_DIR}/pentest_app.py"
EOF
chmod +x "${SCRIPT_DIR}/run_pentest.sh"

# Create launcher for CLI assessment
cat > "${SCRIPT_DIR}/run_assessment.sh" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/security-venv/bin/activate"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           AWS Security Assessment Suite                       ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Select an option:"
echo "  1) NIST 800-53 Controls Assessment (CLI)"
echo "  2) NIST 800-53 Controls Assessment (Streamlit UI)"
echo "  3) AWS Penetration Test (CLI)"
echo "  4) AWS Penetration Test (Streamlit UI)"
echo "  5) Run Both CLI Assessments"
echo "  6) Exit"
echo ""
read -p "Enter choice [1-6]: " choice

case $choice in
    1)
        python "${SCRIPT_DIR}/nist_800_53_controls.py"
        ;;
    2)
        streamlit run "${SCRIPT_DIR}/nist_controls_app.py"
        ;;
    3)
        python "${SCRIPT_DIR}/aws_pentest_toolkit.py"
        ;;
    4)
        streamlit run "${SCRIPT_DIR}/pentest_app.py"
        ;;
    5)
        echo "Running NIST Controls Assessment..."
        python "${SCRIPT_DIR}/nist_800_53_controls.py" --export --output nist_results.json
        echo ""
        echo "Running Penetration Test..."
        python "${SCRIPT_DIR}/aws_pentest_toolkit.py" --output pentest_results.json
        echo ""
        echo "Results saved to nist_results.json and pentest_results.json"
        ;;
    6)
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo "Invalid option"
        exit 1
        ;;
esac
EOF
chmod +x "${SCRIPT_DIR}/run_assessment.sh"

log_success "Launcher scripts created"

#-------------------------------------------------------------------------------
# Step 8: Create activation script for quick access
#-------------------------------------------------------------------------------
echo ""
log_info "Step 8: Creating quick activation script..."

cat > "${SCRIPT_DIR}/activate_env.sh" << EOF
#!/bin/bash
# Quick activation script - source this file to activate the environment
# Usage: source activate_env.sh

SCRIPT_DIR="${SCRIPT_DIR}"
source "\${SCRIPT_DIR}/security-venv/bin/activate"
cd "\${SCRIPT_DIR}"

echo ""
echo -e "\033[0;32m✓ Security environment activated!\033[0m"
echo ""
echo "Available commands:"
echo "  ./run_nist_controls.sh    - Launch NIST 800-53 Assessment UI"
echo "  ./run_pentest.sh          - Launch Penetration Testing UI"  
echo "  ./run_assessment.sh       - Interactive menu for all tools"
echo ""
echo "Or run directly:"
echo "  streamlit run nist_controls_app.py"
echo "  streamlit run pentest_app.py"
echo "  python nist_800_53_controls.py --help"
echo "  python aws_pentest_toolkit.py --help"
echo ""
EOF
chmod +x "${SCRIPT_DIR}/activate_env.sh"

log_success "Activation script created"

#-------------------------------------------------------------------------------
# Summary
#-------------------------------------------------------------------------------
echo ""
echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                    SETUP COMPLETE!                                    ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${GREEN}Your AWS Security Assessment environment is ready!${NC}"
echo ""
echo "📁 Location: ${SCRIPT_DIR}"
echo ""
echo "🚀 Quick Start Commands:"
echo ""
echo "   # Activate the environment"
echo "   source ${SCRIPT_DIR}/activate_env.sh"
echo ""
echo "   # Or run apps directly:"
echo "   ${SCRIPT_DIR}/run_nist_controls.sh      # NIST 800-53 UI"
echo "   ${SCRIPT_DIR}/run_pentest.sh            # PenTest UI"
echo "   ${SCRIPT_DIR}/run_assessment.sh         # Interactive menu"
echo ""

# Test AWS connection one more time
if aws sts get-caller-identity &>/dev/null; then
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    echo -e "🔐 AWS Connection: ${GREEN}Connected${NC}"
    echo -e "   Account ID: ${ACCOUNT_ID}"
else
    echo -e "🔐 AWS Connection: ${YELLOW}Not configured${NC}"
    echo "   Run 'aws configure' to set up credentials"
fi

echo ""
echo -e "${BLUE}Happy Security Testing! 🛡️${NC}"
echo ""

