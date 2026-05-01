"""
SLyK-53 REMEDIATE Lambda — New Security Controls
=================================================
Automated generation of remediation runbooks and patching logic for:
- AC-2: Account Management remediation
- AU-6: Audit configuration remediation
- CM-6: Configuration drift remediation
- SI-2: Flaw remediation and patching
- RA-5: Vulnerability remediation
"""
import json
import boto3
from datetime import datetime, timezone
from botocore.exceptions import ClientError


# =============================================================================
# Remediation Playbooks
# =============================================================================

def _scan_ac2_issues():
    """Scan for AC-2 issues that need remediation."""
    iam = boto3.client("iam")
    issues = []
    
    users = iam.list_users()["Users"]
    for user in users:
        username = user["UserName"]
        
        # Check MFA
        mfa = iam.list_mfa_devices(UserName=username)["MFADevices"]
        if not mfa:
            issues.append({"type": "no_mfa", "user": username})
        
        # Check tags
        try:
            tags = iam.list_user_tags(UserName=username)["Tags"]
            tag_keys = [t["Key"].lower() for t in tags]
            if "owner" not in tag_keys:
                issues.append({"type": "no_owner_tag", "user": username})
        except ClientError:
            issues.append({"type": "no_owner_tag", "user": username})
    
    return issues


def _generate_ac2_scripts(issues):
    """Generate remediation scripts for AC-2 issues."""
    scripts = []
    
    mfa_users = [i["user"] for i in issues if i["type"] == "no_mfa"]
    if mfa_users:
        scripts.append("# Enable MFA for users without it")
        scripts.append("# Note: MFA device setup requires user interaction")
        for user in mfa_users[:5]:
            scripts.append(f"# User {user} needs MFA enabled")
            scripts.append(f"aws iam create-virtual-mfa-device --virtual-mfa-device-name {user}-mfa --outfile /tmp/{user}-qr.png --bootstrap-method QRCodePNG")
    
    untagged = [i["user"] for i in issues if i["type"] == "no_owner_tag"]
    if untagged:
        scripts.append("")
        scripts.append("# Add owner tags to untagged users")
        for user in untagged[:5]:
            scripts.append(f'aws iam tag-user --user-name {user} --tags Key=Owner,Value=CHANGE_ME Key=Purpose,Value=CHANGE_ME')
    
    return scripts


def _scan_au6_issues():
    """Scan for AU-6 issues that need remediation."""
    cloudtrail = boto3.client("cloudtrail")
    cloudwatch = boto3.client("cloudwatch")
    issues = []
    
    # Check CloudTrail status
    try:
        trails = cloudtrail.describe_trails()["trailList"]
        if not trails:
            issues.append({"type": "no_cloudtrail"})
        else:
            for trail in trails:
                status = cloudtrail.get_trail_status(Name=trail["TrailARN"])
                if not status.get("IsLogging"):
                    issues.append({"type": "cloudtrail_not_logging", "trail": trail["Name"]})
    except ClientError:
        pass
    
    # Check for security alarms
    try:
        alarms = cloudwatch.describe_alarms()
        alarm_names = [a["AlarmName"].lower() for a in alarms.get("MetricAlarms", [])]
        required_alarms = ["unauthorized", "root", "console-login-failure"]
        for req in required_alarms:
            if not any(req in name for name in alarm_names):
                issues.append({"type": "missing_alarm", "alarm": req})
    except ClientError:
        pass
    
    return issues


def _generate_au6_scripts(issues):
    """Generate remediation scripts for AU-6 issues."""
    scripts = []
    
    if any(i["type"] == "no_cloudtrail" for i in issues):
        scripts.append("# Create CloudTrail trail")
        scripts.append("aws cloudtrail create-trail --name security-audit-trail --s3-bucket-name YOUR_BUCKET --is-multi-region-trail --enable-log-file-validation")
        scripts.append("aws cloudtrail start-logging --name security-audit-trail")
    
    not_logging = [i for i in issues if i["type"] == "cloudtrail_not_logging"]
    for issue in not_logging:
        scripts.append(f"aws cloudtrail start-logging --name {issue['trail']}")
    
    missing_alarms = [i for i in issues if i["type"] == "missing_alarm"]
    if missing_alarms:
        scripts.append("")
        scripts.append("# Create security monitoring alarms")
        scripts.append("# These require a CloudWatch Logs log group from CloudTrail")
        for alarm in missing_alarms:
            scripts.append(f"# Missing alarm for: {alarm['alarm']}")
    
    return scripts


