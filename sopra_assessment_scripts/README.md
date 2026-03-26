# SOPRA Assessment Scripts — For System Administrator Team

**Purpose:** Run these scripts on your target machines to collect assessment data. The output CSV is imported into SOPRA so the GRC team can run assessments.

---

## The Link: Assessment ↔ Remediation

| Assessment Script | Remediation Script | Correlation |
|-------------------|-------------------|-------------|
| `AD_001_assessment.ps1` | `AD_001.ps1` (in sopra_remediation_scripts/) | 1:1 — same control ID |
| `NET_001_assessment.ps1` | `NET_001.ps1` | 1:1 |
| ... | ... | All 200 controls |

- **Assessment script** → Runs the *check* (does the control pass or fail?)
- **Remediation script** → Runs the *fix* (if it failed, how do we fix it?)

---

## How to Use

### Option 1: Run All Assessments (Full Scan)

```powershell
# Run from the sopra_assessment_scripts folder
# Requires: Domain Admin (for AD), appropriate rights for other categories
.\Run-All-Assessments.ps1
```

**Output:** `sopra_assessment_results.csv` in the same folder.

### Option 2: Run Individual Scripts

```powershell
# Run specific controls (e.g., Active Directory only)
.\AD_001_assessment.ps1
.\AD_002_assessment.ps1
# ...
```

Each script appends one row to `sopra_assessment_results.csv`.

### Option 3: Run by Category

Run all scripts for a category (e.g., all `AD_*`, all `NET_*`) by invoking them in sequence.

---

## Where to Run

| Category | Run On | Notes |
|----------|--------|------|
| AD-* (Active Directory) | Domain Controller or machine with RSAT | Requires AD PowerShell module |
| NET-* (Network) | Network devices / management server | Some checks may need Cisco IOS, etc. |
| END-* (Endpoint) | Workstation or server | Local checks |
| SRV-*, CFG-*, etc. | Target server | Varies by control |

---

## Hand Off to GRC Team

1. Run the assessment scripts on the appropriate targets.
2. Collect `sopra_assessment_results.csv`.
3. Send the CSV to the GRC/SOPRA team.
4. GRC imports the CSV into SOPRA (**Assessment** tab → **Upload CSV**).

---

## CSV Format (SOPRA Import)

The scripts produce CSV with these columns:

```
category,control_id,control_name,status,severity,evidence,notes,assessed_by,assessment_date
```

- `status` = Passed | Failed | Manual Review | Not Assessed
- `severity` = Critical | High | Medium | Low (for failures)
- `evidence` = What the script found (automated or from discovery)

---

## Script Types

- **Automated checks** (e.g., AD-001, AD-004): Script evaluates and sets Pass/Fail.
- **Discovery + Manual Review**: Script runs discovery commands; human reviews output and updates CSV if needed.

---

## Requirements

- **PowerShell 5.1+** (Windows)
- **Active Directory module** (for AD-* scripts): `Install-WindowsFeature RSAT-AD-PowerShell` or equivalent
- **Run as Administrator** where required (e.g., AD-006 on DC for registry)
