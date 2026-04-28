#!/usr/bin/env python3
"""
Migrate from grc_tools to GRCP
================================
Renames directories, services, and deploy agent from the old
old service naming to the unified GRCP naming.

Run on EC2: sudo python3 migrate_to_grcp.py
"""

import os
import sys
import subprocess
import shutil
import time

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"

OLD_HOME = "/home/ec2-user/grc_tools"
NEW_HOME = "/home/ec2-user/grcp"
S3_BUCKET = "saelarallpurpose"
REGION = "us-east-1"


def run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.returncode


def log(msg):
    print(f"{BLUE}[migrate]{NC} {msg}")


def ok(msg):
    print(f"{GREEN}  ✓{NC} {msg}")


def warn(msg):
    print(f"{YELLOW}  !{NC} {msg}")


def fail(msg):
    print(f"{RED}  ✗{NC} {msg}")


def main():
    print(f"""
{BLUE}╔═══════════════════════════════════════════════════════════════╗
║   Migrate to GRCP — Rename Everything                          ║
╚═══════════════════════════════════════════════════════════════╝{NC}
""")

    if os.geteuid() != 0:
        fail("Must run as root: sudo python3 migrate_to_grcp.py")
        sys.exit(1)

    # Step 1: Stop all old services
    log("Step 1: Stopping old services...")
    for svc in ["saelar", "sopra", "beekeeper", "grc-deploy-agent", "grcp-saelar", "grcp-sopra", "grcp-beekeeper"]:
        run(f"systemctl stop {svc} 2>/dev/null")
    run("pkill -f 'streamlit run' 2>/dev/null")
    time.sleep(2)
    ok("All services stopped")

    # Step 2: Copy grc_tools to grcp
    log("Step 2: Copying grc_tools -> grcp...")
    if os.path.exists(OLD_HOME):
        if os.path.exists(NEW_HOME):
            backup = f"{NEW_HOME}.bak"
            if os.path.exists(backup):
                shutil.rmtree(backup, ignore_errors=True)
            shutil.move(NEW_HOME, backup)
            warn(f"Moved existing {NEW_HOME} to {backup}")

        shutil.copytree(OLD_HOME, NEW_HOME, symlinks=True, dirs_exist_ok=True)
        ok(f"Copied {OLD_HOME} -> {NEW_HOME}")
    elif os.path.exists(NEW_HOME):
        ok(f"{NEW_HOME} already exists")
    else:
        fail(f"Neither {OLD_HOME} nor {NEW_HOME} found")
        sys.exit(1)

    # Step 3: Find streamlit binaries
    log("Step 3: Locating streamlit binaries...")
    apps = {}
    for app_name in ["saelar", "sopra", "beekeeper"]:
        app_dir = os.path.join(NEW_HOME, app_name)
        if os.path.isdir(app_dir):
            # Check for streamlit in venv
            streamlit = os.path.join(app_dir, "venv", "bin", "streamlit")
            if not os.path.isfile(streamlit):
                # Check symlinked venv
                out, _ = run(f'find /home/ec2-user -path "*{app_name}*/venv/bin/streamlit" 2>/dev/null')
                if out:
                    venv_source = str(os.path.dirname(os.path.dirname(out.split("\n")[0])))
                    target_venv = os.path.join(app_dir, "venv")
                    if os.path.islink(target_venv):
                        os.unlink(target_venv)
                    elif os.path.isdir(target_venv):
                        shutil.rmtree(target_venv, ignore_errors=True)
                    os.symlink(venv_source, target_venv)
                    streamlit = os.path.join(target_venv, "bin", "streamlit")

            # Determine the entry point
            entry = None
            for candidate in ["nist_setup.py", "sopra_setup.py", "app.py", "main.py"]:
                if os.path.isfile(os.path.join(app_dir, candidate)):
                    entry = candidate
                    break

            if os.path.isfile(streamlit) and entry:
                apps[app_name] = {"dir": app_dir, "streamlit": streamlit, "entry": entry}
                ok(f"Found {app_name}: {entry} with {streamlit}")
            elif os.path.isfile(streamlit):
                warn(f"Found {app_name} streamlit but no entry point")
            else:
                warn(f"Found {app_name} directory but no streamlit")

    # Step 4: Port mapping
    port_map = {
        "saelar": 8484,
        "sopra": 4444,
        "beekeeper": 4445,
    }

    # Step 5: Create new systemd services
    log("Step 4: Creating GRCP systemd services...")
    for app_name, info in apps.items():
        port = port_map.get(app_name, 8080)
        service_name = f"grcp-{app_name}"
        service_content = f"""[Unit]
Description=GRCP - {app_name.upper()}
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory={info['dir']}
Environment=S3_BUCKET_NAME={S3_BUCKET}
ExecStart={info['streamlit']} run {info['entry']} --server.port {port} --server.address 0.0.0.0 --server.headless true --server.fileWatcherType none
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
        with open(f"/etc/systemd/system/{service_name}.service", "w") as f:
            f.write(service_content)
        ok(f"Created {service_name}.service (port {port})")

    # Step 6: Disable old services
    log("Step 5: Disabling old service names...")
    for old_svc in ["saelar", "sopra", "beekeeper", "grc-deploy-agent", "grc-deploy-agent"]:
        run(f"systemctl disable {old_svc} 2>/dev/null")
        old_file = f"/etc/systemd/system/{old_svc}.service"
        if os.path.isfile(old_file):
            os.rename(old_file, f"{old_file}.old")
            ok(f"Disabled and archived {old_svc}.service")

    # Step 7: Install new deploy agent
    log("Step 6: Setting up GRCP deploy agent...")
    agent_src = os.path.join(NEW_HOME, "saelar", "deploy", "s3_deploy_agent.sh")
    if not os.path.isfile(agent_src):
        # Pull from S3
        run(f'aws s3 cp s3://{S3_BUCKET}/deployments/fixes/s3_deploy_agent.sh /usr/local/bin/grcp-deploy-agent.sh --region {REGION}')
    else:
        shutil.copy2(agent_src, "/usr/local/bin/grcp-deploy-agent.sh")

    run("chmod +x /usr/local/bin/grcp-deploy-agent.sh")

    agent_service = f"""[Unit]
