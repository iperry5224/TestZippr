#!/usr/bin/env python3
"""Troubleshoot ngrok tunnels (saelar, sopra, igento) on EC2.

Root cause (Feb 2026): Separate ngrok processes were conflicting:
- A standalone `ngrok start igento` had igento.ngrok.dev claimed
- ngrok-tunnels (start --all) failed with ERR_NGROK_334 "already online"

Fix: Kill conflicting ngrok processes, then restart ngrok-tunnels.
"""
import os
import sys
from deploy_igento_to_aws import get_instance_ip, _ssh, KEY_FILE

def main():
    ip = get_instance_ip()
    if not ip:
        print("No EC2 instance found")
        sys.exit(1)
    print("EC2 IP:", ip)
    if not os.path.exists(KEY_FILE):
        print("Key file not found:", KEY_FILE)
        sys.exit(1)

    print("\n--- All ngrok processes ---")
    r = _ssh(ip, "pgrep -a ngrok || echo '(none)'", timeout=10)
    print(r.stdout or r.stderr or "(empty)")

    print("\n--- ngrok-tunnels service status ---")
    r = _ssh(ip, "sudo systemctl status ngrok-tunnels --no-pager", timeout=10)
    print(r.stdout or r.stderr or "(empty)")

    print("\n--- Ports 8484 (saelar), 8080 (sopra), 8000 (igento) ---")
    r = _ssh(ip, "ss -tlnp 2>/dev/null | grep -E '8484|8080|8000' || true", timeout=10)
    print(r.stdout or r.stderr or "(none listening)")

    print("\n--- Fix: Kill ALL ngrok, restart ngrok-tunnels ---")
    r = _ssh(ip, "sudo pkill -f ngrok; sleep 3; pgrep -a ngrok || echo 'All ngrok stopped'; sudo systemctl start ngrok-tunnels; sleep 8; sudo systemctl status ngrok-tunnels --no-pager", timeout=30)
    print(r.stdout or r.stderr or "(empty)")
    if r.returncode != 0 and r.stderr:
        print("[stderr]", r.stderr)

if __name__ == "__main__":
    main()
