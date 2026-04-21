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


def handler(event, context):
    params = {p["name"]: p["value"] for p in event.get("parameters", [])}
    control_id = params.get("control_id", "").upper()
    action = params.get("action", "generate")

    playbook = REMEDIATION_PLAYBOOKS.get(control_id)
    if not playbook:
        available = ", ".join(REMEDIATION_PLAYBOOKS.keys())
        body = json.dumps({
            "error": f"No remediation playbook for {control_id}",
            "available_controls": available,
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
            "httpMethod": "POST",
            "httpStatusCode": 200,
            "responseBody": {"application/json": {"body": body}},
        },
    }
