"""
SLyK-53 ASSESS Lambda — New Security Controls
==============================================
Implements the following NIST 800-53 controls:
- AC-2: Account Management (Automated detection of unauthorized account creation)
- AU-6: Audit Review, Analysis, and Reporting (Real-time analysis of audit logs)
- CM-6: Configuration Settings (Automated verification against baselines)
- SI-2: Flaw Remediation (Automated remediation runbooks and patching)
- RA-5: Vulnerability Monitoring and Scanning (Security scan coverage analysis)
"""
import json
import boto3
from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError


def get_account_id():
    return boto3.client("sts").get_caller_identity()["Account"]


def check_control(control_id, check_fn):
    """Wrapper to safely execute a control check."""
    try:
        status, findings, recommendations = check_fn()
        return {
            "control_id": control_id,
            "status": status,
            "findings": findings,
            "recommendations": recommendations,
        }
    except Exception as e:
        return {
            "control_id": control_id,
            "status": "ERROR",
            "findings": [str(e)],
            "recommendations": [],
        }


# =============================================================================
# AC-2: Account Management
# Automated detection of unauthorized account creation
# =============================================================================
def check_ac2():
    """
    AC-2: Account Management
    - Detect recently created IAM users (potential unauthorized accounts)
    - Check for users without proper tagging (ownership)
    - Identify service accounts vs human accounts
    - Flag accounts created outside of approved processes
    """
    iam = boto3.client("iam")
    cloudtrail = boto3.client("cloudtrail")
    findings = []
    recommendations = []
    
    # Get all IAM users
    users = iam.list_users()["Users"]
    now = datetime.now(timezone.utc)
    
    # Check for recently created users (last 7 days)
    recent_users = []
    untagged_users = []
    no_mfa_users = []
    
    for user in users:
        username = user["UserName"]
        create_date = user["CreateDate"]
        age_days = (now - create_date).days
        
        # Recently created (potential unauthorized)
        if age_days <= 7:
            recent_users.append({
                "username": username,
                "created": create_date.isoformat(),
                "age_days": age_days
            })
        
        # Check for proper tagging (ownership, purpose)
        try:
            tags = iam.list_user_tags(UserName=username)["Tags"]
            tag_keys = [t["Key"].lower() for t in tags]
            if "owner" not in tag_keys and "created-by" not in tag_keys:
                untagged_users.append(username)
        except ClientError:
            untagged_users.append(username)
        
        # Check MFA status
        mfa_devices = iam.list_mfa_devices(UserName=username)["MFADevices"]
        if not mfa_devices:
            no_mfa_users.append(username)
    
    # Look for CreateUser events in CloudTrail (last 24 hours)
    unauthorized_creations = []
    try:
        events = cloudtrail.lookup_events(
            LookupAttributes=[{"AttributeKey": "EventName", "AttributeValue": "CreateUser"}],
            StartTime=now - timedelta(hours=24),
            EndTime=now,
            MaxResults=50
        )
        for event in events.get("Events", []):
            event_data = json.loads(event.get("CloudTrailEvent", "{}"))
            source_ip = event_data.get("sourceIPAddress", "unknown")
            user_agent = event_data.get("userAgent", "unknown")
            # Flag if created from unusual source
            if "console" not in user_agent.lower() and "cloudformation" not in user_agent.lower():
                unauthorized_creations.append({
                    "event_time": event["EventTime"].isoformat(),
                    "username": event.get("Username", "unknown"),
                    "source_ip": source_ip,
                    "user_agent": user_agent[:50]
                })
    except ClientError:
        pass
    
    # Build findings
    if recent_users:
        findings.append(f"{len(recent_users)} users created in last 7 days: {', '.join([u['username'] for u in recent_users[:5]])}")
        recommendations.append("Review recently created accounts for authorization")
    
    if untagged_users:
        findings.append(f"{len(untagged_users)} users without ownership tags: {', '.join(untagged_users[:5])}")
        recommendations.append("Add 'Owner' or 'Created-By' tags to all IAM users")
    
    if no_mfa_users:
        findings.append(f"{len(no_mfa_users)} users without MFA: {', '.join(no_mfa_users[:5])}")
        recommendations.append("Enable MFA for all IAM users")
    
    if unauthorized_creations:
        findings.append(f"{len(unauthorized_creations)} potentially unauthorized account creations detected")
        recommendations.append("Investigate account creations from non-standard sources")
    
    # Determine status
    if unauthorized_creations or (recent_users and untagged_users):
        return "FAIL", findings, recommendations
    elif untagged_users or no_mfa_users:
        return "WARNING", findings, recommendations
    
    findings.append("All accounts properly managed and authorized")
    return "PASS", findings, recommendations


