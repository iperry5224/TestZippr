"""
SOPRA AI-Powered Vulnerability Remediation Engine
===================================================
Features:
  1. AI-Generated Remediation Plans (Bedrock-powered per-control playbooks)
  2. Automated Risk Prioritization / Attack Chain Detection
  3. Remediation Validation Scripts (post-fix verification)
  4. Change Impact Analysis (downstream effect warnings)
  5. Continuous Learning (track remediation success/failure)
  6. Automated Ticket Generation (ServiceNow / Jira export)
"""
import streamlit as st
import json
import os
from datetime import datetime, timedelta

from sopra.persistence import load_results_from_file, _DATA_DIR, _load_json, _save_json
from sopra.utils import calculate_risk_score
from sopra_controls import get_control_by_id, get_remediation_script

# ---------------------------------------------------------------------------
# Bedrock helper (reuse from ai_assistant)
# ---------------------------------------------------------------------------
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    _HAS_BOTO = True
except ImportError:
    _HAS_BOTO = False

# Claude removed per policy
_BEDROCK_MODELS = [
    "nvidia.nemotron-nano-12b-v2",
    "amazon.titan-text-express-v1",
    "meta.llama3-8b-instruct-v1:0",
    "mistral.mistral-7b-instruct-v0:2",
]

def _call_bedrock(prompt, max_tokens=2048):
    """Quick single-turn Bedrock call with model fallback."""
    if not _HAS_BOTO:
        return None
    try:
        bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        for model_id in _BEDROCK_MODELS:
            try:
                resp = bedrock.converse(
                    modelId=model_id,
                    messages=[{"role": "user", "content": [{"text": prompt}]}],
                    inferenceConfig={"maxTokens": max_tokens, "temperature": 0.4},
                )
                return resp["output"]["message"]["content"][0]["text"]
            except Exception:
                continue
    except Exception:
        pass
    return None


# =====================================================================
# 1. AI-GENERATED REMEDIATION PLANS
# =====================================================================
_PLAN_CACHE_FILE = "ai_remed_plans.json"

def generate_ai_remediation_plan(finding):
    """Generate an AI-powered custom remediation plan for a single finding."""
    control = get_control_by_id(finding.get("control_id", ""))
    ctrl_name = finding.get("control_name", "Unknown")
    ctrl_id = finding.get("control_id", "N/A")
    category = finding.get("category", "N/A")
    severity = finding.get("severity", "Unknown")
    evidence = finding.get("evidence", "")
    family = finding.get("family", "")

    # Check cache first
    cache = _load_json(_PLAN_CACHE_FILE, default={})
    if ctrl_id in cache:
        return cache[ctrl_id]

    prompt = f"""You are a senior cybersecurity engineer. Generate a detailed remediation plan for:

Control: {ctrl_id} - {ctrl_name}
Category: {category}
Severity: {severity}
Family: {family}
Evidence: {evidence}
Description: {control.description if control else 'N/A'}
Expected Result: {control.expected_result if control else 'N/A'}

Provide:
1. Executive Summary (2-3 sentences)
2. Prerequisites (tools, access, approvals needed)
3. Step-by-step remediation procedure (numbered, with commands)
4. Rollback procedure if something goes wrong
5. Verification steps to confirm the fix worked
6. Estimated effort (time, personnel)

Use PowerShell commands for Windows environments. Be specific and actionable."""

    ai_result = _call_bedrock(prompt)

    if ai_result:
        cache[ctrl_id] = ai_result
        _save_json(_PLAN_CACHE_FILE, cache)
        return ai_result

    # Fallback — generate a structured template
    steps = ""
    if control and control.remediation_steps:
        for s in control.remediation_steps:
            steps += f"\n  Step {s.step_number}: {s.description}"
            if s.command:
                steps += f"\n    Command: {s.command}"
            if s.estimated_time:
                steps += f"\n    Time: {s.estimated_time}"
            if s.requires_downtime:
                steps += "\n    ⚠️ REQUIRES DOWNTIME"

    plan = f"""**AI Remediation Plan — {ctrl_id}: {ctrl_name}**

**Executive Summary:**
{ctrl_name} has been identified as a {severity}-severity finding in the {category} domain. Immediate remediation is required to reduce organizational risk and maintain compliance posture.

**Prerequisites:**
- Administrative access to affected systems
- Change management approval (CAB ticket)
- Maintenance window scheduled{'  — DOWNTIME REQUIRED' if control and any(s.requires_downtime for s in (control.remediation_steps or [])) else ''}
- Backup of current configuration

**Remediation Procedure:**{steps if steps else '''
  Step 1: Review current configuration against baseline
  Step 2: Apply hardening settings per organizational policy
  Step 3: Test in non-production environment first
  Step 4: Deploy to production during maintenance window
  Step 5: Validate with post-change verification'''}

**Rollback Procedure:**
  1. Restore configuration backup taken in prerequisites
  2. Verify system functionality after rollback
  3. Document rollback reason in change management ticket

**Verification:**
  1. Re-run SOPRA assessment for control {ctrl_id}
  2. Confirm status changes from "Failed" to "Passed"
  3. Review system logs for any anomalies post-change

**Estimated Effort:** 1-4 hours depending on environment complexity"""

    cache[ctrl_id] = plan
    _save_json(_PLAN_CACHE_FILE, cache)
    return plan


