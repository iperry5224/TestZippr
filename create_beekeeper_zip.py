#!/usr/bin/env python3
"""Create BeeKeeper zip with all contents for deployment or backup."""
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent

FILES = [
    "container_xray_app.py",
    "container_xray/__init__.py",
    "container_xray/scanner.py",
    "container_xray/ai_engine.py",
    "container_xray/test_data.py",
    "container_xray/assets/beekeeper_logo.png",
    "beekeeper.service",
]

ZIP_NAME = "beekeeper.zip"


def main():
    zip_path = ROOT / ZIP_NAME
    config_src = ROOT / ".streamlit" / "beekeeper_config.toml"
    if not config_src.exists():
        config_src = ROOT / ".streamlit" / "config.toml"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in FILES:
            p = ROOT / f
            if p.exists():
                zf.write(p, f)
        if config_src.exists():
            zf.write(config_src, ".streamlit/config.toml")

    print(f"Created {ZIP_NAME} ({zip_path.stat().st_size / 1024:.1f} KB)")
    return zip_path


if __name__ == "__main__":
    main()
