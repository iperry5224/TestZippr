#!/bin/bash
#===============================================================================
# SOPRA full bundle — one-shot install (venv + dependencies)
# Run from the directory created after unzipping sopra_full_install.zip
#
# Usage:
#   chmod +x install_sopra.sh
#   ./install_sopra.sh
#===============================================================================

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo ""
echo "SOPRA — installing Python environment and dependencies"
echo "Directory: $ROOT"
echo ""

if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 is required. Install Python 3.8+ and retry."
    exit 1
fi

PYVER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Using Python $PYVER"

if [ ! -f "$ROOT/requirements.txt" ]; then
    echo "ERROR: requirements.txt not found in $ROOT"
    exit 1
fi

if [ ! -f "$ROOT/sopra_setup.py" ]; then
    echo "ERROR: sopra_setup.py not found — unzip the full bundle in this directory first."
    exit 1
fi

echo "Creating virtual environment: $ROOT/venv"
python3 -m venv "$ROOT/venv"
# shellcheck source=/dev/null
source "$ROOT/venv/bin/activate"

python -m pip install --upgrade pip wheel setuptools
echo "Installing requirements.txt ..."
python -m pip install -r "$ROOT/requirements.txt"

echo "Installing additional packages used by SOPRA features ..."
python -m pip install numpy openpyxl XlsxWriter requests

echo "Ensuring Streamlit 1.27+ (st.rerun support) ..."
python -m pip install "streamlit>=1.27"

if [ -z "${AWS_DEFAULT_REGION:-}" ]; then
    TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
        -H "X-aws-ec2-metadata-token-ttl-seconds: 60" --max-time 2 2>/dev/null || true)
    if [ -n "$TOKEN" ]; then
        R=$(curl -s --max-time 2 -H "X-aws-ec2-metadata-token: $TOKEN" \
            http://169.254.169.254/latest/meta-data/placement/region 2>/dev/null || true)
        if [ -n "$R" ]; then
            export AWS_DEFAULT_REGION="$R"
            echo "Set AWS_DEFAULT_REGION=$R (from instance metadata)"
        fi
    fi
fi

chmod +x "$ROOT/start_sopra.sh" 2>/dev/null || true

echo ""
echo "==================================================================="
echo "  Install complete."
echo ""
echo "  Start SOPRA:"
echo "    ./start_sopra.sh"
echo ""
echo "  Optional: set port before start"
echo "    export SOPRA_PORT=8080 && ./start_sopra.sh"
echo "==================================================================="
echo ""
