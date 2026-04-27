"""SLyK-53 REMEDIATE Lambda — generate and execute remediation scripts."""
import json
import boto3


REMEDIATION_PLAYBOOKS = {
    "AC-2": {
        "title": "Account Management — Enable MFA",
        "description": "Enable MFA for all IAM users without it.",
        "scan": lambda: _find_users_without_mfa(),
        "generate": lambda targets: [
            f"aws iam create-virtual-mfa-device --virtual-mfa-device-name {u}-mfa --outfile /tmp/{u}-qr.png --bootstrap-method QRCodePNG"
            for u in targets
        ],
    },
    "AC-6": {
        "title": "Least Privilege — Remove Overly Permissive Policies",
        "description": "Identify and flag policies with Action:* Resource:*.",
        "scan": lambda: _find_admin_policies(),
        "generate": lambda targets: [
            f"# Review and scope down policy: {p}\naws iam get-policy --policy-arn {p}" for p in targets
        ],
    },
    "AU-2": {
        "title": "Event Logging — Enable CloudTrail",
        "description": "Ensure CloudTrail is enabled and logging.",
        "scan": lambda: _check_cloudtrail(),
        "generate": lambda targets: [
            "aws cloudtrail create-trail --name saelar-audit-trail --s3-bucket-name <YOUR_BUCKET> --is-multi-region-trail",
            "aws cloudtrail start-logging --name saelar-audit-trail",
        ],
    },
    "IA-2": {
        "title": "Root MFA — Enable MFA on Root Account",
        "description": "Root account MFA must be enabled via the Console.",
        "scan": lambda: _check_root_mfa(),
        "generate": lambda targets: [
            "# Root MFA must be enabled manually via AWS Console:",
            "# 1. Sign in as root: https://console.aws.amazon.com/",
            "# 2. Go to IAM > Security credentials",
            "# 3. Enable virtual MFA device",
        ],
    },
    "SC-7": {
        "title": "Boundary Protection — Restrict Security Groups",
        "description": "Remove 0.0.0.0/0 rules from security groups on non-web ports.",
        "scan": lambda: _find_open_security_groups(),
        "generate": lambda targets: [
            f"aws ec2 revoke-security-group-ingress --group-id {sg} --protocol tcp --port {port} --cidr 0.0.0.0/0"
            for sg, port in targets
        ],
    },
    "SC-28": {
        "title": "Encryption at Rest — Enable S3 Default Encryption",
        "description": "Enable SSE-S3 encryption on unencrypted buckets.",
        "scan": lambda: _find_unencrypted_buckets(),
        "generate": lambda targets: [
            f"aws s3api put-bucket-encryption --bucket {b} --server-side-encryption-configuration '{{\"Rules\":[{{\"ApplyServerSideEncryptionByDefault\":{{\"SSEAlgorithm\":\"AES256\"}}}}]}}'"
            for b in targets
        ],
    },
    "SI-4": {
        "title": "System Monitoring — Enable GuardDuty",
        "description": "Enable GuardDuty for continuous threat detection.",
        "scan": lambda: _check_guardduty(),
        "generate": lambda targets: [
            "aws guardduty create-detector --enable --finding-publishing-frequency FIFTEEN_MINUTES",
        ],
    },
}


def _find_users_without_mfa():
    iam = boto3.client("iam")
    users = iam.list_users()["Users"]
    return [u["UserName"] for u in users if not iam.list_mfa_devices(UserName=u["UserName"])["MFADevices"]]


def _find_admin_policies():
    iam = boto3.client("iam")
    policies = iam.list_policies(Scope="Local", OnlyAttached=True)["Policies"]
    admin = []
    for p in policies[:20]:
        ver = iam.get_policy_version(PolicyArn=p["Arn"], VersionId=p["DefaultVersionId"])
        doc = ver["PolicyVersion"]["Document"]
        for s in doc.get("Statement", []):
            if s.get("Effect") == "Allow" and s.get("Action") == "*" and s.get("Resource") == "*":
                admin.append(p["Arn"])
    return admin