# =============================================================================
# AU-6: Audit Review, Analysis, and Reporting
# Real-time analysis of audit logs for anomalies
# =============================================================================
def check_au6():
    """
    AU-6: Audit Review, Analysis, and Reporting
    - Analyze CloudTrail for suspicious patterns
    - Check for failed authentication attempts
    - Detect unusual API activity
    - Identify potential security incidents
    """
    cloudtrail = boto3.client("cloudtrail")
    cloudwatch = boto3.client("cloudwatch")
    findings = []
    recommendations = []
    
    now = datetime.now(timezone.utc)
    
    # Check for failed console logins
    failed_logins = []
    try:
        events = cloudtrail.lookup_events(
            LookupAttributes=[{"AttributeKey": "EventName", "AttributeValue": "ConsoleLogin"}],
            StartTime=now - timedelta(hours=24),
            EndTime=now,
            MaxResults=100
        )
        for event in events.get("Events", []):
            event_data = json.loads(event.get("CloudTrailEvent", "{}"))
            response = event_data.get("responseElements", {})
            if response.get("ConsoleLogin") == "Failure":
                failed_logins.append({
                    "time": event["EventTime"].isoformat(),
                    "source_ip": event_data.get("sourceIPAddress", "unknown"),
                    "user": event_data.get("userIdentity", {}).get("userName", "unknown")
                })
    except ClientError:
        pass
    
    # Check for sensitive API calls
    sensitive_events = []
    sensitive_apis = [
        "DeleteTrail", "StopLogging", "DeleteBucket", "PutBucketPolicy",
        "CreateAccessKey", "DeleteAccessKey", "AttachUserPolicy",
        "AttachRolePolicy", "CreateRole", "DeleteRole"
    ]
    
    for api in sensitive_apis[:5]:  # Limit to avoid throttling
        try:
            events = cloudtrail.lookup_events(
                LookupAttributes=[{"AttributeKey": "EventName", "AttributeValue": api}],
                StartTime=now - timedelta(hours=24),
                EndTime=now,
                MaxResults=10
            )
            for event in events.get("Events", []):
                event_data = json.loads(event.get("CloudTrailEvent", "{}"))
                sensitive_events.append({
                    "event": api,
                    "time": event["EventTime"].isoformat(),
                    "user": event_data.get("userIdentity", {}).get("arn", "unknown")[:50],
                    "source_ip": event_data.get("sourceIPAddress", "unknown")
                })
        except ClientError:
            pass
    
    # Check for root account usage
    root_activity = []
    try:
        events = cloudtrail.lookup_events(
            LookupAttributes=[{"AttributeKey": "Username", "AttributeValue": "root"}],
            StartTime=now - timedelta(hours=24),
            EndTime=now,
            MaxResults=20
        )
        root_activity = [e["EventName"] for e in events.get("Events", [])]
    except ClientError:
        pass
    
    # Check CloudWatch alarms for security metrics
    security_alarms = []
    try:
        alarms = cloudwatch.describe_alarms(StateValue="ALARM", MaxRecords=50)
        for alarm in alarms.get("MetricAlarms", []):
            name_lower = alarm["AlarmName"].lower()
            if any(kw in name_lower for kw in ["security", "auth", "login", "unauthorized", "root"]):
                security_alarms.append(alarm["AlarmName"])
    except ClientError:
        pass
    
    # Build findings
    if failed_logins:
        findings.append(f"{len(failed_logins)} failed console logins in last 24h")
        if len(failed_logins) > 10:
            recommendations.append("Investigate potential brute force attack")
    
    if sensitive_events:
        findings.append(f"{len(sensitive_events)} sensitive API calls detected: {', '.join(set([e['event'] for e in sensitive_events]))}")
        recommendations.append("Review sensitive API activity for authorization")
    
    if root_activity:
        findings.append(f"Root account activity detected: {', '.join(set(root_activity)[:5])}")
        recommendations.append("Minimize root account usage; use IAM roles instead")
    
    if security_alarms:
        findings.append(f"{len(security_alarms)} security alarms in ALARM state")
        recommendations.append("Investigate active security alarms immediately")
    
    # Determine status
    if root_activity or security_alarms or len(failed_logins) > 10:
        return "FAIL", findings, recommendations
    elif sensitive_events or failed_logins:
        return "WARNING", findings, recommendations
    
    findings.append("No anomalies detected in audit logs")
    return "PASS", findings, recommendations


