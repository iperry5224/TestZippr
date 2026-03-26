#!/usr/bin/env python3
"""Create SAELAR EC2 update zip - syncs local changes to EC2."""
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = [
    "nist_setup.py",
    "nist_dashboard.py",
    "nist_pages.py",
    "risk_score_app.py",
    "risk_score_calculator.py",
    "start_saelar_fixed.sh",
]
ZIP_NAME = "saelar_ec2_update.zip"

def main():
    zip_path = ROOT / ZIP_NAME
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in FILES:
            p = ROOT / f
            if p.exists():
                arcname = "start_saelar.sh" if f == "start_saelar_fixed.sh" else f
                zf.write(p, arcname)
    print(f"Created {ZIP_NAME} ({zip_path.stat().st_size / 1024:.1f} KB)")
    return zip_path

if __name__ == "__main__":
    main()
