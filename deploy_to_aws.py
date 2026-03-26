#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
  SAELAR + SOPRA → AWS EC2 Deployment
  Automated infrastructure creation and application deployment
═══════════════════════════════════════════════════════════════════════════════
  Creates: Key pair, Security group, IAM role, EC2 instance
  Deploys: Both apps with systemd services + ngrok tunnels
  Result:  https://saelar.ngrok.dev  &  https://sopra.ngrok.dev
═══════════════════════════════════════════════════════════════════════════════
"""

import boto3
import io
import json
import os
import subprocess
import sys
import time
import zipfile
import tempfile
from pathlib import Path

# Force UTF-8 stdout on Windows to handle special characters
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ─── Configuration ────────────────────────────────────────────────────────────
REGION          = "us-east-1"
INSTANCE_TYPE   = "t3.medium"       # 2 vCPU, 4 GB RAM — comfortable for both apps
KEY_NAME        = "saelar-sopra-key"
KEY_FILE        = "saelar-sopra-key.pem"
SG_NAME         = "saelar-sopra-sg"
ROLE_NAME       = "SaelarSopraEC2Role"
PROFILE_NAME    = "SaelarSopraEC2Profile"
INSTANCE_NAME   = "SAELAR-SOPRA-Server"
DISK_GB         = 20
SSH_USER        = "ubuntu"          # Ubuntu AMI default

SAELAR_PORT     = 8484
SOPRA_PORT      = 8080

NGROK_TOKEN     = "36tYWSq8csrb0yWQVpMLCjAbnTL_32tNgrk27z4aWQecyM2KP"

# ─── Files to include in the deployment package ──────────────────────────────
INCLUDE_ROOT_FILES = [
    "nist_setup.py",                # SAELAR entry point
    "nist_800_53_controls.py",
    "nist_800_53_rev5_full.py",
    "nist_auth.py",
    "nist_dashboard.py",
    "nist_pages.py",
    "sopra_setup.py",               # SOPRA entry point
    "sopra_controls.py",
    "risk_score_app.py",
    "risk_score_calculator.py",
    "cisa_kev_checker.py",
    "ssp_generator.py",
    "wordy.py",
    "requirements.txt",
    "kev_catalog_cache.json",
]

INCLUDE_DIRS = [
    "sopra",                        # SOPRA package
    "assets",                       # Logos, avatars
    "demo_csv_data",                # Sample CSV data
    "templates",                    # Document templates
    ".streamlit",                   # Streamlit config
]

# ─── AWS Clients ──────────────────────────────────────────────────────────────
ec2_client  = boto3.client("ec2",  region_name=REGION)
iam_client  = boto3.client("iam",  region_name=REGION)
ssm_client  = boto3.client("ssm",  region_name=REGION)

# ─── Helpers ──────────────────────────────────────────────────────────────────
CYAN   = ""
GREEN  = ""
YELLOW = ""
RED    = ""
BOLD   = ""
RESET  = ""

def banner(msg):
    print(f"\n{'='*64}")
    print(f"  {msg}")
    print(f"{'='*64}\n")

def ok(msg):
    print(f"  [OK] {msg}")

def warn(msg):
    print(f"  [!!] {msg}")

def fail(msg):
    print(f"  [FAIL] {msg}")

def info(msg):
    print(f"  [->] {msg}")

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1: EC2 Key Pair
# ══════════════════════════════════════════════════════════════════════════════
def create_key_pair():
    banner("PHASE 1 / 8 — EC2 Key Pair")

    # Check if key already exists
    try:
        ec2_client.describe_key_pairs(KeyNames=[KEY_NAME])
        if os.path.exists(KEY_FILE):
            ok(f"Key pair '{KEY_NAME}' exists and .pem is on disk")
            return
        else:
            warn(f"Key pair exists but .pem missing locally — recreating")
            ec2_client.delete_key_pair(KeyName=KEY_NAME)
    except ec2_client.exceptions.ClientError:
        pass

    resp = ec2_client.create_key_pair(KeyName=KEY_NAME)
    with open(KEY_FILE, "w") as f:
        f.write(resp["KeyMaterial"])

    # Fix Windows file permissions so SSH will accept the key
    if sys.platform == "win32":
        subprocess.run(["icacls", KEY_FILE, "/reset"],
                       capture_output=True, check=False)
        subprocess.run(["icacls", KEY_FILE, "/grant:r",
                        f"{os.environ['USERNAME']}:(R)"],
                       capture_output=True, check=False)
        subprocess.run(["icacls", KEY_FILE, "/inheritance:r"],
                       capture_output=True, check=False)
    else:
        os.chmod(KEY_FILE, 0o400)

    ok(f"Created key pair '{KEY_NAME}' → {KEY_FILE}")


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2: Security Group
# ══════════════════════════════════════════════════════════════════════════════
def create_security_group():
    banner("PHASE 2 / 8 — Security Group")

    # Default VPC
    vpcs = ec2_client.describe_vpcs(
        Filters=[{"Name": "is-default", "Values": ["true"]}]
    )
    vpc_id = vpcs["Vpcs"][0]["VpcId"]
    info(f"Default VPC: {vpc_id}")

    # Check existing
    sgs = ec2_client.describe_security_groups(
        Filters=[{"Name": "group-name", "Values": [SG_NAME]}]
    )
    if sgs["SecurityGroups"]:
        sg_id = sgs["SecurityGroups"][0]["GroupId"]
        ok(f"Security group already exists: {sg_id}")
        return sg_id

    sg = ec2_client.create_security_group(
        GroupName=SG_NAME,
        Description="SAELAR and SOPRA - SSH and app ports",
        VpcId=vpc_id,
    )
    sg_id = sg["GroupId"]

    ec2_client.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {
                "IpProtocol": "tcp", "FromPort": 22, "ToPort": 22,
                "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "SSH"}],
            },
            {
                "IpProtocol": "tcp",
                "FromPort": SAELAR_PORT, "ToPort": SAELAR_PORT,
                "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "SAELAR"}],
            },
            {
                "IpProtocol": "tcp",
                "FromPort": SOPRA_PORT, "ToPort": SOPRA_PORT,
                "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "SOPRA"}],
            },
        ],
    )

    ok(f"Created security group: {sg_id}")
    ok(f"Inbound rules: SSH (22), SAELAR ({SAELAR_PORT}), SOPRA ({SOPRA_PORT})")
    return sg_id


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 3: IAM Role with Bedrock Access
# ══════════════════════════════════════════════════════════════════════════════
def create_iam_role():
    banner("PHASE 3 / 8 — IAM Role + Instance Profile")

    trust = json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ec2.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }],
    })

    # Create role (idempotent)
    try:
        iam_client.get_role(RoleName=ROLE_NAME)
        ok(f"IAM role exists: {ROLE_NAME}")
    except iam_client.exceptions.NoSuchEntityException:
        iam_client.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=trust,
            Description="EC2 role for SAELAR/SOPRA with Bedrock access",
        )
        ok(f"Created IAM role: {ROLE_NAME}")

    # Attach Bedrock permissions
    bedrock_policy = json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": ["bedrock:*", "bedrock-runtime:*"],
            "Resource": "*",
        }],
    })
    iam_client.put_role_policy(
        RoleName=ROLE_NAME,
        PolicyName="BedrockFullAccess",
        PolicyDocument=bedrock_policy,
    )
    ok("Bedrock permissions attached")

    # Instance profile (idempotent)
    try:
        iam_client.get_instance_profile(InstanceProfileName=PROFILE_NAME)
        ok(f"Instance profile exists: {PROFILE_NAME}")
    except iam_client.exceptions.NoSuchEntityException:
        iam_client.create_instance_profile(InstanceProfileName=PROFILE_NAME)
        try:
            iam_client.add_role_to_instance_profile(
                InstanceProfileName=PROFILE_NAME, RoleName=ROLE_NAME,
            )
        except iam_client.exceptions.LimitExceededException:
            pass  # role already attached
        ok(f"Created instance profile: {PROFILE_NAME}")
        info("Waiting 12s for IAM propagation...")
        time.sleep(12)

    return PROFILE_NAME


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 4: Launch EC2 Instance
# ══════════════════════════════════════════════════════════════════════════════
USER_DATA = """#!/bin/bash
set -ex
exec > /var/log/user-data.log 2>&1

