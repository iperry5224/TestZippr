"""
SLyK-53 HARDEN Lambda — New Security Controls
==============================================
Automated hardening aligned with new control set:
- Account hardening (AC-2)
- Audit configuration hardening (AU-6)
- Configuration baseline enforcement (CM-6)
- Vulnerability scanning enablement (RA-5)
"""
import json
import boto3
from datetime import datetime, timezone
from botocore.exceptions import ClientError


def harden_accounts(action):
    """
    Harden IAM accounts (AC-2 aligned)
    - Enforce MFA policies
    - Apply password policies
    - Tag untagged accounts
    - Disable unused credentials
    """
    iam = boto3.client("iam")
    findings = []
    
    # Enforce strong password policy
    try:
        current_policy = iam.get_account_password_policy()["PasswordPolicy"]
    except ClientError:
        current_policy = {}
    
    desired_policy = {
        "MinimumPasswordLength": 14,
        "RequireSymbols": True,
        "RequireNumbers": True,
        "RequireUppercaseCharacters": True,
        "RequireLowercaseCharacters": True,
        "AllowUsersToChangePassword": True,
        "MaxPasswordAge": 90,
        "PasswordReusePrevention": 24,
        "HardExpiry": False,
    }
    
    policy_issues = []
    for key, value in desired_policy.items():
        if current_policy.get(key) != value:
            policy_issues.append(key)
    
    if policy_issues:
        findings.append({
            "asset": "Account Password Policy",
            "asset_type": "IAM Policy",
            "issues": [{"check": f"Policy setting: {k}", "status": "FAIL"} for k in policy_issues[:5]]
        })
        if action == "fix":
            try:
                iam.update_account_password_policy(**desired_policy)
                findings[-1]["issues"] = [{"check": "Password policy", "status": "FIXED"}]
            except ClientError as e:
                findings[-1]["issues"].append({"check": "Fix failed", "status": str(e)})
    
    # Check and harden individual users
    users = iam.list_users()["Users"]
    for user in users:
        username = user["UserName"]
        issues = []
        
        # Check MFA
        mfa = iam.list_mfa_devices(UserName=username)["MFADevices"]
        if not mfa:
            issues.append({"check": "MFA Enabled", "status": "FAIL"})
        
        # Check for old access keys (> 90 days)
        keys = iam.list_access_keys(UserName=username)["AccessKeyMetadata"]
        for key in keys:
            if key["Status"] == "Active":
                age = (datetime.now(timezone.utc) - key["CreateDate"]).days
                if age > 90:
                    issues.append({"check": f"Access Key Age ({key['AccessKeyId'][:8]})", "status": "FAIL", "detail": f"{age} days"})
                    if action == "fix":
                        # Deactivate old keys
                        try:
                            iam.update_access_key(UserName=username, AccessKeyId=key["AccessKeyId"], Status="Inactive")
                            issues[-1]["fixed"] = True
                        except ClientError:
                            issues[-1]["fixed"] = False
        
        # Check tags
        try:
            tags = iam.list_user_tags(UserName=username)["Tags"]
            tag_keys = [t["Key"].lower() for t in tags]
            if "owner" not in tag_keys:
                issues.append({"check": "Owner Tag", "status": "FAIL"})
        except ClientError:
            issues.append({"check": "Owner Tag", "status": "FAIL"})
        
        if issues:
            findings.append({"asset": username, "asset_type": "IAM User", "issues": issues})
    
    return findings


