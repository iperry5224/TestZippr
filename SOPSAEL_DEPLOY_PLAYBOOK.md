# SOPSAEL Deployment Playbook — Play by Play

Step-by-step guide to deploy containerized SAELAR + SOPRA to EC2.

---

## Prerequisites Checklist

- [ ] **AWS credentials** configured (`aws configure` or env vars)
- [ ] **Key pair** `saelar-sopra-key.pem` in project root (or path set in script)
- [ ] **Python 3** with `boto3` if launching new EC2 (`pip install boto3`)
- [ ] **Network access** in Cursor when running deploy (uncheck "Run in sandbox" if prompted)

---

## Scenario A: Fresh Sandbox — No EC2 Yet

### Step 1: Create key pair in AWS (if you don't have it)

1. AWS Console → EC2 → Key Pairs → Create key pair
2. Name: `saelar-sopra-key`
3. Save the `.pem` file to your project root: `c:\Users\iperr\TestZippr\`

### Step 2: Launch the EC2 instance

From TestZippr root:

```powershell
python sopsael/deploy/launch_sopsael_ec2.py
```

**What it does:** Creates an Ubuntu EC2 named `sopsael` with Docker, security group (22, 8443, 5224), and IAM profile for Bedrock.

**Wait:** ~2–3 minutes for bootstrap.

**Output:** Public IP (e.g. `44.223.74.174`). Note it.

### Step 3: Deploy SOPSAEL

```powershell
python deploy_sopsael_to_ec2.py
```

(If the IP changed, edit `deploy_sopsael_to_ec2.py` → `TARGETS["sopsael"]` with the new IP.)

---

## Scenario B: Existing EC2 / Sandbox

### Step 1: Configure the target

Edit `deploy_sopsael_to_ec2.py`, line 26:

```python
TARGETS = {
    "sopsael": "44.223.74.174",
    "sandbox": "YOUR_SANDBOX_IP",   # <-- Put your EC2 IP here
}
```

### Step 2: Ensure EC2 is ready

- Ubuntu (or similar Linux)
- Docker installed
- Security group allows: **22** (SSH), **8443** (SAELAR), **5224** (SOPRA)
- SSH user: `ubuntu` (for Ubuntu AMI)

### Step 3: Deploy

```powershell
cd c:\Users\iperr\TestZippr

# To sopsael
python deploy_sopsael_to_ec2.py

# To sandbox (after setting IP in script)
python deploy_sopsael_to_ec2.py sandbox

# Or use IP directly
python deploy_sopsael_to_ec2.py 12.34.56.78
```

---

## What the Deploy Script Does (Play by Play)

| Step | Action | Time |
|------|--------|------|
| 1 | Runs `prepare_sopsael.py` — copies SAELAR + SOPRA into `sopsael/` | ~5 sec |
| 2 | Fixes `start_containers_ec2.sh` line endings | instant |
| 3 | `scp` copies entire `sopsael/` folder to EC2 `~/sopsael` | 1–2 min |
| 4 | SSH → EC2: fixes script, builds `sopsael-saelar` Docker image | 2–4 min |
| 5 | SSH → EC2: builds `sopsael-sopra` Docker image | 2–4 min |
| 6 | SSH → EC2: runs `start_containers_ec2.sh` (stops old, starts new) | ~10 sec |

**Total:** ~5–10 minutes.

---

## After Deploy — Verify

### 1. Check containers

```bash
ssh -i saelar-sopra-key.pem ubuntu@YOUR_IP "sudo docker ps"
```

You should see `sopsael-saelar` and `sopsael-sopra` running.

### 2. Open in browser

- **SAELAR:** http://YOUR_IP:8443  
  Login: `admin` / `admin123`
- **SOPRA:** http://YOUR_IP:5224

### 3. If SAELAR asks for AWS credentials

On EC2 with IAM profile, it should use the instance role. If prompted:
- Create IAM user with `AmazonBedrockFullAccess`
- Create access key, enter in SAELAR UI

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `Permission denied (publickey)` | Use `ubuntu` (not `ec2-user`). Check key path. |
| `Connection refused` / timeout | Security group: 22, 8443, 5224 open. EC2 started? |
| `No such file or directory` | Run from **TestZippr root**. |
| Script fails at scp | Run with **network permission** (disable sandbox). |
| Containers fail to start | SSH in, run `sudo docker logs sopsael-saelar` |
| EC2 was stopped | Start it: `aws ec2 start-instances --instance-ids i-xxxxx` |

---

## Quick Reference

| Item | Value |
|------|-------|
| SAELAR port | 8443 |
| SOPRA port | 5224 |
| SSH user | ubuntu |
| Key | saelar-sopra-key.pem |
| IAM profile (for Bedrock) | SaelarSopraEC2Profile |
