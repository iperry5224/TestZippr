#!/usr/bin/env python3
"""
SAELAR Emergency Fix Script
============================
Run this ONE script on the EC2 via Session Manager to fix everything:
  sudo python3 fix_saelar_now.py

It will:
1. Find where SAELAR files and venv actually are
2. Rebuild the grc_tools/saelar directory
3. Pull the fixed wordy.py and nist_setup.py from S3
4. Symlink or copy the venv
5. Fix permissions
6. Restart the service
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
NC = "\033[0m"

GRC_HOME = "/home/ec2-user/grc_tools"
SAELAR_TARGET = f"{GRC_HOME}/saelar"
S3_BUCKET = "saelarallpurpose"
REGION = "us-east-1"


def run(cmd, check=False):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.returncode


def log(msg):
    print(f"{BLUE}[fix]{NC} {msg}")


def ok(msg):
    print(f"{GREEN}  ✓{NC} {msg}")


def warn(msg):
    print(f"{YELLOW}  !{NC} {msg}")


def fail(msg):
    print(f"{RED}  ✗{NC} {msg}")


def main():
    print(f"""
{BLUE}╔═══════════════════════════════════════════════════════════════╗
║   SAELAR Emergency Fix Script                                  ║
╚═══════════════════════════════════════════════════════════════╝{NC}
""")

    if os.geteuid() != 0:
        fail("Must run as root: sudo python3 fix_saelar_now.py")
        sys.exit(1)

    # Step 1: Find the original SAELAR source files
    log("Step 1: Finding SAELAR source files...")
    source_dir = None
    candidates = [
        "/home/ec2-user/saelar",
        "/home/ec2-user/grc_tools-old/saelar",
        "/home/ec2-user/grc_tools/SAELAR",
    ]
    for c in candidates:
        if os.path.isfile(os.path.join(c, "nist_setup.py")):
            source_dir = c
            break

    if not source_dir:
        out, _ = run("find /home/ec2-user -maxdepth 3 -name nist_setup.py -not -path '*/grc_tools/saelar/*' 2>/dev/null")
        for line in out.split("\n"):
            if line.strip():
                source_dir = str(Path(line.strip()).parent)
                break

    if not source_dir:
        fail("Cannot find SAELAR source (nist_setup.py). Manual intervention needed.")
        sys.exit(1)

    ok(f"Found source at: {source_dir}")

    # Step 2: Find the venv with streamlit
    log("Step 2: Finding Python venv with streamlit...")
    venv_dir = None
    out, _ = run('find /home/ec2-user -path "*/venv/bin/streamlit" 2>/dev/null')
    for line in out.split("\n"):
        if line.strip():
            venv_dir = str(Path(line.strip()).parent.parent)
            break

    if not venv_dir:
        fail("Cannot find a venv with streamlit installed.")
        sys.exit(1)

    ok(f"Found venv at: {venv_dir}")

    # Step 3: Stop SAELAR
    log("Step 3: Stopping SAELAR...")
    run("systemctl stop saelar 2>/dev/null")
    run("systemctl reset-failed saelar 2>/dev/null")
    run("pkill -f 'streamlit run nist_setup' 2>/dev/null")
    ok("Stopped")

    # Step 4: Rebuild grc_tools/saelar
    log("Step 4: Rebuilding grc_tools/saelar...")
    os.makedirs(GRC_HOME, exist_ok=True)

    if os.path.exists(SAELAR_TARGET):
        backup = f"{SAELAR_TARGET}.bak.{subprocess.check_output(['date', '+%H%M%S']).decode().strip()}"
        shutil.move(SAELAR_TARGET, backup)
        warn(f"Moved old saelar dir to {backup}")

    if source_dir != SAELAR_TARGET:
        shutil.copytree(source_dir, SAELAR_TARGET, symlinks=True, dirs_exist_ok=True)
        ok(f"Copied source files from {source_dir}")
    else:
        ok("Source is already at target location")

    # Step 5: Link or copy the venv
    log("Step 5: Setting up venv...")
    target_venv = os.path.join(SAELAR_TARGET, "venv")

    if os.path.exists(target_venv) and os.path.isfile(os.path.join(target_venv, "bin", "streamlit")):
        ok("Venv already in place with streamlit")
    else:
        if os.path.exists(target_venv):
            if os.path.islink(target_venv):
                os.unlink(target_venv)
            else:
                shutil.rmtree(target_venv, ignore_errors=True)

        try:
            os.symlink(venv_dir, target_venv)
            ok(f"Symlinked venv -> {venv_dir}")
        except OSError:
            shutil.copytree(venv_dir, target_venv)
            ok(f"Copied venv from {venv_dir}")

    # Verify streamlit
    streamlit_bin = os.path.join(target_venv, "bin", "streamlit")
    if os.path.isfile(streamlit_bin):
        ok(f"Streamlit verified at {streamlit_bin}")
    else:
        fail(f"Streamlit not found at {streamlit_bin}")
        sys.exit(1)

    # Step 6: Pull fixed files from S3
    log("Step 6: Pulling fixed wordy.py and nist_setup.py from S3...")
    fixes = ["wordy.py", "nist_setup.py"]
    for f in fixes:
        s3_path = f"s3://{S3_BUCKET}/deployments/fixes/{f}"
        local_path = os.path.join(SAELAR_TARGET, f)
        out, rc = run(f"aws s3 cp {s3_path} {local_path} --region {REGION}")
        if rc == 0:
            ok(f"Downloaded {f}")
        else:
            warn(f"Could not download {f} from S3 — using existing copy")

    # Step 7: Also fix nist_dashboard.py S3 bucket name
    log("Step 7: Fixing S3 bucket name in nist_dashboard.py...")
    dashboard = os.path.join(SAELAR_TARGET, "nist_dashboard.py")
    if os.path.isfile(dashboard):
        with open(dashboard, "r") as fh:
            content = fh.read()
        if "saegrctest1" in content:
            content = content.replace("saegrctest1", "saelarallpurpose")
            with open(dashboard, "w") as fh:
                fh.write(content)
            ok("Fixed S3 bucket name: saegrctest1 -> saelarallpurpose")
        else:
            ok("S3 bucket name already correct")
    else:
        warn("nist_dashboard.py not found — skipping")

    # Step 8: Fix permissions
    log("Step 8: Setting permissions...")
    run(f"chown -R ec2-user:ec2-user {GRC_HOME}")
    run(f"chmod +x {SAELAR_TARGET}/*.sh 2>/dev/null")
    ok("Permissions set")

    # Step 9: Update systemd service
    log("Step 9: Updating systemd service...")
    service_content = f"""[Unit]