echo "===== SAELAR/SOPRA Bootstrap ====="

# System update
apt-get update -y
apt-get upgrade -y

# Python
apt-get install -y python3-pip python3-venv python3-dev unzip htop

# ngrok
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
  | gpg --dearmor -o /usr/share/keyrings/ngrok.gpg
echo "deb [signed-by=/usr/share/keyrings/ngrok.gpg] https://ngrok-agent.s3.amazonaws.com/deb stable main" \
  > /etc/apt/sources.list.d/ngrok.list
apt-get update -y
apt-get install -y ngrok

# App directory
mkdir -p /opt/apps
chown ubuntu:ubuntu /opt/apps

# Signal done
touch /tmp/user_data_complete
echo "===== Bootstrap complete ====="
"""


def get_ubuntu_ami():
    """Latest Ubuntu 22.04 LTS AMI via SSM Parameter Store."""
    resp = ssm_client.get_parameter(
        Name="/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id"
    )
    return resp["Parameter"]["Value"]


def launch_instance(sg_id, profile_name):
    banner("PHASE 4 / 8 — Launch EC2 Instance")

    # Check for existing
    existing = ec2_client.describe_instances(
        Filters=[
            {"Name": "tag:Name", "Values": [INSTANCE_NAME]},
            {"Name": "instance-state-name",
             "Values": ["running", "stopped", "pending"]},
        ]
    )
    for r in existing["Reservations"]:
        for inst in r["Instances"]:
            iid = inst["InstanceId"]
            state = inst["State"]["Name"]
            ok(f"Found existing instance {iid} ({state})")
            if state == "stopped":
                info("Starting stopped instance …")
                ec2_client.start_instances(InstanceIds=[iid])
                ec2_client.get_waiter("instance_running").wait(InstanceIds=[iid])
            if state in ("stopped", "pending"):
                ec2_client.get_waiter("instance_running").wait(InstanceIds=[iid])
            desc = ec2_client.describe_instances(InstanceIds=[iid])
            ip = desc["Reservations"][0]["Instances"][0].get("PublicIpAddress", "")
            ok(f"Public IP: {ip}")
            return iid, ip

    ami = get_ubuntu_ami()
    info(f"AMI:  {ami}  (Ubuntu 22.04)")
    info(f"Type: {INSTANCE_TYPE}  |  Disk: {DISK_GB} GB gp3")

    resp = ec2_client.run_instances(
        ImageId=ami,
        InstanceType=INSTANCE_TYPE,
        KeyName=KEY_NAME,
        SecurityGroupIds=[sg_id],
        MinCount=1, MaxCount=1,
        IamInstanceProfile={"Name": profile_name},
        BlockDeviceMappings=[{
            "DeviceName": "/dev/sda1",
            "Ebs": {"VolumeSize": DISK_GB, "VolumeType": "gp3",
                     "DeleteOnTermination": True},
        }],
        UserData=USER_DATA,
        TagSpecifications=[{
            "ResourceType": "instance",
            "Tags": [{"Key": "Name", "Value": INSTANCE_NAME}],
        }],
    )

    iid = resp["Instances"][0]["InstanceId"]
    ok(f"Launched: {iid}")

    info("Waiting for instance to enter RUNNING state …")
    ec2_client.get_waiter("instance_running").wait(InstanceIds=[iid])

    desc = ec2_client.describe_instances(InstanceIds=[iid])
    ip = desc["Reservations"][0]["Instances"][0]["PublicIpAddress"]
    ok(f"Running!  Public IP: {ip}")

    info("Waiting for status checks (1-2 min) …")
    ec2_client.get_waiter("instance_status_ok").wait(InstanceIds=[iid])
    ok("All status checks passed")

    return iid, ip


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 5: Build Deployment Package
# ══════════════════════════════════════════════════════════════════════════════
def build_zip():
    banner("PHASE 5 / 8 — Build Deployment Package")

    root = Path(os.getcwd())
    zip_path = root / "deploy_package.zip"

    count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Root-level files
        for fname in INCLUDE_ROOT_FILES:
            fpath = root / fname
            if fpath.exists():
                zf.write(fpath, fname)
                count += 1

        # Directories (recursive, skip __pycache__ and .pyc)
        for dname in INCLUDE_DIRS:
            dpath = root / dname
            if not dpath.exists():
                warn(f"Directory not found, skipping: {dname}/")
                continue
            for fpath in dpath.rglob("*"):
                if fpath.is_dir():
                    continue
                if "__pycache__" in str(fpath):
                    continue
                if fpath.suffix == ".pyc":
                    continue
                arcname = str(fpath.relative_to(root))
                zf.write(fpath, arcname)
                count += 1

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    ok(f"deploy_package.zip  ({count} files, {size_mb:.1f} MB)")
    return str(zip_path)


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 6: Upload & Install
# ══════════════════════════════════════════════════════════════════════════════
def _ssh(ip, cmd, timeout=300):
    """Run command on the instance via SSH."""
    r = subprocess.run(
        ["ssh",
         "-o", "StrictHostKeyChecking=no",
         "-o", "ConnectTimeout=10",
         "-o", "ServerAliveInterval=15",
         "-i", KEY_FILE,
         f"{SSH_USER}@{ip}",
         cmd],
        capture_output=True, text=True, timeout=timeout,
    )
    return r


def _scp(ip, local, remote):
    """Copy a file to the instance."""
    r = subprocess.run(
        ["scp",
         "-o", "StrictHostKeyChecking=no",
         "-i", KEY_FILE,
         local,
         f"{SSH_USER}@{ip}:{remote}"],
        capture_output=True, text=True, timeout=300,
    )
    return r.returncode == 0


def wait_for_ssh(ip, max_wait=180):
    info(f"Waiting for SSH on {ip} …")
    t0 = time.time()
    while time.time() - t0 < max_wait:
        try:
            r = _ssh(ip, "echo ready", timeout=10)
            if r.returncode == 0 and "ready" in (r.stdout or ""):
                ok("SSH is ready")
                return True
        except Exception:
            pass
        time.sleep(5)
    fail(f"SSH not ready after {max_wait}s")
    return False


def wait_for_bootstrap(ip, max_wait=300):
    info("Waiting for bootstrap (apt + ngrok install) …")
    t0 = time.time()
    while time.time() - t0 < max_wait:
        r = _ssh(ip, "test -f /tmp/user_data_complete && echo done", timeout=10)
        if "done" in (r.stdout or ""):
            ok("Bootstrap complete")
            return True
        time.sleep(10)
    warn("Bootstrap may still be running — proceeding anyway")
    return False


def deploy_code(ip, zip_path):
    banner("PHASE 6 / 8 — Upload & Install Dependencies")

    if not wait_for_ssh(ip):
        fail("Cannot connect via SSH — aborting")
        sys.exit(1)

    wait_for_bootstrap(ip)

    # Upload
    info("Uploading deployment package …")
    if not _scp(ip, zip_path, "/tmp/deploy_package.zip"):
        fail("SCP failed!")
        sys.exit(1)
    ok("Upload complete")

    # Extract
    info("Extracting on instance …")
    _ssh(ip, "cd /opt/apps && sudo unzip -o /tmp/deploy_package.zip")
    _ssh(ip, "sudo chown -R ubuntu:ubuntu /opt/apps")
    ok("Extracted to /opt/apps")

    # Python venv + deps
    info("Creating Python virtualenv and installing dependencies …")
    _ssh(ip, "python3 -m venv /opt/apps/venv")
    r = _ssh(ip, "/opt/apps/venv/bin/pip install --upgrade pip", timeout=60)
    r = _ssh(ip, "/opt/apps/venv/bin/pip install -r /opt/apps/requirements.txt",
             timeout=180)
    if r.returncode == 0:
        ok("All Python dependencies installed")
    else:
        warn(f"pip install had warnings — check logs")
        if r.stderr:
            print(f"      {r.stderr[:200]}")


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 7: Configure ngrok + systemd Services
# ══════════════════════════════════════════════════════════════════════════════
def configure_services(ip):
    banner("PHASE 7 / 8 — Configure ngrok & systemd Services")

    VENV_PY = "/opt/apps/venv/bin/python"
    VENV_STREAMLIT = "/opt/apps/venv/bin/streamlit"

    # ── ngrok config ──────────────────────────────────────────────────────
    info("Writing ngrok configuration …")
    ngrok_yml = f"""version: "2"
