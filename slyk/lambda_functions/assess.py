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


def handler(event, context):
    params = {p["name"]: p["value"] for p in event.get("parameters", [])}
    families_str = params.get("families", "ALL")
    families = families_str.split(",") if families_str != "ALL" else ["ALL"]

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

    body = json.dumps({"summary": summary, "controls": results})

    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup", ""),
            "apiPath": event.get("apiPath", ""),
            "httpMethod": "POST",
            "httpStatusCode": 200,
            "responseBody": {"application/json": {"body": body}},
        },
    }