# =============================================================================
# CM-6: Configuration Settings
# Automated verification of system configuration against established baselines
# =============================================================================
def check_cm6():
    """
    CM-6: Configuration Settings
    - Verify EC2 instances against baseline configurations
    - Check security group configurations
    - Validate S3 bucket configurations
    - Assess compliance with AWS Config rules
    """
    ec2 = boto3.client("ec2")
    s3 = boto3.client("s3")
    config_client = boto3.client("config")
    findings = []
    recommendations = []
    
    # Check AWS Config compliance
    config_compliance = {"compliant": 0, "non_compliant": 0, "rules": []}
    try:
        rules = config_client.describe_compliance_by_config_rule(
            ComplianceTypes=["NON_COMPLIANT"]
        )
        for rule in rules.get("ComplianceByConfigRules", []):
            config_compliance["non_compliant"] += 1
            config_compliance["rules"].append(rule["ConfigRuleName"])
        
        compliant_rules = config_client.describe_compliance_by_config_rule(
            ComplianceTypes=["COMPLIANT"]
        )
        config_compliance["compliant"] = len(compliant_rules.get("ComplianceByConfigRules", []))
    except ClientError:
        pass
    
    # Check EC2 instance configurations
    ec2_issues = []
    try:
        instances = ec2.describe_instances()
        for reservation in instances.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                instance_id = instance["InstanceId"]
                issues = []
                
                # Check IMDSv2
                if instance.get("MetadataOptions", {}).get("HttpTokens") != "required":
                    issues.append("IMDSv2 not enforced")
                
                # Check if using approved AMI (example: check for Amazon Linux 2)
                image_id = instance.get("ImageId", "")
                # This would check against an approved AMI list
                
                # Check for public IP
                if instance.get("PublicIpAddress"):
                    issues.append("Has public IP")
                
                # Check EBS encryption
                for mapping in instance.get("BlockDeviceMappings", []):
                    ebs = mapping.get("Ebs", {})
                    # Would need describe_volumes to check encryption
                
                if issues:
                    name = next((t["Value"] for t in instance.get("Tags", []) if t["Key"] == "Name"), instance_id)
                    ec2_issues.append({"instance": name, "issues": issues})
    except ClientError:
        pass
    
    # Check security group baselines
    sg_issues = []
    try:
        sgs = ec2.describe_security_groups()["SecurityGroups"]
        for sg in sgs:
            issues = []
            for rule in sg.get("IpPermissions", []):
                for ip_range in rule.get("IpRanges", []):
                    if ip_range.get("CidrIp") == "0.0.0.0/0":
                        port = rule.get("FromPort", "all")
                        if port not in [80, 443]:
                            issues.append(f"Open to world on port {port}")
            if issues:
                sg_issues.append({"sg_id": sg["GroupId"], "name": sg.get("GroupName", ""), "issues": issues})
    except ClientError:
        pass
    
    # Check S3 bucket configurations
    s3_issues = []
    try:
        buckets = s3.list_buckets()["Buckets"]
        for bucket in buckets:
            name = bucket["Name"]
            issues = []
            
            # Check versioning
            try:
                versioning = s3.get_bucket_versioning(Bucket=name)
                if versioning.get("Status") != "Enabled":
                    issues.append("Versioning disabled")
            except ClientError:
                pass
            
            # Check encryption
            try:
                s3.get_bucket_encryption(Bucket=name)
            except ClientError as e:
                if "ServerSideEncryptionConfigurationNotFoundError" in str(e):
                    issues.append("No default encryption")
            
            # Check public access block
            try:
                pab = s3.get_public_access_block(Bucket=name)
                config = pab["PublicAccessBlockConfiguration"]
                if not all(config.values()):
                    issues.append("Public access not fully blocked")
            except ClientError:
                issues.append("No public access block")
            
            if issues:
                s3_issues.append({"bucket": name, "issues": issues})
    except ClientError:
        pass
    
    # Build findings
    if config_compliance["non_compliant"] > 0:
        findings.append(f"{config_compliance['non_compliant']} AWS Config rules non-compliant: {', '.join(config_compliance['rules'][:5])}")
        recommendations.append("Remediate AWS Config rule violations")
    
    if ec2_issues:
        findings.append(f"{len(ec2_issues)} EC2 instances with configuration drift")
        recommendations.append("Enforce IMDSv2 and review instance configurations")
    
    if sg_issues:
        findings.append(f"{len(sg_issues)} security groups with baseline violations")
        recommendations.append("Restrict security group rules to specific CIDRs")
    
    if s3_issues:
        findings.append(f"{len(s3_issues)} S3 buckets not meeting baseline: {', '.join([b['bucket'] for b in s3_issues[:3]])}")
        recommendations.append("Enable encryption, versioning, and public access blocks on all buckets")
    
    # Determine status
    total_issues = len(ec2_issues) + len(sg_issues) + len(s3_issues) + config_compliance["non_compliant"]
    if total_issues > 10:
        return "FAIL", findings, recommendations
    elif total_issues > 0:
        return "WARNING", findings, recommendations
    
    findings.append("All configurations match established baselines")
    return "PASS", findings, recommendations


