# SAELAR - Security Architecture and Evaluation

## EC2 Deployment Package

This package contains everything needed to deploy SAELAR on an EC2 instance.

## Quick Start

```bash
# 1. Upload and extract
unzip saelar_deploy.zip
cd saelar_deploy

# 2. Run installer
chmod +x install.sh
./install.sh

# 3. Start SAELAR
source saelar-venv/bin/activate
streamlit run nist_setup.py --server.port 8443
```

## Files Included

| File | Description |
|------|-------------|
| `nist_setup.py` | Main SAELAR application |
| `nist_dashboard.py` | Dashboard components |
| `nist_pages.py` | Page renderers |
| `nist_auth.py` | Authentication module |
| `nist_800_53_controls.py` | Control definitions |
| `nist_800_53_rev5_full.py` | Full Rev 5 implementation |
| `requirements.txt` | Python dependencies |
| `install.sh` | EC2 installation script |
| `saelar.sh` | Launch script (Linux) |
| `assets/` | Logo and images |

## Modes of Operation

### Standard Mode (Cloud)
- Uses AWS Bedrock for AI
- Requires internet connectivity
- Data stays within AWS

```bash
streamlit run nist_setup.py --server.port 8443
```

### Air-Gapped Mode (No Internet)
- Uses local Ollama for AI
- No internet required
- Fully isolated operation

```bash
# Install Ollama
./install.sh --with-ollama

# Start Ollama (in background)
ollama serve &

# Start SAELAR in air-gapped mode
export SAELAR_AIRGAPPED=true
streamlit run nist_setup.py --server.port 8443
```

## AWS Configuration

SAELAR needs AWS credentials for:
- Cloud assessments (standard mode)
- Bedrock AI (if not in air-gapped mode)

Configure via:
1. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
2. IAM role attached to EC2 instance
3. SAELAR's built-in credential configuration

## EC2 Security Group

Ensure your security group allows:
- **Port 8443** for SAELAR
- **Port 11434** (only if using Ollama remotely)

## Troubleshooting

### "Module not found" errors
```bash
source saelar-venv/bin/activate
pip install -r requirements.txt
```

### Ollama not connecting (air-gapped mode)
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

### AWS credentials not working
```bash
# Verify credentials
aws sts get-caller-identity

# Or configure in SAELAR UI
```

## Support

For issues or questions, contact your system administrator.
