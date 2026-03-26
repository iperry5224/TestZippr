#!/bin/bash
#===============================================================================
# Setup HTTPS for Streamlit Apps
#===============================================================================

echo "🔒 HTTPS Setup Options for Streamlit"
echo "======================================"
echo ""

# Check if ngrok is installed
if command -v ngrok &> /dev/null; then
    echo "✅ ngrok is installed"
else
    echo "📥 Installing ngrok..."
    curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
    echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
    sudo apt update && sudo apt install ngrok -y
fi

echo ""
echo "To start HTTPS tunnel, run:"
echo "  ngrok http 8501"
echo ""
echo "This will give you a secure https:// URL like:"
echo "  https://abc123.ngrok.io"