# =====================================================================
# 2. AUTOMATED RISK PRIORITIZATION / ATTACK CHAIN DETECTION
# =====================================================================
ATTACK_CHAINS = [
    {
        "name": "Lateral Movement via Credential Theft",
        "description": "Weak AD controls + missing endpoint protection enable credential harvesting and lateral movement across the domain.",
        "controls": ["AD-001", "AD-002", "AD-004", "END-005", "END-001", "IAM-001", "IAM-002"],
        "impact": "Critical — Full domain compromise possible",
        "break_point": "Implement MFA (IAM-001) and remove local admin rights (END-005) to break the chain.",
        "color": "#e94560",
    },
    {
        "name": "Data Exfiltration Path",
        "description": "Missing DLP, weak encryption, and poor network segmentation create a clear exfiltration path for sensitive data.",
        "controls": ["DAT-002", "DAT-003", "DAT-004", "NET-001", "NET-002", "MON-001"],
        "impact": "Critical — Sensitive data at risk of unauthorized disclosure",
        "break_point": "Deploy DLP (DAT-002) and enforce network segmentation (NET-001) as priority.",
        "color": "#e94560",
    },
    {
        "name": "Ransomware Susceptibility",
        "description": "Unpatched endpoints, missing application control, and weak backup protection leave the environment vulnerable to ransomware.",
        "controls": ["END-002", "END-004", "END-007", "SRV-007", "DAT-005", "END-008"],
        "impact": "High — Business continuity at severe risk",
        "break_point": "Prioritize patch management (END-002) and verify backup integrity (DAT-005/SRV-007).",
        "color": "#ff6b6b",
    },
    {
        "name": "Insider Threat Exposure",
        "description": "Insufficient access controls, no separation of duties, and weak monitoring enable malicious insider activity.",
        "controls": ["IAM-002", "IAM-003", "IAM-007", "IAM-008", "MON-001", "MON-005", "MON-008"],
        "impact": "High — Privileged abuse undetectable",
        "break_point": "Implement RBAC (IAM-003) and deploy user behavior analytics (MON-008).",
        "color": "#ff6b6b",
    },
    {
        "name": "Physical Breach to Digital Compromise",
        "description": "Weak physical access controls combined with unencrypted endpoints enable physical attackers to access digital assets.",
        "controls": ["PHY-001", "PHY-004", "PHY-002", "END-007", "END-005", "SRV-004"],
        "impact": "Medium — Requires physical proximity",
        "break_point": "Enforce full disk encryption (END-007) and server room access controls (PHY-004).",
        "color": "#ffc107",
    },
    {
        "name": "Audit & Compliance Blind Spots",
        "description": "Missing SIEM, incomplete logging, and no log protection create blind spots that prevent detection and break compliance.",
        "controls": ["MON-001", "MON-002", "MON-003", "MON-004", "AD-010", "SRV-010", "END-009"],
        "impact": "High — Cannot detect or prove security posture",
        "break_point": "Deploy SIEM (MON-001) with centralized log aggregation (MON-002) immediately.",
        "color": "#ff6b6b",
    },
]

