"""
CISA BOD 22-01 - Known Exploited Vulnerabilities (KEV) Checker
===============================================================
Implements CISA Binding Operational Directive 22-01 compliance checking
for SAELAR-53.

BOD 22-01 requires remediation of Known Exploited Vulnerabilities:
- Vulnerabilities with CVE assigned before 2021: 6 months to remediate
- Vulnerabilities with CVE assigned 2021 or later: 2 weeks to remediate

KEV Catalog: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
JSON Feed: https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json

Author: SAELAR Security Architecture and Evaluation
"""

import json
import requests
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import os


# CISA KEV Catalog URL
KEV_CATALOG_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"


class RemediationStatus(Enum):
    """Status of KEV remediation."""
    OVERDUE = "OVERDUE"           # Past due date
    DUE_SOON = "DUE SOON"         # Within 7 days of due date
    IN_PROGRESS = "IN PROGRESS"   # Being worked on
    REMEDIATED = "REMEDIATED"     # Fixed
    NOT_APPLICABLE = "N/A"        # Not present in environment


class Severity(Enum):
    """Severity classification for BOD 22-01."""
    CRITICAL = "CRITICAL"  # Overdue KEVs
    HIGH = "HIGH"          # Due within 7 days
    MEDIUM = "MEDIUM"      # Due within 30 days
    LOW = "LOW"            # Due > 30 days


@dataclass
class KEVEntry:
    """Represents a single Known Exploited Vulnerability."""
    cve_id: str
    vendor_project: str
    product: str
    vulnerability_name: str
    date_added: datetime
    due_date: datetime
    short_description: str
    required_action: str
    known_ransomware_campaign_use: str = "Unknown"
    notes: str = ""
    
    @property
    def days_until_due(self) -> int:
        """Days until remediation is due (negative if overdue)."""
        return (self.due_date - datetime.now()).days
    
    @property
    def is_overdue(self) -> bool:
        """Check if remediation deadline has passed."""
        return datetime.now() > self.due_date
    
    @property
    def severity(self) -> Severity:
        """Determine severity based on due date."""
        days = self.days_until_due
        if days < 0:
            return Severity.CRITICAL
        elif days <= 7:
            return Severity.HIGH
        elif days <= 30:
            return Severity.MEDIUM
        else:
            return Severity.LOW
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'cve_id': self.cve_id,
            'vendor_project': self.vendor_project,
            'product': self.product,
            'vulnerability_name': self.vulnerability_name,
            'date_added': self.date_added.isoformat(),
            'due_date': self.due_date.isoformat(),
            'short_description': self.short_description,
            'required_action': self.required_action,
            'known_ransomware_campaign_use': self.known_ransomware_campaign_use,
            'days_until_due': self.days_until_due,
            'is_overdue': self.is_overdue,
            'severity': self.severity.value,
        }


@dataclass
class KEVFinding:
    """A KEV found in the environment."""
    kev: KEVEntry
    affected_assets: List[str] = field(default_factory=list)
    status: RemediationStatus = RemediationStatus.IN_PROGRESS
    remediation_notes: str = ""
    assigned_to: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            **self.kev.to_dict(),
            'affected_assets': self.affected_assets,
            'affected_asset_count': len(self.affected_assets),
            'status': self.status.value,
            'remediation_notes': self.remediation_notes,
            'assigned_to': self.assigned_to,
        }


@dataclass
class BOD2201Assessment:
    """BOD 22-01 Compliance Assessment Results."""
    assessment_date: datetime
    organization: str
    total_kevs_in_catalog: int = 0
    kevs_found: List[KEVFinding] = field(default_factory=list)
    
    @property
    def total_findings(self) -> int:
        return len(self.kevs_found)
    
    @property
    def overdue_count(self) -> int:
        return len([k for k in self.kevs_found if k.kev.is_overdue])
    
    @property
    def due_soon_count(self) -> int:
        return len([k for k in self.kevs_found if 0 <= k.kev.days_until_due <= 7])
    
    @property
    def critical_count(self) -> int:
        return len([k for k in self.kevs_found if k.kev.severity == Severity.CRITICAL])
    
    @property
    def high_count(self) -> int:
        return len([k for k in self.kevs_found if k.kev.severity == Severity.HIGH])
    
    @property
    def compliance_status(self) -> str:
        """Overall BOD 22-01 compliance status."""
        if self.overdue_count > 0:
            return "NON-COMPLIANT"
        elif self.due_soon_count > 0:
            return "AT RISK"
        elif self.total_findings > 0:
            return "COMPLIANT - ACTIVE KEVs"
        else:
            return "COMPLIANT"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'assessment_date': self.assessment_date.isoformat(),
            'organization': self.organization,
            'total_kevs_in_catalog': self.total_kevs_in_catalog,
            'compliance_status': self.compliance_status,
            'summary': {
                'total_kevs_found': self.total_findings,
                'overdue': self.overdue_count,
                'due_within_7_days': self.due_soon_count,
                'critical': self.critical_count,
                'high': self.high_count,
            },
            'findings': [f.to_dict() for f in self.kevs_found],
        }


