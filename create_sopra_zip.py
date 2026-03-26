#!/usr/bin/env python3
"""
Create SOPRA deployment zip for EC2 sandbox.
Usage: python create_sopra_zip.py
Output: SOPRA_Sandbox_YYYYMMDD.zip
"""

import zipfile
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent

SOPRA_ROOT_FILES = [
    "sopra_setup.py",
    "sopra_controls.py",
    "risk_score_app.py",
    "risk_score_calculator.py",
    "cisa_kev_checker.py",
    "ssp_generator.py",
    "wordy.py",
    "requirements.txt",
]

SOPRA_DIRS = [
    "sopra",
    "assets",
    "demo_csv_data",
    "templates",
    ".streamlit",
]

# Optional - include if present
OPTIONAL_FILES = ["kev_catalog_cache.json"]


def main():
    date_str = datetime.now().strftime("%Y%m%d")
    zip_name = f"SOPRA_Sandbox_{date_str}.zip"
    zip_path = ROOT / zip_name

    count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in SOPRA_ROOT_FILES + OPTIONAL_FILES:
            fpath = ROOT / fname
            if fpath.exists():
                zf.write(fpath, fname)
                count += 1

        for dname in SOPRA_DIRS:
            dpath = ROOT / dname
            if not dpath.exists():
                continue
            for fpath in dpath.rglob("*"):
                if fpath.is_dir():
                    continue
                if "__pycache__" in str(fpath):
                    continue
                if fpath.suffix == ".pyc":
                    continue
                arcname = str(fpath.relative_to(ROOT)).replace("\\", "/")
                zf.write(fpath, arcname)
                count += 1

        # Add install script
        install_path = ROOT / "install_sopra_ec2.sh"
        if install_path.exists():
            zf.write(install_path, "install_sopra_ec2.sh")
            count += 1

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"Created {zip_name} ({count} files, {size_mb:.1f} MB)")
    return zip_path


if __name__ == "__main__":
    main()
