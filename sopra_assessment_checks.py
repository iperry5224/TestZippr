"""
SOPRA Assessment Checks - 1:1 correlations to remediation scripts.
Each entry defines PowerShell logic to CHECK a control (not fix it).
Output: CSV row for SOPRA import.
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class AssessmentCheck:
    """Assessment logic for a control - runs on target, outputs Pass/Fail."""
    control_id: str
    category: str
    # PowerShell to run. Must set $STATUS='Passed'|'Failed', $SEVERITY, $EVIDENCE
    script: str

# Assessment scripts - direct correlations to sopra_controls remediation steps
# Uses same/similar commands as remediation "audit" step, but evaluates result
ASSESSMENT_CHECKS = {
    "AD-001": AssessmentCheck(
        "AD-001", "Active Directory Security", r"""
$count = (Get-ADGroupMember -Identity 'Domain Admins' -ErrorAction SilentlyContinue).Count
if ($count -gt 5) { $STATUS='Failed'; $SEVERITY='Critical'; $EVIDENCE="Found $count Domain Admin accounts (max 5 recommended)" }
else { $STATUS='Passed'; $SEVERITY=''; $EVIDENCE="Found $count Domain Admin accounts" }
"""),
    "AD-002": AssessmentCheck(
        "AD-002", "Active Directory Security", r"""
try { $gmsa = (Get-ADServiceAccount -Filter * -ErrorAction SilentlyContinue).Count }
catch { $gmsa = 0 }
$users = Get-ADUser -Filter {ServicePrincipalName -ne '$null'} -Properties PasswordLastSet -ErrorAction SilentlyContinue
$old = ($users | Where-Object { $_.PasswordLastSet -lt (Get-Date).AddDays(-90) }).Count
if ($old -gt 0) { $STATUS='Failed'; $SEVERITY='High'; $EVIDENCE="$old service accounts with password older than 90 days" }
else { $STATUS='Passed'; $SEVERITY=''; $EVIDENCE="Service accounts within password age policy" }
"""),
    "AD-003": AssessmentCheck(
        "AD-003", "Active Directory Security", r"""
$gpos = (Get-GPO -All -ErrorAction SilentlyContinue).Count
if ($gpos -eq 0) { $STATUS='Failed'; $SEVERITY='Medium'; $EVIDENCE="Could not enumerate GPOs - check GroupPolicy module" }
else { $STATUS='Passed'; $SEVERITY=''; $EVIDENCE="Enumerated $gpos GPOs - manual review of permissions recommended" }
"""),
    "AD-004": AssessmentCheck(
        "AD-004", "Active Directory Security", r"""
$pol = Get-ADDefaultDomainPasswordPolicy -ErrorAction SilentlyContinue
if (-not $pol) { $STATUS='Failed'; $SEVERITY='High'; $EVIDENCE="Could not read domain password policy" }
elseif ($pol.MinPasswordLength -lt 14) { $STATUS='Failed'; $SEVERITY='High'; $EVIDENCE="Min password length $($pol.MinPasswordLength) (recommend 14+)" }
elseif ($pol.PasswordHistoryCount -lt 24) { $STATUS='Failed'; $SEVERITY='Medium'; $EVIDENCE="Password history $($pol.PasswordHistoryCount) (recommend 24+)" }
else { $STATUS='Passed'; $SEVERITY=''; $EVIDENCE="MinLength=$($pol.MinPasswordLength), History=$($pol.PasswordHistoryCount)" }
"""),
    "AD-005": AssessmentCheck(
        "AD-005", "Active Directory Security", r"""
$kerberoast = (Get-ADUser -Filter {ServicePrincipalName -ne '$null' -and DoesNotRequirePreAuth -eq $true} -ErrorAction SilentlyContinue).Count
if ($kerberoast -gt 0) { $STATUS='Failed'; $SEVERITY='High'; $EVIDENCE="$kerberoast accounts vulnerable to Kerberoasting (pre-auth disabled)" }
else { $STATUS='Passed'; $SEVERITY=''; $EVIDENCE="No Kerberoastable accounts found" }
"""),
    "AD-006": AssessmentCheck(
        "AD-006", "Active Directory Security", r"""
$val = Get-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters' -Name 'LDAPServerIntegrity' -ErrorAction SilentlyContinue
if (-not $val) { $STATUS='Failed'; $SEVERITY='Medium'; $EVIDENCE="Run on Domain Controller - registry not found" }
elseif ($val.LDAPServerIntegrity -eq 2) { $STATUS='Passed'; $SEVERITY=''; $EVIDENCE="LDAP signing required (value=2)" }
else { $STATUS='Failed'; $SEVERITY='High'; $EVIDENCE="LDAP signing not required (value=$($val.LDAPServerIntegrity))" }
"""),
    "AD-007": AssessmentCheck(
        "AD-007", "Active Directory Security", r"""
$adminCount = (Get-ADUser -Filter {adminCount -eq 1} -ErrorAction SilentlyContinue).Count
$STATUS='Passed'; $SEVERITY=''; $EVIDENCE="Found $adminCount accounts with adminCount=1 (protected groups)"
"""),
    "AD-008": AssessmentCheck(
        "AD-008", "Active Directory Security", r"""
$trusts = Get-ADTrust -Filter * -ErrorAction SilentlyContinue
$cnt = ($trusts | Measure-Object).Count
$STATUS='Passed'; $SEVERITY=''; $EVIDENCE="Found $cnt trust relationship(s) - verify SID filtering manually"
"""),
    "AD-009": AssessmentCheck(
        "AD-009", "Active Directory Security", r"""
$cutoff = (Get-Date).AddDays(-90)
$stale = (Get-ADUser -Filter {Enabled -eq $true} -Properties LastLogonDate -ErrorAction SilentlyContinue | Where-Object { $_.LastLogonDate -lt $cutoff -or $null -eq $_.LastLogonDate }).Count
if ($stale -gt 10) { $STATUS='Failed'; $SEVERITY='Medium'; $EVIDENCE="$stale enabled accounts inactive >90 days" }
else { $STATUS='Passed'; $SEVERITY=''; $EVIDENCE="$stale stale accounts (threshold 10)" }
"""),
    "AD-010": AssessmentCheck(
        "AD-010", "Active Directory Security", r"""
$audit = auditpol /get /category:* 2>$null
if ($audit) { $STATUS='Passed'; $SEVERITY=''; $EVIDENCE="Audit policy retrieved - verify categories manually" }
else { $STATUS='Failed'; $SEVERITY='Medium'; $EVIDENCE="Could not retrieve audit policy (run as admin)" }
"""),
}

def get_assessment_check(control_id: str) -> Optional[AssessmentCheck]:
    return ASSESSMENT_CHECKS.get(control_id)
