#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix Igento ngrok tunnel - run igento-only to avoid conflict with saelar/sopra."""
import io
import os
import subprocess
import sys
import tempfile
import time
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import boto3

KEY_FILE = "saelar-sopra-key.pem"
INSTANCE_NAME = "SAELAR-SOPRA-Server"
SSH_USER = "ubuntu"
REGION = "us-east-1"
NGROK_TOKEN = "36tYWSq8csrb0yWQVpMLCjAbnTL_32tNgrk27z4aWQecyM2KP"
IGENTO_PORT = 8000

ec2 = boto3.client("ec2", region_name=REGION)

def ssh(ip, cmd, timeout=60):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
         "-i", KEY_FILE, f"{SSH_USER}@{ip}", cmd],
        capture_output=True, text=True, timeout=timeout,
    )
    return r

def scp(ip, local, remote):
    r = subprocess.run(
        ["scp", "-o", "StrictHostKeyChecking=no", "-i", KEY_FILE,
         local, f"{SSH_USER}@{ip}:{remote}"],
        capture_output=True, timeout=30,
    )
    return r.returncode == 0

def get_ip():
    r = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Name", "Values": [INSTANCE_NAME]},
            {"Name": "instance-state-name", "Values": ["running"]},
        ]
    )
    for res in r.get("Reservations", []):
        for inst in res.get("Instances", []):
            if inst.get("PublicIpAddress"):
                return inst["PublicIpAddress"]
    return None

def main():
    print("\n=== Igento ngrok fix (igento-only tunnel) ===\n")
    print("Note: saelar.ngrok.dev and sopra.ngrok.dev are already in use")
    print("      (likely your local ngrok). Starting igento tunnel only.\n")

    if not os.path.exists(KEY_FILE):
        print(f"Error: {KEY_FILE} not found")
        sys.exit(1)
    ip = get_ip()
    if not ip:
        print("Error: No running EC2 instance found")
        sys.exit(1)
    print(f"Instance: {ip}\n")

    # Igento-only ngrok config
    ngrok_yml = f"""version: "2"
authtoken: {NGROK_TOKEN}
tunnels:
  igento:
    addr: {IGENTO_PORT}
    proto: http
    domain: igento.ngrok.dev
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(ngrok_yml)
        yml_path = f.name

    # Upload config
    scp(ip, yml_path, "/tmp/ngrok-igento.yml")
    os.unlink(yml_path)
    ssh(ip, "mkdir -p /home/ubuntu/.config/ngrok")
    ssh(ip, "cp /tmp/ngrok-igento.yml /home/ubuntu/.config/ngrok/ngrok-igento.yml")

    # ngrok path (we know it's /usr/local/bin/ngrok from previous run)
    ngrok_path = "/usr/local/bin/ngrok"

    # systemd service - ONLY igento tunnel
    unit = f"""[Unit]
Description=ngrok tunnel for Igento (igento.ngrok.dev)
After=network.target igento.service

[Service]
Type=simple
User=ubuntu
ExecStart={ngrok_path} start igento --config /home/ubuntu/.config/ngrok/ngrok-igento.yml
Restart=always
RestartSec=10
Environment=HOME=/home/ubuntu

[Install]
WantedBy=multi-user.target
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".service", delete=False) as f:
        f.write(unit)
        svc_path = f.name
    scp(ip, svc_path, "/tmp/ngrok-igento.service")
    os.unlink(svc_path)

    print("1. Installing ngrok-igento service...")
    ssh(ip, "sudo cp /tmp/ngrok-igento.service /etc/systemd/system/ngrok-igento.service")
    ssh(ip, "sudo systemctl daemon-reload")
    ssh(ip, "sudo systemctl enable ngrok-igento")
    ssh(ip, "sudo systemctl stop ngrok-tunnels")  # stop the failing all-in-one
    ssh(ip, "sudo systemctl start ngrok-igento")
    print("   Started ngrok-igento (igento tunnel only)\n")

    print("2. Waiting 12s for tunnel to register...")
    time.sleep(12)

    print("3. Status:")
    r = ssh(ip, "sudo systemctl is-active ngrok-igento")
    print(f"   ngrok-igento: {(r.stdout or '').strip()}")
    r = ssh(ip, "sudo systemctl is-active igento")
    print(f"   igento app:   {(r.stdout or '').strip()}")

    if (r.stdout or "").strip() != "active":
        r2 = ssh(ip, "sudo journalctl -u ngrok-igento --no-pager -n 15 2>&1")
        print("\n   ngrok-igento logs:")
        print(r2.stdout or r2.stderr or "?")

    print("\n=== Try https://igento.ngrok.dev (and /mcp for MCP) ===\n")
    print("To restore saelar/sopra on EC2: stop your local ngrok first,")
    print("then run: sudo systemctl start ngrok-tunnels\n")

if __name__ == "__main__":
    main()
