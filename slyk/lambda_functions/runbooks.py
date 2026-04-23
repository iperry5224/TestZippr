"""
SLyK-53 RUNBOOKS Lambda — Predefined ISSO workflows
=====================================================
Provides a catalog of step-by-step runbooks that ISSOs can execute
by name. Each runbook orchestrates multiple SLyK actions in sequence.

Usage via Bedrock Agent:
  "Run the monthly compliance check"
  "Show me available runbooks"
  "Execute the incident response runbook"
"""

import json
import os
import time
import boto3
from datetime import datetime, timezone
from botocore.exceptions import ClientError

REGION = os.environ.get("SLYK_REGION", os.environ.get("AWS_REGION", "us-east-1"))
S3_BUCKET = os.environ.get("S3_BUCKET_NAME", "saelarallpurpose")

BEDROCK_MODEL_CANDIDATES = [
    "amazon.nova-pro-v1:0",
    "amazon.nova-lite-v1:0",
    "amazon.nova-micro-v1:0",
    "meta.llama3-1-70b-instruct-v1:0",
    "meta.llama3-1-8b-instruct-v1:0",
    "mistral.mistral-large-2407-v1:0",
    "mistral.mixtral-8x7b-instruct-v0:1",
    "amazon.titan-text-express-v1",
    "amazon.titan-text-lite-v1",
]


def call_bedrock(prompt, max_tokens=2048):
    """Call Bedrock with model succession."""
    bedrock = boto3.client("bedrock-runtime", region_name=REGION)
    for model_id in BEDROCK_MODEL_CANDIDATES:
        try:
            resp = bedrock.converse(
                modelId=model_id,
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={"maxTokens": max_tokens, "temperature": 0.3},
            )
            return resp["output"]["message"]["content"][0]["text"]
        except Exception:
            continue
    return "AI analysis unavailable"


def get_account_id():
    return boto3.client("sts", region_name=REGION).get_caller_identity()["Account"]


def save_runbook_result(runbook_name, result):
    """Save runbook execution result to S3 for audit trail."""
    try:
        s3 = boto3.client("s3", region_name=REGION)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_name = runbook_name.replace(" ", "_").lower()
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=f"slyk/runbook_results/{safe_name}_{timestamp}.json",
            Body=json.dumps(result, indent=2, default=str).encode("utf-8"),
            ContentType="application/json",
        )
    except Exception:
        pass