def _check_cloudtrail():
    ct = boto3.client("cloudtrail")
    trails = ct.describe_trails()["trailList"]
    if not trails:
        return ["no-trail"]
    inactive = [t["Name"] for t in trails if not ct.get_trail_status(Name=t["TrailARN"]).get("IsLogging")]
    return inactive if inactive else []


def _check_root_mfa():
    iam = boto3.client("iam")
    summary = iam.get_account_summary()["SummaryMap"]
    return ["root"] if summary.get("AccountMFAEnabled", 0) == 0 else []


def _find_open_security_groups():
    ec2 = boto3.client("ec2")
    sgs = ec2.describe_security_groups()["SecurityGroups"]
    open_rules = []
    for sg in sgs:
        for rule in sg.get("IpPermissions", []):
            for ip in rule.get("IpRanges", []):
                if ip.get("CidrIp") == "0.0.0.0/0" and rule.get("FromPort") not in [80, 443]:
                    open_rules.append((sg["GroupId"], rule.get("FromPort", "all")))
    return open_rules


def _find_unencrypted_buckets():
    s3 = boto3.client("s3")
    buckets = s3.list_buckets()["Buckets"]
    unencrypted = []
    for b in buckets:
        try:
            s3.get_bucket_encryption(Bucket=b["Name"])
        except:
            unencrypted.append(b["Name"])
    return unencrypted


def _check_guardduty():
    gd = boto3.client("guardduty")
    detectors = gd.list_detectors()["DetectorIds"]
    return [] if detectors else ["not-enabled"]


def remediate_securityhub_finding(finding_id, action="generate"):
    """Generate or execute remediation for a specific Security Hub finding."""
    sh = boto3.client("securityhub")

    try:
        resp = sh.get_findings(Filters={
            "Id": [{"Value": finding_id, "Comparison": "EQUALS"}]
        })
        findings = resp.get("Findings", [])
        if not findings:
            return {"error": f"Finding {finding_id} not found"}

        finding = findings[0]
        title = finding.get("Title", "")
        description = finding.get("Description", "")
        severity = finding.get("Severity", {}).get("Label", "UNKNOWN")
        product = finding.get("ProductName", "")
        resources = finding.get("Resources", [])
        resource_type = resources[0].get("Type", "") if resources else ""
        resource_id = resources[0].get("Id", "") if resources else ""
        remediation_text = finding.get("Remediation", {}).get("Recommendation", {}).get("Text", "")
        remediation_url = finding.get("Remediation", {}).get("Recommendation", {}).get("Url", "")

        scripts = []

        if "S3" in resource_type or "s3" in title.lower():
            bucket = resource_id.split(":")[-1] if ":" in resource_id else resource_id
            if "encrypt" in title.lower() or "encryption" in description.lower():
                scripts.append(f"aws s3api put-bucket-encryption --bucket {bucket} --server-side-encryption-configuration '{{\"Rules\":[{{\"ApplyServerSideEncryptionByDefault\":{{\"SSEAlgorithm\":\"AES256\"}}}}}}'")
            if "public" in title.lower() or "public" in description.lower():
                scripts.append(f"aws s3api put-public-access-block --bucket {bucket} --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true")
            if "versioning" in title.lower():
                scripts.append(f"aws s3api put-bucket-versioning --bucket {bucket} --versioning-configuration Status=Enabled")

        elif "IAM" in resource_type or "iam" in title.lower():
            if "mfa" in title.lower():
                scripts.append("# Enable MFA for the affected user via AWS Console or CLI")
                scripts.append("# aws iam create-virtual-mfa-device --virtual-mfa-device-name <user>-mfa --outfile /tmp/qr.png --bootstrap-method QRCodePNG")
            if "key" in title.lower() and ("rotate" in title.lower() or "age" in title.lower() or "old" in description.lower()):
                scripts.append("# Rotate old access keys:")
                scripts.append("# aws iam create-access-key --user-name <user>")
                scripts.append("# aws iam delete-access-key --user-name <user> --access-key-id <old-key-id>")
            if "policy" in title.lower() and ("admin" in title.lower() or "wildcard" in description.lower()):
                scripts.append("# Review and scope down the overly permissive policy")

        elif "EC2" in resource_type or "ec2" in title.lower():
            instance_id = resource_id.split("/")[-1] if "/" in resource_id else resource_id
            if "security group" in title.lower() or "unrestricted" in title.lower():
                scripts.append(f"# Review and restrict security group rules for instance {instance_id}")
                scripts.append(f"aws ec2 describe-instance-attribute --instance-id {instance_id} --attribute groupSet")
            if "imds" in title.lower() or "metadata" in title.lower():
                scripts.append(f"aws ec2 modify-instance-metadata-options --instance-id {instance_id} --http-tokens required --http-endpoint enabled")

        if not scripts:
            scripts.append(f"# AWS Recommendation: {remediation_text}" if remediation_text else "# No automated remediation available — manual review required")
            if remediation_url:
                scripts.append(f"# Reference: {remediation_url}")

        result = {
            "source": "security_hub",
            "finding_id": finding_id,
            "title": title,
            "severity": severity,
            "product": product,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "remediation_scripts": scripts,
            "aws_recommendation": remediation_text,
            "reference_url": remediation_url,
            "action": action,
        }

        if action == "execute":
            executed = []
            for script in scripts:
                if script.startswith("#"):
                    continue
                try:
                    import subprocess
                    subprocess.run(script, shell=True, capture_output=True, timeout=30)
                    executed.append({"script": script[:80], "status": "executed"})
                except Exception as e:
                    executed.append({"script": script[:80], "status": f"failed: {e}"})
            result["execution_results"] = executed

        # Update workflow status if fix was executed
        if action == "execute" and executed:
            try:
                sh.batch_update_findings(
                    FindingIdentifiers=[{"Id": finding_id, "ProductArn": finding.get("ProductArn", "")}],
                    Workflow={"Status": "NOTIFIED"},
                    Note={"Text": "Remediation applied by SLyK-53", "UpdatedBy": "SLyK-53"}
                )
                result["finding_status_updated"] = True
            except:
                result["finding_status_updated"] = False

        return result

    except ClientError as e:
        return {"error": str(e)}


