"""
SLyK-53 ALERT TRIAGE Lambda
=============================
Triggered by EventBridge when Security Hub detects CRITICAL/HIGH findings.
Automatically:
  1. Analyzes the finding
  2. Maps to NIST control
  3. Generates remediation
  4. Invokes Bedrock for AI risk assessment
  5. Sends alert via SNS with finding + recommended fix

Trigger: EventBridge rule on Security Hub findings (CRITICAL, HIGH)
"""

import json
import os
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

REGION = os.environ.get("SLYK_REGION", os.environ.get("AWS_REGION", "us-east-1"))
S3_BUCKET = os.environ.get("S3_BUCKET_NAME", "saelarallpurpose")
SNS_TOPIC_ARN = os.environ.get("SLYK_ALERT_TOPIC_ARN", "")
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
BEDROCK_MODEL = os.environ.get("BEDROCK_MODEL", BEDROCK_MODEL_CANDIDATES[0])

NIST_MAP = {
    "AwsIamUser": "AC", "AwsIamPolicy": "AC", "AwsIamRole": "AC",
    "AwsS3Bucket": "SC", "AwsEc2Instance": "SC", "AwsEc2SecurityGroup": "SC",
    "AwsRdsDbInstance": "SC", "AwsKmsKey": "SC",
    "AwsCloudTrailTrail": "AU", "AwsLambdaFunction": "CM",
    "AwsSecretsManagerSecret": "IA",
}


def get_nist_family(resource_type):
    for key, family in NIST_MAP.items():
        if key.lower() in resource_type.lower():
            return family
    return "SI"


def generate_auto_remediation(finding):
    """Generate remediation scripts based on finding type."""
    title = finding.get("Title", "").lower()
    resources = finding.get("Resources", [])
    resource_type = resources[0].get("Type", "") if resources else ""
    resource_id = resources[0].get("Id", "") if resources else ""

    scripts = []

    if "s3" in resource_type.lower():
        bucket = resource_id.split(":")[-1] if ":" in resource_id else resource_id.split("/")[-1]
        if "encrypt" in title or "encryption" in title:
            scripts.append(f"aws s3api put-bucket-encryption --bucket {bucket} --server-side-encryption-configuration '{{\"Rules\":[{{\"ApplyServerSideEncryptionByDefault\":{{\"SSEAlgorithm\":\"AES256\"}}}}}}'")
        if "public" in title:
            scripts.append(f"aws s3api put-public-access-block --bucket {bucket} --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true")
        if "version" in title:
            scripts.append(f"aws s3api put-bucket-versioning --bucket {bucket} --versioning-configuration Status=Enabled")

    elif "ec2" in resource_type.lower():
        instance_id = resource_id.split("/")[-1] if "/" in resource_id else resource_id
        if "metadata" in title or "imds" in title:
            scripts.append(f"aws ec2 modify-instance-metadata-options --instance-id {instance_id} --http-tokens required --http-endpoint enabled")
        if "security group" in title or "unrestricted" in title:
            scripts.append(f"# Review security groups for {instance_id}")
            scripts.append(f"aws ec2 describe-instance-attribute --instance-id {instance_id} --attribute groupSet")

    elif "iam" in resource_type.lower():
        if "mfa" in title:
            scripts.append("# Enable MFA via Console: IAM > Users > Security credentials > MFA")
        if "key" in title and ("rotate" in title or "age" in title):
            scripts.append("# Rotate access keys: aws iam create-access-key / delete-access-key")
        if "policy" in title and ("admin" in title or "*" in title):
            scripts.append("# Review overly permissive IAM policy and scope down")

    if not scripts:
        aws_rec = finding.get("Remediation", {}).get("Recommendation", {}).get("Text", "")
        scripts.append(f"# AWS Recommendation: {aws_rec}" if aws_rec else "# Manual review required")
        url = finding.get("Remediation", {}).get("Recommendation", {}).get("Url", "")
        if url:
            scripts.append(f"# Reference: {url}")

    return scripts


def call_bedrock_analysis(finding):
    """Use Bedrock to generate an AI risk assessment of the finding.
    Tries models in succession order until one responds."""
    bedrock = boto3.client("bedrock-runtime", region_name=REGION)

    prompt = f"""You are SLyK, an AI security analyst. A Security Hub finding has been detected. Provide a brief risk assessment in 3-4 sentences covering:
1. What this finding means for the organization
2. The potential impact if not addressed
3. Priority level (Immediate/High/Medium)

Finding:
Title: {finding.get('Title', '')}
Severity: {finding.get('Severity', {}).get('Label', '')}
Description: {finding.get('Description', '')[:500]}
Resource: {finding.get('Resources', [{}])[0].get('Type', '')} - {finding.get('Resources', [{}])[0].get('Id', '')[:100]}
"""

    models_to_try = [BEDROCK_MODEL] + [m for m in BEDROCK_MODEL_CANDIDATES if m != BEDROCK_MODEL]

    for model_id in models_to_try:
        try:
            response = bedrock.converse(
                modelId=model_id,
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={"maxTokens": 500, "temperature": 0.3},
            )
            return response["output"]["message"]["content"][0]["text"]
        except Exception:
            continue

    return "AI analysis unavailable — no Bedrock models accessible"


