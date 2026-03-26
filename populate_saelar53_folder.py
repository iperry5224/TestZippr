#!/usr/bin/env python3
"""Copy SAELAR full-install set into SAELAR-53/ (same list as create_saelar_full_install_zip.py)."""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEST = ROOT / "SAELAR-53"

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
OPTIONAL_ROOT_FILES = ["kev_catalog_cache.json"]
DIRS = ["assets", ".streamlit", "templates", "demo_csv_data"]
SCRIPT_FILES = ["install_saelar.sh", "start_saelar.sh"]


def main():
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)

    missing = []
    for name in ROOT_FILES:
        src = ROOT / name
        if not src.is_file():
            missing.append(name)
            continue
        shutil.copy2(src, DEST / name)
    if missing:
        print("ERROR: missing:", missing)
        raise SystemExit(1)

    for name in OPTIONAL_ROOT_FILES:
        src = ROOT / name
        if src.is_file():
            shutil.copy2(src, DEST / name)

    for dname in DIRS:
        src = ROOT / dname
        if not src.exists():
            continue
        dst = DEST / dname
        dst.parent.mkdir(parents=True, exist_ok=True)

        def ignore(dirpath, names):
            return [
                n
                for n in names
                if n == "__pycache__" or n.endswith(".pyc")
            ]

        shutil.copytree(src, dst, ignore=ignore)

    for sname in SCRIPT_FILES:
        src = ROOT / sname
        if not src.is_file():
            print(f"ERROR: {sname} missing")
            raise SystemExit(1)
        text = src.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
        (DEST / sname).write_text(text, encoding="utf-8", newline="\n")
        try:
            import os
            os.chmod(DEST / sname, 0o755)
        except OSError:
            pass

    overview = """# SAELAR-53

SAELAR-53 application source (NIST 800-53 Rev 5 assessment Streamlit app).

## Entry point

- **Main app:** `nist_setup.py`

## Run (after venv + deps)

```bash
cd SAELAR-53
python -m venv venv
source venv/bin/activate   # or .\\venv\\Scripts\\activate on Windows
pip install -r requirements.txt
streamlit run nist_setup.py
```

## Linux EC2 one-shot

```bash
chmod +x install_saelar.sh start_saelar.sh
./install_saelar.sh
./start_saelar.sh
```

This folder is synced from the repo root using `populate_saelar53_folder.py` (same file list as `create_saelar_full_install_zip.py`).
"""
    (DEST / "README.md").write_text(overview, encoding="utf-8", newline="\n")
    print(f"Wrote {DEST}")


if __name__ == "__main__":
    main()
