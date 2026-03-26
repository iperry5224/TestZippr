#!/usr/bin/env python3
"""
Prepare SOPSAEL - Copy SAELAR and SOPRA into container-ready directories.
Run from TestZippr root: python sopsael/prepare_sopsael.py
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOPSAEL = Path(__file__).resolve().parent

SAELAR_FILES = [
    "nist_setup.py",
    "nist_dashboard.py",
    "nist_pages.py",
    "nist_auth.py",
    "nist_800_53_rev5_full.py",
    "nist_800_53_controls.py",
    "risk_score_app.py",
    "risk_score_calculator.py",
    "requirements.txt",
    "entrypoint.sh",
]

SAELAR_DIRS = ["assets", "ssl_certs"]

SOPRA_FILES = [
    "sopra_setup.py",
    "sopra_controls.py",
    "risk_score_app.py",
    "risk_score_calculator.py",
    "cisa_kev_checker.py",
    "ssp_generator.py",
    "wordy.py",
    "requirements.txt",
]

SOPRA_DIRS = ["sopra", "assets", "demo_csv_data", "templates", ".streamlit"]


def copy_file(src: Path, dst: Path):
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return True
    return False


def copy_dir(src: Path, dst: Path, exclude: set = None):
    exclude = exclude or {"__pycache__", ".pyc", ".git"}
    if not src.exists():
        return 0
    count = 0
    for f in src.rglob("*"):
        if f.is_dir():
            continue
        if any(x in str(f) for x in exclude):
            continue
        rel = f.relative_to(src)
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)
        count += 1
    return count


def main():
    saelar_dst = SOPSAEL / "saelar"
    sopra_dst = SOPSAEL / "sopra_app"
    saelar_dst.mkdir(exist_ok=True)
    sopra_dst.mkdir(exist_ok=True)

    print("Copying SAELAR...")
    for f in SAELAR_FILES:
        if copy_file(ROOT / f, saelar_dst / f):
            print(f"  + {f}")
    for d in SAELAR_DIRS:
        n = copy_dir(ROOT / d, saelar_dst / d)
        if n:
            print(f"  + {d}/ ({n} files)")

    print("\nCopying SOPRA...")
    for f in SOPRA_FILES:
        if copy_file(ROOT / f, sopra_dst / f):
            print(f"  + {f}")
    for d in SOPRA_DIRS:
        n = copy_dir(ROOT / d, sopra_dst / d)
        if n:
            print(f"  + {d}/ ({n} files)")

    # Ensure kev cache if exists
    kev = ROOT / "kev_catalog_cache.json"
    if kev.exists():
        shutil.copy2(kev, sopra_dst / "kev_catalog_cache.json")
        print("  + kev_catalog_cache.json")

    print("\nDone. Run: cd sopsael && docker compose up -d")


if __name__ == "__main__":
    main()
