#!/bin/bash
# SAELAR - Security Architecture and Evaluation Launch Command
# Launches the NIST 800-53 Rev 5 Assessment Tool with ngrok tunnel

PORT="${1:-8443}"

cd /mnt/c/Users/iperr/TestZippr

# Kill any existing SAELAR and ngrok processes
echo "  Stopping any existing SAELAR instances..."
pkill -f 'streamlit run nist_setup.py' 2>/dev/null
pkill -f 'ngrok http' 2>/dev/null
sleep 1

# Activate virtual environment if not already active
if [[ -z "$VIRTUAL_ENV" ]]; then
    source security-venv/bin/activate 2>/dev/null || source security-venv/Scripts/activate 2>/dev/null
fi

echo ""
echo "  ╔═══════════════════════════════════════════════════════════╗"
echo "  ║                                                           ║"
echo "  ║   SAELAR - Real-Time Risk Transparency & Remediation      ║"
echo "  ║       NIST 800-53 Rev 5 Security Assessment Tool          ║"
echo "  ║                                                           ║"
echo "  ╚═══════════════════════════════════════════════════════════╝"
echo ""

# Start SAELAR in background
echo "  Starting SAELAR..."
nohup streamlit run nist_setup.py --server.port $PORT > /tmp/saelar.log 2>&1 &
SAELAR_PID=$!
echo "  ✓ SAELAR started (PID: $SAELAR_PID)"
echo "    Local URL: http://localhost:$PORT"
echo ""

# Wait a moment for Streamlit to start
sleep 3

# Start ngrok tunnel in background
echo "  Starting ngrok tunnel..."
nohup ngrok http $PORT > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!
echo "  ✓ ngrok started (PID: $NGROK_PID)"
echo ""

# Wait for ngrok to initialize and get the public URL
sleep 3
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -o '"public_url":"https://[^"]*"' | head -1 | cut -d'"' -f4)

echo "  ════════════════════════════════════════════════════════════"
echo ""
echo "  📍 Access URLs:"
echo "     Local:    http://localhost:$PORT"
if [ -n "$NGROK_URL" ]; then
    echo "     Public:   $NGROK_URL"
else
    echo "     Public:   Check http://localhost:4040 for ngrok URL"
fi
echo ""
echo "  📁 Log files:"
echo "     SAELAR:   /tmp/saelar.log"
echo "     ngrok:    /tmp/ngrok.log"
echo ""
echo "  🛑 To stop everything:"
echo "     killsaelar"
echo ""
echo "  ════════════════════════════════════════════════════════════"
echo ""
