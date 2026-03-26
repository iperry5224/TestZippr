#!/usr/bin/env python3
"""Create a zip with risk_score_app.py and risk_score_calculator.py for EC2 fix."""
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = [
    "risk_score_app.py",
    "risk_score_calculator.py",
    "start_saelar_fixed.sh",
]
ZIP_NAME = "saelar_risk_fix.zip"

def main():
    zip_path = ROOT / ZIP_NAME
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in FILES:
            p = ROOT / f
            if p.exists():
                arcname = "start_saelar.sh" if f == "start_saelar_fixed.sh" else f
                zf.write(p, arcname)
    print(f"Created {ZIP_NAME}")
    return zip_path

if __name__ == "__main__":
    main()
