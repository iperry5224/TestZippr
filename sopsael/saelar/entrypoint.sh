#!/bin/bash
set -e

echo "=========================================="
echo "  SAELAR - Security Assessment Tool"
echo "  Starting container..."
echo "=========================================="

# Check if AWS credentials are available
if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "✓ AWS credentials found in environment variables"
elif [ -f "/root/.aws/credentials" ]; then
    echo "✓ AWS credentials file mounted"
else
    echo "⚠ Warning: No AWS credentials found"
    echo "  Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables"
    echo "  Or mount your ~/.aws directory to /root/.aws"
fi

# Check if logo exists
if [ -f "/app/assets/saelar_logo.png" ]; then
    echo "✓ Logo file found"
else
    echo "⚠ Warning: Logo file not found at /app/assets/saelar_logo.png"
fi

# Set default region if not set
export AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}

echo ""
echo "Starting Streamlit on port ${STREAMLIT_SERVER_PORT:-8484}..."
echo "=========================================="

# Execute the main command
exec "$@"