authtoken: {NGROK_TOKEN}
tunnels:
  saelar:
    addr: {SAELAR_PORT}
    proto: http
    domain: saelar.ngrok.dev
  sopra:
    addr: {SOPRA_PORT}
    proto: http
    domain: sopra.ngrok.dev
"""
    # Write via a temp file to avoid quoting issues
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".yml",
                                      delete=False, dir=".")
    tmp.write(ngrok_yml)
    tmp.close()
    _scp(ip, tmp.name, "/tmp/ngrok.yml")
    os.unlink(tmp.name)

    _ssh(ip, "mkdir -p /home/ubuntu/.config/ngrok")
    _ssh(ip, "cp /tmp/ngrok.yml /home/ubuntu/.config/ngrok/ngrok.yml")
    ok("ngrok.yml installed")

    # ── SAELAR systemd service ────────────────────────────────────────────
    info("Creating SAELAR service …")
    saelar_unit = f"""[Unit]
Description=SAELAR - NIST 800-53 Risk Assessment Platform
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/apps
ExecStart={VENV_STREAMLIT} run nist_setup.py \\
    --server.port {SAELAR_PORT} \\
    --server.address 0.0.0.0 \\
    --server.headless true
Restart=always
RestartSec=5
Environment=HOME=/home/ubuntu
Environment=AWS_DEFAULT_REGION={REGION}

