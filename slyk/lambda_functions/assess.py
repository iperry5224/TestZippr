"""SLyK-53 ASSESS Lambda — NIST 800-53 compliance assessment."""
import json
import boto3
from botocore.exceptions import ClientError


def get_account_id():
    return boto3.client("sts").get_caller_identity()["Account"]


def check_control(control_id, check_fn):
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


def check_ac2():
    iam = boto3.client("iam")
    findings, recs = [], []
    users = iam.list_users()["Users"]
    mfa_missing = []
    for u in users:
        mfa = iam.list_mfa_devices(UserName=u["UserName"])["MFADevices"]
        if not mfa:
            mfa_missing.append(u["UserName"])
    if mfa_missing:
        findings.append(f"{len(mfa_missing)} users without MFA: {', '.join(mfa_missing[:5])}")
        recs.append("Enable MFA for all IAM users")
        return "FAIL", findings, recs
    findings.append("All IAM users have MFA enabled")
    return "PASS", findings, recs


def check_ac6():
    iam = boto3.client("iam")
    findings, recs = [], []
    policies = iam.list_policies(Scope="Local", OnlyAttached=True)["Policies"]
    admin_policies = []
    for p in policies[:20]:
        ver = iam.get_policy_version(PolicyArn=p["Arn"], VersionId=p["DefaultVersionId"])
        doc = ver["PolicyVersion"]["Document"]
        stmts = doc.get("Statement", []) if isinstance(doc, dict) else []
        for s in stmts:
            if s.get("Effect") == "Allow" and s.get("Action") == "*" and s.get("Resource") == "*":
                admin_policies.append(p["PolicyName"])
    if admin_policies:
        findings.append(f"{len(admin_policies)} overly permissive policies: {', '.join(admin_policies[:3])}")
        recs.append("Apply least privilege — remove Action:* Resource:* policies")
        return "FAIL", findings, recs
    findings.append("No overly permissive custom policies found")
    return "PASS", findings, recs


def check_au2():
    ct = boto3.client("cloudtrail")
    findings, recs = [], []
    trails = ct.describe_trails()["trailList"]
    if not trails:
        return "FAIL", ["No CloudTrail trails configured"], ["Enable CloudTrail"]
    active = [t for t in trails if ct.get_trail_status(Name=t["TrailARN"]).get("IsLogging")]
    if not active:
        return "FAIL", ["CloudTrail exists but not logging"], ["Start CloudTrail logging"]
    findings.append(f"{len(active)} active CloudTrail trail(s)")
    return "PASS", findings, recs


def check_ia2():
    iam = boto3.client("iam")
    findings, recs = [], []
    summary = iam.get_account_summary()["SummaryMap"]
    if summary.get("AccountMFAEnabled", 0) == 0:
        findings.append("Root account MFA not enabled")
        recs.append("Enable MFA on root account immediately")
        return "FAIL", findings, recs
    findings.append("Root account MFA enabled")
    return "PASS", findings, recs


def check_sc7():
    ec2 = boto3.client("ec2")
    findings, recs = [], []
    sgs = ec2.describe_security_groups()["SecurityGroups"]
    open_sgs = []
    for sg in sgs:
        for rule in sg.get("IpPermissions", []):
            for ip_range in rule.get("IpRanges", []):
                if ip_range.get("CidrIp") == "0.0.0.0/0" and rule.get("FromPort") not in [80, 443]:
                    open_sgs.append(f"{sg['GroupId']} (port {rule.get('FromPort', 'all')})")
    if open_sgs:
        findings.append(f"{len(open_sgs)} security groups with unrestricted access: {', '.join(open_sgs[:3])}")
        recs.append("Restrict security group rules to specific CIDRs")
        return "WARNING", findings, recs
    findings.append("No overly permissive security groups found")
    return "PASS", findings, recs


def check_sc28():
    s3 = boto3.client("s3")
    findings, recs = [], []
    buckets = s3.list_buckets()["Buckets"]
    unencrypted = []
    for b in buckets:
        try:
            s3.get_bucket_encryption(Bucket=b["Name"])
        except ClientError:
            unencrypted.append(b["Name"])
    if unencrypted:
        findings.append(f"{len(unencrypted)} S3 buckets without encryption: {', '.join(unencrypted[:3])}")
        recs.append("Enable default encryption (SSE-S3 or SSE-KMS) on all buckets")
        return "FAIL", findings, recs
    findings.append("All S3 buckets have default encryption enabled")
    return "PASS", findings, recs


def check_si4():
    findings, recs = [], []
    try:
        gd = boto3.client("guardduty")
        detectors = gd.list_detectors()["DetectorIds"]
        if detectors:
            findings.append(f"GuardDuty enabled (detector: {detectors[0][:12]}...)")
            return "PASS", findings, recs
        findings.append("GuardDuty not enabled")
        recs.append("Enable GuardDuty for threat detection")
        return "FAIL", findings, recs
    except ClientError as e:
        findings.append(f"Could not check GuardDuty: {e}")
        return "WARNING", findings, recs


CONTROL_CHECKS = {
    "AC-2": ("Account Management", check_ac2),
    "AC-6": ("Least Privilege", check_ac6),
    "AU-2": ("Event Logging", check_au2),
    "IA-2": ("Identification and Authentication", check_ia2),
    "SC-7": ("Boundary Protection", check_sc7),
    "SC-28": ("Protection of Information at Rest", check_sc28),
    "SI-4": ("System Monitoring", check_si4),
}


# =========================================================================
# SECURITY HUB INTEGRATION
# =========================================================================

