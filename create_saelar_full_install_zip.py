#!/usr/bin/env python3
"""
Build saelar_full_install.zip — complete SAELAR tree + install_saelar.sh + start_saelar.sh.

On EC2 after transfer:
  unzip -o saelar_full_install.zip -d SAELAR
  cd SAELAR
  chmod +x install_saelar.sh start_saelar.sh
  ./install_saelar.sh
  ./start_saelar.sh

Usage: python create_saelar_full_install_zip.py
"""

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ZIP_NAME = "saelar_full_install.zip"

ROOT_FILES = [
    "nist_setup.py",
    "nist_dashboard.py",
    "nist_pages.py",
    "nist_auth.py",
    "nist_800_53_controls.py",
    "nist_800_53_rev5_full.py",
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
    "assets",
    ".streamlit",
    "templates",
    "demo_csv_data",
]

SCRIPT_FILES = [
    "install_saelar.sh",
    "start_saelar.sh",
]

README_BUNDLE = """# SAELAR full install bundle

## Quick start (Linux EC2)

```bash
unzip -o saelar_full_install.zip -d SAELAR
cd SAELAR
chmod +x install_saelar.sh start_saelar.sh
./install_saelar.sh
./start_saelar.sh
```

- Default URL: `http://<instance-ip>:8484`
- Change port: `export SAELAR_PORT=8080` then `./start_saelar.sh`
- Requires Python 3.8+ and outbound AWS API access; attach an IAM instance profile with Bedrock and assessment permissions.

## Contents

All SAELAR Python modules, `assets/`, `.streamlit/`, `templates/`, `demo_csv_data/` (when present), `requirements.txt`, and install/launch scripts.
"""


def _unix_bytes(path: Path) -> bytes:
    """Normalize to LF for shell scripts and consistency inside zip."""
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