[Install]
WantedBy=multi-user.target
"""
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".service",
                                      delete=False, dir=".")
    tmp.write(saelar_unit)
    tmp.close()
    _scp(ip, tmp.name, "/tmp/saelar.service")
    os.unlink(tmp.name)
    _ssh(ip, "sudo cp /tmp/saelar.service /etc/systemd/system/saelar.service")
    ok("saelar.service created")

    # ── SOPRA systemd service ─────────────────────────────────────────────
    info("Creating SOPRA service …")
    sopra_unit = f"""[Unit]
Description=SOPRA - Security Operations Platform for Risk Assessment
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/apps
ExecStart={VENV_STREAMLIT} run sopra_setup.py \\
    --server.port {SOPRA_PORT} \\
    --server.address 0.0.0.0 \\
    --server.headless true
Restart=always
RestartSec=5
Environment=HOME=/home/ubuntu
Environment=AWS_DEFAULT_REGION={REGION}

[Install]
WantedBy=multi-user.target
"""
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".service",
                                      delete=False, dir=".")
    tmp.write(sopra_unit)
    tmp.close()
    _scp(ip, tmp.name, "/tmp/sopra.service")
    os.unlink(tmp.name)
    _ssh(ip, "sudo cp /tmp/sopra.service /etc/systemd/system/sopra.service")
    ok("sopra.service created")

    # ── ngrok systemd service ─────────────────────────────────────────────
    info("Creating ngrok tunnel service …")
    ngrok_unit = f"""[Unit]