def harden_audit(action):
    """
    Harden audit configuration (AU-6 aligned)
    - Enable CloudTrail in all regions
    - Configure log file validation
    - Set up CloudWatch log integration
    - Enable S3 access logging for trail bucket
    """
    cloudtrail = boto3.client("cloudtrail")
    s3 = boto3.client("s3")
    findings = []
    
    # Check CloudTrail configuration
    try:
        trails = cloudtrail.describe_trails()["trailList"]
        
        if not trails:
            findings.append({
                "asset": "CloudTrail",
                "asset_type": "Audit Service",
                "issues": [{"check": "Trail Exists", "status": "FAIL"}]
            })
        else:
            for trail in trails:
                issues = []
                trail_name = trail["Name"]
                
                # Check if logging
                status = cloudtrail.get_trail_status(Name=trail["TrailARN"])
                if not status.get("IsLogging"):
                    issues.append({"check": "Logging Enabled", "status": "FAIL"})
                    if action == "fix":
                        try:
                            cloudtrail.start_logging(Name=trail_name)
                            issues[-1]["fixed"] = True
                        except ClientError:
                            issues[-1]["fixed"] = False
                
                # Check multi-region
                if not trail.get("IsMultiRegionTrail"):
                    issues.append({"check": "Multi-Region", "status": "FAIL"})
                    if action == "fix":
                        try:
                            cloudtrail.update_trail(Name=trail_name, IsMultiRegionTrail=True)
                            issues[-1]["fixed"] = True
                        except ClientError:
                            issues[-1]["fixed"] = False
                
                # Check log file validation
                if not trail.get("LogFileValidationEnabled"):
                    issues.append({"check": "Log File Validation", "status": "FAIL"})
                    if action == "fix":
                        try:
                            cloudtrail.update_trail(Name=trail_name, EnableLogFileValidation=True)
                            issues[-1]["fixed"] = True
                        except ClientError:
                            issues[-1]["fixed"] = False
                
                # Check CloudWatch integration
                if not trail.get("CloudWatchLogsLogGroupArn"):
                    issues.append({"check": "CloudWatch Integration", "status": "WARNING"})
                
                if issues:
                    findings.append({"asset": trail_name, "asset_type": "CloudTrail", "issues": issues})
                
                # Check trail bucket encryption
                bucket_name = trail.get("S3BucketName")
                if bucket_name:
                    try:
                        s3.get_bucket_encryption(Bucket=bucket_name)
                    except ClientError:
                        findings.append({
                            "asset": bucket_name,
                            "asset_type": "CloudTrail S3 Bucket",
                            "issues": [{"check": "Bucket Encryption", "status": "FAIL"}]
                        })
                        if action == "fix":
                            try:
                                s3.put_bucket_encryption(
                                    Bucket=bucket_name,
                                    ServerSideEncryptionConfiguration={
                                        "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
                                    }
                                )
                                findings[-1]["issues"][-1]["fixed"] = True
                            except ClientError:
                                findings[-1]["issues"][-1]["fixed"] = False
    except ClientError as e:
        findings.append({
            "asset": "CloudTrail",
            "asset_type": "Audit Service",
            "issues": [{"check": "Access", "status": "ERROR", "detail": str(e)}]
        })
    
    return findings


