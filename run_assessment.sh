#!/bin/bash
SCRIPT_DIR="/mnt/c/Users/iperr/TestZippr"
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