Description=ngrok tunnels (SAELAR + SOPRA)
After=network.target saelar.service sopra.service

[Service]
Type=simple
User=ubuntu
ExecStart=/usr/bin/ngrok start --all --config /home/ubuntu/.config/ngrok/ngrok.yml
Restart=always
RestartSec=10
Environment=HOME=/home/ubuntu

[Install]
WantedBy=multi-user.target
"""
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".service",
                                      delete=False, dir=".")
    tmp.write(ngrok_unit)
    tmp.close()
    _scp(ip, tmp.name, "/tmp/ngrok-tunnels.service")
    os.unlink(tmp.name)
    _ssh(ip, "sudo cp /tmp/ngrok-tunnels.service /etc/systemd/system/ngrok-tunnels.service")
    ok("ngrok-tunnels.service created")

    # ── Enable & start everything ─────────────────────────────────────────
    info("Starting all services …")
    _ssh(ip, "sudo systemctl daemon-reload")
    _ssh(ip, "sudo systemctl enable saelar sopra ngrok-tunnels")

    _ssh(ip, "sudo systemctl start saelar")
    ok("SAELAR started")
    time.sleep(3)

    _ssh(ip, "sudo systemctl start sopra")
    ok("SOPRA started")
    time.sleep(3)

    _ssh(ip, "sudo systemctl start ngrok-tunnels")
    ok("ngrok tunnels started")
    time.sleep(5)


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 8: Verify
# ══════════════════════════════════════════════════════════════════════════════
def verify(ip, instance_id):
    banner("PHASE 8 / 8 — Verification")

    all_good = True
    for svc in ["saelar", "sopra", "ngrok-tunnels"]:
        r = _ssh(ip, f"sudo systemctl is-active {svc}", timeout=10)
        status = (r.stdout or "").strip()
        if status == "active":
            ok(f"{svc}: {status}")
        else:
            fail(f"{svc}: {status}")
            # Show last few log lines
            r2 = _ssh(ip, f"sudo journalctl -u {svc} --no-pager -n 10", timeout=10)
            if r2.stdout:
                print(f"      Last log lines:\n{r2.stdout}")
            all_good = False

    # ── Final summary ─────────────────────────────────────────────────────
    print(f"\n{'='*64}")
    if all_good:
        print(f"  DEPLOYMENT COMPLETE!")
    else:
        print(f"  DEPLOYMENT FINISHED (check warnings above)")
    print(f"{'='*64}\n")

    print(f"  Instance:    {instance_id}")
    print(f"  Public IP:   {ip}")
    print(f"  SSH:         ssh -i {KEY_FILE} {SSH_USER}@{ip}")
    print()
    print(f"  === ACCESS URLs ===")
    print(f"  SAELAR:      https://saelar.ngrok.dev")
    print(f"  SOPRA:       https://sopra.ngrok.dev")
    print()
    print(f"  Direct (via IP):")
    print(f"  SAELAR:      http://{ip}:{SAELAR_PORT}")
    print(f"  SOPRA:       http://{ip}:{SOPRA_PORT}")
    print()
    print(f"  Service management (SSH in first):")
    print(f"    sudo systemctl status saelar")
    print(f"    sudo systemctl status sopra")
    print(f"    sudo systemctl status ngrok-tunnels")
    print(f"    sudo journalctl -u saelar -f       # live logs")
    print(f"    sudo journalctl -u sopra -f")
    print()
    print(f"  NOTE: Stop your local ngrok -- the EC2 ngrok now")
    print(f"  owns saelar.ngrok.dev and sopra.ngrok.dev")
    print()


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════
def main():
    print(f"\n{BOLD}{CYAN}")
    print("  +==============================================================+")
    print("  |   SAELAR + SOPRA  ->  AWS EC2 Deployment                     |")
    print("  |   Automated Infrastructure & Application Setup               |")
    print("  +==============================================================+")
    print(f"{RESET}")

    t0 = time.time()

    try:
        # Infrastructure
        create_key_pair()
        sg_id = create_security_group()
        profile = create_iam_role()

        # Instance
        instance_id, ip = launch_instance(sg_id, profile)

        # Package & deploy
        zip_path = build_zip()
        deploy_code(ip, zip_path)

        # Services
        configure_services(ip)

        # Verify
        verify(ip, instance_id)

    except KeyboardInterrupt:
        print(f"\n{YELLOW}Interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        fail(f"Deployment error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    elapsed = time.time() - t0
    print(f"  Total time: {elapsed/60:.1f} minutes\n")


if __name__ == "__main__":
    main()
