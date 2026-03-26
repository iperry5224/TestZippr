#!/bin/bash
# SAELAR - Kill/Stop Command
# Stops SAELAR and ngrok processes

echo ""
echo "  Stopping SAELAR and ngrok..."

# Kill SAELAR (streamlit)
SAELAR_PIDS=$(pgrep -f "streamlit run nist_setup.py" 2>/dev/null)
if [ -n "$SAELAR_PIDS" ]; then
    pkill -f "streamlit run nist_setup.py"
    echo "  ✓ SAELAR stopped"
else
    echo "  ⚠ SAELAR was not running"
fi

# Kill ngrok
NGROK_PIDS=$(pgrep -f "ngrok http" 2>/dev/null)
if [ -n "$NGROK_PIDS" ]; then
    pkill -f "ngrok http"
    echo "  ✓ ngrok stopped"
else
    echo "  ⚠ ngrok was not running"
fi

echo ""
