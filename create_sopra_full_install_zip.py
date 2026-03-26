#!/usr/bin/env python3
"""
Build sopra_full_install.zip — complete SOPRA tree + install_sopra.sh + start_sopra.sh.

On EC2 after transfer:
  unzip -o sopra_full_install.zip -d SOPRA
  cd SOPRA
  chmod +x install_sopra.sh start_sopra.sh
  ./install_sopra.sh
  ./start_sopra.sh

Usage: python create_sopra_full_install_zip.py
"""

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ZIP_NAME = "sopra_full_install.zip"

ROOT_FILES = [
    "sopra_setup.py",
    "sopra_controls.py",
    "risk_score_app.py",
    "risk_score_calculator.py",
    "cisa_kev_checker.py",
    "ssp_generator.py",
    "wordy.py",
    "requirements.txt",
]

OPTIONAL_ROOT_FILES = [
    "kev_catalog_cache.json",
]

DIRS = [
    "sopra",
    "assets",
    "demo_csv_data",
    "templates",
    ".streamlit",
]

SCRIPT_FILES = [
    "install_sopra.sh",
    "start_sopra.sh",
]

README_BUNDLE = """# SOPRA full install bundle

## Quick start (Linux EC2)

```bash
unzip -o sopra_full_install.zip -d SOPRA
cd SOPRA
chmod +x install_sopra.sh start_sopra.sh
./install_sopra.sh
./start_sopra.sh
```

- Default URL: `http://<instance-ip>:8080`
- Change port: `export SOPRA_PORT=8180` then `./start_sopra.sh`
- Requires Python 3.8+; AI features need AWS Bedrock access (IAM instance profile or credentials).

## Contents

`sopra_setup.py`, `sopra_controls.py`, shared modules (`risk_score_*`, `cisa_kev_checker`, `ssp_generator`, `wordy`), `sopra/` package, `assets/`, `.streamlit/`, `templates/`, `demo_csv_data/`, `requirements.txt`, and install/launch scripts.
"""


def _unix_bytes(path: Path) -> bytes:
    text = path.read_text(encoding="utf-8", errors="replace")
    return text.replace("\r\n", "\n").encode("utf-8")


def main():
    zip_path = ROOT / ZIP_NAME
    count = 0
    missing_required: list[str] = []

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in ROOT_FILES:
            p = ROOT / name
            if not p.is_file():
                missing_required.append(name)
                continue
            zf.write(p, name)
            count += 1

        if missing_required:
            print("ERROR: Missing required files:")
            for m in missing_required:
                print(f"  - {m}")
            raise SystemExit(1)

        for name in OPTIONAL_ROOT_FILES:
            p = ROOT / name
            if p.is_file():
                zf.write(p, name)
                count += 1

        for dname in DIRS:
            dpath = ROOT / dname
            if not dpath.exists():
                continue
            for fpath in dpath.rglob("*"):
                if fpath.is_dir():
                    continue
                if "__pycache__" in fpath.parts:
                    continue
                if fpath.suffix == ".pyc":
                    continue
                arc = str(fpath.relative_to(ROOT)).replace("\\", "/")
                zf.write(fpath, arc)
                count += 1

        for sname in SCRIPT_FILES:
            sp = ROOT / sname
            if not sp.is_file():
                print(f"ERROR: {sname} not found at repo root")
                raise SystemExit(1)
            zi = zipfile.ZipInfo(sname)
            zi.external_attr = 0o755 << 16
            zf.writestr(zi, _unix_bytes(sp))
            count += 1

        zf.writestr("README_BUNDLE.md", README_BUNDLE.replace("\r\n", "\n"))
        count += 1

    mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"Created {ZIP_NAME} ({count} entries, {mb:.1f} MB)")
    print(f"Path: {zip_path}")
    return zip_path


if __name__ == "__main__":
    main()
