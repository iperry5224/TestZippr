#!/usr/bin/env python3
"""
Deploy SOPSAEL (containerized SAELAR + SOPRA) to EC2
====================================================
One command to prepare, copy, build, and start.

Usage:
    python deploy_sopsael_to_ec2.py              # uses default (sopsael)
    python deploy_sopsael_to_ec2.py sandbox      # uses sandbox IP
    python deploy_sopsael_to_ec2.py 12.34.56.78  # direct IP

Prerequisites: EC2 running with Docker, key pair, security group (22, 8443, 5224)
"""
import os
import subprocess
import sys
from pathlib import Path

# === CONFIGURE YOUR TARGETS ===
KEY = "saelar-sopra-key.pem"
USER = "ubuntu"

TARGETS = {
    "sopsael": "44.223.74.174",   # main sopsael EC2
    "sandbox": "CHANGE_ME",       # <-- put your sandbox EC2 IP here
}

SAELAR_PORT = 8443
SOPRA_PORT = 5224


def fix_start_script():
    """Ensure start script has Unix line endings (avoids CRLF issues on EC2)."""
    p = Path("sopsael/deploy/start_containers_ec2.sh")
    if p.exists():
        text = p.read_text(encoding="utf-8")
        p.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")
        print("  [OK] Fixed line endings in start script")


def run(cmd, check=True):
    r = subprocess.run(cmd, shell=True)
    if check and r.returncode != 0:
        sys.exit(r.returncode)
    return r.returncode


def main():
    target = (sys.argv[1] if len(sys.argv) > 1 else "sopsael").strip().lower()
    ip = TARGETS.get(target, target)

    if ip == "CHANGE_ME":
        print(f"\n[!] Target '{target}' not configured. Edit deploy_sopsael_to_ec2.py and set the IP for '{target}'.\n")
        sys.exit(1)

    if not Path(KEY).exists():
        print(f"\n[!] Key file not found: {KEY}\nPlace it in the project root or edit KEY in this script.\n")
        sys.exit(1)

    print("\n" + "=" * 55)
    print("  Deploy SOPSAEL to EC2")
    print("=" * 55)
    print(f"\n  Target: {target} ({ip})")
    print()

    # 1. Prepare
    print("1. Preparing sopsael...")
    run(f'python sopsael/prepare_sopsael.py')
    fix_start_script()
    print()

    # 2. Copy
    print("2. Copying to EC2...")
    run(f'scp -i {KEY} -o StrictHostKeyChecking=no -r sopsael {USER}@{ip}:~/')
    print("  [OK] Uploaded\n")

    # 3. Build & Start (fix line endings on EC2 too, just in case)
    print("3. Building containers and starting...")
    cmd = (
        f'ssh -i {KEY} -o StrictHostKeyChecking=no {USER}@{ip} '
        '"cd sopsael && sed -i \\"s/\\\\r$//\\" deploy/start_containers_ec2.sh && '
        'sudo docker build -t sopsael-saelar ./saelar && '
        'sudo docker build -t sopsael-sopra ./sopra_app && '
        'sudo bash deploy/start_containers_ec2.sh"'
    )
    run(cmd)
    print()

    print("=" * 55)
    print("  [OK] Deploy complete")
    print("=" * 55)
    print(f"\n  SAELAR:  http://{ip}:{SAELAR_PORT}")
    print(f"  SOPRA:   http://{ip}:{SOPRA_PORT}")
    print(f"\n  SSH:     ssh -i {KEY} {USER}@{ip}\n")


if __name__ == "__main__":
    main()
