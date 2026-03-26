#!/bin/bash
# =============================================================================
# SAELAR EC2 Installation Script
# =============================================================================
# This script installs SAELAR on an Amazon Linux 2 / Ubuntu EC2 instance
#
# Usage:
#   chmod +x install.sh
#   ./install.sh
#
# For air-gapped mode, also run:
#   ./install.sh --with-ollama
# =============================================================================

set -e

echo ""
echo "============================================================"
echo "  SAELAR - Security Architecture and Evaluation"
echo "  EC2 Installation Script"
echo "============================================================"
echo ""

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    OS="unknown"
fi

echo "[INFO] Detected OS: $OS"

# Install Python and dependencies
echo "[INFO] Installing Python and system dependencies..."

if [ "$OS" == "amzn" ] || [ "$OS" == "rhel" ] || [ "$OS" == "centos" ]; then
    # Amazon Linux / RHEL / CentOS
    sudo yum update -y
    sudo yum install -y python3 python3-pip python3-devel git
elif [ "$OS" == "ubuntu" ] || [ "$OS" == "debian" ]; then
    # Ubuntu / Debian
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv git
else
    echo "[WARN] Unknown OS, assuming Python3 is installed"
fi

# Create virtual environment
echo "[INFO] Creating Python virtual environment..."
python3 -m venv saelar-venv
source saelar-venv/bin/activate

# Install Python packages
echo "[INFO] Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Create assets directory if needed
mkdir -p assets

# Set permissions
chmod +x saelar.sh 2>/dev/null || true
chmod +x install.sh 2>/dev/null || true
chmod +x generate_ssl_certs.sh 2>/dev/null || true

# Install Ollama if requested (for air-gapped mode)
if [ "$1" == "--with-ollama" ]; then
    echo ""
    echo "[INFO] Installing Ollama for air-gapped mode..."
    curl -fsSL https://ollama.ai/install.sh | sh
    
    echo "[INFO] Pulling Llama 3 8B model (this may take a while)..."
    ollama pull llama3:8b
    
    echo "[INFO] Ollama installed. Start it with: ollama serve"
fi

echo ""
echo "============================================================"
echo "  Installation Complete!"
echo "============================================================"
echo ""
echo "  To start SAELAR:"
echo "    source saelar-venv/bin/activate"
echo "    streamlit run nist_setup.py --server.port 8443"
echo ""
echo "  Or use the launch script:"
echo "    ./saelar.sh"
echo ""
echo "  For air-gapped mode (no internet):"
echo "    export SAELAR_AIRGAPPED=true"
echo "    ollama serve &"
echo "    streamlit run nist_setup.py --server.port 8443"
echo ""
echo "  Make sure your EC2 security group allows port 8443!"
echo ""
