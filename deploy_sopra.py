#!/usr/bin/env python3
"""
SOPRA Deployment Script
========================
Deploys SOPRA to GRC_Titan alongside SAELAR.

Run on EC2: sudo python3 deploy_sopra.py
"""

import os
import sys
import subprocess
import time

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"

S3_BUCKET = "saelarallpurpose"
REGION = "us-east-1"
SOPRA_DIR = "/home/ec2-user/grc_tools/sopra"
SOPRA_PORT = 4444


def run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.returncode


def log(msg):
    print(f"{BLUE}[sopra]{NC} {msg}")


def ok(msg):
    print(f"{GREEN}  ✓{NC} {msg}")


def fail(msg):
    print(f"{RED}  ✗{NC} {msg}")


def warn(msg):
    print(f"{YELLOW}  !{NC} {msg}")


def main():
    print(f"""
{BLUE}╔═══════════════════════════════════════════════════════════════╗
║   SOPRA Deployment to GRC_Titan                                ║
╚═══════════════════════════════════════════════════════════════╝{NC}
""")

    if os.geteuid() != 0:
        fail("Must run as root: sudo python3 deploy_sopra.py")
        sys.exit(1)

    # Step 1: Download from S3
    log("Step 1: Downloading SOPRA from S3...")
    _, rc = run(f'aws s3 cp "s3://{S3_BUCKET}/sopra_full_install (1).zip" /tmp/sopra.zip --region {REGION}')
    if rc != 0:
        fail("Could not download from S3")
        sys.exit(1)
    ok("Downloaded sopra.zip")

    # Step 2: Create directory and extract
    log("Step 2: Extracting to /home/ec2-user/grc_tools/sopra...")
    os.makedirs(SOPRA_DIR, exist_ok=True)
    _, rc = run(f"unzip -o /tmp/sopra.zip -d {SOPRA_DIR}")
    if rc != 0:
        fail("Unzip failed")
        sys.exit(1)

    out, _ = run(f"ls {SOPRA_DIR}/sopra_setup.py 2>/dev/null")
    if out:
        ok(f"Extracted — sopra_setup.py found")
    else:
        fail("sopra_setup.py not found after extraction")
        sys.exit(1)

    # Step 3: Set up venv
    log("Step 3: Setting up Python virtual environment...")
    venv_path = os.path.join(SOPRA_DIR, "venv")

    if os.path.isfile(os.path.join(venv_path, "bin", "python3")):
        ok("Venv already exists")
    else:
        _, rc = run(f"python3 -m venv {venv_path}")
        if rc != 0:
            fail("Could not create venv")
            sys.exit(1)
        ok("Venv created")

    # Step 4: Install dependencies
    log("Step 4: Installing dependencies...")
    pip_bin = os.path.join(venv_path, "bin", "pip")
    req_file = os.path.join(SOPRA_DIR, "requirements.txt")

    if os.path.isfile(req_file):
        _, rc = run(f"{pip_bin} install -q -r {req_file}")
        if rc == 0:
            ok("Dependencies installed")
        else:
            warn("Some dependencies may have failed — continuing")
    else:
        warn("No requirements.txt found — installing streamlit manually")

    # Ensure streamlit is installed
    streamlit_bin = os.path.join(venv_path, "bin", "streamlit")
    if not os.path.isfile(streamlit_bin):
        run(f"{pip_bin} install streamlit")

    if os.path.isfile(streamlit_bin):
        ok(f"Streamlit verified: {streamlit_bin}")
    else:
        fail("Streamlit not found after install")
        sys.exit(1)

    # Step 5: Fix permissions
    log("Step 5: Setting permissions...")
    run("chown -R ec2-user:ec2-user /home/ec2-user/grc_tools/sopra")
    run(f"chmod +x {SOPRA_DIR}/*.sh 2>/dev/null")
    ok("Permissions set")

    # Step 6: Create systemd service
    log("Step 6: Creating systemd service...")
    service = f"""[Unit]
Description=SOPRA - On-Premise Risk Assessment Tool
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory={SOPRA_DIR}
Environment=S3_BUCKET_NAME={S3_BUCKET}
ExecStart={streamlit_bin} run sopra_setup.py --server.port {SOPRA_PORT} --server.address 0.0.0.0 --server.headless true --server.fileWatcherType none
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
    with open("/etc/systemd/system/sopra.service", "w") as f:
        f.write(service)
    run("systemctl daemon-reload")
    run("systemctl enable sopra")
    ok("Service created and enabled")

    # Step 7: Start SOPRA
    log("Step 7: Starting SOPRA...")
    run("systemctl start sopra")
    time.sleep(5)

    out, _ = run("systemctl is-active sopra")
    if out.strip() == "active":
        ok("SOPRA is RUNNING!")
    else:
        out2, _ = run("journalctl -u sopra --since '30 seconds ago' --no-pager")
        fail(f"Status: {out.strip()}")
        print(out2)
        sys.exit(1)

    # Step 8: Verify port
    log("Step 8: Verifying port...")
    time.sleep(3)
    out, _ = run(f"ss -tlnp | grep {SOPRA_PORT}")
    if out:
        ok(f"Listening on port {SOPRA_PORT}")
    else:
        warn(f"Port {SOPRA_PORT} not yet listening — may need a moment")

    # Cleanup
    run("rm -f /tmp/sopra.zip")

    # Summary
    print(f"""
{GREEN}╔═══════════════════════════════════════════════════════════════╗
║                SOPRA DEPLOYED SUCCESSFULLY!                     ║
╚═══════════════════════════════════════════════════════════════╝{NC}

  Location:     {SOPRA_DIR}
  Streamlit:    {streamlit_bin}
  Port:         {SOPRA_PORT}
  Service:      sopra.service (auto-start on boot)

  Commands:
    sudo systemctl status sopra       # check status
    sudo systemctl restart sopra      # restart
    sudo journalctl -u sopra -f       # live logs

  URL: https://nih-sopra.nesdis-hq.noaa.gov:4444/

  GRC_Titan now runs:
    /home/ec2-user/grc_tools/saelar/  → port 8484
    /home/ec2-user/grc_tools/sopra/   → port 4444
""")


if __name__ == "__main__":
    main()