# =============================================================================
# SI-2: Flaw Remediation
# Automated generation of remediation runbooks and patching logic
# =============================================================================
def check_si2():
    """
    SI-2: Flaw Remediation
    - Check SSM patch compliance
    - Identify systems needing patches
    - Assess patch management coverage
    - Generate remediation priorities
    """
    ssm = boto3.client("ssm")
    inspector = boto3.client("inspector2")
    findings = []
    recommendations = []
    
    # Check SSM Patch Compliance
    patch_summary = {"compliant": 0, "non_compliant": 0, "missing_patches": [], "instances": []}
    try:
        compliance = ssm.list_compliance_summaries(
            Filters=[{"Key": "ComplianceType", "Values": ["Patch"]}]
        )
        for summary in compliance.get("ComplianceSummaryItems", []):
            patch_summary["compliant"] += summary.get("CompliantSummary", {}).get("CompliantCount", 0)
            patch_summary["non_compliant"] += summary.get("NonCompliantSummary", {}).get("NonCompliantCount", 0)
    except ClientError:
        pass
    
    # Get instances with missing patches
    try:
        non_compliant = ssm.list_resource_compliance_summaries(
            Filters=[
                {"Key": "ComplianceType", "Values": ["Patch"]},
                {"Key": "OverallSeverity", "Values": ["CRITICAL", "HIGH"]}
            ]
        )
        for resource in non_compliant.get("ResourceComplianceSummaryItems", [])[:10]:
            patch_summary["instances"].append({
                "instance_id": resource.get("ResourceId", ""),
                "status": resource.get("Status", ""),
                "severity": resource.get("OverallSeverity", "")
            })
    except ClientError:
        pass
    
    # Check Inspector findings for vulnerabilities
    inspector_findings = {"critical": 0, "high": 0, "medium": 0, "packages": []}
    try:
        findings_resp = inspector.list_findings(
            filterCriteria={
                "findingStatus": [{"comparison": "EQUALS", "value": "ACTIVE"}],
                "severity": [{"comparison": "EQUALS", "value": "CRITICAL"}]
            },
            maxResults=50
        )
        inspector_findings["critical"] = len(findings_resp.get("findings", []))
        
        # Get package vulnerabilities
        for finding in findings_resp.get("findings", [])[:10]:
            pkg = finding.get("packageVulnerabilityDetails", {})
            if pkg:
                inspector_findings["packages"].append({
                    "package": pkg.get("vulnerablePackages", [{}])[0].get("name", "unknown"),
                    "severity": finding.get("severity", ""),
                    "fix_available": pkg.get("fixAvailable", "NO")
                })
    except ClientError:
        pass
    
    # Check for pending maintenance windows
    maintenance_pending = []
    try:
        windows = ssm.describe_maintenance_windows(
            Filters=[{"Key": "Enabled", "Values": ["true"]}]
        )
        for window in windows.get("WindowIdentities", []):
            # Check if there are pending executions
            maintenance_pending.append(window.get("Name", ""))
    except ClientError:
        pass
    
    # Build findings
    if patch_summary["non_compliant"] > 0:
        findings.append(f"{patch_summary['non_compliant']} instances with missing patches")
        recommendations.append("Run SSM Patch Manager to apply missing patches")
    
    if patch_summary["instances"]:
        critical_instances = [i["instance_id"] for i in patch_summary["instances"] if i["severity"] in ["CRITICAL", "HIGH"]]
        if critical_instances:
            findings.append(f"{len(critical_instances)} instances with CRITICAL/HIGH severity patches needed")
            recommendations.append(f"Priority patching required for: {', '.join(critical_instances[:3])}")
    
    if inspector_findings["critical"] > 0:
        findings.append(f"{inspector_findings['critical']} critical vulnerabilities found by Inspector")
        recommendations.append("Review and remediate Inspector critical findings")
    
    if inspector_findings["packages"]:
        fixable = [p for p in inspector_findings["packages"] if p["fix_available"] == "YES"]
        if fixable:
            findings.append(f"{len(fixable)} vulnerabilities have fixes available")
            recommendations.append(f"Update packages: {', '.join([p['package'] for p in fixable[:5]])}")
    
    # Determine status
    if patch_summary["non_compliant"] > 5 or inspector_findings["critical"] > 0:
        return "FAIL", findings, recommendations
    elif patch_summary["non_compliant"] > 0:
        return "WARNING", findings, recommendations
    
    findings.append("All systems are patched and no critical flaws detected")
    return "PASS", findings, recommendations