def _scan_cm6_issues():
    """Scan for CM-6 configuration drift issues."""
    ec2 = boto3.client("ec2")
    s3 = boto3.client("s3")
    issues = []
    
    # Check EC2 configurations
    try:
        instances = ec2.describe_instances()
        for res in instances.get("Reservations", []):
            for inst in res.get("Instances", []):
                if inst.get("MetadataOptions", {}).get("HttpTokens") != "required":
                    issues.append({"type": "imdsv2", "instance": inst["InstanceId"]})
    except ClientError:
        pass
    
    # Check S3 configurations
    try:
        buckets = s3.list_buckets()["Buckets"]
        for bucket in buckets:
            name = bucket["Name"]
            try:
                s3.get_bucket_encryption(Bucket=name)
            except ClientError:
                issues.append({"type": "s3_no_encryption", "bucket": name})
            
            try:
                pab = s3.get_public_access_block(Bucket=name)
                if not all(pab["PublicAccessBlockConfiguration"].values()):
                    issues.append({"type": "s3_public_access", "bucket": name})
            except ClientError:
                issues.append({"type": "s3_public_access", "bucket": name})
    except ClientError:
        pass
    
    return issues


def _generate_cm6_scripts(issues):
    """Generate remediation scripts for CM-6 issues."""
    scripts = []
    
    imdsv2_instances = [i["instance"] for i in issues if i["type"] == "imdsv2"]
    if imdsv2_instances:
        scripts.append("# Enforce IMDSv2 on EC2 instances")
        for inst in imdsv2_instances[:10]:
            scripts.append(f"aws ec2 modify-instance-metadata-options --instance-id {inst} --http-tokens required --http-endpoint enabled")
    
    unencrypted = [i["bucket"] for i in issues if i["type"] == "s3_no_encryption"]
    if unencrypted:
        scripts.append("")
        scripts.append("# Enable S3 default encryption")
        for bucket in unencrypted[:10]:
            scripts.append(f"aws s3api put-bucket-encryption --bucket {bucket} --server-side-encryption-configuration '{{\"Rules\":[{{\"ApplyServerSideEncryptionByDefault\":{{\"SSEAlgorithm\":\"AES256\"}}}}]}}'")
    
    public_buckets = [i["bucket"] for i in issues if i["type"] == "s3_public_access"]
    if public_buckets:
        scripts.append("")
        scripts.append("# Block public access on S3 buckets")
        for bucket in public_buckets[:10]:
            scripts.append(f"aws s3api put-public-access-block --bucket {bucket} --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true")
    
    return scripts


def _scan_si2_issues():
    """Scan for SI-2 patching issues."""
    ssm = boto3.client("ssm")
    issues = []
    
    try:
        # Get non-compliant instances
        compliance = ssm.list_resource_compliance_summaries(
            Filters=[
                {"Key": "ComplianceType", "Values": ["Patch"]},
                {"Key": "Status", "Values": ["NON_COMPLIANT"]}
            ]
        )
        for resource in compliance.get("ResourceComplianceSummaryItems", []):
            issues.append({
                "type": "patch_non_compliant",
                "instance": resource.get("ResourceId", ""),
                "severity": resource.get("OverallSeverity", "MEDIUM")
            })
    except ClientError:
        pass
    
    return issues


