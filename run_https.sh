#!/bin/bash
#===============================================================================
# Run Streamlit with HTTPS (Secure)
#===============================================================================

SCRIPT_DIR="/mnt/c/Users/iperr/TestZippr"
CERT_DIR="$SCRIPT_DIR/ssl_certs"

# Activate virtual environment
source "$SCRIPT_DIR/security-venv/bin/activate"

# Check if certificates exist
if [ ! -f "$CERT_DIR/streamlit.crt" ] || [ ! -f "$CERT_DIR/streamlit.key" ]; then
    echo "⚠️  SSL certificates not found. Generating..."
    bash "$SCRIPT_DIR/generate_ssl_certs.sh"
fi

echo ""
echo "🔒 Starting Streamlit with HTTPS..."
echo "======================================"
echo ""

# Run Streamlit with SSL
streamlit run "$SCRIPT_DIR/nist_rev5_comprehensive_app.py" \
    --server.sslCertFile="$CERT_DIR/streamlit.crt" \
    --server.sslKeyFile="$CERT_DIR/streamlit.key" \
    --server.port=8501 \
    --server.address=0.0.0.0