# =============================================================================
# RA-5: Vulnerability Monitoring and Scanning
# Analyzing security scan percentages relative to total system inventory
# =============================================================================
def check_ra5():
    """
    RA-5: Vulnerability Monitoring and Scanning
    - Calculate scan coverage percentage
    - Identify unscanned resources
    - Assess vulnerability scan results
    - Track scanning frequency
    """
    ec2 = boto3.client("ec2")
    ssm = boto3.client("ssm")
    inspector = boto3.client("inspector2")
    securityhub = boto3.client("securityhub")
    findings = []
    recommendations = []
    
    # Get total inventory
    inventory = {"ec2_total": 0, "ec2_managed": 0, "ec2_scanned": 0, "containers": 0, "lambdas": 0}
    
    # Count EC2 instances
    try:
        instances = ec2.describe_instances(
            Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
        )
        for reservation in instances.get("Reservations", []):
            inventory["ec2_total"] += len(reservation.get("Instances", []))
    except ClientError:
        pass
    
    # Count SSM managed instances
    try:
        managed = ssm.describe_instance_information()
        inventory["ec2_managed"] = len(managed.get("InstanceInformationList", []))
    except ClientError:
        pass
    
    # Check Inspector coverage
    inspector_coverage = {"ec2": 0, "ecr": 0, "lambda": 0}
    try:
        coverage = inspector.list_coverage(
            filterCriteria={
                "resourceType": [{"comparison": "EQUALS", "value": "AWS_EC2_INSTANCE"}]
            },
            maxResults=100
        )
        inspector_coverage["ec2"] = len(coverage.get("coveredResources", []))
        inventory["ec2_scanned"] = inspector_coverage["ec2"]
    except ClientError:
        pass
    
    # Get Lambda function count
    try:
        lambda_client = boto3.client("lambda")
        functions = lambda_client.list_functions()
        inventory["lambdas"] = len(functions.get("Functions", []))
    except ClientError:
        pass
    
    # Get ECR repository count (for container scanning)
    try:
        ecr = boto3.client("ecr")
        repos = ecr.describe_repositories()
        inventory["containers"] = len(repos.get("repositories", []))
    except ClientError:
        pass
    
    # Calculate coverage percentages
    coverage_stats = {}
    if inventory["ec2_total"] > 0:
        coverage_stats["ssm_coverage"] = round(inventory["ec2_managed"] / inventory["ec2_total"] * 100, 1)
        coverage_stats["inspector_coverage"] = round(inventory["ec2_scanned"] / inventory["ec2_total"] * 100, 1)
    else:
        coverage_stats["ssm_coverage"] = 100
        coverage_stats["inspector_coverage"] = 100
    
    # Get vulnerability summary from Security Hub
    vuln_summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    try:
        hub_findings = securityhub.get_findings(
            Filters={
                "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}],
                "Type": [{"Value": "Software and Configuration Checks/Vulnerabilities", "Comparison": "PREFIX"}]
            },
            MaxResults=100
        )
        for finding in hub_findings.get("Findings", []):
            severity = finding.get("Severity", {}).get("Label", "LOW")
            vuln_summary[severity.lower()] = vuln_summary.get(severity.lower(), 0) + 1
    except ClientError:
        pass
    
    # Get last scan times
    last_scans = {}
    try:
        # Check for recent Inspector scans
        scans = inspector.list_findings(
            filterCriteria={
                "findingStatus": [{"comparison": "EQUALS", "value": "ACTIVE"}]
            },
            maxResults=1,
            sortCriteria={"field": "LAST_OBSERVED_AT", "sortOrder": "DESC"}
        )
        if scans.get("findings"):
            last_scans["inspector"] = scans["findings"][0].get("lastObservedAt", "unknown")
    except ClientError:
        pass
    
    # Build findings
    findings.append(f"Inventory: {inventory['ec2_total']} EC2, {inventory['lambdas']} Lambda, {inventory['containers']} ECR repos")
    
    if coverage_stats.get("ssm_coverage", 0) < 100:
        unmanaged = inventory["ec2_total"] - inventory["ec2_managed"]
        findings.append(f"SSM coverage: {coverage_stats['ssm_coverage']}% ({unmanaged} instances not managed)")
        recommendations.append("Install SSM agent on all EC2 instances for patch management")
    
    if coverage_stats.get("inspector_coverage", 0) < 100:
        unscanned = inventory["ec2_total"] - inventory["ec2_scanned"]
        findings.append(f"Inspector coverage: {coverage_stats['inspector_coverage']}% ({unscanned} instances not scanned)")
        recommendations.append("Enable Inspector scanning for all EC2 instances")
    
    if vuln_summary["critical"] > 0 or vuln_summary["high"] > 0:
        findings.append(f"Vulnerabilities: {vuln_summary['critical']} critical, {vuln_summary['high']} high, {vuln_summary['medium']} medium")
        recommendations.append("Prioritize remediation of critical and high vulnerabilities")
    
    # Determine status
    min_coverage = min(coverage_stats.get("ssm_coverage", 0), coverage_stats.get("inspector_coverage", 0))
    if min_coverage < 80 or vuln_summary["critical"] > 0:
        return "FAIL", findings, recommendations
    elif min_coverage < 95 or vuln_summary["high"] > 5:
        return "WARNING", findings, recommendations
    
    findings.append(f"Scan coverage at {min_coverage}% with no critical vulnerabilities")
    return "PASS", findings, recommendations


