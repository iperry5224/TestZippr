#!/usr/bin/env python3
"""Disable Igento on EC2 until otherwise directed.

Stops and disables:
- igento.service (Igento app)
- ngrok-igento (Igento tunnel)
"""
import os
import subprocess
import sys

KEY_FILE = "saelar-sopra-key.pem"
SSH_USER = "ubuntu"
EC2_IP = "18.232.122.255"


def get_ip():
    try:
        import boto3
        ec2 = boto3.client("ec2", region_name="us-east-1")
        r = ec2.describe_instances(
            Filters=[
                {"Name": "tag:Name", "Values": ["SAELAR-SOPRA-Server"]},
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


def ssh(ip, cmd, timeout=30):
    return subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
         "-i", KEY_FILE, f"{SSH_USER}@{ip}", cmd],
        capture_output=True, text=True, timeout=timeout,
    )


def main():
    if not os.path.exists(KEY_FILE):
        print(f"Error: {KEY_FILE} not found")
        sys.exit(1)

    ip = get_ip()
    print(f"Disabling Igento on EC2 ({ip})...")

    r = ssh(ip, "sudo systemctl stop igento ngrok-igento 2>/dev/null; sudo systemctl disable igento ngrok-igento 2>/dev/null; echo 'Done'; sudo systemctl is-enabled igento ngrok-igento 2>/dev/null || true")
    print(r.stdout or r.stderr or "(no output)")
    print("\nIgento disabled. To re-enable: sudo systemctl enable igento ngrok-igento && sudo systemctl start igento ngrok-igento")


if __name__ == "__main__":
    main()
