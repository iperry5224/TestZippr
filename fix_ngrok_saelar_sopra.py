#!/usr/bin/env python3
"""
Re-enable ngrok tunnels for SAELAR and SOPRA on EC2.

Creates ngrok-saelar-sopra service (saelar + sopra only) so it can run
alongside ngrok-igento without domain conflicts.

Usage: python fix_ngrok_saelar_sopra.py
"""
import os
import subprocess
import sys
import tempfile
import time

KEY_FILE = "saelar-sopra-key.pem"
INSTANCE_NAME = "SAELAR-SOPRA-Server"
SSH_USER = "ubuntu"
NGROK_TOKEN = "36tYWSq8csrb0yWQVpMLCjAbnTL_32tNgrk27z4aWQecyM2KP"
SAELAR_PORT = 8484
SOPRA_PORT = 8080
EC2_IP = "18.232.122.255"  # Fallback if boto3 unavailable


def get_ip():
    try:
        import boto3
        ec2 = boto3.client("ec2", region_name="us-east-1")
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
    except Exception:
        pass
    return EC2_IP


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


def main():
    print("\n=== Re-enable ngrok for SAELAR & SOPRA ===\n")

    if not os.path.exists(KEY_FILE):
        print(f"Error: {KEY_FILE} not found")
        sys.exit(1)

    ip = get_ip()
    print(f"EC2 IP: {ip}\n")

    # Step 1: Diagnose
    print("1. Diagnosing current state...")
    r = ssh(ip, "pgrep -a ngrok || echo '(no ngrok)'; echo '---'; sudo systemctl is-active saelar sopra ngrok-tunnels ngrok-igento 2>/dev/null || true; echo '---'; ss -tlnp 2>/dev/null | grep -E '8484|8080' || echo '(ports not listening)'")
    print(r.stdout or r.stderr or "(empty)")
    print()

    # Step 2: Ensure SAELAR and SOPRA are running
    print("2. Ensuring SAELAR and SOPRA are running...")
    ssh(ip, "sudo systemctl start saelar sopra 2>/dev/null; sleep 2; sudo systemctl is-active saelar sopra")
    print("   saelar & sopra started (if they exist)\n")

    # Step 3: Create ngrok-saelar-sopra config (saelar + sopra only)
    print("3. Creating ngrok-saelar-sopra config...")
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
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(ngrok_yml)
        yml_path = f.name
    scp(ip, yml_path, "/tmp/ngrok-saelar-sopra.yml")
    os.unlink(yml_path)
    ssh(ip, "mkdir -p /home/ubuntu/.config/ngrok && cp /tmp/ngrok-saelar-sopra.yml /home/ubuntu/.config/ngrok/ngrok-saelar-sopra.yml")
    print("   Config uploaded\n")

    # Step 4: Create systemd service
    print("4. Creating ngrok-saelar-sopra systemd service...")
    ngrok_path = "/usr/bin/ngrok"
    r = ssh(ip, "which ngrok 2>/dev/null || echo /usr/local/bin/ngrok")
    if r.stdout and "ngrok" in (r.stdout or ""):
        ngrok_path = (r.stdout or "").strip().split("\n")[0] or ngrok_path

    unit = f"""[Unit]
Description=ngrok tunnels for SAELAR and SOPRA
After=network.target saelar.service sopra.service

[Service]
Type=simple
User=ubuntu
ExecStart={ngrok_path} start saelar sopra --config /home/ubuntu/.config/ngrok/ngrok-saelar-sopra.yml
Restart=always
RestartSec=10
Environment=HOME=/home/ubuntu

[Install]
WantedBy=multi-user.target
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".service", delete=False) as f:
        f.write(unit)
        svc_path = f.name
    scp(ip, svc_path, "/tmp/ngrok-saelar-sopra.service")
    os.unlink(svc_path)
    ssh(ip, "sudo cp /tmp/ngrok-saelar-sopra.service /etc/systemd/system/ngrok-saelar-sopra.service")
    ssh(ip, "sudo systemctl daemon-reload")
    ssh(ip, "sudo systemctl enable ngrok-saelar-sopra")
    print("   Service installed\n")

    # Step 5: Stop ngrok-tunnels (conflicts), start ngrok-saelar-sopra, then restart ngrok-igento
    print("5. Starting ngrok-saelar-sopra...")
    ssh(ip, "sudo systemctl stop ngrok-tunnels 2>/dev/null; sudo systemctl stop ngrok-igento 2>/dev/null; sleep 2; true")
    ssh(ip, "sudo pkill -f ngrok 2>/dev/null; sleep 3; pgrep -a ngrok || echo 'All ngrok stopped'; true")
    ssh(ip, "sudo systemctl start ngrok-saelar-sopra")
    print("   Started\n")
    # ngrok-igento left stopped (Igento disabled until further notice)

    # Step 6: Wait and verify
    print("6. Waiting 12s for tunnels to register...")
    time.sleep(12)

    print("\n7. Verification:")
    r = ssh(ip, "sudo systemctl is-active ngrok-saelar-sopra")
    status = (r.stdout or "").strip()
    print(f"   ngrok-saelar-sopra: {status}")

    if status != "active":
        r2 = ssh(ip, "sudo journalctl -u ngrok-saelar-sopra --no-pager -n 25 2>&1")
        print("\n   Logs:")
        print(r2.stdout or r2.stderr or "?")

    print("\n=== Try these URLs ===")
    print("  https://sopra.ngrok.dev")
    print("  https://saelar.ngrok.dev")
    print("\nIf they fail: Stop any LOCAL ngrok using these domains (Task Manager -> ngrok.exe)")
    print("Reserved domains can only be used by one ngrok agent at a time.\n")


if __name__ == "__main__":
    main()