def _generate_si2_scripts(issues):
    """Generate remediation scripts for SI-2 patching issues."""
    scripts = []
    
    non_compliant = [i for i in issues if i["type"] == "patch_non_compliant"]
    if non_compliant:
        scripts.append("# SSM Patch Manager Remediation Runbook")
        scripts.append("")
        scripts.append("# Option 1: Run patch baseline scan and install")
        scripts.append("aws ssm send-command \\")
        scripts.append("  --document-name 'AWS-RunPatchBaseline' \\")
        scripts.append("  --targets 'Key=tag:PatchGroup,Values=Production' \\")
        scripts.append("  --parameters 'Operation=Install' \\")
        scripts.append("  --max-concurrency '10%' \\")
        scripts.append("  --max-errors '10%'")
        scripts.append("")
        scripts.append("# Option 2: Target specific instances")
        
        critical = [i["instance"] for i in non_compliant if i["severity"] == "CRITICAL"]
        high = [i["instance"] for i in non_compliant if i["severity"] == "HIGH"]
        
        if critical:
            scripts.append("")
            scripts.append("# CRITICAL severity instances (patch immediately):")
            for inst in critical[:5]:
                scripts.append(f"aws ssm send-command --document-name 'AWS-RunPatchBaseline' --instance-ids {inst} --parameters 'Operation=Install'")
        
        if high:
            scripts.append("")
            scripts.append("# HIGH severity instances:")
            for inst in high[:5]:
                scripts.append(f"aws ssm send-command --document-name 'AWS-RunPatchBaseline' --instance-ids {inst} --parameters 'Operation=Install'")
    
    return scripts


def _scan_ra5_issues():
    """Scan for RA-5 vulnerability scanning issues."""
    ec2 = boto3.client("ec2")
    ssm = boto3.client("ssm")
    issues = []
    
    # Get all running instances
    try:
        instances = ec2.describe_instances(
            Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
        )
        all_instances = []
        for res in instances.get("Reservations", []):
            for inst in res.get("Instances", []):
                all_instances.append(inst["InstanceId"])
    except ClientError:
        all_instances = []
    
    # Get SSM managed instances
    try:
        managed = ssm.describe_instance_information()
        managed_ids = [i["InstanceId"] for i in managed.get("InstanceInformationList", [])]
    except ClientError:
        managed_ids = []
    
    # Find unmanaged instances
    for inst_id in all_instances:
        if inst_id not in managed_ids:
            issues.append({"type": "not_managed", "instance": inst_id})
    
    return issues


def _generate_ra5_scripts(issues):
    """Generate remediation scripts for RA-5 issues."""
    scripts = []
    
    unmanaged = [i["instance"] for i in issues if i["type"] == "not_managed"]
    if unmanaged:
        scripts.append("# Install SSM Agent on unmanaged instances")
        scripts.append("# For Amazon Linux 2:")
        scripts.append("# sudo yum install -y amazon-ssm-agent")
        scripts.append("# sudo systemctl enable amazon-ssm-agent")
        scripts.append("# sudo systemctl start amazon-ssm-agent")
        scripts.append("")
        scripts.append("# Unmanaged instances that need SSM agent:")
        for inst in unmanaged[:10]:
            scripts.append(f"# - {inst}")
        scripts.append("")
        scripts.append("# Enable Inspector scanning")
        scripts.append("aws inspector2 enable --resource-types EC2 ECR LAMBDA")
        scripts.append("")
        scripts.append("# Verify Inspector coverage")
        scripts.append("aws inspector2 list-coverage --filter-criteria '{\"resourceType\":[{\"comparison\":\"EQUALS\",\"value\":\"AWS_EC2_INSTANCE\"}]}'")
    
    return scripts


# =============================================================================
# Playbook Registry
# =============================================================================

