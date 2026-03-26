# SOPSAEL Deployment Summary

## Instance Details

| Item | Value |
|------|-------|
| **Instance Name** | sopsael |
| **Instance ID** | i-0f62b1059a10974d6 |
| **Public IP** | 44.223.74.174 |
| **Region** | us-east-1 |
| **Key Pair** | saelar-sopra-key.pem |
| **IAM Profile** | SaelarSopraEC2Profile (Bedrock access) |
| **Network** | Containers use `--network host` → inherit instance IAM (Bedrock works) |

## Access URLs

| App | Port | URL |
|-----|------|-----|
| **SAELAR** | 8443 | http://44.223.74.174:8443 |
| **SOPRA** | 5224 | http://44.223.74.174:5224 |

## SSH Access

```bash
ssh -i saelar-sopra-key.pem ubuntu@44.223.74.174
```

## Container Management

Containers use `--network host` so they inherit the EC2 instance IAM role (Bedrock access).

```bash
# SSH to instance
ssh -i saelar-sopra-key.pem ubuntu@44.223.74.174

# View running containers
sudo docker ps

# View logs
sudo docker logs -f sopsael-saelar
sudo docker logs -f sopsael-sopra

# Restart containers (use start script - preserves host network + IAM)
cd ~/sopsael && sudo bash deploy/start_containers_ec2.sh

# Stop containers
sudo docker stop sopsael-saelar sopsael-sopra
```

## Redeploy (after code changes)

From TestZippr root:

```powershell
# 1. Update local sopsael (if needed)
python sopsael/prepare_sopsael.py

# 2. Copy to EC2
scp -i saelar-sopra-key.pem -r sopsael ubuntu@44.223.74.174:~/

# 3. Rebuild and restart (uses host network for IAM/Bedrock)
ssh -i saelar-sopra-key.pem ubuntu@44.223.74.174 "cd sopsael && sudo docker build -t sopsael-saelar ./saelar && sudo docker build -t sopsael-sopra ./sopra_app && sudo bash deploy/start_containers_ec2.sh"
```

## Security Group

- **sopsael-sg**: Ports 22 (SSH), 8443 (SAELAR), 5224 (SOPRA)

---
*Deployed: February 2026*