# =========================================================================
# RUNBOOK: Monthly Compliance Assessment
# =========================================================================
def rb_monthly_compliance():
    """Full monthly NIST 800-53 compliance assessment with Security Hub."""
    steps = []

    # Step 1: NIST Control Assessment
    steps.append({"step": 1, "name": "NIST 800-53 Control Assessment", "status": "running"})
    iam = boto3.client("iam", region_name=REGION)
    ec2 = boto3.client("ec2", region_name=REGION)
    s3 = boto3.client("s3", region_name=REGION)

    findings = {}

    # IAM checks
    users = iam.list_users()["Users"]
    mfa_missing = [u["UserName"] for u in users if not iam.list_mfa_devices(UserName=u["UserName"])["MFADevices"]]
    findings["iam_users_without_mfa"] = mfa_missing
    findings["total_iam_users"] = len(users)

    # S3 checks
    buckets = s3.list_buckets()["Buckets"]
    unencrypted = []
    for b in buckets:
        try:
            s3.get_bucket_encryption(Bucket=b["Name"])
        except ClientError:
            unencrypted.append(b["Name"])
    findings["unencrypted_buckets"] = unencrypted

    # CloudTrail
    ct = boto3.client("cloudtrail", region_name=REGION)
    trails = ct.describe_trails()["trailList"]
    active_trails = [t["Name"] for t in trails if ct.get_trail_status(Name=t["TrailARN"]).get("IsLogging")]
    findings["active_cloudtrails"] = active_trails

    steps[0]["status"] = "complete"
    steps[0]["findings"] = findings

    # Step 2: Security Hub Findings Import
    steps.append({"step": 2, "name": "Security Hub Finding Import", "status": "running"})
    try:
        sh = boto3.client("securityhub", region_name=REGION)
        sh_findings = sh.get_findings(
            Filters={
                "SeverityLabel": [
                    {"Value": "CRITICAL", "Comparison": "EQUALS"},
                    {"Value": "HIGH", "Comparison": "EQUALS"},
                ],
                "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}],
            },
            MaxResults=50,
        )["Findings"]
        steps[1]["status"] = "complete"
        steps[1]["findings_count"] = len(sh_findings)
        steps[1]["critical"] = sum(1 for f in sh_findings if f.get("Severity", {}).get("Label") == "CRITICAL")
        steps[1]["high"] = sum(1 for f in sh_findings if f.get("Severity", {}).get("Label") == "HIGH")
    except ClientError as e:
        steps[1]["status"] = "error"
        steps[1]["error"] = str(e)
        sh_findings = []

    # Step 3: GuardDuty Check
    steps.append({"step": 3, "name": "GuardDuty Threat Detection Status", "status": "running"})
    try:
        gd = boto3.client("guardduty", region_name=REGION)
        detectors = gd.list_detectors()["DetectorIds"]
        if detectors:
            gd_findings = gd.list_findings(
                DetectorId=detectors[0],
                FindingCriteria={"Criterion": {"severity": {"Gte": 4}}},
                MaxResults=20,
            )["FindingIds"]
            steps[2]["status"] = "complete"
            steps[2]["detector_active"] = True
            steps[2]["medium_plus_findings"] = len(gd_findings)
        else:
            steps[2]["status"] = "warning"
            steps[2]["detector_active"] = False
    except ClientError as e:
        steps[2]["status"] = "error"
        steps[2]["error"] = str(e)

    # Step 4: AI Executive Summary
    steps.append({"step": 4, "name": "AI Executive Summary Generation", "status": "running"})
    prompt = f"""Generate a brief executive compliance summary based on these findings:
- IAM users without MFA: {len(mfa_missing)} of {len(users)}
- Unencrypted S3 buckets: {len(unencrypted)}
- Active CloudTrail trails: {len(active_trails)}
- Security Hub critical findings: {steps[1].get('critical', 'N/A')}
- Security Hub high findings: {steps[1].get('high', 'N/A')}
- GuardDuty active: {steps[2].get('detector_active', 'N/A')}

Provide: overall risk level, top 3 priorities, and recommended immediate actions."""

    summary = call_bedrock(prompt)
    steps[3]["status"] = "complete"
    steps[3]["executive_summary"] = summary

    # Step 5: Save Report
    steps.append({"step": 5, "name": "Save Compliance Report to S3", "status": "running"})
    result = {
        "runbook": "Monthly Compliance Assessment",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "account_id": get_account_id(),
        "steps": steps,
        "executive_summary": summary,
    }
    save_runbook_result("monthly_compliance", result)
    steps[4]["status"] = "complete"

    return result