REMEDIATION_PLAYBOOKS = {
    "AC-2": {
        "title": "Account Management — Unauthorized Account Detection",
        "description": "Remediate unauthorized accounts, enable MFA, add ownership tags",
        "scan": _scan_ac2_issues,
        "generate": _generate_ac2_scripts,
    },
    "AU-6": {
        "title": "Audit Review, Analysis, and Reporting",
        "description": "Configure CloudTrail, enable security alarms, set up log analysis",
        "scan": _scan_au6_issues,
        "generate": _generate_au6_scripts,
    },
    "CM-6": {
        "title": "Configuration Settings — Baseline Verification",
        "description": "Remediate configuration drift, enforce IMDSv2, secure S3 buckets",
        "scan": _scan_cm6_issues,
        "generate": _generate_cm6_scripts,
    },
    "SI-2": {
        "title": "Flaw Remediation — Patching and Runbooks",
        "description": "Generate patching runbooks, apply SSM patches, remediate vulnerabilities",
        "scan": _scan_si2_issues,
        "generate": _generate_si2_scripts,
    },
    "RA-5": {
        "title": "Vulnerability Monitoring and Scanning",
        "description": "Enable scanning coverage, install SSM agents, configure Inspector",
        "scan": _scan_ra5_issues,
        "generate": _generate_ra5_scripts,
    },
}


def _action_params(event):
    """Parse action parameters from Bedrock event."""
    raw = event.get("parameters")
    if not raw or not isinstance(raw, list):
        return {}
    out = {}
    for p in raw:
        if not isinstance(p, dict):
            continue
        n = p.get("name")
        if n is None or n == "":
            continue
        v = p.get("value", "")
        out[n] = v if isinstance(v, str) else (str(v) if v is not None else "")
    return out


def publish_event(detail_type, detail):
    """Publish event to EventBridge for notifications."""
    try:
        events = boto3.client("events")
        events.put_events(
            Entries=[
                {
                    "Source": "slyk.remediate",
                    "DetailType": detail_type,
                    "Detail": json.dumps(detail, default=str),
                    "EventBusName": "default"
                }
            ]
        )
    except Exception:
        pass  # Don't fail remediation if notification fails


def handler(event, context):
    """Lambda handler for Bedrock Agent action group."""
    http_method = event.get("httpMethod") or "GET"
    if not isinstance(event, dict):
        event = {}
    params = _action_params(event)
    control_id = params.get("control_id", "").upper()
    action = params.get("action", "generate")

    playbook = REMEDIATION_PLAYBOOKS.get(control_id)
    if not playbook:
        available = ", ".join(REMEDIATION_PLAYBOOKS.keys())
        body = json.dumps({
            "error": f"No remediation playbook for {control_id}",
            "available_controls": available,
            "description": "Specify a control ID: AC-2, AU-6, CM-6, SI-2, or RA-5",
        })
    else:
        issues = playbook["scan"]()
        scripts = playbook["generate"](issues)

        result = {
            "control_id": control_id,
            "title": playbook["title"],
            "description": playbook["description"],
            "issues_found": len(issues),
            "issues": issues[:20],
            "remediation_scripts": scripts,
            "action": action,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        if action == "execute":
            executed = []
            for script in scripts:
                if script.startswith("#"):
                    continue
                try:
                    import subprocess
                    proc = subprocess.run(script, shell=True, capture_output=True, timeout=30)
                    executed.append({"script": script[:80], "status": "executed", "exit_code": proc.returncode})
                except Exception as e:
                    executed.append({"script": script[:80], "status": f"failed: {e}"})
            result["execution_results"] = executed
            
            # Publish remediation event
            publish_event("SLyK Remediation Action", {
                "control_id": control_id,
                "action": "execute",
                "issues_remediated": len(executed),
                "message": f"Executed {len(executed)} remediation scripts for {control_id}",
                "scripts_executed": [e["script"] for e in executed[:5]]
            })
        else:
            # Publish event for generated playbook
            if issues:
                publish_event("SLyK Remediation Action", {
                    "control_id": control_id,
                    "action": "generate",
                    "issues_found": len(issues),
                    "message": f"Generated remediation playbook for {control_id} with {len(issues)} issues"
                })

        body = json.dumps(result, default=str)

    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup", ""),
            "apiPath": event.get("apiPath", ""),
            "httpMethod": http_method,
            "httpStatusCode": 200,
            "responseBody": {"application/json": {"body": body}},
        },
    }
