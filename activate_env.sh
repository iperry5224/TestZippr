#!/bin/bash
# Quick activation script - source this file to activate the environment
# Usage: source activate_env.sh

SCRIPT_DIR="/mnt/c/Users/iperr/TestZippr"
source "${SCRIPT_DIR}/security-venv/bin/activate"
cd "${SCRIPT_DIR}"

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