def detect_attack_chains(findings):
    """Analyze failed controls to identify active attack chains."""
    failed_ids = set(f.get("control_id", "") for f in findings if f.get("status") == "Failed")
    detected = []
    for chain in ATTACK_CHAINS:
        matched = [c for c in chain["controls"] if c in failed_ids]
        if len(matched) >= 2:
            pct = round(len(matched) / len(chain["controls"]) * 100)
            detected.append({
                **chain,
                "matched_controls": matched,
                "match_pct": pct,
                "total_controls": len(chain["controls"]),
            })
    detected.sort(key=lambda x: -x["match_pct"])
    return detected


# =====================================================================
# 3. REMEDIATION VALIDATION SCRIPTS
# =====================================================================
VALIDATION_SCRIPTS = {
    "AD-001": '# Verify no unnecessary Domain Admin accounts\n$domainAdmins = Get-ADGroupMember "Domain Admins" | Select-Object Name, SamAccountName\nWrite-Host "Domain Admins count: $($domainAdmins.Count)" -ForegroundColor Cyan\n$domainAdmins | Format-Table -AutoSize\nif ($domainAdmins.Count -le 3) { Write-Host "PASS: Domain Admin count within acceptable limit" -ForegroundColor Green }\nelse { Write-Host "FAIL: Too many Domain Admin accounts ($($domainAdmins.Count))" -ForegroundColor Red }',
    "AD-004": '# Verify password policy enforcement\n$policy = Get-ADDefaultDomainPasswordPolicy\nWrite-Host "Min Password Length: $($policy.MinPasswordLength)"\nWrite-Host "Complexity Enabled: $($policy.ComplexityEnabled)"\nWrite-Host "Lockout Threshold: $($policy.LockoutThreshold)"\nif ($policy.MinPasswordLength -ge 14 -and $policy.ComplexityEnabled) { Write-Host "PASS: Password policy meets requirements" -ForegroundColor Green }\nelse { Write-Host "FAIL: Password policy does not meet requirements" -ForegroundColor Red }',
    "END-001": '# Verify endpoint protection is running\n$av = Get-MpComputerStatus\nWrite-Host "Antivirus Enabled: $($av.AntivirusEnabled)"\nWrite-Host "Real-time Protection: $($av.RealTimeProtectionEnabled)"\nWrite-Host "Signature Age (days): $($av.AntivirusSignatureAge)"\nif ($av.AntivirusEnabled -and $av.RealTimeProtectionEnabled -and $av.AntivirusSignatureAge -le 3) { Write-Host "PASS: Endpoint protection active and current" -ForegroundColor Green }\nelse { Write-Host "FAIL: Endpoint protection issues detected" -ForegroundColor Red }',
    "END-002": '# Verify patch compliance\n$updates = Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 5\nWrite-Host "Last 5 patches:"\n$updates | Format-Table HotFixID, InstalledOn -AutoSize\n$latest = $updates[0].InstalledOn\n$daysSince = (New-TimeSpan -Start $latest -End (Get-Date)).Days\nif ($daysSince -le 30) { Write-Host "PASS: Patches applied within 30 days ($daysSince days ago)" -ForegroundColor Green }\nelse { Write-Host "FAIL: Last patch was $daysSince days ago" -ForegroundColor Red }',
    "END-007": '# Verify BitLocker encryption\n$bl = Get-BitLockerVolume -MountPoint "C:"\nWrite-Host "Protection Status: $($bl.ProtectionStatus)"\nWrite-Host "Encryption Method: $($bl.EncryptionMethod)"\nWrite-Host "Volume Status: $($bl.VolumeStatus)"\nif ($bl.ProtectionStatus -eq "On") { Write-Host "PASS: BitLocker is active" -ForegroundColor Green }\nelse { Write-Host "FAIL: BitLocker is not protecting this volume" -ForegroundColor Red }',
    "IAM-001": '# Verify MFA enforcement\n# Requires Azure AD / Entra ID module\ntry {\n  $mfaUsers = Get-MgUser -All | Where-Object { $_.StrongAuthenticationRequirements.State -ne "Enforced" }\n  Write-Host "Users without MFA enforced: $($mfaUsers.Count)"\n  if ($mfaUsers.Count -eq 0) { Write-Host "PASS: MFA enforced for all users" -ForegroundColor Green }\n  else { Write-Host "FAIL: $($mfaUsers.Count) users lack MFA" -ForegroundColor Red }\n} catch { Write-Host "INFO: Install Microsoft.Graph module to verify MFA" -ForegroundColor Yellow }',
    "NET-001": '# Verify network segmentation (basic check)\n$adapters = Get-NetAdapter | Where-Object Status -eq "Up"\nforeach ($a in $adapters) {\n  $ip = Get-NetIPAddress -InterfaceIndex $a.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue\n  Write-Host "$($a.Name): $($ip.IPAddress)/$($ip.PrefixLength)"\n}\n$fwProfiles = Get-NetFirewallProfile\nforeach ($p in $fwProfiles) { Write-Host "Firewall $($p.Name): Enabled=$($p.Enabled)" }\nif (($fwProfiles | Where-Object Enabled -eq $true).Count -eq 3) { Write-Host "PASS: All firewall profiles enabled" -ForegroundColor Green }\nelse { Write-Host "FAIL: Not all firewall profiles enabled" -ForegroundColor Red }',
    "MON-001": '# Verify SIEM / event log forwarding\n$subscriptions = wecutil es 2>$null\nif ($subscriptions) { Write-Host "PASS: Event subscriptions found: $($subscriptions.Count)" -ForegroundColor Green }\nelse { Write-Host "INFO: No WEC subscriptions — verify SIEM agent is installed" -ForegroundColor Yellow }\n# Check common SIEM agents\n$agents = @("splunkd","winlogbeat","nxlog","ossec")\nforeach ($a in $agents) {\n  $svc = Get-Service -Name $a -ErrorAction SilentlyContinue\n  if ($svc) { Write-Host "PASS: $a is $($svc.Status)" -ForegroundColor Green }\n}',
}

