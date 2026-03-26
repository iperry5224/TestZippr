"""
SOPRA Control Crosswalk Engine
================================
Provides bidirectional mapping between:
  - SOPRA findings ↔ NIST 800-53 Rev 5 controls
  - SOPRA findings ↔ CIS Controls v8 benchmarks

Features:
  1. Reverse index: NIST control → all SOPRA findings
  2. Reverse index: CIS benchmark → all SOPRA findings
  3. Assessment-aware crosswalk (includes pass/fail status from last run)
  4. Export to CSV for auditors
"""
import csv
import io
from collections import defaultdict
from datetime import datetime

from sopra_controls import ALL_CONTROLS


# =====================================================================
# 1. NIST 800-53 REVERSE INDEX
# =====================================================================

# NIST 800-53 family names for display
NIST_FAMILIES = {
    "AC": "Access Control",
    "AT": "Awareness and Training",
    "AU": "Audit and Accountability",
    "CA": "Assessment, Authorization, and Monitoring",
    "CM": "Configuration Management",
    "CP": "Contingency Planning",
    "IA": "Identification and Authentication",
    "IR": "Incident Response",
    "MA": "Maintenance",
    "MP": "Media Protection",
    "PE": "Physical and Environmental Protection",
    "PL": "Planning",
    "PM": "Program Management",
    "PS": "Personnel Security",
    "PT": "PII Processing and Transparency",
    "RA": "Risk Assessment",
    "SA": "System and Services Acquisition",
    "SC": "System and Communications Protection",
    "SI": "System and Information Integrity",
    "SR": "Supply Chain Risk Management",
    "AR": "Accountability, Audit, and Risk Management",
}


def _get_nist_family(nist_id):
    """Extract the family prefix from a NIST control ID (e.g., 'AC-2(3)' → 'AC')."""
    return nist_id.split("-")[0] if "-" in nist_id else nist_id[:2]


def _get_nist_family_name(nist_id):
    """Get the full family name for a NIST control ID."""
    prefix = _get_nist_family(nist_id)
    return NIST_FAMILIES.get(prefix, "Unknown")


def build_nist_reverse_index():
    """
    Build reverse index: NIST 800-53 control → list of SOPRA control dicts.
    Returns: {
        "AC-2": [{"sopra_id": "AD-001", "sopra_name": "...", "category": "...", ...}, ...],
        ...
    }
    """
    index = defaultdict(list)
    for cid, ctrl in ALL_CONTROLS.items():
        entry = {
            "sopra_id": cid,
            "sopra_name": ctrl.name,
            "category": ctrl.category,
            "family": ctrl.family.value,
            "severity": ctrl.default_severity.value,
        }
        for nist_id in (ctrl.nist_mapping or []):
            index[nist_id].append(entry)
    # Sort by NIST control ID
    return dict(sorted(index.items(), key=lambda x: (_get_nist_family(x[0]), x[0])))


def build_nist_reverse_index_with_findings(findings):
    """
    Build assessment-aware reverse index that includes pass/fail status.
    Returns: {
        "AC-2": [{"sopra_id": "AD-001", "status": "Failed", "severity": "Critical", ...}, ...],
        ...
    }
    """
    # Build finding lookup
    finding_map = {}
    for f in (findings or []):
        finding_map[f.get("control_id", "")] = f

    index = defaultdict(list)
    for cid, ctrl in ALL_CONTROLS.items():
        finding = finding_map.get(cid, {})
        entry = {
            "sopra_id": cid,
            "sopra_name": ctrl.name,
            "category": ctrl.category,
            "family": ctrl.family.value,
            "default_severity": ctrl.default_severity.value,
            "status": finding.get("status", "Not Assessed"),
            "finding_severity": finding.get("severity", ""),
            "evidence": finding.get("evidence", ""),
        }
        for nist_id in (ctrl.nist_mapping or []):
            index[nist_id].append(entry)

    return dict(sorted(index.items(), key=lambda x: (_get_nist_family(x[0]), x[0])))