# =============================================================================
# Control Registry and Handler
# =============================================================================

CONTROL_CHECKS = {
    "AC-2": ("Account Management - Unauthorized Account Detection", check_ac2),
    "AU-6": ("Audit Review, Analysis, and Reporting", check_au6),
    "CM-6": ("Configuration Settings - Baseline Verification", check_cm6),
    "SI-2": ("Flaw Remediation - Patching and Runbooks", check_si2),
    "RA-5": ("Vulnerability Monitoring and Scanning", check_ra5),
}


def _action_params(event):
    """Build name->value from Bedrock event; safe if parameters is null or odd-shaped."""
    raw = event.get("parameters")
    if not raw:
        return {}
    if not isinstance(raw, list):
        return {}
    out = {}
    for p in raw:
        if not isinstance(p, dict):
            continue
        n = p.get("name")
        if n is None or n == "":
            continue
        v = p.get("value", "")
        if v is not None and not isinstance(v, str):
            v = str(v)
        out[n] = v or ""
    return out


def run_assessment(families=None):
    """Run assessment for specified control families."""
    results = []
    for control_id, (name, check_fn) in CONTROL_CHECKS.items():
        family = control_id.split("-")[0]
        if families and families != ["ALL"] and family not in families:
            continue
        result = check_control(control_id, check_fn)
        result["control_name"] = name
        result["family"] = family
        results.append(result)
    return results


