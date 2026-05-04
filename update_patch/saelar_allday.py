#!/usr/bin/env python3
"""
SAELAR All-Day Service Installer
=================================
Sets up SAELAR as a systemd service so it runs 24/7, survives reboots,
and auto-restarts on crashes.

Usage:
    sudo python3 saelar_allday.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
NC = "\033[0m"


def banner():
    print(f"""
{CYAN}╔═══════════════════════════════════════════════════════════════════════╗
║   SAELAR All-Day — Permanent Service Installer                        ║
║   Run once, stays running forever                                     ║
╚═══════════════════════════════════════════════════════════════════════╝{NC}
""")


def check_root():
    if os.geteuid() != 0:
        print(f"{RED}[ERROR]{NC} This script must be run as root.")
        print(f"        Run: {CYAN}sudo python3 saelar_allday.py{NC}")
        sys.exit(1)
    print(f"{GREEN}[✓]{NC} Running as root")


def find_saelar():
    candidates = [
        "/home/ec2-user/saelar",
        "/home/ubuntu/saelar",
        "/home/ssm-user/saelar",
        "/opt/saelar",
        "/home/ec2-user/SAELAR-53",
    ]
    for path in candidates:
        if os.path.isfile(os.path.join(path, "nist_setup.py")):
            return path

    print(f"{YELLOW}[!]{NC} Searching filesystem for SAELAR...")
    result = subprocess.run(
        ["find", "/", "-maxdepth", "5", "-name", "nist_setup.py",
         "-not", "-path", "*/update_patch/*",
         "-not", "-path", "*/saelar_deploy/*",
         "-not", "-path", "*/.backup_*"],
        capture_output=True, text=True, timeout=30
    )
    for line in result.stdout.strip().split("\n"):
        if line:
            return str(Path(line).parent)

    return None


def find_streamlit(saelar_dir):
    candidates = [
        os.path.join(saelar_dir, "venv", "bin", "streamlit"),
        os.path.join(saelar_dir, "security-venv", "bin", "streamlit"),
        os.path.join(saelar_dir, ".venv", "bin", "streamlit"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path

    result = subprocess.run(
        ["find", "/", "-path", "*/bin/streamlit", "-type", "f"],
        capture_output=True, text=True, timeout=15
    )
    for line in result.stdout.strip().split("\n"):
        if line:
            return line.strip()

    return shutil.which("streamlit")


def detect_user(saelar_dir):
    stat = os.stat(saelar_dir)
    import pwd
    try:
        return pwd.getpwuid(stat.st_uid).pw_name
    except KeyError:
        return "ec2-user"


def stop_existing():
    print(f"{BLUE}[1/5]{NC} Stopping any running SAELAR instances...")
    subprocess.run(["systemctl", "stop", "saelar"], capture_output=True)
    subprocess.run(["pkill", "-f", "streamlit run nist_setup"], capture_output=True)
    import time
    time.sleep(2)
    print(f"{GREEN}[✓]{NC} Cleared")


def create_service(saelar_dir, streamlit_bin, run_user, s3_bucket):
    print(f"{BLUE}[2/5]{NC} Creating systemd service...")

    service_content = f"""[Unit]
Description=SAELAR - NIST 800-53 Assessment Tool
After=network.target
StartLimitIntervalSec=300
StartLimitBurst=5

[Service]
Type=simple
User={run_user}
WorkingDirectory={saelar_dir}
Environment=S3_BUCKET_NAME={s3_bucket}
Environment=SAELAR_OUTPUT_DIR=/tmp/saelar_docs
ExecStart={streamlit_bin} run nist_setup.py --server.port 8484 --server.address 0.0.0.0 --server.headless true --server.fileWatcherType none
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""

    service_path = "/etc/systemd/system/saelar.service"
    with open(service_path, "w") as f:
        f.write(service_content)

    print(f"{GREEN}[✓]{NC} Service file created at {service_path}")


def enable_service():
    print(f"{BLUE}[3/5]{NC} Enabling service to start on boot...")
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "enable", "saelar"], check=True)
    print(f"{GREEN}[✓]{NC} Service enabled")


def start_service():
    print(f"{BLUE}[4/5]{NC} Starting SAELAR...")
    subprocess.run(["systemctl", "start", "saelar"], check=True)
    import time
    time.sleep(3)

    result = subprocess.run(
        ["systemctl", "is-active", "saelar"],
        capture_output=True, text=True
    )
    status = result.stdout.strip()
    if status == "active":
        print(f"{GREEN}[✓]{NC} SAELAR is running!")
    else:
        print(f"{RED}[!]{NC} Service status: {status}")
        print(f"    Check logs with: {CYAN}journalctl -u saelar -n 50{NC}")


def print_summary(saelar_dir, streamlit_bin, run_user, s3_bucket):
    print(f"""
{GREEN}╔═══════════════════════════════════════════════════════════════════════╗
║                    ALL-DAY SETUP COMPLETE!                              ║
╚═══════════════════════════════════════════════════════════════════════╝{NC}

  {CYAN}Configuration:{NC}
    SAELAR directory:  {saelar_dir}
    Streamlit binary:  {streamlit_bin}
    Running as user:   {run_user}
    S3 bucket:         {s3_bucket}
    Port:              8484
    Generated docs:    /tmp/saelar_docs/

  {CYAN}What happens now:{NC}
    ✓ SAELAR is running right now
    ✓ Starts automatically on every reboot
    ✓ Auto-restarts within 5 seconds if it crashes
    ✓ You never need to SSH in to restart it

  {CYAN}Useful commands:{NC}
    sudo systemctl status saelar       # check status
    sudo systemctl restart saelar      # restart
    sudo systemctl stop saelar         # stop
    sudo journalctl -u saelar -f       # live logs
    sudo journalctl -u saelar -n 100   # last 100 log lines
""")


def main():
    banner()
    check_root()

    saelar_dir = find_saelar()
    if not saelar_dir:
        print(f"{RED}[ERROR]{NC} Could not find SAELAR installation (nist_setup.py).")
        sys.exit(1)
    print(f"{GREEN}[✓]{NC} Found SAELAR at: {saelar_dir}")

    streamlit_bin = find_streamlit(saelar_dir)
    if not streamlit_bin:
        print(f"{RED}[ERROR]{NC} Could not find streamlit binary.")
        print(f"        Is it installed? Try: pip3 install streamlit")
        sys.exit(1)
    print(f"{GREEN}[✓]{NC} Found streamlit at: {streamlit_bin}")

    run_user = detect_user(saelar_dir)
    print(f"{GREEN}[✓]{NC} Will run as user: {run_user}")

    s3_bucket = os.environ.get("S3_BUCKET_NAME", "saelarallpurpose")
    print(f"{GREEN}[✓]{NC} S3 bucket: {s3_bucket}")

    print()
    stop_existing()
    create_service(saelar_dir, streamlit_bin, run_user, s3_bucket)
    enable_service()
    start_service()

    print(f"\n{BLUE}[5/5]{NC} Verifying...")
    result = subprocess.run(
        ["systemctl", "is-active", "saelar"],
        capture_output=True, text=True
    )
    if result.stdout.strip() == "active":
        print(f"{GREEN}[✓]{NC} SAELAR is alive and will stay running!")
    else:
        print(f"{YELLOW}[!]{NC} Service may need attention. Check logs:")
        print(f"    sudo journalctl -u saelar -n 50")

    print_summary(saelar_dir, streamlit_bin, run_user, s3_bucket)


if __name__ == "__main__":
    main()