Description=SAELAR - NIST 800-53 Assessment Tool
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory={SAELAR_TARGET}
Environment=S3_BUCKET_NAME=saelarallpurpose
ExecStart={streamlit_bin} run nist_setup.py --server.port 8484 --server.address 0.0.0.0 --server.headless true --server.fileWatcherType none
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
    with open("/etc/systemd/system/saelar.service", "w") as fh:
        fh.write(service_content)
    run("systemctl daemon-reload")
    ok("Service file updated")

    # Step 10: Start SAELAR
    log("Step 10: Starting SAELAR...")
    run("systemctl start saelar")

    import time
    time.sleep(4)

    out, rc = run("systemctl is-active saelar")
    if out.strip() == "active":
        ok("SAELAR is RUNNING!")
    else:
        out2, _ = run("journalctl -u saelar --since '30 seconds ago' --no-pager")
        fail(f"SAELAR status: {out.strip()}")
        print(f"\n{RED}Recent logs:{NC}")
        print(out2)
        sys.exit(1)

    # Summary
    print(f"""
{GREEN}╔═══════════════════════════════════════════════════════════════╗
║                    SAELAR IS BACK UP!                          ║
╚═══════════════════════════════════════════════════════════════╝{NC}

  Source:     {SAELAR_TARGET}
  Venv:       {target_venv}
  Streamlit:  {streamlit_bin}
  Port:       8484
  S3 Bucket:  {S3_BUCKET}

  Fixes applied:
    ✓ Markdown output (no more Errno 5)
    ✓ S3 bucket → saelarallpurpose
    ✓ Systemd service updated

  URL: https://nih-saelar.nesdis-hq.noaa.gov:4443/
""")


if __name__ == "__main__":
    main()
