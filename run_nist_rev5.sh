#!/bin/bash
SCRIPT_DIR="/mnt/c/Users/iperr/TestZippr"
source "${SCRIPT_DIR}/security-venv/bin/activate"
echo "🛡️ Starting NIST 800-53 Rev 5 Comprehensive Assessment..."
streamlit run "${SCRIPT_DIR}/nist_rev5_comprehensive_app.py"