class CISAKEVChecker:
    """
    CISA BOD 22-01 Known Exploited Vulnerabilities Checker.
    
    Downloads the KEV catalog from CISA and compares against
    vulnerability scan results to identify compliance gaps.
    """
    
    def __init__(self, cache_file: str = None):
        """
        Initialize the KEV checker.
        
        Args:
            cache_file: Optional path to cache the KEV catalog locally
        """
        self.cache_file = cache_file or os.path.join(
            os.path.dirname(__file__), 'kev_catalog_cache.json'
        )
        self.kev_catalog: Dict[str, KEVEntry] = {}
        self.catalog_version: str = ""
        self.catalog_date: datetime = None
        
    def download_kev_catalog(self, force_refresh: bool = False) -> bool:
        """
        Download the KEV catalog from CISA.
        
        Args:
            force_refresh: If True, ignore cache and download fresh
            
        Returns:
            True if successful, False otherwise
        """
        # Check cache first
        if not force_refresh and os.path.exists(self.cache_file):
            cache_age = datetime.now().timestamp() - os.path.getmtime(self.cache_file)
            if cache_age < 86400:  # Less than 24 hours old
                return self._load_from_cache()
        
        try:
            print("[*] Downloading CISA KEV catalog...")
            response = requests.get(KEV_CATALOG_URL, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            self._parse_catalog(data)
            
            # Cache the catalog
            with open(self.cache_file, 'w') as f:
                json.dump(data, f)
            
            print(f"[OK] Loaded {len(self.kev_catalog)} KEVs from CISA catalog")
            return True
            
        except requests.RequestException as e:
            print(f"[ERROR] Failed to download KEV catalog: {e}")
            # Try to load from cache as fallback
            return self._load_from_cache()
        except Exception as e:
            print(f"[ERROR] Error processing KEV catalog: {e}")
            return False
    
    def _load_from_cache(self) -> bool:
        """Load KEV catalog from local cache."""
        if not os.path.exists(self.cache_file):
            return False
            
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
            self._parse_catalog(data)
            print(f"[OK] Loaded {len(self.kev_catalog)} KEVs from cache")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to load cache: {e}")
            return False
    
    def _parse_catalog(self, data: Dict) -> None:
        """Parse the KEV catalog JSON."""
        self.catalog_version = data.get('catalogVersion', 'Unknown')
        
        date_str = data.get('dateReleased', '')
        if date_str:
            try:
                self.catalog_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                self.catalog_date = datetime.now()
        
        self.kev_catalog = {}
        
        for vuln in data.get('vulnerabilities', []):
            try:
                # Parse dates
                date_added = datetime.strptime(vuln['dateAdded'], '%Y-%m-%d')
                due_date = datetime.strptime(vuln['dueDate'], '%Y-%m-%d')
                
                kev = KEVEntry(
                    cve_id=vuln['cveID'],
                    vendor_project=vuln.get('vendorProject', 'Unknown'),
                    product=vuln.get('product', 'Unknown'),
                    vulnerability_name=vuln.get('vulnerabilityName', 'Unknown'),
                    date_added=date_added,
                    due_date=due_date,
                    short_description=vuln.get('shortDescription', ''),
                    required_action=vuln.get('requiredAction', 'Apply updates per vendor instructions.'),
                    known_ransomware_campaign_use=vuln.get('knownRansomwareCampaignUse', 'Unknown'),
                    notes=vuln.get('notes', ''),
                )
                self.kev_catalog[kev.cve_id] = kev
            except Exception as e:
                print(f"[WARN] Error parsing KEV entry: {e}")
                continue
    
    def check_cve(self, cve_id: str) -> Optional[KEVEntry]:
        """
        Check if a CVE is in the KEV catalog.
        
        Args:
            cve_id: CVE identifier (e.g., 'CVE-2021-44228')
            
        Returns:
            KEVEntry if found, None otherwise
        """
        return self.kev_catalog.get(cve_id.upper())
    
    def check_cve_list(self, cve_list: List[str]) -> List[KEVEntry]:
        """
        Check a list of CVEs against the KEV catalog.
        
        Args:
            cve_list: List of CVE identifiers
            
        Returns:
            List of KEVEntry objects for CVEs found in KEV catalog
        """
        found = []
        for cve in cve_list:
            kev = self.check_cve(cve)
            if kev:
                found.append(kev)
        return found
    
    def assess_vulnerabilities(
        self, 
        vulnerabilities: List[Dict[str, Any]],
        organization: str = "Organization"
    ) -> BOD2201Assessment:
        """
        Assess a list of vulnerabilities against BOD 22-01 requirements.
        
        Args:
            vulnerabilities: List of vulnerability dictionaries with at least:
                - cve_id: CVE identifier
                - affected_assets: List of affected asset names (optional)
            organization: Organization name for the report
            
        Returns:
            BOD2201Assessment with findings
        """
        assessment = BOD2201Assessment(
            assessment_date=datetime.now(),
            organization=organization,
            total_kevs_in_catalog=len(self.kev_catalog),
        )
        
        for vuln in vulnerabilities:
            cve_id = vuln.get('cve_id') or vuln.get('cveID') or vuln.get('CVE')
            if not cve_id:
                continue
                
            kev = self.check_cve(cve_id)
            if kev:
                finding = KEVFinding(
                    kev=kev,
                    affected_assets=vuln.get('affected_assets', vuln.get('hosts', [])),
                    status=RemediationStatus.IN_PROGRESS,
                )
                assessment.kevs_found.append(finding)
        
        # Sort by severity (overdue first)
        assessment.kevs_found.sort(key=lambda x: x.kev.days_until_due)
        
        return assessment
    
    def get_overdue_kevs(self) -> List[KEVEntry]:
        """Get all KEVs that are past their due date."""
        return [kev for kev in self.kev_catalog.values() if kev.is_overdue]
    
    def get_kevs_due_soon(self, days: int = 7) -> List[KEVEntry]:
        """Get KEVs due within specified days."""
        return [
            kev for kev in self.kev_catalog.values() 
            if 0 <= kev.days_until_due <= days
        ]
    
    def get_ransomware_kevs(self) -> List[KEVEntry]:
        """Get KEVs known to be used in ransomware campaigns."""
        return [
            kev for kev in self.kev_catalog.values()
            if kev.known_ransomware_campaign_use.lower() == 'known'
        ]
    
    def search_by_vendor(self, vendor: str) -> List[KEVEntry]:
        """Search KEVs by vendor/project name."""
        vendor_lower = vendor.lower()
        return [
            kev for kev in self.kev_catalog.values()
            if vendor_lower in kev.vendor_project.lower()
        ]
    
    def search_by_product(self, product: str) -> List[KEVEntry]:
        """Search KEVs by product name."""
        product_lower = product.lower()
        return [
            kev for kev in self.kev_catalog.values()
            if product_lower in kev.product.lower()
        ]
    
    def generate_report(self, assessment: BOD2201Assessment) -> str:
        """
        Generate a text report for BOD 22-01 assessment.
        
        Args:
            assessment: BOD2201Assessment results
            
        Returns:
            Formatted text report
        """
        lines = [
            "=" * 70,
            "CISA BOD 22-01 COMPLIANCE ASSESSMENT REPORT",
            "Known Exploited Vulnerabilities (KEV) Analysis",
            "=" * 70,
            "",
            f"Organization: {assessment.organization}",
            f"Assessment Date: {assessment.assessment_date.strftime('%Y-%m-%d %H:%M:%S')}",
            f"KEV Catalog Version: {self.catalog_version}",
            f"Total KEVs in Catalog: {assessment.total_kevs_in_catalog}",
            "",
            "-" * 70,
            "COMPLIANCE STATUS",
            "-" * 70,
            "",
            f"  Status: {assessment.compliance_status}",
            "",
            f"  Total KEVs Found in Environment: {assessment.total_findings}",
            f"  OVERDUE (Past Due Date):         {assessment.overdue_count}",
            f"  Due Within 7 Days:               {assessment.due_soon_count}",
            f"  Critical Severity:               {assessment.critical_count}",
            f"  High Severity:                   {assessment.high_count}",
            "",
        ]
        
        if assessment.overdue_count > 0:
            lines.extend([
                "-" * 70,
                "!!! OVERDUE KEVs - IMMEDIATE ACTION REQUIRED !!!",
                "-" * 70,
                "",
            ])
            
            for finding in assessment.kevs_found:
                if finding.kev.is_overdue:
                    days_overdue = abs(finding.kev.days_until_due)
                    lines.extend([
                        f"  CVE: {finding.kev.cve_id}",
                        f"  Vendor: {finding.kev.vendor_project} | Product: {finding.kev.product}",
                        f"  Vulnerability: {finding.kev.vulnerability_name}",
                        f"  Due Date: {finding.kev.due_date.strftime('%Y-%m-%d')} ({days_overdue} days OVERDUE)",
                        f"  Ransomware Use: {finding.kev.known_ransomware_campaign_use}",
                        f"  Affected Assets: {len(finding.affected_assets)}",
                        f"  Required Action: {finding.kev.required_action}",
                        "",
                    ])
        
        if assessment.due_soon_count > 0:
            lines.extend([
                "-" * 70,
                "KEVs DUE WITHIN 7 DAYS",
                "-" * 70,
                "",
            ])
            
            for finding in assessment.kevs_found:
                if 0 <= finding.kev.days_until_due <= 7:
                    lines.extend([
                        f"  CVE: {finding.kev.cve_id}",
                        f"  Vendor: {finding.kev.vendor_project} | Product: {finding.kev.product}",
                        f"  Due Date: {finding.kev.due_date.strftime('%Y-%m-%d')} ({finding.kev.days_until_due} days remaining)",
                        f"  Required Action: {finding.kev.required_action}",
                        "",
                    ])
        
        # All findings summary
        if assessment.total_findings > 0:
            lines.extend([
                "-" * 70,
                "ALL KEV FINDINGS",
                "-" * 70,
                "",
            ])
            
            for finding in assessment.kevs_found:
                status_icon = "!!!" if finding.kev.is_overdue else "(!)" if finding.kev.days_until_due <= 7 else "   "
                lines.append(
                    f"  {status_icon} {finding.kev.cve_id} | {finding.kev.vendor_project} | "
                    f"Due: {finding.kev.due_date.strftime('%Y-%m-%d')} | "
                    f"Assets: {len(finding.affected_assets)}"
                )
            
            lines.append("")
        
        lines.extend([
            "-" * 70,
            "REMEDIATION GUIDANCE",
            "-" * 70,
            "",
            "Per CISA BOD 22-01:",
            "  - CVEs assigned before 2021: Remediate within 6 months of addition to KEV",
            "  - CVEs assigned 2021 or later: Remediate within 2 weeks of addition to KEV",
            "",
            "Priority Actions:",
            "  1. Address all OVERDUE KEVs immediately",
            "  2. Prioritize KEVs used in ransomware campaigns",
            "  3. Plan remediation for KEVs due within 7 days",
            "  4. Track all KEVs in POA&M until remediated",
            "",
            "=" * 70,
            f"Report Generated by SAELAR BOD 22-01 Module",
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 70,
        ])
        
        return "\n".join(lines)


# Convenience function for quick checks
def check_cves_against_kev(cve_list: List[str]) -> List[Dict]:
    """
    Quick check of CVE list against KEV catalog.
    
    Args:
        cve_list: List of CVE identifiers
        
    Returns:
        List of KEV entries found (as dictionaries)
    """
    checker = CISAKEVChecker()
    if not checker.download_kev_catalog():
        return []
    
    found = checker.check_cve_list(cve_list)
    return [kev.to_dict() for kev in found]


# Main execution for testing
if __name__ == '__main__':
    print("CISA BOD 22-01 KEV Checker")
    print("=" * 50)
    
    checker = CISAKEVChecker()
    
    if checker.download_kev_catalog():
        print(f"\nCatalog Version: {checker.catalog_version}")
        print(f"Total KEVs: {len(checker.kev_catalog)}")
        
        # Show some stats
        overdue = checker.get_overdue_kevs()
        print(f"Overdue KEVs: {len(overdue)}")
        
        due_soon = checker.get_kevs_due_soon(7)
        print(f"Due within 7 days: {len(due_soon)}")
        
        ransomware = checker.get_ransomware_kevs()
        print(f"Known ransomware use: {len(ransomware)}")
        
        # Example: Check some common CVEs
        test_cves = [
            'CVE-2021-44228',  # Log4Shell
            'CVE-2021-34527',  # PrintNightmare
            'CVE-2023-23397',  # Outlook elevation of privilege
            'CVE-2024-3400',   # Palo Alto PAN-OS
        ]
        
        print(f"\nChecking test CVEs...")
        for cve in test_cves:
            kev = checker.check_cve(cve)
            if kev:
                print(f"  [KEV] {cve}: {kev.vulnerability_name}")
                print(f"        Due: {kev.due_date.strftime('%Y-%m-%d')} | Overdue: {kev.is_overdue}")
            else:
                print(f"  [---] {cve}: Not in KEV catalog")

