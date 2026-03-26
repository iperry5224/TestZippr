#!/usr/bin/env python3
"""
Create SOPRA EC2 update zip - syncs local changes (including Verify All Evidence) to EC2.
Usage: python create_sopra_ec2_update.py
Output: sopra_ec2_update.zip
"""

import zipfile
from pathlib import Path

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

# Optional root files (included if present)
OPTIONAL_ROOT_FILES = [
    "kev_catalog_cache.json",
]

SOPRA_DIRS = [
    "sopra",
    "assets",
    "demo_csv_data",
    "templates",
    ".streamlit",
]

ZIP_NAME = "sopra_ec2_update.zip"


def main():
    zip_path = ROOT / ZIP_NAME
    count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in SOPRA_ROOT_FILES + OPTIONAL_ROOT_FILES:
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

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"Created {ZIP_NAME} ({count} files, {size_mb:.1f} MB)")
    return zip_path


if __name__ == "__main__":
    main()