# =========================================================================
# RUNBOOK: Quarterly Hardening Review
# =========================================================================
def rb_quarterly_hardening():
    """Scan S3, EC2, and IAM for hardening gaps."""
    steps = []

    # Step 1: S3 Hardening
    steps.append({"step": 1, "name": "S3 Bucket Hardening Scan", "status": "running"})
    s3 = boto3.client("s3", region_name=REGION)
    buckets = s3.list_buckets()["Buckets"]
    s3_issues = []
    for b in buckets:
        name = b["Name"]
        issues = []
        try:
            pab = s3.get_public_access_block(Bucket=name)
            if not all(pab["PublicAccessBlockConfiguration"].values()):
                issues.append("Public access not fully blocked")
        except:
            issues.append("No public access block configured")
        try:
            s3.get_bucket_encryption(Bucket=name)
        except:
            issues.append("Default encryption disabled")
        ver = s3.get_bucket_versioning(Bucket=name)
        if ver.get("Status") != "Enabled":
            issues.append("Versioning disabled")
        if issues:
            s3_issues.append({"bucket": name, "issues": issues})
    steps[0]["status"] = "complete"
    steps[0]["buckets_scanned"] = len(buckets)
    steps[0]["buckets_with_issues"] = len(s3_issues)
    steps[0]["details"] = s3_issues

    # Step 2: EC2 Hardening
    steps.append({"step": 2, "name": "EC2 Instance Hardening Scan", "status": "running"})
    ec2 = boto3.client("ec2", region_name=REGION)
    instances = []
    for page in ec2.get_paginator("describe_instances").paginate(MaxResults=50):
        for r in page["Reservations"]:
            instances.extend(r["Instances"])
    ec2_issues = []
    for inst in instances:
        iid = inst["InstanceId"]
        issues = []
        if inst.get("MetadataOptions", {}).get("HttpTokens") != "required":
            issues.append("IMDSv2 not enforced")
        if inst.get("PublicIpAddress"):
            issues.append(f"Public IP: {inst['PublicIpAddress']}")
        if not inst.get("IamInstanceProfile"):
            issues.append("No IAM role attached")
        if issues:
            name = next((t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Name"), iid)
            ec2_issues.append({"instance": f"{name} ({iid})", "issues": issues})
    steps[1]["status"] = "complete"
    steps[1]["instances_scanned"] = len(instances)
    steps[1]["instances_with_issues"] = len(ec2_issues)
    steps[1]["details"] = ec2_issues

    # Step 3: IAM Hardening
    steps.append({"step": 3, "name": "IAM User Hardening Scan", "status": "running"})
    iam = boto3.client("iam", region_name=REGION)
    users = iam.list_users()["Users"]
    iam_issues = []
    for u in users:
        uname = u["UserName"]
        issues = []
        mfa = iam.list_mfa_devices(UserName=uname)["MFADevices"]
        if not mfa:
            issues.append("MFA not enabled")
        keys = iam.list_access_keys(UserName=uname)["AccessKeyMetadata"]
        for k in keys:
            if k["Status"] == "Active":
                age = (datetime.now(timezone.utc) - k["CreateDate"]).days
                if age > 90:
                    issues.append(f"Access key {k['AccessKeyId'][:8]}... is {age} days old")
        if issues:
            iam_issues.append({"user": uname, "issues": issues})
    steps[2]["status"] = "complete"
    steps[2]["users_scanned"] = len(users)
    steps[2]["users_with_issues"] = len(iam_issues)
    steps[2]["details"] = iam_issues

    # Step 4: AI Hardening Report
    steps.append({"step": 4, "name": "AI Hardening Recommendations", "status": "running"})
    total_issues = len(s3_issues) + len(ec2_issues) + len(iam_issues)
    prompt = f"""Generate a hardening summary and prioritized recommendations:
- S3: {len(s3_issues)} of {len(buckets)} buckets need hardening
- EC2: {len(ec2_issues)} of {len(instances)} instances need hardening
- IAM: {len(iam_issues)} of {len(users)} users need hardening
- Total issues: {total_issues}

Top S3 issues: {json.dumps(s3_issues[:3], default=str)}
Top EC2 issues: {json.dumps(ec2_issues[:3], default=str)}
Top IAM issues: {json.dumps(iam_issues[:3], default=str)}

Provide prioritized remediation steps."""

    recommendations = call_bedrock(prompt)
    steps[3]["status"] = "complete"
    steps[3]["recommendations"] = recommendations

    result = {
        "runbook": "Quarterly Hardening Review",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "account_id": get_account_id(),
        "steps": steps,
        "total_issues": total_issues,
        "recommendations": recommendations,
    }
    save_runbook_result("quarterly_hardening", result)
    return result


# =========================================================================
# RUNBOOK: Incident Response Triage
# =========================================================================
def rb_incident_response():
    """IR triage — check GuardDuty, Security Hub, and CloudTrail for active threats."""
    steps = []

    # Step 1: GuardDuty Active Threats
    steps.append({"step": 1, "name": "GuardDuty Active Threat Check", "status": "running"})
    try:
        gd = boto3.client("guardduty", region_name=REGION)
        detectors = gd.list_detectors()["DetectorIds"]
        gd_details = []
        if detectors:
            finding_ids = gd.list_findings(
                DetectorId=detectors[0],
                FindingCriteria={"Criterion": {"severity": {"Gte": 7}}},
                MaxResults=20,
            )["FindingIds"]
            if finding_ids:
                findings = gd.get_findings(DetectorId=detectors[0], FindingIds=finding_ids[:10])["Findings"]
                for f in findings:
                    gd_details.append({
                        "type": f.get("Type", ""),
                        "severity": f.get("Severity", 0),
                        "title": f.get("Title", ""),
                        "resource": f.get("Resource", {}).get("ResourceType", ""),
                    })
            steps[0]["status"] = "complete"
            steps[0]["high_severity_findings"] = len(finding_ids)
            steps[0]["details"] = gd_details
        else:
            steps[0]["status"] = "warning"
            steps[0]["message"] = "GuardDuty not enabled"
    except ClientError as e:
        steps[0]["status"] = "error"
        steps[0]["error"] = str(e)

    # Step 2: Security Hub Critical Findings
    steps.append({"step": 2, "name": "Security Hub Critical Finding Scan", "status": "running"})
    try:
        sh = boto3.client("securityhub", region_name=REGION)
        critical = sh.get_findings(
            Filters={
                "SeverityLabel": [{"Value": "CRITICAL", "Comparison": "EQUALS"}],
                "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}],
                "WorkflowStatus": [{"Value": "NEW", "Comparison": "EQUALS"}],
            },
            MaxResults=20,
        )["Findings"]
        sh_details = [{"title": f.get("Title", ""), "product": f.get("ProductName", ""), "resource": f.get("Resources", [{}])[0].get("Id", "")[:80]} for f in critical]
        steps[1]["status"] = "complete"
        steps[1]["critical_findings"] = len(critical)
        steps[1]["details"] = sh_details
    except ClientError as e:
        steps[1]["status"] = "error"
        steps[1]["error"] = str(e)

    # Step 3: Recent CloudTrail Anomalies
    steps.append({"step": 3, "name": "CloudTrail Suspicious Activity Check", "status": "running"})
    try:
        ct = boto3.client("cloudtrail", region_name=REGION)
        from datetime import timedelta
        end = datetime.now(timezone.utc)
        start = end - timedelta(hours=24)
        events = ct.lookup_events(
            LookupAttributes=[{"AttributeKey": "EventName", "AttributeValue": "ConsoleLogin"}],
            StartTime=start,
            EndTime=end,
            MaxResults=20,
        )["Events"]
        failed_logins = [e for e in events if "Failed" in json.dumps(e.get("CloudTrailEvent", ""))]
        steps[2]["status"] = "complete"
        steps[2]["login_events_24h"] = len(events)
        steps[2]["failed_logins_24h"] = len(failed_logins)
    except ClientError as e:
        steps[2]["status"] = "error"
        steps[2]["error"] = str(e)

    # Step 4: AI Threat Assessment
    steps.append({"step": 4, "name": "AI Threat Assessment", "status": "running"})
    prompt = f"""You are SLyK, an incident response analyst. Based on the following real-time data, provide an IR triage assessment:

GuardDuty: {steps[0].get('high_severity_findings', 'N/A')} high-severity findings
Security Hub: {steps[1].get('critical_findings', 'N/A')} critical findings
CloudTrail: {steps[2].get('login_events_24h', 'N/A')} login events, {steps[2].get('failed_logins_24h', 'N/A')} failed in last 24h

Top GuardDuty findings: {json.dumps(steps[0].get('details', [])[:3], default=str)}
Top Security Hub findings: {json.dumps(steps[1].get('details', [])[:3], default=str)}

Provide:
1. Threat level (Critical/High/Medium/Low)
2. Whether immediate containment is recommended
3. Top 3 immediate actions
4. Affected resources to isolate"""

    assessment = call_bedrock(prompt)
    steps[3]["status"] = "complete"
    steps[3]["threat_assessment"] = assessment

    result = {
        "runbook": "Incident Response Triage",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "account_id": get_account_id(),
        "steps": steps,
        "threat_assessment": assessment,
    }
    save_runbook_result("incident_response", result)
    return result


# =========================================================================
# RUNBOOK: ATO Readiness Check
# =========================================================================
def rb_ato_readiness():
    """Check ATO readiness — verifies all controls, docs, and evidence."""
    steps = []

    # Step 1: Control Coverage
    steps.append({"step": 1, "name": "NIST Control Coverage Assessment", "status": "running"})
    from assess import CONTROL_CHECKS, check_control
    results = []
    for control_id, (name, check_fn) in CONTROL_CHECKS.items():
        result = check_control(control_id, check_fn)
        result["control_name"] = name
        results.append(result)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    total = len(results)
    steps[0]["status"] = "complete"
    steps[0]["passed"] = passed
    steps[0]["failed"] = failed
    steps[0]["total"] = total
    steps[0]["compliance_pct"] = round(passed / total * 100, 1) if total > 0 else 0

    # Step 2: Documentation Check
    steps.append({"step": 2, "name": "Compliance Documentation Inventory", "status": "running"})
    try:
        s3 = boto3.client("s3", region_name=REGION)
        doc_types = {"SSP": 0, "POAM": 0, "RAR": 0}
        for prefix in ["Documentation/SSPs/", "Documentation/POA&Ms/", "Documentation/"]:
            resp = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix, MaxKeys=100)
            for obj in resp.get("Contents", []):
                key = obj["Key"].upper()
                for dt in doc_types:
                    if dt in key:
                        doc_types[dt] += 1
        steps[1]["status"] = "complete"
        steps[1]["documents"] = doc_types
    except Exception as e:
        steps[1]["status"] = "error"
        steps[1]["error"] = str(e)

    # Step 3: Security Services Verification
    steps.append({"step": 3, "name": "Required Security Services Check", "status": "running"})
    services_status = {}
    try:
        sh = boto3.client("securityhub", region_name=REGION)
        sh.describe_hub()
        services_status["SecurityHub"] = "ENABLED"
    except:
        services_status["SecurityHub"] = "DISABLED"
    try:
        gd = boto3.client("guardduty", region_name=REGION)
        services_status["GuardDuty"] = "ENABLED" if gd.list_detectors()["DetectorIds"] else "DISABLED"
    except:
        services_status["GuardDuty"] = "DISABLED"
    try:
        ct = boto3.client("cloudtrail", region_name=REGION)
        trails = ct.describe_trails()["trailList"]
        services_status["CloudTrail"] = "ENABLED" if trails else "DISABLED"
    except:
        services_status["CloudTrail"] = "DISABLED"
    try:
        config = boto3.client("config", region_name=REGION)
        recorders = config.describe_configuration_recorders()["ConfigurationRecorders"]
        services_status["AWSConfig"] = "ENABLED" if recorders else "DISABLED"
    except:
        services_status["AWSConfig"] = "DISABLED"

    steps[2]["status"] = "complete"
    steps[2]["services"] = services_status
    steps[2]["all_enabled"] = all(v == "ENABLED" for v in services_status.values())

    # Step 4: AI Readiness Assessment
    steps.append({"step": 4, "name": "AI ATO Readiness Assessment", "status": "running"})
    prompt = f"""Assess ATO readiness based on:
- NIST compliance: {passed}/{total} controls passing ({steps[0]['compliance_pct']}%)
- Failed controls: {failed}
- Documents: SSPs={doc_types.get('SSP', 0)}, POA&Ms={doc_types.get('POAM', 0)}, RARs={doc_types.get('RAR', 0)}
- Security services: {json.dumps(services_status)}

Provide:
1. ATO readiness level (Ready / Nearly Ready / Significant Gaps / Not Ready)
2. Gaps that must be closed before authorization
3. Estimated remediation effort
4. Recommended next steps"""

    assessment = call_bedrock(prompt)
    steps[3]["status"] = "complete"
    steps[3]["readiness_assessment"] = assessment

    result = {
        "runbook": "ATO Readiness Check",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "account_id": get_account_id(),
        "steps": steps,
        "readiness_assessment": assessment,
    }
    save_runbook_result("ato_readiness", result)
    return result


# =========================================================================
# RUNBOOK: POA&M Review
# =========================================================================
def rb_poam_review():
    """Review open POA&M items and check if any have been remediated."""
    steps = []

    # Step 1: Get current failed controls
    steps.append({"step": 1, "name": "Current Failed Controls Scan", "status": "running"})
    from assess import CONTROL_CHECKS, check_control
    failed_controls = []
    for control_id, (name, check_fn) in CONTROL_CHECKS.items():
        result = check_control(control_id, check_fn)
        if result["status"] == "FAIL":
            result["control_name"] = name
            failed_controls.append(result)
    steps[0]["status"] = "complete"
    steps[0]["open_poam_items"] = len(failed_controls)
    steps[0]["controls"] = failed_controls

    # Step 2: AI POA&M Status Report
    steps.append({"step": 2, "name": "AI POA&M Status Report", "status": "running"})
    control_summary = "\n".join([f"- {c['control_id']}: {c.get('control_name', '')} — {', '.join(c.get('findings', []))}" for c in failed_controls])
    prompt = f"""Generate a POA&M status report for an ISSO. {len(failed_controls)} controls are currently failing:

{control_summary}

For each item provide:
1. Weakness description
2. Recommended milestone date (realistic)
3. Resources required
4. Priority (1=highest)

Format as a structured POA&M table."""

    poam_report = call_bedrock(prompt, max_tokens=4096)
    steps[1]["status"] = "complete"
    steps[1]["poam_report"] = poam_report

    result = {
        "runbook": "POA&M Review",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "account_id": get_account_id(),
        "steps": steps,
        "open_items": len(failed_controls),
        "poam_report": poam_report,
    }
    save_runbook_result("poam_review", result)
    return result


# =========================================================================
# RUNBOOK: New System Onboarding
# =========================================================================
def rb_system_onboarding():
    """Verify baseline security for a newly onboarded system."""
    steps = []

    # Step 1: Account baseline
    steps.append({"step": 1, "name": "Account Security Baseline Check", "status": "running"})
    iam = boto3.client("iam", region_name=REGION)
    summary = iam.get_account_summary()["SummaryMap"]
    baseline = {
        "root_mfa": summary.get("AccountMFAEnabled", 0) == 1,
        "password_policy_exists": True,
        "total_users": summary.get("Users", 0),
        "total_roles": summary.get("Roles", 0),
        "total_policies": summary.get("Policies", 0),
    }
    try:
        iam.get_account_password_policy()
    except:
        baseline["password_policy_exists"] = False
    steps[0]["status"] = "complete"
    steps[0]["baseline"] = baseline

    # Step 2: Required services
    steps.append({"step": 2, "name": "Required Services Enablement", "status": "running"})
    services = {}
    checks = [
        ("SecurityHub", lambda: boto3.client("securityhub", region_name=REGION).describe_hub()),
        ("GuardDuty", lambda: bool(boto3.client("guardduty", region_name=REGION).list_detectors()["DetectorIds"])),
        ("CloudTrail", lambda: bool(boto3.client("cloudtrail", region_name=REGION).describe_trails()["trailList"])),
    ]
    for name, check_fn in checks:
        try:
            check_fn()
            services[name] = "ENABLED"
        except:
            services[name] = "NOT_ENABLED"
    steps[1]["status"] = "complete"
    steps[1]["services"] = services

    # Step 3: AI Onboarding Checklist
    steps.append({"step": 3, "name": "AI Onboarding Checklist", "status": "running"})
    prompt = f"""Generate a security onboarding checklist for a new FISMA system on AWS.

Current state:
- Root MFA: {'Enabled' if baseline['root_mfa'] else 'NOT ENABLED'}
- Password policy: {'Configured' if baseline['password_policy_exists'] else 'NOT CONFIGURED'}
- IAM users: {baseline['total_users']}, Roles: {baseline['total_roles']}
- Security Hub: {services.get('SecurityHub', 'UNKNOWN')}
- GuardDuty: {services.get('GuardDuty', 'UNKNOWN')}
- CloudTrail: {services.get('CloudTrail', 'UNKNOWN')}

Provide a prioritized checklist of what the ISSO must complete before the system goes to assessment."""

    checklist = call_bedrock(prompt)
    steps[2]["status"] = "complete"
    steps[2]["checklist"] = checklist

    result = {
        "runbook": "New System Onboarding",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "account_id": get_account_id(),
        "steps": steps,
        "checklist": checklist,
    }
    save_runbook_result("system_onboarding", result)
    return result


# =========================================================================
# RUNBOOK CATALOG
# =========================================================================

RUNBOOK_CATALOG = {
    "monthly_compliance": {
        "name": "Monthly Compliance Assessment",
        "description": "Full NIST 800-53 assessment with Security Hub import, GuardDuty check, and AI executive summary.",
        "audience": "ISSO, Security Manager",
        "frequency": "Monthly",
        "steps": ["NIST Control Assessment", "Security Hub Import", "GuardDuty Check", "AI Executive Summary", "Save Report"],
        "function": rb_monthly_compliance,
    },
    "quarterly_hardening": {
        "name": "Quarterly Hardening Review",
        "description": "Comprehensive hardening scan of S3, EC2, and IAM with AI remediation recommendations.",
        "audience": "ISSO, System Admin",
        "frequency": "Quarterly",
        "steps": ["S3 Hardening Scan", "EC2 Hardening Scan", "IAM Hardening Scan", "AI Recommendations"],
        "function": rb_quarterly_hardening,
    },
    "incident_response": {
        "name": "Incident Response Triage",
        "description": "Real-time IR triage — checks GuardDuty, Security Hub, and CloudTrail for active threats with AI threat assessment.",
        "audience": "ISSO, IR Team, SOC",
        "frequency": "On-demand / When alerted",
        "steps": ["GuardDuty Threat Check", "Security Hub Critical Scan", "CloudTrail Anomaly Check", "AI Threat Assessment"],
        "function": rb_incident_response,
    },
    "ato_readiness": {
        "name": "ATO Readiness Check",
        "description": "Verify control compliance, documentation inventory, and security service status for Authorization to Operate.",
        "audience": "ISSO, Authorizing Official",
        "frequency": "Pre-assessment / On-demand",
        "steps": ["Control Coverage", "Documentation Inventory", "Security Services Check", "AI Readiness Assessment"],
        "function": rb_ato_readiness,
    },
    "poam_review": {
        "name": "POA&M Review",
        "description": "Scan for open POA&M items, check remediation status, and generate AI-assisted milestone recommendations.",
        "audience": "ISSO",
        "frequency": "Monthly",
        "steps": ["Failed Controls Scan", "AI POA&M Status Report"],
        "function": rb_poam_review,
    },
    "system_onboarding": {
        "name": "New System Onboarding",
        "description": "Security baseline verification and checklist generation for newly onboarded FISMA systems.",
        "audience": "ISSO, System Owner",
        "frequency": "Per new system",
        "steps": ["Account Baseline Check", "Required Services Check", "AI Onboarding Checklist"],
        "function": rb_system_onboarding,
    },
}


# =========================================================================
# LAMBDA HANDLER
# =========================================================================

def handler(event, context):
    params = {p["name"]: p["value"] for p in event.get("parameters", [])}
    action = params.get("action", "list")
    runbook_id = params.get("runbook_id", "").lower().replace(" ", "_").replace("-", "_")

    if action == "list" or not runbook_id:
        catalog = []
        for rid, rb in RUNBOOK_CATALOG.items():
            catalog.append({
                "runbook_id": rid,
                "name": rb["name"],
                "description": rb["description"],
                "audience": rb["audience"],
                "frequency": rb["frequency"],
                "steps": rb["steps"],
            })
        body = json.dumps({"available_runbooks": catalog, "total": len(catalog)})

    elif runbook_id in RUNBOOK_CATALOG:
        rb = RUNBOOK_CATALOG[runbook_id]
        result = rb["function"]()
        body = json.dumps(result, default=str)

    else:
        available = ", ".join(RUNBOOK_CATALOG.keys())
        body = json.dumps({
            "error": f"Unknown runbook: {runbook_id}",
            "available": available,
        })

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
