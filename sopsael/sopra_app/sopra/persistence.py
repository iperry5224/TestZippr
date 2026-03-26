"""
SOPRA Persistence — File I/O helpers for assessment data, history, and ISSO toolkit.
"""
import os
import json
from datetime import datetime

# =============================================================================
# CROSS-TAB DATA SHARING — persist results to disk for pop-out remediation tab
# =============================================================================
_PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
_RESULTS_FILE = os.path.join(_PROJECT_ROOT, ".sopra_results.json")
_HISTORY_FILE = os.path.join(_PROJECT_ROOT, ".sopra_assessment_history.json")

def save_results_to_file(results):
    """Save assessment results to JSON so the pop-out remediation tab can read them."""
    try:
        with open(_RESULTS_FILE, 'w') as f:
            json.dump(results, f)
        # Also append to assessment history for ConMon trending
        _append_to_history(results)
    except Exception:
        pass

def load_results_from_file():
    """Load assessment results written by the main tab."""
    try:
        if os.path.exists(_RESULTS_FILE):
            with open(_RESULTS_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return None

def _append_to_history(results):
    """Append an assessment snapshot to the history log for continuous monitoring."""
    try:
        history = load_assessment_history()
        findings = results.get("findings", [])
        total = len(findings)
        passed = len([f for f in findings if f["status"] == "Passed"])
        failed = len([f for f in findings if f["status"] == "Failed"])
        sev = {}
        for f in findings:
            if f["status"] == "Failed":
                s = f.get("severity", "Unknown")
                sev[s] = sev.get(s, 0) + 1
        cat_scores = {}
        cats = {}
        for f in findings:
            c = f.get("category", "Unknown")
            if c not in cats:
                cats[c] = {"p": 0, "f": 0}
            if f["status"] == "Passed":
                cats[c]["p"] += 1
            elif f["status"] == "Failed":
                cats[c]["f"] += 1
        for c, v in cats.items():
            t = v["p"] + v["f"]
            cat_scores[c] = round((v["p"] / max(t, 1)) * 100, 1)
        snapshot = {
            "timestamp": results.get("timestamp", datetime.now().isoformat()),
            "source": results.get("source", "Unknown"),
            "total": total, "passed": passed, "failed": failed,
            "compliance_pct": round((passed / max(total, 1)) * 100, 1),
            "severity_counts": sev,
            "category_scores": cat_scores
        }
        # Deduplicate by timestamp (don't re-add same assessment)
        existing_ts = {h["timestamp"] for h in history}
        if snapshot["timestamp"] not in existing_ts:
            history.append(snapshot)
            with open(_HISTORY_FILE, 'w') as f:
                json.dump(history, f, indent=2)
    except Exception:
        pass

def load_assessment_history():
    """Load full assessment history for continuous monitoring."""
    try:
        if os.path.exists(_HISTORY_FILE):
            with open(_HISTORY_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return []

# =============================================================================
# ISSO TOOLKIT — Persistence helpers for all ISSO features
# =============================================================================
_DATA_DIR = os.path.join(_PROJECT_ROOT, ".sopra_data")
os.makedirs(_DATA_DIR, exist_ok=True)

def _load_json(filename, default=None):
    fp = os.path.join(_DATA_DIR, filename)
    try:
        if os.path.exists(fp):
            with open(fp, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return default if default is not None else []

def _save_json(filename, data):
    fp = os.path.join(_DATA_DIR, filename)
    try:
        with open(fp, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def _next_id(items, prefix="ITEM"):
    nums = []
    for it in items:
        try:
            nums.append(int(it["id"].split("-")[-1]))
        except Exception:
            pass
    return f"{prefix}-{max(nums, default=0) + 1:04d}"