def send_sns_alert(finding, nist_family, scripts, ai_analysis):
    """Send alert via SNS."""
    if not SNS_TOPIC_ARN:
        return False

    sns = boto3.client("sns", region_name=REGION)

    severity = finding.get("Severity", {}).get("Label", "UNKNOWN")
    title = finding.get("Title", "Unknown Finding")
    resources = finding.get("Resources", [])
    resource_id = resources[0].get("Id", "")[:80] if resources else "Unknown"
    product = finding.get("ProductName", finding.get("GeneratorId", "").split("/")[0])

    severity_emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡"}.get(severity, "⚪")

    message = f"""{severity_emoji} SLyK-53 SECURITY ALERT — {severity}

Finding: {title}
Severity: {severity}
Source: {product}
Resource: {resource_id}
NIST Family: {nist_family}
Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

── AI Risk Assessment ──
{ai_analysis}

── Recommended Remediation ──
{chr(10).join(scripts)}

── Action Required ──
Review and apply the remediation above, or ask SLyK:
  "Remediate finding {finding.get('Id', '')[:60]}"

This alert was generated automatically by SLyK-53 (SAE Lightweight Yaml Kit).
"""

    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"[SLyK-53] {severity} — {title[:80]}",
            Message=message,
        )
        return True
    except ClientError as e:
        print(f"SNS publish failed: {e}")
        return False


def log_to_s3(finding, nist_family, scripts, ai_analysis):
    """Log the alert to S3 for audit trail."""
    try:
        s3 = boto3.client("s3", region_name=REGION)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        finding_id = finding.get("Id", "unknown").split("/")[-1][:30]

        log_data = {
            "timestamp": timestamp,
            "finding_id": finding.get("Id", ""),
            "title": finding.get("Title", ""),
            "severity": finding.get("Severity", {}).get("Label", ""),
            "nist_family": nist_family,
            "resource": finding.get("Resources", [{}])[0].get("Id", ""),
            "remediation_scripts": scripts,
            "ai_analysis": ai_analysis,
            "alert_sent": bool(SNS_TOPIC_ARN),
        }

        s3.put_object(
            Bucket=S3_BUCKET,
            Key=f"slyk/alerts/{timestamp}_{finding_id}.json",
            Body=json.dumps(log_data, indent=2).encode("utf-8"),
            ContentType="application/json",
        )
    except Exception as e:
        print(f"S3 logging failed: {e}")


def handler(event, context):
    """
    EventBridge handler — triggered by Security Hub findings.

    Event format (from EventBridge):
    {
        "source": "aws.securityhub",
        "detail-type": "Security Hub Findings - Imported",
        "detail": {
            "findings": [{ ... finding object ... }]
        }
    }

    Can also be invoked directly by Bedrock Agent action group.
    """
    # Determine if this is an EventBridge event or Bedrock Agent call
    if event.get("source") == "aws.securityhub":
        # EventBridge trigger
        findings = event.get("detail", {}).get("findings", [])
    elif event.get("actionGroup"):
        # Bedrock Agent action group call
        params = {p["name"]: p["value"] for p in event.get("parameters", [])}
        severity = params.get("severity", "CRITICAL,HIGH")
        max_results = int(params.get("max_findings", "10"))

        sh = boto3.client("securityhub", region_name=REGION)
        resp = sh.get_findings(
            Filters={
                "SeverityLabel": [{"Value": s.strip(), "Comparison": "EQUALS"} for s in severity.split(",")],
                "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}],
                "WorkflowStatus": [{"Value": "NEW", "Comparison": "EQUALS"}],
            },
            MaxResults=max_results,
        )
        findings = resp.get("Findings", [])
    else:
        findings = []

    results = []

    for finding in findings:
        severity_label = finding.get("Severity", {}).get("Label", "")
        if severity_label not in ("CRITICAL", "HIGH"):
            continue

        resource_type = finding.get("Resources", [{}])[0].get("Type", "")
        nist_family = get_nist_family(resource_type)

        scripts = generate_auto_remediation(finding)
        ai_analysis = call_bedrock_analysis(finding)

        alert_sent = send_sns_alert(finding, nist_family, scripts, ai_analysis)
        log_to_s3(finding, nist_family, scripts, ai_analysis)

        results.append({
            "finding_id": finding.get("Id", ""),
            "title": finding.get("Title", ""),
            "severity": severity_label,
            "nist_family": nist_family,
            "remediation_scripts": scripts,
            "ai_analysis": ai_analysis,
            "alert_sent": alert_sent,
        })

    response_data = {
        "findings_processed": len(results),
        "alerts_sent": sum(1 for r in results if r["alert_sent"]),
        "results": results,
    }

    # Return format depends on caller
    if event.get("actionGroup"):
        body = json.dumps(response_data, default=str)
        if event.get("function"):
            return {"messageVersion": "1.0", "response": {"actionGroup": event.get("actionGroup", ""), "function": event.get("function", ""), "functionResponse": {"responseBody": {"TEXT": {"body": body}}}}}
        return {"messageVersion": "1.0", "response": {"actionGroup": event.get("actionGroup", ""), "apiPath": event.get("apiPath", ""), "httpMethod": "POST", "httpStatusCode": 200, "responseBody": {"application/json": {"body": body}}}}

    return response_data