SECURITYHUB_NIST_MAP = {
    "IAM": "AC",
    "EC2": "SC",
    "S3": "SC",
    "RDS": "SC",
    "CloudTrail": "AU",
    "CloudWatch": "SI",
    "GuardDuty": "SI",
    "Inspector": "RA",
    "Macie": "SC",
    "KMS": "SC",
    "Lambda": "CM",
    "Config": "CA",
    "SNS": "IR",
    "SecretsManager": "IA",
    "SSM": "CM",
    "ELB": "SC",
    "WAF": "SC",
}


def import_security_hub_findings(max_findings=100, severity_filter=None):
    """Import findings from AWS Security Hub and map to NIST controls."""
    try:
        sh = boto3.client("securityhub")

        filters = {
            "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}],
            "WorkflowStatus": [{"Value": "NEW", "Comparison": "EQUALS"}],
        }
        if severity_filter:
            filters["SeverityLabel"] = [{"Value": s, "Comparison": "EQUALS"} for s in severity_filter]

        findings = []
        paginator_token = None

        while True:
            kwargs = {"Filters": filters, "MaxResults": min(max_findings - len(findings), 100)}
            if paginator_token:
                kwargs["NextToken"] = paginator_token

            resp = sh.get_findings(**kwargs)
            findings.extend(resp.get("Findings", []))

            paginator_token = resp.get("NextToken")
            if not paginator_token or len(findings) >= max_findings:
                break

        # Process findings
        processed = []
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFORMATIONAL": 0}
        product_counts = {}

        for f in findings:
            severity = f.get("Severity", {}).get("Label", "INFORMATIONAL")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

            product = f.get("ProductName", f.get("GeneratorId", "Unknown").split("/")[0])
            product_counts[product] = product_counts.get(product, 0) + 1

            resource_type = ""
            resource_id = ""
            resources = f.get("Resources", [])
            if resources:
                resource_type = resources[0].get("Type", "")
                resource_id = resources[0].get("Id", "")

            nist_family = "SI"
            for service_key, family in SECURITYHUB_NIST_MAP.items():
                if service_key.lower() in product.lower() or service_key.lower() in resource_type.lower():
                    nist_family = family
                    break

            compliance_controls = []
            compliance = f.get("Compliance", {})
            for assoc in compliance.get("AssociatedStandards", []):
                compliance_controls.append(assoc.get("StandardsId", ""))
            for ctrl in compliance.get("SecurityControlId", ""):
                compliance_controls.append(ctrl)

            processed.append({
                "finding_id": f.get("Id", ""),
                "title": f.get("Title", ""),
                "description": f.get("Description", "")[:500],
                "severity": severity,
                "severity_score": f.get("Severity", {}).get("Normalized", 0),
                "product": product,
                "resource_type": resource_type,
                "resource_id": resource_id[:100],
                "region": f.get("Region", ""),
                "nist_family": nist_family,
                "compliance_controls": compliance_controls,
                "remediation_text": f.get("Remediation", {}).get("Recommendation", {}).get("Text", ""),
                "remediation_url": f.get("Remediation", {}).get("Recommendation", {}).get("Url", ""),
                "first_observed": f.get("FirstObservedAt", ""),
                "last_observed": f.get("LastObservedAt", ""),
                "workflow_status": f.get("Workflow", {}).get("Status", ""),
            })

        return {
            "total_findings": len(processed),
            "severity_counts": severity_counts,
            "product_counts": product_counts,
            "findings": processed,
        }

    except ClientError as e:
        return {"error": str(e), "total_findings": 0, "findings": []}


def run_assessment(families=None):
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


def _respond(event, body_data):
    """Build response for both function-based and API-based action groups."""
    body = json.dumps(body_data, default=str) if not isinstance(body_data, str) else body_data
    if event.get("function"):
        return {"messageVersion": "1.0", "response": {"actionGroup": event.get("actionGroup", ""), "function": event.get("function", ""), "functionResponse": {"responseBody": {"TEXT": {"body": body}}}}}
    return {"messageVersion": "1.0", "response": {"actionGroup": event.get("actionGroup", ""), "apiPath": event.get("apiPath", ""), "httpMethod": "POST", "httpStatusCode": 200, "responseBody": {"application/json": {"body": body}}}}


def handler(event, context):
    params = {p["name"]: p["value"] for p in event.get("parameters", [])}
    api_path = event.get("apiPath", "")

    # Route to Security Hub import if requested
    if api_path == "/securityhub" or params.get("source") == "securityhub":
        max_findings = int(params.get("max_findings", "50"))
        severity = params.get("severity", "").upper()
        severity_filter = severity.split(",") if severity else None

        sh_results = import_security_hub_findings(
            max_findings=max_findings,
            severity_filter=severity_filter,
        )

        return _respond(event, sh_results)

    # Standard NIST assessment
    families_str = params.get("families", "ALL")
    families = families_str.split(",") if families_str != "ALL" else ["ALL"]
    include_securityhub = params.get("include_securityhub", "false").lower() == "true"

    results = run_assessment(families)

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    warnings = sum(1 for r in results if r["status"] == "WARNING")
    total = len(results)
    compliance_pct = round(passed / total * 100, 1) if total > 0 else 0

    summary = {
        "account_id": get_account_id(),
        "total_controls": total,
        "passed": passed,
        "failed": failed,
        "warnings": warnings,
        "compliance_percentage": compliance_pct,
    }

    response_data = {"summary": summary, "controls": results}

    # Include Security Hub findings if requested
    if include_securityhub:
        sh_results = import_security_hub_findings(max_findings=50, severity_filter=["CRITICAL", "HIGH"])
        response_data["security_hub"] = sh_results
        summary["security_hub_findings"] = sh_results["total_findings"]
        summary["critical_findings"] = sh_results["severity_counts"].get("CRITICAL", 0)
        summary["high_findings"] = sh_results["severity_counts"].get("HIGH", 0)

    return _respond(event, response_data)
