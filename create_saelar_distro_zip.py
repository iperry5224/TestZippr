#!/usr/bin/env python3
"""
Create a full SAELAR distribution zip for installing on another cloud.
Extract and run: ./install_saelar_ec2.sh  (or pip install -r requirements.txt && streamlit run nist_setup.py)
"""
import zipfile
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
DEPLOY = ROOT / "saelar_deploy"

# All saelar_deploy files to include (relative to saelar_deploy)
DEPLOY_FILES = [
    "nist_setup.py",
    "nist_pages.py",
    "nist_dashboard.py",
    "nist_auth.py",
    "nist_800_53_rev5_full.py",
    "nist_800_53_controls.py",
    "requirements.txt",
    "README.md",
    "LINUX_INSTALL.md",
    "install.sh",
    "install_saelar",
    "install saelar",
    "install_saelar_ec2.sh",
    "saelar.sh",
    "saelar.bat",
    "saelar.ps1",
    "saelar-airgapped.bat",
    "saelar-airgapped.ps1",
    "generate_ssl_certs.sh",
]

# From repo root (same level as nist_setup when extracted)
ROOT_FILES = [
    "risk_score_app.py",
    "risk_score_calculator.py",
]

ZIP_PREFIX = "SAELAR-distro"
ZIP_EXT = ".zip"


def main():
    date_str = datetime.now().strftime("%Y%m%d")
    zip_name = f"{ZIP_PREFIX}-{date_str}{ZIP_EXT}"
    zip_path = ROOT / zip_name

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in DEPLOY_FILES:
            p = DEPLOY / f
            if p.exists():
                zf.write(p, f)
        for f in ROOT_FILES:
            p = ROOT / f
            if p.exists():
                zf.write(p, f)

    size_kb = zip_path.stat().st_size / 1024
    print(f"Created {zip_name} ({size_kb:.1f} KB)")
    print(f"Path: {zip_path}")
    print("Linux: unzip, then run ./install_saelar or \"./install saelar\"")
    return zip_path


if __name__ == "__main__":
    main()
