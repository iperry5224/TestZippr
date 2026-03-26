#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IGENTO -> AWS EC2 Deployment"""
import io
import os
import subprocess
import sys
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import boto3
import tempfile
import time
import zipfile
from pathlib import Path

# Reuse deploy_to_aws config
REGION          = "us-east-1"
KEY_NAME        = "saelar-sopra-key"
KEY_FILE        = "saelar-sopra-key.pem"
SG_NAME         = "saelar-sopra-sg"
INSTANCE_NAME   = "SAELAR-SOPRA-Server"
SSH_USER        = "ubuntu"
NGROK_TOKEN     = "36tYWSq8csrb0yWQVpMLCjAbnTL_32tNgrk27z4aWQecyM2KP"
NGROK_ENDPOINT_ID = "rd_39cdEPBWYyjteSHN0aoLsWJZxtH"  # Reserved domain for igento.ngrok.dev

SAELAR_PORT     = 8484
SOPRA_PORT      = 8080
IGENTO_PORT     = 8000

ec2_client = boto3.client("ec2", region_name=REGION)

def ok(msg):    print(f"  [OK] {msg}")
def warn(msg):  print(f"  [!!] {msg}")
def fail(msg):  print(f"  [FAIL] {msg}")
def info(msg):  print(f"  [->] {msg}")


def get_instance_ip():
    """Get public IP of the SAELAR-SOPRA EC2 instance."""
    r = ec2_client.describe_instances(
        Filters=[
            {"Name": "tag:Name", "Values": [INSTANCE_NAME]},
            {"Name": "instance-state-name", "Values": ["running"]},
        ]
    )
    for res in r.get("Reservations", []):
        for inst in res.get("Instances", []):
            ip = inst.get("PublicIpAddress")
            if ip:
                return ip
    return None


def add_igento_port_to_sg():
    """Add Igento port 8000 to security group if not already present."""
    sgs = ec2_client.describe_security_groups(
        Filters=[{"Name": "group-name", "Values": [SG_NAME]}]
    )
    if not sgs["SecurityGroups"]:
        fail(f"Security group {SG_NAME} not found")
        sys.exit(1)
    sg_id = sgs["SecurityGroups"][0]["GroupId"]
    rules = sgs["SecurityGroups"][0].get("IpPermissions", [])
    for r in rules:
        if r.get("FromPort") == IGENTO_PORT:
            ok(f"Port {IGENTO_PORT} already in security group")
            return sg_id
    ec2_client.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[{
            "IpProtocol": "tcp",
            "FromPort": IGENTO_PORT,
            "ToPort": IGENTO_PORT,
            "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "Igento MCP"}],
        }],
    )
    ok(f"Added port {IGENTO_PORT} to security group")
    return sg_id


def build_igento_zip():
    """Build zip of igento folder."""
    root = Path(__file__).resolve().parent
    igento_dir = root / "igento"
    zip_path = root / "igento_deploy.zip"
    if not igento_dir.exists():
        fail("igento/ directory not found")
        sys.exit(1)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fpath in igento_dir.rglob("*"):
            if fpath.is_dir() or "__pycache__" in str(fpath) or fpath.suffix == ".pyc":
                continue
            arcname = "igento/" + str(fpath.relative_to(igento_dir))
            zf.write(fpath, arcname)
    ok(f"Built igento_deploy.zip ({zip_path.stat().st_size / 1024:.1f} KB)")
    return str(zip_path)


def _ssh(ip, cmd, timeout=300):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
         "-i", KEY_FILE, f"{SSH_USER}@{ip}", cmd],
        capture_output=True, text=True, timeout=timeout,
    )
    return r


def _scp(ip, local, remote):
    r = subprocess.run(
        ["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY_FILE,
         local, f"{SSH_USER}@{ip}:{remote}"],
        capture_output=True, text=True, timeout=300,
    )
    return r.returncode == 0