def get_validation_script(control_id):
    """Return a PowerShell validation script for a given control, or generate a generic one."""
    if control_id in VALIDATION_SCRIPTS:
        return VALIDATION_SCRIPTS[control_id]

    control = get_control_by_id(control_id)
    if not control:
        return None

    # Generate generic validation script
    return f"""# Validation Script for {control_id}: {control.name}
# Generated by SOPRA AI Remediation Engine
# Run this AFTER applying remediation to verify the fix

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Validating: {control_id} - {control.name}" -ForegroundColor Cyan
Write-Host "Expected: {control.expected_result}" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check Procedure (manual verification):
# {control.check_procedure.strip().replace(chr(10), chr(10) + '# ') if control.check_procedure else 'Refer to organizational security baseline'}

Write-Host ""
Write-Host "Manual Verification Required:" -ForegroundColor Yellow
Write-Host "  1. Run the check procedure above"
Write-Host "  2. Compare results against expected outcome"
Write-Host "  3. Re-run SOPRA assessment to confirm PASS status"
Write-Host ""
Write-Host "Re-run SOPRA assessment for {control_id} to confirm remediation." -ForegroundColor Cyan
"""


# =====================================================================
# 4. CHANGE IMPACT ANALYSIS
# =====================================================================
IMPACT_DB = {
    "AD-001": {"impact": "Removing Domain Admin accounts may break service accounts and scheduled tasks that rely on DA privileges.", "affected": "Service accounts, scheduled tasks, SCCM, backup agents", "downtime": "Possible — test in staging first", "rollback": "Re-add account to Domain Admins group"},
    "AD-004": {"impact": "Stricter password policies will force password resets at next logon. Users may be locked out if complexity requirements increase significantly.", "affected": "All domain users, service accounts with static passwords", "downtime": "No — but expect helpdesk ticket surge", "rollback": "Revert GPO to previous password policy settings"},
    "END-002": {"impact": "Applying patches may require reboots and could break applications with specific version dependencies.", "affected": "All patched endpoints, line-of-business applications", "downtime": "Yes — schedule maintenance window", "rollback": "Uninstall specific KB updates via DISM or WUSA"},
    "END-004": {"impact": "Application whitelisting will block any unlisted executables. Users running unapproved software will be impacted.", "affected": "All endpoints with AppLocker/WDAC, developer workstations", "downtime": "No — but may block legitimate tools", "rollback": "Switch AppLocker to audit mode"},
    "END-005": {"impact": "Removing local admin rights will prevent users from installing software or changing system settings.", "affected": "All workstations, developer machines, power users", "downtime": "No — but requires PAM solution for elevation", "rollback": "Re-add users to local Administrators group"},
    "NET-001": {"impact": "Network segmentation changes may disrupt traffic flows between previously connected systems.", "affected": "Cross-VLAN communication, printers, file shares, DNS", "downtime": "Possible — test ACLs in monitor mode first", "rollback": "Remove new firewall rules / VLAN assignments"},
    "NET-002": {"impact": "Tightening firewall rules may block legitimate traffic that wasn't previously documented.", "affected": "All systems traversing the firewall", "downtime": "Possible — implement rules in log-only mode first", "rollback": "Revert to previous firewall rule set"},
    "IAM-001": {"impact": "Enforcing MFA will require all users to enroll an authenticator. Users without smartphones need hardware tokens.", "affected": "All users, remote access, VPN, cloud apps", "downtime": "No — but users locked out until enrolled", "rollback": "Disable MFA requirement in conditional access policy"},
    "SRV-003": {"impact": "Database security changes may affect application connection strings and stored procedure permissions.", "affected": "All applications connecting to the database", "downtime": "Possible — test with application team", "rollback": "Restore database permissions from backup"},
    "DAT-003": {"impact": "Enabling encryption at rest may temporarily increase disk I/O and require initial encryption time.", "affected": "Storage performance, backup processes", "downtime": "Minimal — initial encryption runs in background", "rollback": "Decrypt volumes (time-consuming)"},
    "MON-001": {"impact": "SIEM deployment increases network traffic from log forwarding and requires storage capacity planning.", "affected": "Network bandwidth, storage infrastructure", "downtime": "No — additive deployment", "rollback": "Disable log forwarding agents"},
}

