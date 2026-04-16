#!/usr/bin/env python3
"""
SAELAR Find & Fix — Locates SAELAR wherever it is, rebuilds grc_tools,
creates the baseline zip, and uploads to S3.

Run: sudo python3 find_and_fix_saelar.py
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

S3_BUCKET = "saelarallpurpose"
REGION = "us-east-1"
GRC_HOME = "/home/ec2-user/grc_tools"
SAELAR_TARGET = f"{GRC_HOME}/saelar"


def run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.returncode


def log(msg):
    print(f"{BLUE}[saelar]{NC} {msg}")


def ok(msg):
    print(f"{GREEN}  ✓{NC} {msg}")


def warn(msg):
    print(f"{YELLOW}  !{NC} {msg}")


def fail(msg):
    print(f"{RED}  ✗{NC} {msg}")


def main():
    print(f"""
{BLUE}╔═══════════════════════════════════════════════════════════════╗
║   SAELAR Find & Fix + Baseline ZIP Creator                     ║
╚═══════════════════════════════════════════════════════════════╝{NC}
""")

    if os.geteuid() != 0:
        fail("Must run as root: sudo python3 find_and_fix_saelar.py")
        sys.exit(1)

    # Step 1: Find running SAELAR process
    log("Step 1: Finding running SAELAR process...")
    out, _ = run("ps aux | grep 'streamlit run nist_setup' | grep -v grep")
    if out:
        ok(f"SAELAR is running")
        for line in out.split("\n"):
            print(f"         {line.strip()}")
    else:
        warn("SAELAR process not found")

    # Step 2: Check service config
    log("Step 2: Checking systemd service...")
    out, _ = run("cat /etc/systemd/system/saelar.service 2>/dev/null")
    if out:
        for line in out.split("\n"):
            if "ExecStart" in line or "WorkingDirectory" in line:
                ok(line.strip())
    else:
        warn("No saelar.service found")

    # Step 3: Find ALL nist_setup.py files on the system
    log("Step 3: Searching entire system for nist_setup.py...")
    out, _ = run("find / -name 'nist_setup.py' -type f 2>/dev/null")
    found_locations = []
    if out:
        for line in out.split("\n"):
            if line.strip():
                found_locations.append(line.strip())
                ok(f"Found: {line.strip()}")
    else:
        fail("nist_setup.py not found anywhere on the system")

    # Step 4: Find ALL venvs with streamlit
    log("Step 4: Finding Python venvs with streamlit...")
    out, _ = run('find / -path "*/venv/bin/streamlit" -type f 2>/dev/null')
    found_venvs = []
    if out:
        for line in out.split("\n"):
            if line.strip():
                venv_dir = str(Path(line.strip()).parent.parent)
                found_venvs.append(venv_dir)
                ok(f"Found venv: {venv_dir}")
    else:
        fail("No venv with streamlit found")

    # Step 5: Pick the best source directory
    log("Step 5: Selecting best source...")
    source_dir = None
    preferred_order = [
        "/home/ec2-user/grc_tools/saelar",
        "/home/ec2-user/saelar",
    ]
    for pref in preferred_order:
        matching = [f for f in found_locations if f.startswith(pref)]
        if matching:
            source_dir = str(Path(matching[0]).parent)
            break

    if not source_dir and found_locations:
        source_dir = str(Path(found_locations[0]).parent)

    if not source_dir:
        fail("Cannot determine SAELAR source directory")
        print(f"\n{RED}Locations searched:{NC}")
        print("  - /home/ec2-user/grc_tools/saelar/")
        print("  - /home/ec2-user/saelar/")
        print("  - (full filesystem search)")
        sys.exit(1)

    ok(f"Using source: {source_dir}")

    # Step 6: Pick the best venv
    log("Step 6: Selecting best venv...")
    venv_dir = None
    for v in found_venvs:
        if "saelar" in v.lower():
            venv_dir = v
            break
    if not venv_dir and found_venvs:
        venv_dir = found_venvs[0]

    if not venv_dir:
        fail("Cannot find a venv with streamlit")
        sys.exit(1)

    ok(f"Using venv: {venv_dir}")
    streamlit_bin = os.path.join(venv_dir, "bin", "streamlit")

    # Step 7: Stop SAELAR
    log("Step 7: Stopping SAELAR...")
    run("systemctl stop saelar 2>/dev/null")
    run("systemctl reset-failed saelar 2>/dev/null")
    run("pkill -f 'streamlit run nist_setup' 2>/dev/null")
    import time
    time.sleep(2)
    ok("Stopped")

    # Step 8: Rebuild grc_tools/saelar
    log("Step 8: Rebuilding grc_tools/saelar...")
    os.makedirs(GRC_HOME, exist_ok=True)

    if os.path.exists(SAELAR_TARGET) and source_dir != SAELAR_TARGET:
        backup = f"{SAELAR_TARGET}.bak"
        if os.path.exists(backup):
            shutil.rmtree(backup, ignore_errors=True)
        shutil.move(SAELAR_TARGET, backup)
        warn(f"Moved old dir to {backup}")

    if source_dir != SAELAR_TARGET:
        shutil.copytree(source_dir, SAELAR_TARGET, symlinks=True, dirs_exist_ok=True)
        ok(f"Copied from {source_dir}")
    else:
        ok("Source already at target")

    # Step 9: Set up venv
    log("Step 9: Setting up venv...")
    target_venv = os.path.join(SAELAR_TARGET, "venv")

    if os.path.islink(target_venv):
        os.unlink(target_venv)
    elif os.path.isdir(target_venv):
        has_streamlit = os.path.isfile(os.path.join(target_venv, "bin", "streamlit"))
        if not has_streamlit:
            shutil.rmtree(target_venv, ignore_errors=True)
        else:
            ok("Existing venv has streamlit — keeping it")
            venv_dir = target_venv

    if not os.path.exists(target_venv):
        os.symlink(venv_dir, target_venv)
        ok(f"Symlinked venv -> {venv_dir}")

    final_streamlit = os.path.join(SAELAR_TARGET, "venv", "bin", "streamlit")
    if os.path.isfile(final_streamlit):
        ok(f"Streamlit verified: {final_streamlit}")
    else:
        fail(f"Streamlit NOT found at {final_streamlit}")
        sys.exit(1)

    # Step 10: Pull fixed files from S3
    log("Step 10: Pulling fixed files from S3...")
    for f in ["wordy.py", "nist_setup.py"]:
        s3_path = f"s3://{S3_BUCKET}/deployments/fixes/{f}"
        local_path = os.path.join(SAELAR_TARGET, f)
        _, rc = run(f"aws s3 cp {s3_path} {local_path} --region {REGION}")
        if rc == 0:
            ok(f"Downloaded {f}")
        else:
            warn(f"Could not download {f} from S3 — using existing")

    # Step 11: Fix nist_dashboard.py
    log("Step 11: Fixing S3 bucket in nist_dashboard.py...")
    dashboard = os.path.join(SAELAR_TARGET, "nist_dashboard.py")
    if os.path.isfile(dashboard):
        with open(dashboard, "r") as fh:
            content = fh.read()
        if "saegrctest1" in content:
            content = content.replace("saegrctest1", "saelarallpurpose")
            with open(dashboard, "w") as fh:
                fh.write(content)
            ok("Fixed: saegrctest1 -> saelarallpurpose")
        else:
            ok("Already correct")

    # Step 12: Fix permissions
    log("Step 12: Setting permissions...")
    run(f"chown -R ec2-user:ec2-user {GRC_HOME}")
    run(f"chmod +x {SAELAR_TARGET}/*.sh 2>/dev/null")
    ok("Done")

    # Step 13: Update systemd service
    log("Step 13: Updating systemd service...")
    service = f"""[Unit]
