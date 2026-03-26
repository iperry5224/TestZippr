#!/bin/bash
# SAELAR Quick Launch - EC2

cd /home/ec2-user

[ -f saelar-venv/bin/activate ] && source saelar-venv/bin/activate
[ -f venv/bin/activate ] && source venv/bin/activate

APP=nist_setup.py
[ -f nist.setup.py ] && APP=nist.setup.py

# IMDSv2: get token first (required when metadata requires auth)
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 60" --max-time 2 2>/dev/null)
if [ -n "$TOKEN" ]; then
  IP=$(curl -s --max-time 2 -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null)
fi
[ -z "$IP" ] || [[ ! "$IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] && IP="localhost"
echo ""
echo "SAELAR starting at http://${IP}:8443"
echo ""

streamlit run "$APP" --server.port 8443 --server.address 0.0.0.0 --server.headless true
