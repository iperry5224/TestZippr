#!/usr/bin/env python3
"""
Verify SAELAR and SOPRA ngrok tunnels are up and running.
Run every 24h via Task Scheduler to ensure availability.
"""
import subprocess
import sys
from datetime import datetime

KEY_FILE = "c:\\Users\\iperr\\TestZippr\\saelar-sopra-key.pem"
SSH_USER = "ubuntu"
EC2_IP = "18.232.122.255"
URLS = [
    ("SOPRA", "https://sopra.ngrok.dev"),
    ("SAELAR", "https://saelar.ngrok.dev"),
]


def ssh(cmd, timeout=20):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
         "-i", KEY_FILE, f"{SSH_USER}@{EC2_IP}", cmd],
        capture_output=True, text=True, timeout=timeout,
    )
    return r


def check_http(url, timeout=25):
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "VerifyScript/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status in (200, 302)
    except Exception:
        return False


def main():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results = []

    # 1. Check ngrok API on EC2
    r = ssh("curl -s http://127.0.0.1:4040/api/tunnels 2>/dev/null")
    tunnels_ok = "saelar" in (r.stdout or "") and "sopra" in (r.stdout or "")

    # 2. Check services
    r = ssh("sudo systemctl is-active saelar sopra ngrok-saelar-sopra 2>/dev/null")
    svc_out = (r.stdout or "").strip().split("\n")
    saelar_ok = len(svc_out) > 0 and "active" in (svc_out[0] or "")
    sopra_ok = len(svc_out) > 1 and "active" in (svc_out[1] or "")
    ngrok_ok = len(svc_out) > 2 and "active" in (svc_out[2] or "")

    # 3. Check public URLs
    sopra_url_ok = check_http(URLS[0][1])
    saelar_url_ok = check_http(URLS[1][1])

    # Build report
    all_ok = tunnels_ok and saelar_ok and sopra_ok and ngrok_ok and sopra_url_ok and saelar_url_ok

    results.append(f"[{ts}] SAELAR/SOPRA Tunnel Verification")
    results.append(f"  ngrok tunnels: {'OK' if tunnels_ok else 'FAIL'}")
    results.append(f"  saelar service: {'OK' if saelar_ok else 'FAIL'}")
    results.append(f"  sopra service: {'OK' if sopra_ok else 'FAIL'}")
    results.append(f"  ngrok-saelar-sopra: {'OK' if ngrok_ok else 'FAIL'}")
    results.append(f"  https://sopra.ngrok.dev: {'OK' if sopra_url_ok else 'FAIL'}")
    results.append(f"  https://saelar.ngrok.dev: {'OK' if saelar_url_ok else 'FAIL'}")
    results.append(f"  Overall: {'UP' if all_ok else 'ISSUE DETECTED'}")

    report = "\n".join(results)
    print(report)

    # Log to file
    log_path = "c:\\Users\\iperr\\TestZippr\\ngrok_verify.log"
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(report + "\n\n")
    except Exception:
        pass

    # If ngrok down, restart it
    if not ngrok_ok or not tunnels_ok:
        results.append("  Attempting restart of ngrok-saelar-sopra...")
        r = ssh("sudo systemctl restart ngrok-saelar-sopra; sleep 12; sudo systemctl is-active ngrok-saelar-sopra")
        restarted = "active" in (r.stdout or "")
        results.append(f"  Restart: {'OK' if restarted else 'FAIL'}")
        print(results[-2])
        print(results[-1])
    elif not all_ok:
        # URLs failing but services OK - try full fix script
        results.append("  Running fix_ngrok_saelar_sopra.py...")
        try:
            r = subprocess.run(
                [sys.executable, "c:\\Users\\iperr\\TestZippr\\fix_ngrok_saelar_sopra.py"],
                capture_output=True, text=True, timeout=60, cwd="c:\\Users\\iperr\\TestZippr",
            )
            results.append(f"  Fix script: {'OK' if r.returncode == 0 else 'FAIL'}")
            print(results[-2])
            print(results[-1])
        except Exception as e:
            results.append(f"  Fix script error: {e}")
            print(results[-1])

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