def get_nist_coverage_stats(findings=None):
    """
    Calculate NIST 800-53 coverage statistics.
    Returns per-family stats: how many NIST controls are covered, how many SOPRA controls map to each.
    """
    index = build_nist_reverse_index_with_findings(findings) if findings else build_nist_reverse_index()

    family_stats = defaultdict(lambda: {
        "nist_controls": set(),
        "sopra_controls": set(),
        "passed": 0,
        "failed": 0,
        "not_assessed": 0,
    })

    for nist_id, entries in index.items():
        family = _get_nist_family(nist_id)
        family_stats[family]["nist_controls"].add(nist_id)
        for entry in entries:
            family_stats[family]["sopra_controls"].add(entry["sopra_id"])
            status = entry.get("status", "Not Assessed")
            if status == "Passed":
                family_stats[family]["passed"] += 1
            elif status == "Failed":
                family_stats[family]["failed"] += 1
            else:
                family_stats[family]["not_assessed"] += 1

    # Convert sets to counts
    result = {}
    for family, stats in sorted(family_stats.items()):
        result[family] = {
            "family_name": NIST_FAMILIES.get(family, "Unknown"),
            "nist_control_count": len(stats["nist_controls"]),
            "sopra_control_count": len(stats["sopra_controls"]),
            "nist_controls": sorted(stats["nist_controls"]),
            "passed": stats["passed"],
            "failed": stats["failed"],
            "not_assessed": stats["not_assessed"],
        }
    return result


# =====================================================================
# 2. CIS CONTROLS v8 REVERSE INDEX
# =====================================================================

CIS_CONTROLS = {
    "1": "Inventory and Control of Enterprise Assets",
    "2": "Inventory and Control of Software Assets",
    "3": "Data Protection",
    "4": "Secure Configuration of Enterprise Assets and Software",
    "5": "Account Management",
    "6": "Access Control Management",
    "7": "Continuous Vulnerability Management",
    "8": "Audit Log Management",
    "9": "Email and Web Browser Protections",
    "10": "Malware Defenses",
    "11": "Data Recovery",
    "12": "Network Infrastructure Management",
    "13": "Network Monitoring and Defense",
    "14": "Security Awareness and Skills Training",
    "15": "Service Provider Management",
    "16": "Application Software Security",
    "17": "Incident Response Management",
    "18": "Penetration Testing",
}


def _get_cis_family(cis_id):
    """Extract the CIS control family number (e.g., '7.1' → '7')."""
    if not cis_id or cis_id == "N/A":
        return None
    return cis_id.split(".")[0]


def build_cis_reverse_index():
    """
    Build reverse index: CIS Controls v8 benchmark → list of SOPRA controls.
    Returns: {"7.1": [{"sopra_id": "VM-001", ...}, ...], ...}
    """
    index = defaultdict(list)
    for cid, ctrl in ALL_CONTROLS.items():
        if ctrl.cis_mapping and ctrl.cis_mapping != "N/A":
            entry = {
                "sopra_id": cid,
                "sopra_name": ctrl.name,
                "category": ctrl.category,
                "family": ctrl.family.value,
                "severity": ctrl.default_severity.value,
            }
            index[ctrl.cis_mapping].append(entry)
    return dict(sorted(index.items(), key=lambda x: (int(_get_cis_family(x[0]) or 99), x[0])))


def build_cis_reverse_index_with_findings(findings):
    """CIS reverse index with assessment status."""
    finding_map = {f.get("control_id", ""): f for f in (findings or [])}

    index = defaultdict(list)
    for cid, ctrl in ALL_CONTROLS.items():
        if ctrl.cis_mapping and ctrl.cis_mapping != "N/A":
            finding = finding_map.get(cid, {})
            entry = {
                "sopra_id": cid,
                "sopra_name": ctrl.name,
                "category": ctrl.category,
                "family": ctrl.family.value,
                "default_severity": ctrl.default_severity.value,
                "status": finding.get("status", "Not Assessed"),
                "finding_severity": finding.get("severity", ""),
            }
            index[ctrl.cis_mapping].append(entry)
    return dict(sorted(index.items(), key=lambda x: (int(_get_cis_family(x[0]) or 99), x[0])))