def deploy_igento(ip, zip_path):
    """Upload, extract, install deps, create service."""
    info("Uploading igento package …")
    if not _scp(ip, zip_path, "/tmp/igento_deploy.zip"):
        fail("SCP failed")
        sys.exit(1)
    ok("Upload complete")

    info("Extracting to /opt/apps …")
    _ssh(ip, "cd /opt/apps && unzip -o /tmp/igento_deploy.zip")
    _ssh(ip, "sudo chown -R ubuntu:ubuntu /opt/apps/igento")
    ok("Extracted")

    info("Installing MCP in venv …")
    r = _ssh(ip, "/opt/apps/venv/bin/pip install -r /opt/apps/igento/requirements.txt", timeout=120)
    if r.returncode != 0:
        warn("pip install had issues")
        if r.stderr:
            print(r.stderr[:500])
    else:
        ok("MCP installed")


def configure_igento_service(ip):
    """Create igento systemd service and update ngrok config."""
    VENV_PY = "/opt/apps/venv/bin/python"

    # Igento systemd service
    igento_unit = f"""[Unit]
Description=Igento MCP Server (HTTP)
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/apps/igento
ExecStart={VENV_PY} /opt/apps/igento/igento_server.py --transport streamable-http
Restart=always
RestartSec=5
Environment=HOME=/home/ubuntu

[Install]
WantedBy=multi-user.target
"""
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".service", delete=False)
    tmp.write(igento_unit)
    tmp.close()
    _scp(ip, tmp.name, "/tmp/igento.service")
    os.unlink(tmp.name)
    _ssh(ip, "sudo cp /tmp/igento.service /etc/systemd/system/igento.service")
    ok("igento.service created")

    # Full ngrok config (saelar, sopra, igento) - all three tunnels
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
  igento:
    addr: {IGENTO_PORT}
    proto: http
    domain: igento.ngrok.dev
    # Reserved domain endpoint ID: {NGROK_ENDPOINT_ID}
"""
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False)
    tmp.write(ngrok_yml)
    tmp.close()
    _scp(ip, tmp.name, "/tmp/ngrok.yml")
    os.unlink(tmp.name)
    _ssh(ip, "cp /tmp/ngrok.yml /home/ubuntu/.config/ngrok/ngrok.yml")
    ok("ngrok.yml updated with igento tunnel")

    # Start igento, restart ngrok
    info("Starting Igento service …")
    _ssh(ip, "sudo systemctl daemon-reload")
    _ssh(ip, "sudo systemctl enable igento")
    _ssh(ip, "sudo systemctl start igento")
    ok("Igento started")
    time.sleep(3)

    info("Restarting ngrok tunnels …")
    _ssh(ip, "sudo systemctl restart ngrok-tunnels")
    ok("ngrok restarted")
    time.sleep(5)


def verify(ip):
    for svc in ["igento", "ngrok-tunnels"]:
        r = _ssh(ip, f"sudo systemctl is-active {svc}", timeout=10)
        status = (r.stdout or "").strip()
        if status == "active":
            ok(f"{svc}: {status}")
        else:
            warn(f"{svc}: {status}")
            r2 = _ssh(ip, f"sudo journalctl -u {svc} --no-pager -n 8", timeout=10)
            if r2.stdout:
                print(f"      {r2.stdout[:400]}")


def main():
    print("\n" + "=" * 64)
    print("  IGENTO -> AWS EC2 Deployment")
    print("  https://igento.ngrok.dev")
    print("=" * 64 + "\n")

    if not os.path.exists(KEY_FILE):
        fail(f"PEM key not found: {KEY_FILE}")
        sys.exit(1)

    ip = get_instance_ip()
    if not ip:
        fail(f"No running instance found with tag Name={INSTANCE_NAME}")
        sys.exit(1)
    ok(f"Instance IP: {ip}")

    add_igento_port_to_sg()
    zip_path = build_igento_zip()
    deploy_igento(ip, zip_path)
    configure_igento_service(ip)
    verify(ip)

    print("\n" + "=" * 64)
    print("  IGENTO deployed!")
    print("  URL: https://igento.ngrok.dev")
    print("  MCP endpoint: https://igento.ngrok.dev/mcp")
    print("=" * 64 + "\n")


if __name__ == "__main__":
    main()