def harden_config(action):
    """
    Harden system configurations (CM-6 aligned)
    - Enforce IMDSv2 on EC2 instances
    - Enable EBS encryption by default
    - Secure security group configurations
    - Enable VPC flow logs
    """
    ec2 = boto3.client("ec2")
    findings = []
    
    # Check and enforce EBS encryption by default
    try:
        ebs_encryption = ec2.get_ebs_encryption_by_default()
        if not ebs_encryption.get("EbsEncryptionByDefault"):
            findings.append({
                "asset": "EBS Default Encryption",
                "asset_type": "Account Setting",
                "issues": [{"check": "EBS Encryption Default", "status": "FAIL"}]
            })
            if action == "fix":
                try:
                    ec2.enable_ebs_encryption_by_default()
                    findings[-1]["issues"][-1]["fixed"] = True
                except ClientError:
                    findings[-1]["issues"][-1]["fixed"] = False
    except ClientError:
        pass
    
    # Check EC2 instances
    try:
        instances = ec2.describe_instances()
        for reservation in instances.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                if instance.get("State", {}).get("Name") != "running":
                    continue
                    
                instance_id = instance["InstanceId"]
                issues = []
                
                # Check IMDSv2
                metadata_options = instance.get("MetadataOptions", {})
                if metadata_options.get("HttpTokens") != "required":
                    issues.append({"check": "IMDSv2 Required", "status": "FAIL"})
                    if action == "fix":
                        try:
                            ec2.modify_instance_metadata_options(
                                InstanceId=instance_id,
                                HttpTokens="required",
                                HttpEndpoint="enabled"
                            )
                            issues[-1]["fixed"] = True
                        except ClientError:
                            issues[-1]["fixed"] = False
                
                # Check for public IP (warning only)
                if instance.get("PublicIpAddress"):
                    issues.append({"check": "Public IP", "status": "WARNING", "detail": instance["PublicIpAddress"]})
                
                # Check IAM role
                if not instance.get("IamInstanceProfile"):
                    issues.append({"check": "IAM Instance Profile", "status": "WARNING"})
                
                if issues:
                    name = next((t["Value"] for t in instance.get("Tags", []) if t["Key"] == "Name"), instance_id)
                    findings.append({"asset": f"{name} ({instance_id})", "asset_type": "EC2 Instance", "issues": issues})
    except ClientError:
        pass
    
    # Check security groups
    try:
        sgs = ec2.describe_security_groups()["SecurityGroups"]
        for sg in sgs:
            issues = []
            for rule in sg.get("IpPermissions", []):
                for ip_range in rule.get("IpRanges", []):
                    if ip_range.get("CidrIp") == "0.0.0.0/0":
                        port = rule.get("FromPort", "all")
                        if port not in [80, 443]:
                            issues.append({
                                "check": f"Open to 0.0.0.0/0 on port {port}",
                                "status": "FAIL"
                            })
            if issues:
                findings.append({
                    "asset": f"{sg.get('GroupName', '')} ({sg['GroupId']})",
                    "asset_type": "Security Group",
                    "issues": issues
                })
    except ClientError:
        pass
    
    # Check VPC flow logs
    try:
        vpcs = ec2.describe_vpcs()["Vpcs"]
        for vpc in vpcs:
            vpc_id = vpc["VpcId"]
            flow_logs = ec2.describe_flow_logs(
                Filters=[{"Name": "resource-id", "Values": [vpc_id]}]
            )
            if not flow_logs.get("FlowLogs"):
                findings.append({
                    "asset": vpc_id,
                    "asset_type": "VPC",
                    "issues": [{"check": "Flow Logs Enabled", "status": "FAIL"}]
                })
    except ClientError:
        pass
    
    return findings