def get_impact_analysis(control_id):
    """Return change impact analysis for a control."""
    if control_id in IMPACT_DB:
        return IMPACT_DB[control_id]

    control = get_control_by_id(control_id)
    if not control:
        return None

    # Generate generic impact analysis
    has_downtime = any(s.requires_downtime for s in (control.remediation_steps or []))
    return {
        "impact": f"Applying remediation for {control.name} may affect dependent systems and processes. Review change advisory board (CAB) requirements before proceeding.",
        "affected": f"Systems in the {control.family} domain",
        "downtime": "Yes — schedule maintenance window" if has_downtime else "Minimal — can be applied during business hours",
        "rollback": "Restore pre-change configuration backup"
    }


# =====================================================================
# 5. CONTINUOUS LEARNING — REMEDIATION TRACKING
# =====================================================================
_REMED_TRACKING_FILE = "remediation_tracking.json"

def load_remediation_tracking():
    data = _load_json(_REMED_TRACKING_FILE, default=None)
    if data is None or not isinstance(data, dict):
        return {"entries": [], "stats": {}}
    return data

def save_remediation_tracking(data):
    _save_json(_REMED_TRACKING_FILE, data)

def record_remediation_attempt(control_id, status, notes=""):
    """Record a remediation attempt (success/fail/in_progress)."""
    tracking = load_remediation_tracking()
    entry = {
        "control_id": control_id,
        "status": status,
        "notes": notes,
        "timestamp": datetime.now().isoformat(),
    }
    tracking["entries"].append(entry)

    # Update stats
    if control_id not in tracking["stats"]:
        tracking["stats"][control_id] = {"attempts": 0, "successes": 0, "failures": 0}
    tracking["stats"][control_id]["attempts"] += 1
    if status == "success":
        tracking["stats"][control_id]["successes"] += 1
    elif status == "failed":
        tracking["stats"][control_id]["failures"] += 1

    save_remediation_tracking(tracking)
    return entry