def get_cis_coverage_stats(findings=None):
    """Calculate CIS Controls v8 coverage statistics per control family."""
    index = build_cis_reverse_index_with_findings(findings) if findings else build_cis_reverse_index()

    family_stats = defaultdict(lambda: {
        "benchmarks": set(),
        "sopra_controls": set(),
        "passed": 0,
        "failed": 0,
        "not_assessed": 0,
    })

    for cis_id, entries in index.items():
        fam = _get_cis_family(cis_id)
        if not fam:
            continue
        family_stats[fam]["benchmarks"].add(cis_id)
        for entry in entries:
            family_stats[fam]["sopra_controls"].add(entry["sopra_id"])
            status = entry.get("status", "Not Assessed")
            if status == "Passed":
                family_stats[fam]["passed"] += 1
            elif status == "Failed":
                family_stats[fam]["failed"] += 1
            else:
                family_stats[fam]["not_assessed"] += 1

    result = {}
    for fam, stats in sorted(family_stats.items(), key=lambda x: int(x[0])):
        result[fam] = {
            "family_name": CIS_CONTROLS.get(fam, "Unknown"),
            "benchmark_count": len(stats["benchmarks"]),
            "sopra_control_count": len(stats["sopra_controls"]),
            "benchmarks": sorted(stats["benchmarks"]),
            "passed": stats["passed"],
            "failed": stats["failed"],
            "not_assessed": stats["not_assessed"],
        }
    return result


# =====================================================================
# 3. FORWARD CROSSWALK (SOPRA → NIST + CIS)
# =====================================================================

def build_forward_crosswalk(findings=None):
    """
    Build the forward crosswalk: every SOPRA control with its NIST and CIS mappings + status.
    Returns list of dicts suitable for table display / CSV export.
    """
    finding_map = {f.get("control_id", ""): f for f in (findings or [])}

    rows = []
    for cid, ctrl in sorted(ALL_CONTROLS.items()):
        finding = finding_map.get(cid, {})
        rows.append({
            "SOPRA Control ID": cid,
            "Control Name": ctrl.name,
            "Category": ctrl.category,
            "NIST Family": ctrl.family.value,
            "NIST 800-53 Mappings": ", ".join(ctrl.nist_mapping or []),
            "CIS v8 Mapping": ctrl.cis_mapping or "N/A",
            "Default Severity": ctrl.default_severity.value,
            "Assessment Status": finding.get("status", "Not Assessed"),
            "Finding Severity": finding.get("severity", "") or "",
            "Evidence": finding.get("evidence", "") or "",
        })
    return rows


# =====================================================================
# 4. CSV EXPORT
# =====================================================================

def export_forward_crosswalk_csv(findings=None):
    """Export SOPRA → NIST/CIS crosswalk as CSV string."""
    rows = build_forward_crosswalk(findings)
    if not rows:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def export_nist_reverse_crosswalk_csv(findings=None):
    """Export NIST → SOPRA reverse crosswalk as CSV string."""
    index = build_nist_reverse_index_with_findings(findings) if findings else build_nist_reverse_index()

    output = io.StringIO()
    fieldnames = ["NIST 800-53 Control", "NIST Family", "SOPRA Control ID",
                  "SOPRA Control Name", "Category", "Status", "Severity"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for nist_id, entries in index.items():
        family_name = _get_nist_family_name(nist_id)
        for entry in entries:
            writer.writerow({
                "NIST 800-53 Control": nist_id,
                "NIST Family": family_name,
                "SOPRA Control ID": entry["sopra_id"],
                "SOPRA Control Name": entry["sopra_name"],
                "Category": entry["category"],
                "Status": entry.get("status", "Not Assessed"),
                "Severity": entry.get("finding_severity", entry.get("severity", "")),
            })
    return output.getvalue()


def export_cis_reverse_crosswalk_csv(findings=None):
    """Export CIS → SOPRA reverse crosswalk as CSV string."""
    index = build_cis_reverse_index_with_findings(findings) if findings else build_cis_reverse_index()

    output = io.StringIO()
    fieldnames = ["CIS v8 Benchmark", "CIS Control Family", "SOPRA Control ID",
                  "SOPRA Control Name", "Category", "Status", "Severity"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for cis_id, entries in index.items():
        fam = _get_cis_family(cis_id)
        family_name = CIS_CONTROLS.get(fam, "Unknown") if fam else "Unknown"
        for entry in entries:
            writer.writerow({
                "CIS v8 Benchmark": cis_id,
                "CIS Control Family": family_name,
                "SOPRA Control ID": entry["sopra_id"],
                "SOPRA Control Name": entry["sopra_name"],
                "Category": entry["category"],
                "Status": entry.get("status", "Not Assessed"),
                "Severity": entry.get("finding_severity", entry.get("severity", "")),
            })
    return output.getvalue()
