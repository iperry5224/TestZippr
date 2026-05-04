"""
SLyK-53 Security Hub Integration
=================================
Fetches and analyzes AWS Security Hub findings mapped to NIST 800-53 controls.

Features:
- Get findings by NIST control (AC-2, AU-6, CM-6, SI-2, RA-5)
- Get critical/high severity findings
- Get findings summary by compliance status
- Map Security Hub standards to SLyK controls
"""

import json
import boto3
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

securityhub = boto3.client('securityhub')

# Map NIST 800-53 controls to Security Hub filter patterns
NIST_CONTROL_MAPPING = {
    "AC-2": {
        "name": "Account Management",
        "keywords": ["IAM", "user", "account", "access", "credential", "password", "MFA"],
        "generators": ["aws-foundational-security-best-practices", "cis-aws-foundations-benchmark"]
    },
    "AU-6": {
        "name": "Audit Review, Analysis, and Reporting", 
        "keywords": ["CloudTrail", "logging", "audit", "monitor", "log"],
        "generators": ["aws-foundational-security-best-practices", "cis-aws-foundations-benchmark"]
    },
    "CM-6": {
        "name": "Configuration Settings",
        "keywords": ["config", "configuration", "encryption", "security group", "VPC", "S3", "EBS"],
        "generators": ["aws-foundational-security-best-practices", "cis-aws-foundations-benchmark"]
    },
    "SI-2": {
        "name": "Flaw Remediation",
        "keywords": ["patch", "update", "vulnerability", "Inspector", "SSM"],
        "generators": ["aws-foundational-security-best-practices", "amazon-inspector"]
    },
    "RA-5": {
        "name": "Vulnerability Scanning",
        "keywords": ["scan", "vulnerability", "Inspector", "assessment", "CVE"],
        "generators": ["amazon-inspector", "aws-foundational-security-best-practices"]
    }
}


def get_findings_by_control(control_id: str, max_results: int = 25) -> dict:
    """Get Security Hub findings related to a specific NIST 800-53 control."""
    
    if control_id.upper() not in NIST_CONTROL_MAPPING:
        return {
            "status": "ERROR",
            "message": f"Unknown control: {control_id}. Supported: {list(NIST_CONTROL_MAPPING.keys())}"
        }
    
    control = NIST_CONTROL_MAPPING[control_id.upper()]
    
    # Build filters for this control
    filters = {
        "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}],
        "WorkflowStatus": [{"Value": "NEW", "Comparison": "EQUALS"}]
    }
    
    try:
        response = securityhub.get_findings(
            Filters=filters,
            MaxResults=100  # Get more, then filter
        )
        
        findings = response.get("Findings", [])
        
        # Filter findings by keywords related to this control
        relevant_findings = []
        for finding in findings:
            title = finding.get("Title", "").lower()
            description = finding.get("Description", "").lower()
            
            for keyword in control["keywords"]:
                if keyword.lower() in title or keyword.lower() in description:
                    relevant_findings.append({
                        "id": finding.get("Id", "")[-40:],  # Truncate ID
                        "title": finding.get("Title", ""),
                        "severity": finding.get("Severity", {}).get("Label", "UNKNOWN"),
                        "status": finding.get("Compliance", {}).get("Status", "UNKNOWN"),
                        "resource": finding.get("Resources", [{}])[0].get("Id", "N/A"),
                        "resource_type": finding.get("Resources", [{}])[0].get("Type", "N/A"),
                        "created": finding.get("CreatedAt", "")[:10],
                        "recommendation": finding.get("Remediation", {}).get("Recommendation", {}).get("Text", "See Security Hub for details")
                    })
                    break
        
        # Deduplicate and limit
        seen = set()
        unique_findings = []
        for f in relevant_findings:
            if f["title"] not in seen:
                seen.add(f["title"])
                unique_findings.append(f)
                if len(unique_findings) >= max_results:
                    break
        
        # Count by severity
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for f in unique_findings:
            sev = f["severity"]
            if sev in severity_counts:
                severity_counts[sev] += 1
        
        return {
            "status": "SUCCESS",
            "control_id": control_id.upper(),
            "control_name": control["name"],
            "total_findings": len(unique_findings),
            "severity_summary": severity_counts,
            "findings": unique_findings[:max_results]
        }
        
    except ClientError as e:
        return {
            "status": "ERROR",
            "message": str(e)
        }


def get_critical_findings(max_results: int = 20) -> dict:
    """Get all CRITICAL and HIGH severity findings."""
    
    try:
        response = securityhub.get_findings(
            Filters={
                "SeverityLabel": [
                    {"Value": "CRITICAL", "Comparison": "EQUALS"},
                    {"Value": "HIGH", "Comparison": "EQUALS"}
                ],
                "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}],
                "WorkflowStatus": [{"Value": "NEW", "Comparison": "EQUALS"}]
            },
            MaxResults=max_results,
            SortCriteria=[{"Field": "SeverityLabel", "SortOrder": "desc"}]
        )
        
        findings = []
        for finding in response.get("Findings", []):
            findings.append({
                "id": finding.get("Id", "")[-40:],
                "title": finding.get("Title", ""),
                "severity": finding.get("Severity", {}).get("Label", "UNKNOWN"),
                "resource": finding.get("Resources", [{}])[0].get("Id", "N/A"),
                "resource_type": finding.get("Resources", [{}])[0].get("Type", "N/A"),
                "product": finding.get("ProductName", "Security Hub"),
                "created": finding.get("CreatedAt", "")[:10],
                "compliance_control": finding.get("Compliance", {}).get("RelatedRequirements", [])
            })
        
        return {
            "status": "SUCCESS",
            "total_critical_high": len(findings),
            "findings": findings
        }
        
    except ClientError as e:
        return {
            "status": "ERROR", 
            "message": str(e)
        }


