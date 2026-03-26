# SAELAR Containerization Guide

A complete step-by-step guide to containerize the SAELAR NIST 800-53 Security Assessment Tool using Docker.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Structure](#project-structure)
3. [Step 1: Create the Dockerfile](#step-1-create-the-dockerfile)
4. [Step 2: Create .dockerignore](#step-2-create-dockerignore)
5. [Step 3: Create docker-compose.yml](#step-3-create-docker-composeyml)
6. [Step 4: Create entrypoint.sh](#step-4-create-entrypointsh)
7. [Step 5: Build the Container](#step-5-build-the-container)
8. [Step 6: Run the Container](#step-6-run-the-container)
9. [Environment Variables Reference](#environment-variables-reference)
10. [AWS Credentials Configuration](#aws-credentials-configuration)
11. [Exposing to the Internet](#exposing-to-the-internet)
12. [Troubleshooting](#troubleshooting)
13. [Production Considerations](#production-considerations)

---

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
  - Download: https://www.docker.com/products/docker-desktop/
- **Docker Compose** (included with Docker Desktop)
- **Git** (optional, for version control)

### Verify Installation

```bash
docker --version
docker-compose --version
```

---

## Project Structure

Your SAELAR project should have the following structure:

```
SAELAR/
├── assets/
│   └── saelar_logo.png
├── ssl_certs/                    # Optional: for HTTPS
│   ├── streamlit.crt
│   └── streamlit.key
├── nist_setup.py                 # Main entry point
├── nist_dashboard.py
├── nist_pages.py
├── nist_auth.py
├── requirements.txt
├── Dockerfile                    # You will create this
├── docker-compose.yml            # You will create this
├── .dockerignore                 # You will create this
└── entrypoint.sh                 # You will create this
```

---

## Step 1: Create the Dockerfile

Create a file named `Dockerfile` (no extension) in your project root:

```dockerfile
# =============================================================================
# SAELAR - Security Assessment Tool
# Dockerfile for containerization
# =============================================================================

# Use official Python runtime as base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8484 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for runtime data
RUN mkdir -p /app/ssl_certs /app/assets /root/.aws

# Make entrypoint executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose the Streamlit port
EXPOSE 8484

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8484/_stcore/health || exit 1

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command
CMD ["streamlit", "run", "nist_setup.py", "--server.port=8484", "--server.address=0.0.0.0"]
```

---

## Step 2: Create .dockerignore

Create a file named `.dockerignore` to exclude unnecessary files:

```
# Virtual environments
security-venv/
venv/
env/
.venv/

# Python cache
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# IDE files
.idea/
.vscode/
*.swp
*.swo
.cursor/

# Git
.git/
.gitignore

# Local configuration (will be mounted or set via env vars)
.saelar_aws_config.json
.nist_users.json

# Test files
test_*.py
*_test.py

# Documentation (optional - include if you want docs in container)
# *.md
# *.txt

# OS files
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Temporary files
tmp/
temp/
*.tmp

# Build artifacts
dist/
build/
*.egg-info/

# Shell scripts (not needed in container)
*.sh
!entrypoint.sh

# Batch files
*.bat
*.ps1

# Old/legacy files
nist_rev5_comprehensive_app.py
```

---

## Step 3: Create docker-compose.yml

Create `docker-compose.yml` for easier container management:

```yaml
version: '3.8'

services:
  saelar:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: saelar-app
    ports:
      - "8484:8484"
    environment:
      # Streamlit configuration
      - STREAMLIT_SERVER_PORT=8484
      - STREAMLIT_SERVER_ADDRESS=0.0.0.0
      - STREAMLIT_SERVER_HEADLESS=true
      
      # AWS credentials (Option 1: Environment variables)
      # Uncomment and set these, or use the mounted credentials file
      # - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      # - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      # - AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}
      
      # S3 bucket for reports
      - S3_BUCKET_NAME=${S3_BUCKET_NAME:-your-bucket-name}
      
    volumes:
      # Mount AWS credentials (Option 2: credentials file)
      - ~/.aws:/root/.aws:ro
      
      # Optional: Mount custom logo
      # - ./assets:/app/assets:ro
      
      # Optional: Mount SSL certificates
      # - ./ssl_certs:/app/ssl_certs:ro
      
    restart: unless-stopped
    
    # Resource limits (optional)
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
          
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8484/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

# Optional: Create a network for multiple services
networks:
  default:
    name: saelar-network
```

---

## Step 4: Create entrypoint.sh

Create `entrypoint.sh` for container initialization:

```bash
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
```

---

## Step 5: Build the Container

### Option A: Using Docker Compose (Recommended)

```bash
# Navigate to your project directory
cd /path/to/SAELAR

# Build the container
docker-compose build

# Or build with no cache (for fresh build)
docker-compose build --no-cache
```

### Option B: Using Docker directly

```bash
# Build the image
docker build -t saelar:latest .

# Or with a specific tag
docker build -t saelar:v1.0.0 .
```

---

## Step 6: Run the Container

### Option A: Using Docker Compose (Recommended)

```bash
# Start in foreground (see logs)
docker-compose up

# Start in background (detached)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

### Option B: Using Docker directly

```bash
# Run with AWS credentials as environment variables
docker run -d \
  --name saelar-app \
  -p 8484:8484 \
  -e AWS_ACCESS_KEY_ID=your_access_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret_key \
  -e AWS_DEFAULT_REGION=us-east-1 \
  saelar:latest

# Or mount your AWS credentials file
docker run -d \
  --name saelar-app \
  -p 8484:8484 \
  -v ~/.aws:/root/.aws:ro \
  saelar:latest

# View logs
docker logs -f saelar-app

# Stop the container
docker stop saelar-app

# Remove the container
docker rm saelar-app
```

### Access the Application

Open your browser and navigate to:
- **Local**: http://localhost:8484
- **Network**: http://YOUR_IP_ADDRESS:8484

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `STREAMLIT_SERVER_PORT` | `8484` | Port for Streamlit server |
| `STREAMLIT_SERVER_ADDRESS` | `0.0.0.0` | Bind address |
| `AWS_ACCESS_KEY_ID` | - | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | - | AWS secret key |
| `AWS_DEFAULT_REGION` | `us-east-1` | AWS region |
| `S3_BUCKET_NAME` | - | S3 bucket for reports |
| `SAELAR_LOGO_PATH` | `/app/assets/saelar_logo.png` | Custom logo path |
| `SAELAR_CERT_DIR` | `/app/ssl_certs` | SSL certificates directory |
| `SAELAR_CONFIG_FILE` | `/app/.saelar_aws_config.json` | AWS config cache |
| `SAELAR_USERS_FILE` | `/app/.nist_users.json` | User credentials file |

---

## AWS Credentials Configuration

### Option 1: Environment Variables (Recommended for containers)

Create a `.env` file (DO NOT commit to git):

```env
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=your-saelar-reports-bucket
```

Then run:
```bash
docker-compose --env-file .env up -d
```

### Option 2: Mount AWS Credentials File

If you have AWS CLI configured locally:

```bash
docker run -d \
  -p 8484:8484 \
  -v ~/.aws:/root/.aws:ro \
  saelar:latest
```

### Option 3: AWS IAM Role (For AWS ECS/EKS)

When running on AWS infrastructure, use IAM roles attached to the container task/pod.
No credentials needed in the container - they're provided automatically.

---

## Exposing to the Internet

### Option 1: ngrok (Quick testing)

```bash
# Install ngrok if not installed
# Run ngrok in a separate terminal
ngrok http 8484
```

### Option 2: Reverse Proxy (Production)

Use nginx or Traefik as a reverse proxy. Example nginx config:

```nginx
server {
    listen 80;
    server_name saelar.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8484;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

### Option 3: Cloud Deployment

- **AWS ECS**: Use AWS Fargate with Application Load Balancer
- **AWS EKS**: Deploy as Kubernetes pod with Ingress
- **Azure Container Instances**: Direct deployment with public IP
- **Google Cloud Run**: Serverless container deployment

---

## Troubleshooting

### Container won't start

```bash
# Check container logs
docker logs saelar-app

# Check if port is in use
netstat -an | grep 8484

# Run interactively for debugging
docker run -it --rm -p 8484:8484 saelar:latest /bin/bash
```

### AWS credentials not working

```bash
# Test AWS credentials inside container
docker exec -it saelar-app aws sts get-caller-identity

# Verify environment variables
docker exec -it saelar-app env | grep AWS
```

### Logo not displaying

```bash
# Check if logo file exists in container
docker exec -it saelar-app ls -la /app/assets/

# Copy logo into running container (temporary fix)
docker cp ./assets/saelar_logo.png saelar-app:/app/assets/
```

### High memory usage

Add resource limits in docker-compose.yml or:

```bash
docker run -d --memory=2g --cpus=2 saelar:latest
```

### Permission denied errors

```bash
# Rebuild with correct permissions
docker-compose build --no-cache

# Or fix permissions in Dockerfile
RUN chmod -R 755 /app
```

---

## Production Considerations

### Security Checklist

- [ ] Never commit `.env` files or credentials to git
- [ ] Use AWS IAM roles instead of access keys when possible
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Use a non-root user in the container
- [ ] Scan image for vulnerabilities: `docker scan saelar:latest`
- [ ] Keep base image updated
- [ ] Use secrets management (AWS Secrets Manager, HashiCorp Vault)

### Performance Optimization

- [ ] Multi-stage builds to reduce image size
- [ ] Use `.dockerignore` to exclude unnecessary files
- [ ] Set appropriate resource limits
- [ ] Enable health checks
- [ ] Use a CDN for static assets

### High Availability

- [ ] Run multiple container instances
- [ ] Use a load balancer
- [ ] Configure auto-scaling
- [ ] Set up monitoring and alerting
- [ ] Implement proper logging

---

## Quick Reference Commands

```bash
# Build
docker-compose build

# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Shell into container
docker exec -it saelar-app /bin/bash

# Check health
docker inspect --format='{{.State.Health.Status}}' saelar-app

# Remove all stopped containers
docker container prune

# Remove unused images
docker image prune
```

---

## Files Checklist

Before building, ensure you have:

- [ ] `Dockerfile`
- [ ] `.dockerignore`
- [ ] `docker-compose.yml`
- [ ] `entrypoint.sh`
- [ ] `requirements.txt` (with all dependencies)
- [ ] `assets/saelar_logo.png`
- [ ] All Python source files (`nist_*.py`)

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review container logs: `docker-compose logs -f`
3. Verify all environment variables are set correctly

---

*Document Version: 1.0*
*Last Updated: December 2025*
*SAELAR - Security Architecture and Evaluation Linear Assessment Reporting Tool*