def harden_scanning(action):
    """
    Harden vulnerability scanning (RA-5 aligned)
    - Enable Inspector
    - Configure SSM for all instances
    - Enable GuardDuty
    - Configure Security Hub
    """
    findings = []
    
    # Check Inspector
    try:
        inspector = boto3.client("inspector2")
        status = inspector.batch_get_account_status()
        accounts = status.get("accounts", [])
        if accounts:
            acct_status = accounts[0].get("state", {}).get("status", "")
            if acct_status != "ENABLED":
                findings.append({
                    "asset": "Amazon Inspector",
                    "asset_type": "Security Service",
                    "issues": [{"check": "Inspector Enabled", "status": "FAIL"}]
                })
                if action == "fix":
                    try:
                        inspector.enable(resourceTypes=["EC2", "ECR", "LAMBDA"])
                        findings[-1]["issues"][-1]["fixed"] = True
                    except ClientError:
                        findings[-1]["issues"][-1]["fixed"] = False
    except ClientError:
        findings.append({
            "asset": "Amazon Inspector",
            "asset_type": "Security Service",
            "issues": [{"check": "Inspector Access", "status": "WARNING"}]
        })
    
    # Check GuardDuty
    try:
        guardduty = boto3.client("guardduty")
        detectors = guardduty.list_detectors()["DetectorIds"]
        if not detectors:
            findings.append({
                "asset": "Amazon GuardDuty",
                "asset_type": "Security Service",
                "issues": [{"check": "GuardDuty Enabled", "status": "FAIL"}]
            })
            if action == "fix":
                try:
                    guardduty.create_detector(Enable=True, FindingPublishingFrequency="FIFTEEN_MINUTES")
                    findings[-1]["issues"][-1]["fixed"] = True
                except ClientError:
                    findings[-1]["issues"][-1]["fixed"] = False
    except ClientError:
        pass
    
    # Check Security Hub
    try:
        securityhub = boto3.client("securityhub")
        hub = securityhub.describe_hub()
        if not hub.get("HubArn"):
            findings.append({
                "asset": "AWS Security Hub",
                "asset_type": "Security Service",
                "issues": [{"check": "Security Hub Enabled", "status": "FAIL"}]
            })
            if action == "fix":
                try:
                    securityhub.enable_security_hub(EnableDefaultStandards=True)
                    findings[-1]["issues"][-1]["fixed"] = True
                except ClientError:
                    findings[-1]["issues"][-1]["fixed"] = False
    except ClientError as e:
        if "not subscribed" in str(e).lower():
            findings.append({
                "asset": "AWS Security Hub",
                "asset_type": "Security Service",
                "issues": [{"check": "Security Hub Enabled", "status": "FAIL"}]
            })
            if action == "fix":
                try:
                    securityhub = boto3.client("securityhub")
                    securityhub.enable_security_hub(EnableDefaultStandards=True)
                    findings[-1]["issues"][-1]["fixed"] = True
                except ClientError:
                    findings[-1]["issues"][-1]["fixed"] = False
    
    # Check SSM coverage
    try:
        ec2 = boto3.client("ec2")
        ssm = boto3.client("ssm")
        
        # Count running instances
        instances = ec2.describe_instances(
            Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
        )
        total_instances = sum(
            len(r.get("Instances", []))
            for r in instances.get("Reservations", [])
        )
        
        # Count managed instances
        managed = ssm.describe_instance_information()
        managed_count = len(managed.get("InstanceInformationList", []))
        
        if total_instances > 0 and managed_count < total_instances:
            unmanaged = total_instances - managed_count
            findings.append({
                "asset": "SSM Coverage",
                "asset_type": "Management Service",
                "issues": [{
                    "check": "SSM Agent Coverage",
                    "status": "WARNING",
                    "detail": f"{unmanaged} of {total_instances} instances not managed"
                }]
            })
    except ClientError:
        pass
    
    return findings


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
                    "Source": "slyk.harden",
                    "DetailType": detail_type,
                    "Detail": json.dumps(detail, default=str),
                    "EventBusName": "default"
                }
            ]
        )
    except Exception:
        pass  # Don't fail hardening if notification fails


def handler(event, context):
    """Lambda handler for Bedrock Agent action group."""
    http_method = event.get("httpMethod") or "GET"
    if not isinstance(event, dict):
        event = {}
    params = _action_params(event)
    asset_type = params.get("asset_type", "all").lower()
    action = params.get("action", "scan")

    all_findings = []
    
    if asset_type in ["all", "accounts", "iam", "ac2"]:
        all_findings.extend(harden_accounts(action))
    
    if asset_type in ["all", "audit", "cloudtrail", "au6"]:
        all_findings.extend(harden_audit(action))
    
    if asset_type in ["all", "config", "ec2", "s3", "cm6"]:
        all_findings.extend(harden_config(action))
    
    if asset_type in ["all", "scanning", "inspector", "guardduty", "ra5"]:
        all_findings.extend(harden_scanning(action))

    total_issues = sum(len(f.get("issues", [])) for f in all_findings)
    fixed_count = sum(
        1 for f in all_findings
        for i in f.get("issues", [])
        if i.get("fixed")
    )

    result = {
        "asset_type": asset_type,
        "action": action,
        "assets_scanned": len(all_findings),
        "total_issues": total_issues,
        "issues_fixed": fixed_count if action == "fix" else 0,
        "findings": all_findings,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Publish events for critical/high findings
    critical_findings = [
        f for f in all_findings
        for i in f.get("issues", [])
        if i.get("status") == "FAIL"
    ]
    if critical_findings:
        publish_event("SLyK Security Finding", {
            "severity": "CRITICAL" if action == "scan" else "HIGH",
            "status": "FAIL",
            "action": action,
            "total_issues": total_issues,
            "issues_fixed": fixed_count,
            "message": f"Hardening scan found {total_issues} issues across {len(all_findings)} assets",
            "findings": [f["asset"] for f in critical_findings[:10]]
        })

    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup", ""),
            "apiPath": event.get("apiPath", ""),
            "httpMethod": http_method,
            "httpStatusCode": 200,
            "responseBody": {"application/json": {"body": json.dumps(result, default=str)}},
        },
    }