def get_remediation_success_rate():
    """Calculate overall and per-control remediation success rates."""
    tracking = load_remediation_tracking()
    stats = tracking.get("stats", {})
    total_attempts = sum(s["attempts"] for s in stats.values())
    total_success = sum(s["successes"] for s in stats.values())
    overall_rate = round(total_success / max(total_attempts, 1) * 100, 1)

    per_control = {}
    for cid, s in stats.items():
        per_control[cid] = {
            "attempts": s["attempts"],
            "success_rate": round(s["successes"] / max(s["attempts"], 1) * 100, 1),
        }
    return {"overall_rate": overall_rate, "total_attempts": total_attempts, "per_control": per_control}


# =====================================================================
# 6. AUTOMATED TICKET GENERATION
# =====================================================================
def generate_ticket(finding, ticket_format="servicenow"):
    """Generate a pre-filled remediation ticket."""
    control = get_control_by_id(finding.get("control_id", ""))
    ctrl_id = finding.get("control_id", "N/A")
    ctrl_name = finding.get("control_name", "Unknown")
    severity = finding.get("severity", "Unknown")
    category = finding.get("category", "N/A")
    family = finding.get("family", "N/A")
    evidence = finding.get("evidence", "N/A")

    sev_map = {"Critical": "1 - Critical", "High": "2 - High", "Medium": "3 - Medium", "Low": "4 - Low"}
    sla_map = {"Critical": "24 hours", "High": "72 hours", "Medium": "30 days", "Low": "90 days"}
    priority_map = {"Critical": "P1", "High": "P2", "Medium": "P3", "Low": "P4"}

    description = f"""SOPRA Security Assessment Finding - Remediation Required

Control ID: {ctrl_id}
Control Name: {ctrl_name}
Category: {category}
Family: {family}
Severity: {severity}
SLA Deadline: {sla_map.get(severity, '90 days')}

Evidence:
{evidence}

Description:
{control.description if control else 'See SOPRA assessment report for details.'}

Expected Result:
{control.expected_result if control else 'N/A'}

Remediation Steps:
"""
    if control and control.remediation_steps:
        for s in control.remediation_steps:
            description += f"  {s.step_number}. {s.description}"
            if s.estimated_time:
                description += f" (Est: {s.estimated_time})"
            if s.requires_downtime:
                description += " [REQUIRES DOWNTIME]"
            description += "\n"
    else:
        description += "  Refer to SOPRA assessment report and organizational security baseline.\n"

    due_date = datetime.now() + timedelta(
        hours=24 if severity == "Critical" else 72 if severity == "High" else 720 if severity == "Medium" else 2160
    )

    if ticket_format == "servicenow":
        return {
            "short_description": f"[{ctrl_id}] {ctrl_name} — {severity} Security Finding",
            "description": description,
            "priority": priority_map.get(severity, "P4"),
            "impact": sev_map.get(severity, "4 - Low"),
            "urgency": sev_map.get(severity, "4 - Low"),
            "category": "Security",
            "subcategory": category,
            "assignment_group": "Information Security",
            "due_date": due_date.strftime("%Y-%m-%d %H:%M:%S"),
            "state": "New",
            "cmdb_ci": f"SOPRA-{ctrl_id}",
        }
    else:  # Jira format
        return {
            "summary": f"[{ctrl_id}] {ctrl_name} — {severity} Security Finding",
            "description": description,
            "priority": {"Critical": "Highest", "High": "High", "Medium": "Medium", "Low": "Low"}.get(severity, "Low"),
            "issuetype": "Task",
            "labels": ["sopra", "security", "remediation", severity.lower()],
            "components": [category],
            "duedate": due_date.strftime("%Y-%m-%d"),
            "assignee": "",
        }


def generate_bulk_tickets(findings, ticket_format="servicenow"):
    """Generate tickets for all failed findings."""
    failed = [f for f in findings if f.get("status") == "Failed"]
    tickets = []
    for f in failed:
        tickets.append(generate_ticket(f, ticket_format))
    return tickets
