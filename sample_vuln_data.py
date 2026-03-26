"""
Sample Vulnerability Data for SAELAR BOD 22-01 Testing
=======================================================
Generates realistic sample vulnerability scan data for testing
the KEV checker without requiring actual scanner integration.

This includes a mix of:
- Known Exploited Vulnerabilities (KEVs) - should be flagged
- Regular CVEs - should NOT be flagged
- Various vendors and products
- Different severities
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Sample KEVs (real CVEs that ARE in CISA's KEV catalog)
SAMPLE_KEVS = [
    {
        "cve_id": "CVE-2021-44228",
        "title": "Apache Log4j2 Remote Code Execution (Log4Shell)",
        "vendor": "Apache",
        "product": "Log4j",
        "severity": "CRITICAL",
        "cvss": 10.0,
    },
    {
        "cve_id": "CVE-2021-34527",
        "title": "Microsoft Windows Print Spooler RCE (PrintNightmare)",
        "vendor": "Microsoft",
        "product": "Windows",
        "severity": "CRITICAL",
        "cvss": 8.8,
    },
    {
        "cve_id": "CVE-2023-23397",
        "title": "Microsoft Outlook Privilege Escalation",
        "vendor": "Microsoft",
        "product": "Outlook",
        "severity": "CRITICAL",
        "cvss": 9.8,
    },
    {
        "cve_id": "CVE-2024-3400",
        "title": "Palo Alto Networks PAN-OS Command Injection",
        "vendor": "Palo Alto Networks",
        "product": "PAN-OS",
        "severity": "CRITICAL",
        "cvss": 10.0,
    },
    {
        "cve_id": "CVE-2021-26855",
        "title": "Microsoft Exchange Server SSRF (ProxyLogon)",
        "vendor": "Microsoft",
        "product": "Exchange Server",
        "severity": "CRITICAL",
        "cvss": 9.8,
    },
    {
        "cve_id": "CVE-2020-1472",
        "title": "Microsoft Netlogon Privilege Escalation (Zerologon)",
        "vendor": "Microsoft",
        "product": "Windows",
        "severity": "CRITICAL",
        "cvss": 10.0,
    },
    {
        "cve_id": "CVE-2019-19781",
        "title": "Citrix ADC/Gateway Directory Traversal",
        "vendor": "Citrix",
        "product": "ADC/Gateway",
        "severity": "CRITICAL",
        "cvss": 9.8,
    },
    {
        "cve_id": "CVE-2022-22965",
        "title": "Spring Framework RCE (Spring4Shell)",
        "vendor": "VMware",
        "product": "Spring Framework",
        "severity": "CRITICAL",
        "cvss": 9.8,
    },
    {
        "cve_id": "CVE-2023-27350",
        "title": "PaperCut NG/MF Authentication Bypass",
        "vendor": "PaperCut",
        "product": "NG/MF",
        "severity": "CRITICAL",
        "cvss": 9.8,
    },
    {
        "cve_id": "CVE-2022-41082",
        "title": "Microsoft Exchange Server RCE (ProxyNotShell)",
        "vendor": "Microsoft",
        "product": "Exchange Server",
        "severity": "HIGH",
        "cvss": 8.8,
    },
]

# Sample NON-KEV CVEs (real CVEs that are NOT in CISA's KEV catalog)
SAMPLE_NON_KEVS = [
    {
        "cve_id": "CVE-2023-12345",
        "title": "Sample Application SQL Injection",
        "vendor": "Internal",
        "product": "Custom App",
        "severity": "HIGH",
        "cvss": 7.5,
    },
    {
        "cve_id": "CVE-2023-98765",
        "title": "OpenSSL Information Disclosure",
        "vendor": "OpenSSL",
        "product": "OpenSSL",
        "severity": "MEDIUM",
        "cvss": 5.3,
    },
    {
        "cve_id": "CVE-2022-11111",
        "title": "nginx Buffer Overflow",
        "vendor": "nginx",
        "product": "nginx",
        "severity": "MEDIUM",
        "cvss": 6.5,
    },
    {
        "cve_id": "CVE-2024-00001",
        "title": "PostgreSQL Denial of Service",
        "vendor": "PostgreSQL",
        "product": "PostgreSQL",
        "severity": "LOW",
        "cvss": 4.0,
    },
    {
        "cve_id": "CVE-2023-55555",
        "title": "Apache Tomcat Path Traversal",
        "vendor": "Apache",
        "product": "Tomcat",
        "severity": "MEDIUM",
        "cvss": 5.5,
    },
    {
        "cve_id": "CVE-2022-99999",
        "title": "Redis Authentication Bypass",
        "vendor": "Redis",
        "product": "Redis",
        "severity": "HIGH",
        "cvss": 7.8,
    },
    {
        "cve_id": "CVE-2023-77777",
        "title": "MySQL Privilege Escalation",
        "vendor": "Oracle",
        "product": "MySQL",
        "severity": "MEDIUM",
        "cvss": 6.0,
    },
    {
        "cve_id": "CVE-2024-22222",
        "title": "Docker Container Escape",
        "vendor": "Docker",
        "product": "Docker Engine",
        "severity": "HIGH",
        "cvss": 8.0,
    },
]

# Sample assets/hosts
SAMPLE_ASSETS = [
    {"id": "i-0abc123def456", "name": "prod-web-01", "type": "EC2", "ip": "10.0.1.10"},
    {"id": "i-0def456abc789", "name": "prod-web-02", "type": "EC2", "ip": "10.0.1.11"},
    {"id": "i-0ghi789jkl012", "name": "prod-db-01", "type": "EC2", "ip": "10.0.2.10"},
    {"id": "i-0mno345pqr678", "name": "prod-app-01", "type": "EC2", "ip": "10.0.3.10"},
    {"id": "i-0stu901vwx234", "name": "dev-web-01", "type": "EC2", "ip": "10.1.1.10"},
    {"id": "srv-dc01", "name": "DC01", "type": "Windows Server", "ip": "10.0.0.10"},
    {"id": "srv-dc02", "name": "DC02", "type": "Windows Server", "ip": "10.0.0.11"},
    {"id": "srv-exch01", "name": "EXCH01", "type": "Exchange Server", "ip": "10.0.0.20"},
    {"id": "srv-file01", "name": "FILE01", "type": "Windows Server", "ip": "10.0.0.30"},
    {"id": "fw-palo-01", "name": "FW-EDGE-01", "type": "Palo Alto Firewall", "ip": "10.0.0.1"},
    {"id": "srv-linux-01", "name": "LINUX-APP-01", "type": "Linux Server", "ip": "10.0.4.10"},
    {"id": "srv-linux-02", "name": "LINUX-DB-01", "type": "Linux Server", "ip": "10.0.4.11"},
]


def generate_sample_scan_results(
    include_kevs: bool = True,
    kev_count: int = 5,
    non_kev_count: int = 10,
    randomize_assets: bool = True
) -> List[Dict[str, Any]]:
    """
    Generate sample vulnerability scan results.
    
    Args:
        include_kevs: Whether to include KEV vulnerabilities
        kev_count: Number of KEVs to include (max 10)
        non_kev_count: Number of non-KEV vulns to include
        randomize_assets: Randomly assign assets to vulnerabilities
        
    Returns:
        List of vulnerability dictionaries
    """
    results = []
    
    # Add KEVs
    if include_kevs:
        kevs_to_add = random.sample(SAMPLE_KEVS, min(kev_count, len(SAMPLE_KEVS)))
        for vuln in kevs_to_add:
            # Assign random assets
            if randomize_assets:
                num_assets = random.randint(1, 4)
                affected_assets = random.sample(SAMPLE_ASSETS, num_assets)
            else:
                affected_assets = [SAMPLE_ASSETS[0]]
            
            results.append({
                **vuln,
                "affected_assets": [a["name"] for a in affected_assets],
                "affected_hosts": [a["ip"] for a in affected_assets],
                "first_seen": (datetime.now() - timedelta(days=random.randint(30, 180))).isoformat(),
                "last_seen": datetime.now().isoformat(),
                "plugin_id": random.randint(10000, 99999),
                "is_kev": True,  # Marked for easy identification
            })
    
    # Add non-KEVs
    non_kevs_to_add = random.sample(SAMPLE_NON_KEVS, min(non_kev_count, len(SAMPLE_NON_KEVS)))
    for vuln in non_kevs_to_add:
        if randomize_assets:
            num_assets = random.randint(1, 3)
            affected_assets = random.sample(SAMPLE_ASSETS, num_assets)
        else:
            affected_assets = [SAMPLE_ASSETS[0]]
        
        results.append({
            **vuln,
            "affected_assets": [a["name"] for a in affected_assets],
            "affected_hosts": [a["ip"] for a in affected_assets],
            "first_seen": (datetime.now() - timedelta(days=random.randint(7, 90))).isoformat(),
            "last_seen": datetime.now().isoformat(),
            "plugin_id": random.randint(10000, 99999),
            "is_kev": False,
        })
    
    # Shuffle results
    random.shuffle(results)
    
    return results


def generate_sample_csv() -> str:
    """Generate sample scan results in CSV format."""
    results = generate_sample_scan_results()
    
    lines = ["CVE ID,Title,Vendor,Product,Severity,CVSS,Affected Assets,First Seen"]
    
    for vuln in results:
        assets = "; ".join(vuln["affected_assets"])
        lines.append(
            f'{vuln["cve_id"]},{vuln["title"]},{vuln["vendor"]},'
            f'{vuln["product"]},{vuln["severity"]},{vuln["cvss"]},"{assets}",{vuln["first_seen"]}'
        )
    
    return "\n".join(lines)


def get_sample_cve_list() -> List[str]:
    """Get just the CVE IDs for quick testing."""
    results = generate_sample_scan_results()
    return [v["cve_id"] for v in results]


def get_kev_only_cves() -> List[str]:
    """Get only the CVE IDs that are KEVs."""
    return [v["cve_id"] for v in SAMPLE_KEVS]


def get_mixed_cves(kev_ratio: float = 0.3) -> List[str]:
    """
    Get a mixed list of CVEs with specified KEV ratio.
    
    Args:
        kev_ratio: Proportion of CVEs that should be KEVs (0.0 to 1.0)
    """
    total = 15
    kev_count = int(total * kev_ratio)
    non_kev_count = total - kev_count
    
    results = generate_sample_scan_results(
        include_kevs=True,
        kev_count=kev_count,
        non_kev_count=non_kev_count
    )
    
    return [v["cve_id"] for v in results]


# Pre-built test scenarios
DEMO_SCENARIOS = {
    "critical_outbreak": {
        "name": "Critical Outbreak",
        "description": "Multiple critical KEVs detected including Log4Shell and ProxyLogon",
        "cves": ["CVE-2021-44228", "CVE-2021-26855", "CVE-2020-1472", "CVE-2023-23397", 
                 "CVE-2023-12345", "CVE-2022-11111"],
    },
    "exchange_compromise": {
        "name": "Exchange Server Compromise",
        "description": "Exchange-related KEVs that could indicate active exploitation",
        "cves": ["CVE-2021-26855", "CVE-2022-41082", "CVE-2023-23397",
                 "CVE-2023-55555", "CVE-2022-99999"],
    },
    "ransomware_indicators": {
        "name": "Ransomware Risk",
        "description": "KEVs commonly used in ransomware campaigns",
        "cves": ["CVE-2021-44228", "CVE-2021-34527", "CVE-2020-1472", 
                 "CVE-2019-19781", "CVE-2024-00001"],
    },
    "clean_scan": {
        "name": "Clean Scan",
        "description": "No KEVs found - only regular vulnerabilities",
        "cves": ["CVE-2023-12345", "CVE-2023-98765", "CVE-2022-11111",
                 "CVE-2024-00001", "CVE-2023-55555"],
    },
    "mixed_findings": {
        "name": "Mixed Findings",
        "description": "Typical scan with some KEVs among regular vulnerabilities",
        "cves": ["CVE-2021-44228", "CVE-2023-27350", "CVE-2023-12345",
                 "CVE-2023-98765", "CVE-2022-11111", "CVE-2024-00001",
                 "CVE-2023-55555", "CVE-2022-99999", "CVE-2023-77777"],
    },
}


if __name__ == "__main__":
    print("Sample Vulnerability Data Generator")
    print("=" * 50)
    
    # Show sample data
    results = generate_sample_scan_results(kev_count=3, non_kev_count=5)
    
    print(f"\nGenerated {len(results)} sample vulnerabilities:")
    print("-" * 50)
    
    for vuln in results:
        kev_marker = "[KEV]" if vuln.get("is_kev") else "     "
        print(f"{kev_marker} {vuln['cve_id']}: {vuln['title'][:40]}...")
        print(f"        Assets: {', '.join(vuln['affected_assets'])}")
    
    print("\n" + "=" * 50)
    print("Demo Scenarios Available:")
    for key, scenario in DEMO_SCENARIOS.items():
        print(f"  - {scenario['name']}: {len(scenario['cves'])} CVEs")