Description=GRCP - S3 Deploy Agent
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
Environment=S3_BUCKET_NAME={S3_BUCKET}
Environment=AWS_DEFAULT_REGION={REGION}
Environment=DEPLOY_POLL_INTERVAL=60
ExecStart=/bin/bash /usr/local/bin/grcp-deploy-agent.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
    with open("/etc/systemd/system/grcp-deploy-agent.service", "w") as f:
        f.write(agent_service)
    ok("Created grcp-deploy-agent.service")

    # Step 8: Fix permissions
    log("Step 7: Setting permissions...")
    run(f"chown -R ec2-user:ec2-user {NEW_HOME}")
    ok("Done")

    # Step 9: Reload and start everything
    log("Step 8: Starting GRCP services...")
    run("systemctl daemon-reload")

    for app_name in apps:
        svc = f"grcp-{app_name}"
        run(f"systemctl enable {svc}")
        run(f"systemctl start {svc}")
        time.sleep(3)
        out, _ = run(f"systemctl is-active {svc}")
        if out.strip() == "active":
            ok(f"{svc} is RUNNING")
        else:
            warn(f"{svc} status: {out.strip()}")

    run("systemctl enable grcp-deploy-agent")
    run("systemctl start grcp-deploy-agent")
    out, _ = run("systemctl is-active grcp-deploy-agent")
    if out.strip() == "active":
        ok("grcp-deploy-agent is RUNNING")
    else:
        warn(f"grcp-deploy-agent status: {out.strip()}")

    # Step 10: Create baseline zip
    log("Step 9: Creating GRCP baseline zip...")
    zip_path = "/tmp/grcp-latest.zip"
    run(f"cd {NEW_HOME} && zip -r {zip_path} . -x '*/venv/*' '*/__pycache__/*' '*.pyc' '.env*' '*.pem' '*.key'")
    _, rc = run(f"aws s3 cp {zip_path} s3://{S3_BUCKET}/deployments/grcp-latest.zip --region {REGION}")
    if rc == 0:
        ok(f"Baseline uploaded to s3://{S3_BUCKET}/deployments/grcp-latest.zip")
    else:
        warn("Could not upload baseline to S3")

    # Summary
    print(f"""
{GREEN}╔═══════════════════════════════════════════════════════════════╗
║               MIGRATION TO GRCP COMPLETE!                       ║
╚═══════════════════════════════════════════════════════════════╝{NC}

  Directory:  {NEW_HOME}/
""")

    for app_name, info in apps.items():
        port = port_map.get(app_name, 8080)
        print(f"    grcp-{app_name}  →  port {port}  ({info['entry']})")

    print(f"""
  Deploy agent: grcp-deploy-agent (polls s3://{S3_BUCKET}/deployments/grcp-latest.zip)

  Old services archived (not deleted):
    Old services archived (not deleted)

  New commands:
    sudo systemctl status grcp-saelar
    sudo systemctl status grcp-sopra
    sudo systemctl status grcp-deploy-agent
    sudo journalctl -u grcp-saelar -f
    sudo journalctl -u grcp-deploy-agent -f
""")


if __name__ == "__main__":
    main()