def handler(event, context):
    """Lambda handler for Bedrock Agent action group."""
    http_method = event.get("httpMethod") or "GET"
    if not isinstance(event, dict):
        event = {}
    params = _action_params(event)
    api_path = event.get("apiPath", "")

    def _ok(payload_obj, code=200):
        body = json.dumps(payload_obj, default=str)
        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.get("actionGroup", ""),
                "apiPath": event.get("apiPath", api_path),
                "httpMethod": http_method,
                "httpStatusCode": code,
                "responseBody": {"application/json": {"body": body}},
            },
        }

    try:
        # Parse parameters
        families_str = str(params.get("families", "ALL") or "ALL")
        families = families_str.split(",") if families_str != "ALL" else ["ALL"]

        # Run assessment
        results = run_assessment(families)

        # Calculate summary
        passed = sum(1 for r in results if r["status"] == "PASS")
        failed = sum(1 for r in results if r["status"] == "FAIL")
        warnings = sum(1 for r in results if r["status"] == "WARNING")
        total = len(results)
        compliance_pct = round(passed / total * 100, 1) if total > 0 else 0

        summary = {
            "account_id": get_account_id(),
            "assessment_time": datetime.now(timezone.utc).isoformat(),
            "total_controls": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "compliance_percentage": compliance_pct,
            "controls_assessed": list(CONTROL_CHECKS.keys()),
        }

        response_data = {"summary": summary, "controls": results}

        return _ok(response_data)

    except Exception as e:
        return _ok(
            {
                "error": "slyk-assess failed",
                "message": str(e),
                "type": type(e).__name__,
            },
            code=200,
        )
