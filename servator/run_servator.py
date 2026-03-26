#!/usr/bin/env python3
"""
Run Servator Command Center dashboard.

Usage:
    python run_servator.py
    # or
    streamlit run servator/app/dashboard.py --server.port 8501
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DASHBOARD = ROOT / "servator" / "app" / "dashboard.py"

if __name__ == "__main__":
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(DASHBOARD), "--server.port=8501"],
        cwd=str(ROOT),
    )
