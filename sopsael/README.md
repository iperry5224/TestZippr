# SOPSAEL

Containerized **SAELAR** and **SOPRA** running on ports **8443** and **5224** respectively.

## Quick Start

### 1. Prepare the app copies (from TestZippr root)

```bash
python sopsael/prepare_sopsael.py
```

This copies SAELAR and SOPRA into `sopsael/saelar` and `sopsael/sopra_app`.

### 2. Build and run locally

```bash
cd sopsael
docker compose build
docker compose up -d
```

- **SAELAR:** http://localhost:8443  
- **SOPRA:** http://localhost:5224  

### 3. Launch EC2 (sopsael instance)

```bash
# From TestZippr root, with AWS credentials configured:
python sopsael/deploy/launch_sopsael_ec2.py
```

Creates a new EC2 named `sopsael` with:
- Security group: SSH (22), SAELAR (8443), SOPRA (5224)
- Docker pre-installed via user-data
- Uses existing key pair `saelar-sopra-key`

### 4. Deploy to EC2

After the instance is running (wait ~3 min for bootstrap):

```bash
# Copy sopsael folder to EC2
scp -i saelar-sopra-key.pem -r sopsael ubuntu@<EC2_IP>:~/

# SSH and start containers
ssh -i saelar-sopra-key.pem ubuntu@<EC2_IP>
cd sopsael
docker compose up -d
```

Access:
- **SAELAR:** `http://<EC2_IP>:8443`
- **SOPRA:** `http://<EC2_IP>:5224`

## Ports

| App    | Port | URL                    |
|--------|------|------------------------|
| SAELAR | 8443 | http://host:8443       |
| SOPRA  | 5224 | http://host:5224       |

## Environment

Set `AWS_DEFAULT_REGION` for Bedrock (default: `us-east-1`). On EC2, containers use `--network host` so they inherit the instance IAM role automatically—no credential mounting needed. Ensure the EC2 instance profile has Bedrock permissions.

## Commands

```bash
docker compose up -d      # Start
docker compose down       # Stop
docker compose logs -f    # View logs
docker compose pull       # Update images (after rebuild)
```