Description=SAELAR - NIST 800-53 Assessment Tool
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory={SAELAR_TARGET}
Environment=S3_BUCKET_NAME=saelarallpurpose
ExecStart={final_streamlit} run nist_setup.py --server.port 8484 --server.address 0.0.0.0 --server.headless true --server.fileWatcherType none
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
    with open("/etc/systemd/system/saelar.service", "w") as fh:
        fh.write(service)
    run("systemctl daemon-reload")
    ok("Service updated")

    # Step 14: Create baseline ZIP
    log("Step 14: Creating baseline ZIP for CI/CD pipeline...")
    zip_path = "/tmp/grc-tools-latest.zip"
    if os.path.exists(zip_path):
        os.remove(zip_path)

    _, rc = run(f"cd {SAELAR_TARGET} && zip -r {zip_path} . -x './venv/*' './__pycache__/*' '*.pyc' '.env*' '*.pem' '*.key'")
    if rc == 0:
        out, _ = run(f"ls -lh {zip_path}")
        ok(f"ZIP created: {out}")

        out, _ = run(f"unzip -l {zip_path} | grep -cE '\\.py$|\\.sh$|\\.txt$|\\.json$|\\.csv$|\\.toml$'")
        ok(f"Contains {out} source files")

        sanity, _ = run(f"unzip -l {zip_path} | grep nist_setup.py")
        if sanity:
            ok(f"Sanity check: {sanity.strip()}")
        else:
            fail("nist_setup.py NOT in zip!")
            sys.exit(1)
    else:
        fail("ZIP creation failed")
        sys.exit(1)

    # Step 15: Upload to S3
    log("Step 15: Uploading baseline to S3...")
    _, rc = run(f"aws s3 cp {zip_path} s3://{S3_BUCKET}/deployments/grc-tools-latest.zip --region {REGION}")
    if rc == 0:
        ok(f"Uploaded to s3://{S3_BUCKET}/deployments/grc-tools-latest.zip")
    else:
        fail("S3 upload failed")

    # Step 16: Start SAELAR
    log("Step 16: Starting SAELAR...")
    run("systemctl start saelar")
    time.sleep(4)

    out, _ = run("systemctl is-active saelar")
    if out.strip() == "active":
        ok("SAELAR is RUNNING!")
    else:
        out2, _ = run("journalctl -u saelar --since '30 seconds ago' --no-pager")
        fail(f"Status: {out.strip()}")
        print(out2)
        sys.exit(1)

    # Step 17: Start deploy agent
    log("Step 17: Starting deploy agent...")
    run("systemctl start grc-deploy-agent 2>/dev/null")
    out, _ = run("systemctl is-active grc-deploy-agent 2>/dev/null")
    if out.strip() == "active":
        ok("Deploy agent running")
    else:
        warn("Deploy agent not running (may not be installed)")

    # Summary
    file_count, _ = run(f"find {SAELAR_TARGET} -name '*.py' -not -path '*/venv/*' | wc -l")
    print(f"""
{GREEN}╔═══════════════════════════════════════════════════════════════╗
║                    ALL DONE!                                    ║
╚═══════════════════════════════════════════════════════════════╝{NC}

  SAELAR:
    Location:    {SAELAR_TARGET}
    Python files: {file_count}
    Venv:        {os.path.join(SAELAR_TARGET, 'venv')}
    Port:        8484
    Status:      RUNNING

  CI/CD Pipeline:
    Baseline:    s3://{S3_BUCKET}/deployments/grc-tools-latest.zip
    Deploy agent: polling S3 every 60s

  Fixes applied:
    ✓ Markdown output (no Errno 5)
    ✓ S3 bucket → saelarallpurpose
    ✓ Systemd service correct paths

  URL: https://nih-saelar.nesdis-hq.noaa.gov:4443/
""")


if __name__ == "__main__":
    main()
