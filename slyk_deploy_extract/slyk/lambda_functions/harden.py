"""SLyK-53 HARDEN Lambda — scan and harden AWS assets."""
import json
import boto3
from botocore.exceptions import ClientError


def harden_s3(action):
    s3 = boto3.client("s3")
    buckets = s3.list_buckets()["Buckets"]
    findings = []

    for b in buckets:
        name = b["Name"]
        issues = []

        try:
            pab = s3.get_public_access_block(Bucket=name)
            cfg = pab["PublicAccessBlockConfiguration"]
            if not all(cfg.values()):
                issues.append({"check": "Public Access Block", "status": "FAIL"})
                if action == "fix":
                    s3.put_public_access_block(Bucket=name, PublicAccessBlockConfiguration={
                        "BlockPublicAcls": True, "IgnorePublicAcls": True,
                        "BlockPublicPolicy": True, "RestrictPublicBuckets": True
                    })
                    issues[-1]["fixed"] = True
        except ClientError:
            issues.append({"check": "Public Access Block", "status": "FAIL"})
            if action == "fix":
                try:
                    s3.put_public_access_block(Bucket=name, PublicAccessBlockConfiguration={
                        "BlockPublicAcls": True, "IgnorePublicAcls": True,
                        "BlockPublicPolicy": True, "RestrictPublicBuckets": True
                    })
                    issues[-1]["fixed"] = True
                except:
                    issues[-1]["fixed"] = False

        try:
            s3.get_bucket_encryption(Bucket=name)
        except ClientError:
            issues.append({"check": "Default Encryption", "status": "FAIL"})
            if action == "fix":
                try:
                    s3.put_bucket_encryption(Bucket=name, ServerSideEncryptionConfiguration={
                        "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
                    })
                    issues[-1]["fixed"] = True
                except:
                    issues[-1]["fixed"] = False

        versioning = s3.get_bucket_versioning(Bucket=name)
        if versioning.get("Status") != "Enabled":
            issues.append({"check": "Versioning", "status": "FAIL"})
            if action == "fix":
                try:
                    s3.put_bucket_versioning(Bucket=name, VersioningConfiguration={"Status": "Enabled"})
                    issues[-1]["fixed"] = True
                except:
                    issues[-1]["fixed"] = False

        try:
            s3.get_bucket_logging(Bucket=name).get("LoggingEnabled")
        except:
            pass

        if issues:
            findings.append({"asset": name, "asset_type": "S3 Bucket", "issues": issues})

    return findings


def harden_ec2(action):
    ec2 = boto3.client("ec2")
    findings = []
    instances = []
    paginator = ec2.get_paginator("describe_instances")
    for page in paginator.paginate(MaxResults=50):
        for r in page["Reservations"]:
            instances.extend(r["Instances"])

    for inst in instances:
        iid = inst["InstanceId"]
        issues = []

        if inst.get("MetadataOptions", {}).get("HttpTokens") != "required":
            issues.append({"check": "IMDSv2 Required", "status": "FAIL"})
            if action == "fix":
                try:
                    ec2.modify_instance_metadata_options(InstanceId=iid, HttpTokens="required", HttpEndpoint="enabled")
                    issues[-1]["fixed"] = True
                except:
                    issues[-1]["fixed"] = False

        if inst.get("PublicIpAddress"):
            issues.append({"check": "Public IP Assigned", "status": "WARNING", "detail": inst["PublicIpAddress"]})

        if not inst.get("IamInstanceProfile"):
            issues.append({"check": "IAM Instance Profile", "status": "WARNING", "detail": "No IAM role attached"})

        if issues:
            name_tag = next((t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Name"), iid)
            findings.append({"asset": f"{name_tag} ({iid})", "asset_type": "EC2 Instance", "issues": issues})

    return findings


def harden_iam(action):
    iam = boto3.client("iam")
    findings = []

    cred_report_ready = False
    try:
        iam.generate_credential_report()
        import time
        time.sleep(3)
        cred_report_ready = True
    except:
        pass

    users = iam.list_users()["Users"]
    for u in users:
        uname = u["UserName"]
        issues = []

        mfa = iam.list_mfa_devices(UserName=uname)["MFADevices"]
        if not mfa:
            issues.append({"check": "MFA Enabled", "status": "FAIL"})

        keys = iam.list_access_keys(UserName=uname)["AccessKeyMetadata"]
        for k in keys:
            if k["Status"] == "Active":
                from datetime import datetime, timezone
                age = (datetime.now(timezone.utc) - k["CreateDate"]).days
                if age > 90:
                    issues.append({"check": f"Access Key Age ({k['AccessKeyId'][:8]}...)", "status": "FAIL", "detail": f"{age} days old"})

        if issues:
            findings.append({"asset": uname, "asset_type": "IAM User", "issues": issues})

    return findings


def handler(event, context):
    params = {p["name"]: p["value"] for p in event.get("parameters", [])}
    asset_type = params.get("asset_type", "s3").lower()
    action = params.get("action", "scan")

    if asset_type == "s3":
        findings = harden_s3(action)
    elif asset_type == "ec2":
        findings = harden_ec2(action)
    elif asset_type == "iam":
        findings = harden_iam(action)
    else:
        findings = []

    total_issues = sum(len(f["issues"]) for f in findings)
    fixed_count = sum(1 for f in findings for i in f["issues"] if i.get("fixed"))

    result = {
        "asset_type": asset_type,
        "action": action,
        "assets_scanned": len(findings),
        "total_issues": total_issues,
        "issues_fixed": fixed_count if action == "fix" else 0,
        "findings": findings,
    }

    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup", ""),
            "apiPath": event.get("apiPath", ""),
            "httpMethod": "POST",
            "httpStatusCode": 200,
            "responseBody": {"application/json": {"body": json.dumps(result)}},
        },
    }