def _action_params(event):
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


def handler(event, context):
    http_method = event.get("httpMethod") or "GET"
    if not isinstance(event, dict):
        event = {}
    params = _action_params(event)
    control_id = params.get("control_id", "").upper()
    action = params.get("action", "generate")
    finding_id = params.get("finding_id", "")

    # Route to Security Hub remediation if finding_id provided
    if finding_id:
        result = remediate_securityhub_finding(finding_id, action)
        body = json.dumps(result)
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

    playbook = REMEDIATION_PLAYBOOKS.get(control_id)
    if not playbook:
        available = ", ".join(REMEDIATION_PLAYBOOKS.keys())
        body = json.dumps({
            "error": f"No remediation playbook for {control_id}",
            "available_controls": available,
            "tip": "You can also provide a finding_id from Security Hub for targeted remediation",
        })
    else:
        targets = playbook["scan"]()
        scripts = playbook["generate"](targets)

        result = {
            "control_id": control_id,
            "title": playbook["title"],
            "description": playbook["description"],
            "targets_found": len(targets),
            "targets": targets[:10] if not isinstance(targets[0], tuple) else [f"{t[0]}:{t[1]}" for t in targets[:10]] if targets else [],
            "remediation_scripts": scripts,
            "action": action,
        }

        if action == "execute":
            executed = []
            for script in scripts:
                if script.startswith("#"):
                    continue
                try:
                    import subprocess
                    subprocess.run(script, shell=True, capture_output=True, timeout=30)
                    executed.append({"script": script[:80], "status": "executed"})
                except Exception as e:
                    executed.append({"script": script[:80], "status": f"failed: {e}"})
            result["execution_results"] = executed

        body = json.dumps(result)

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