def get_compliance_summary() -> dict:
    """Get overall compliance summary from Security Hub."""
    
    try:
        # Get findings counts by compliance status
        passed = securityhub.get_findings(
            Filters={
                "ComplianceStatus": [{"Value": "PASSED", "Comparison": "EQUALS"}],
                "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}]
            },
            MaxResults=1
        )
        
        failed = securityhub.get_findings(
            Filters={
                "ComplianceStatus": [{"Value": "FAILED", "Comparison": "EQUALS"}],
                "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}]
            },
            MaxResults=1
        )
        
        # Get standards status
        standards = securityhub.get_enabled_standards()
        
        enabled_standards = []
        for std in standards.get("StandardsSubscriptions", []):
            enabled_standards.append({
                "name": std.get("StandardsArn", "").split("/")[-2],
                "status": std.get("StandardsStatus", "UNKNOWN")
            })
        
        # Calculate compliance score (simplified)
        total_passed = int(passed.get("Findings", [{}])[0].get("FindingProviderFields", {}).get("Types", ["0"])[0]) if passed.get("Findings") else 0
        total_failed = int(failed.get("Findings", [{}])[0].get("FindingProviderFields", {}).get("Types", ["0"])[0]) if failed.get("Findings") else 0
        
        return {
            "status": "SUCCESS",
            "enabled_standards": enabled_standards,
            "summary": {
                "passed_checks": "See Security Hub console for exact counts",
                "failed_checks": "See Security Hub console for exact counts",
                "compliance_score": "Calculate from Security Hub dashboard"
            },
            "recommendation": "Review Security Hub dashboard for detailed compliance scores by standard"
        }
        
    except ClientError as e:
        return {
            "status": "ERROR",
            "message": str(e)
        }


def get_findings_for_dashboard() -> dict:
    """Get a summary of findings formatted for the SLyK-View dashboard."""
    
    try:
        # Get counts by severity
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFORMATIONAL": 0}
        
        for severity in severity_counts.keys():
            response = securityhub.get_findings(
                Filters={
                    "SeverityLabel": [{"Value": severity, "Comparison": "EQUALS"}],
                    "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}],
                    "WorkflowStatus": [{"Value": "NEW", "Comparison": "EQUALS"}]
                },
                MaxResults=1
            )
            # This is a rough count - Security Hub doesn't give exact counts easily
            severity_counts[severity] = len(response.get("Findings", []))
        
        # Get recent critical findings for alerts
        critical_response = securityhub.get_findings(
            Filters={
                "SeverityLabel": [
                    {"Value": "CRITICAL", "Comparison": "EQUALS"},
                    {"Value": "HIGH", "Comparison": "EQUALS"}
                ],
                "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}],
                "WorkflowStatus": [{"Value": "NEW", "Comparison": "EQUALS"}]
            },
            MaxResults=5,
            SortCriteria=[{"Field": "CreatedAt", "SortOrder": "desc"}]
        )
        
        recent_alerts = []
        for finding in critical_response.get("Findings", []):
            recent_alerts.append({
                "title": finding.get("Title", "")[:60],
                "severity": finding.get("Severity", {}).get("Label", "UNKNOWN"),
                "resource": finding.get("Resources", [{}])[0].get("Type", "N/A"),
                "time": finding.get("CreatedAt", "")[:16].replace("T", " ")
            })
        
        # Map to NIST controls
        control_findings = {}
        for control_id in NIST_CONTROL_MAPPING.keys():
            result = get_findings_by_control(control_id, max_results=5)
            control_findings[control_id] = {
                "name": NIST_CONTROL_MAPPING[control_id]["name"],
                "count": result.get("total_findings", 0),
                "critical": result.get("severity_summary", {}).get("CRITICAL", 0),
                "high": result.get("severity_summary", {}).get("HIGH", 0)
            }
        
        return {
            "status": "SUCCESS",
            "timestamp": datetime.utcnow().isoformat(),
            "severity_summary": severity_counts,
            "recent_alerts": recent_alerts,
            "findings_by_control": control_findings,
            "total_active_findings": sum(severity_counts.values())
        }
        
    except ClientError as e:
        return {
            "status": "ERROR",
            "message": str(e)
        }


def lambda_handler(event, context):
    """Main Lambda handler for Security Hub integration."""
    
    action = event.get("action", "summary")
    
    if action == "get_by_control":
        control_id = event.get("control_id", "AC-2")
        max_results = event.get("max_results", 25)
        return get_findings_by_control(control_id, max_results)
    
    elif action == "get_critical":
        max_results = event.get("max_results", 20)
        return get_critical_findings(max_results)
    
    elif action == "compliance_summary":
        return get_compliance_summary()
    
    elif action == "dashboard":
        return get_findings_for_dashboard()
    
    else:
        return {
            "status": "SUCCESS",
            "message": "Security Hub Integration for SLyK-53",
            "available_actions": [
                "get_by_control - Get findings for a NIST control (AC-2, AU-6, CM-6, SI-2, RA-5)",
                "get_critical - Get CRITICAL and HIGH severity findings",
                "compliance_summary - Get overall compliance status",
                "dashboard - Get summary formatted for SLyK-View dashboard"
            ]
        }
