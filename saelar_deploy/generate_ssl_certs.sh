#!/bin/bash
#===============================================================================
# Generate Self-Signed SSL Certificates for Streamlit HTTPS
#===============================================================================

CERT_DIR="/mnt/c/Users/iperr/TestZippr/ssl_certs"
DAYS_VALID=365

echo "🔐 Generating SSL Certificates for HTTPS"
echo "========================================="

# Create certificate directory
mkdir -p "$CERT_DIR"
cd "$CERT_DIR"

# Generate private key
echo "📝 Generating private key..."
openssl genrsa -out streamlit.key 2048

# Generate self-signed certificate
echo "📜 Generating self-signed certificate..."
openssl req -new -x509 -key streamlit.key -out streamlit.crt -days $DAYS_VALID \
    -subj "/C=US/ST=State/L=City/O=SecurityAssessment/CN=localhost"

# Set permissions
chmod 600 streamlit.key
chmod 644 streamlit.crt

echo ""
echo "✅ SSL certificates generated!"
echo ""
echo "📁 Certificate location: $CERT_DIR"
echo "   - Private key: streamlit.key"
echo "   - Certificate: streamlit.crt"
echo ""
echo "🚀 To run Streamlit with HTTPS:"
echo ""
echo "   streamlit run nist_rev5_comprehensive_app.py \\"
echo "     --server.sslCertFile=$CERT_DIR/streamlit.crt \\"
echo "     --server.sslKeyFile=$CERT_DIR/streamlit.key \\"
echo "     --server.port=8501"
echo ""
echo "🌐 Then access via: https://localhost:8501"
echo ""
echo "⚠️  Note: Browser will show security warning for self-signed certs."
echo "    Click 'Advanced' > 'Proceed to localhost' to continue."

