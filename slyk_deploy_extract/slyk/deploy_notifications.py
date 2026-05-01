#!/usr/bin/env python3
"""
SLyK-53 Email Notifications Setup
==================================
Creates SNS topic, EventBridge rules, and configures email notifications.

Usage (from CloudShell):
    python3 deploy_notifications.py

This will:
    1. Create an SNS topic for SLyK alerts
    2. Subscribe ira.perry@noaa.gov to the topic
    3. Create EventBridge rules to trigger on SLyK events
    4. Update Lambda functions to publish events
"""

import json
import os
import boto3
from botocore.exceptions import ClientError

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
VARIANT = os.environ.get("SLYK_VARIANT", "")
VARIANT_SUFFIX = f"-{VARIANT}" if VARIANT else ""

# Configuration
EMAIL_ADDRESS = "ira.perry@noaa.gov"
SNS_TOPIC_NAME = f"slyk{VARIANT_SUFFIX}-security-alerts"
EVENT_BUS_NAME = "default"

# Colors for output
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
NC = "\033[0m"


def log(msg):
    print(f"{BLUE}[slyk-notify]{NC} {msg}")


def ok(msg):
    print(f"{GREEN}  ✓{NC} {msg}")


def warn(msg):
    print(f"{YELLOW}  !{NC} {msg}")


def get_account_id():
    sts = boto3.client("sts", region_name=REGION)
    return sts.get_caller_identity()["Account"]


def create_sns_topic():
    """Create SNS topic for SLyK alerts."""
    log("Step 1: Creating SNS topic...")
    sns = boto3.client("sns", region_name=REGION)
    
    try:
        response = sns.create_topic(
            Name=SNS_TOPIC_NAME,
            Tags=[
                {"Key": "Application", "Value": "SLyK-53"},
                {"Key": "Purpose", "Value": "Security Alerts"},
            ]
        )
        topic_arn = response["TopicArn"]
        ok(f"Created SNS topic: {SNS_TOPIC_NAME}")
        ok(f"Topic ARN: {topic_arn}")
        return topic_arn
    except ClientError as e:
        if "already exists" in str(e).lower():
            # Get existing topic ARN
            account_id = get_account_id()
            topic_arn = f"arn:aws:sns:{REGION}:{account_id}:{SNS_TOPIC_NAME}"
            warn(f"Topic already exists: {topic_arn}")
            return topic_arn
        raise


def subscribe_email(topic_arn):
    """Subscribe email address to SNS topic."""
    log("Step 2: Subscribing email address...")
    sns = boto3.client("sns", region_name=REGION)
    
    # Check if already subscribed
    try:
        subs = sns.list_subscriptions_by_topic(TopicArn=topic_arn)
        for sub in subs.get("Subscriptions", []):
            if sub.get("Endpoint") == EMAIL_ADDRESS:
                warn(f"{EMAIL_ADDRESS} already subscribed")
                return sub.get("SubscriptionArn")
    except ClientError:
        pass
    
    try:
        response = sns.subscribe(
            TopicArn=topic_arn,
            Protocol="email",
            Endpoint=EMAIL_ADDRESS,
            ReturnSubscriptionArn=True
        )
        ok(f"Subscription created for {EMAIL_ADDRESS}")
        ok("CHECK YOUR EMAIL - You must confirm the subscription!")
        return response.get("SubscriptionArn")
    except ClientError as e:
        warn(f"Could not subscribe: {e}")
        return None


def create_eventbridge_rules(topic_arn):
    """Create EventBridge rules to trigger on SLyK events."""
    log("Step 3: Creating EventBridge rules...")
    events = boto3.client("events", region_name=REGION)
    account_id = get_account_id()
    
    # Rule 1: Assessment failures
    rules = [
        {
            "name": f"slyk{VARIANT_SUFFIX}-assessment-alerts",
            "description": "Trigger on SLyK assessment failures",
            "pattern": {
                "source": ["slyk.assess"],
                "detail-type": ["SLyK Assessment Result"],
                "detail": {
                    "status": ["FAIL", "WARNING"]
                }
            }
        },
        {
            "name": f"slyk{VARIANT_SUFFIX}-critical-findings",
            "description": "Trigger on critical security findings",
            "pattern": {
                "source": ["slyk.assess", "slyk.harden"],
                "detail-type": ["SLyK Security Finding"],
                "detail": {
                    "severity": ["CRITICAL", "HIGH"]
                }
            }
        },
        {
            "name": f"slyk{VARIANT_SUFFIX}-remediation-alerts",
            "description": "Trigger on remediation actions",
            "pattern": {
                "source": ["slyk.remediate"],
                "detail-type": ["SLyK Remediation Action"]
            }
        }
    ]
    
    for rule in rules:
        try:
            # Create the rule
            events.put_rule(
                Name=rule["name"],
                Description=rule["description"],
                EventPattern=json.dumps(rule["pattern"]),
                State="ENABLED",
                EventBusName=EVENT_BUS_NAME
            )
            ok(f"Created rule: {rule['name']}")
            
            # Add SNS target
            events.put_targets(
                Rule=rule["name"],
                EventBusName=EVENT_BUS_NAME,
                Targets=[
                    {
                        "Id": "sns-target",
                        "Arn": topic_arn,
                        "InputTransformer": {
                            "InputPathsMap": {
                                "source": "$.source",
                                "detail-type": "$.detail-type",
                                "time": "$.time",
                                "status": "$.detail.status",
                                "control": "$.detail.control_id",
                                "message": "$.detail.message",
                                "findings": "$.detail.findings"
                            },
                            "InputTemplate": '"SLyK-53 Security Alert\\n\\nSource: <source>\\nType: <detail-type>\\nTime: <time>\\nStatus: <status>\\nControl: <control>\\n\\nMessage: <message>\\n\\nFindings: <findings>"'
                        }
                    }
                ]
            )
            ok(f"Added SNS target to {rule['name']}")
            
        except ClientError as e:
            warn(f"Could not create rule {rule['name']}: {e}")
    
    # Grant EventBridge permission to publish to SNS
    sns = boto3.client("sns", region_name=REGION)
    try:
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AllowEventBridgePublish",
                    "Effect": "Allow",
                    "Principal": {"Service": "events.amazonaws.com"},
                    "Action": "sns:Publish",
                    "Resource": topic_arn
                }
            ]
        }
        sns.set_topic_attributes(
            TopicArn=topic_arn,
            AttributeName="Policy",
            AttributeValue=json.dumps(policy)
        )
        ok("Granted EventBridge permission to publish to SNS")
    except ClientError as e:
        warn(f"Could not set SNS policy: {e}")


def update_lambda_permissions():
    """Add EventBridge publish permissions to Lambda role."""
    log("Step 4: Updating Lambda permissions...")
    iam = boto3.client("iam")
    account_id = get_account_id()
    
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "events:PutEvents"
                ],
                "Resource": [
                    f"arn:aws:events:{REGION}:{account_id}:event-bus/default"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "sns:Publish"
                ],
                "Resource": [
                    f"arn:aws:sns:{REGION}:{account_id}:{SNS_TOPIC_NAME}"
                ]
            }
        ]
    }
    
    try:
        iam.put_role_policy(
            RoleName="SLyK-Lambda-Role",
            PolicyName="SLyK-Notification-Permissions",
            PolicyDocument=json.dumps(policy)
        )
        ok("Added EventBridge and SNS permissions to Lambda role")
    except ClientError as e:
        warn(f"Could not update Lambda role: {e}")


def print_summary(topic_arn):
    print(f"""
{GREEN}╔═══════════════════════════════════════════════════════════════════════╗
║           SLyK-53 NOTIFICATIONS CONFIGURED!                            ║
╚═══════════════════════════════════════════════════════════════════════╝{NC}

  {CYAN}Resources Created:{NC}
    SNS Topic:     {topic_arn}
    Email:         {EMAIL_ADDRESS}
    
  {CYAN}EventBridge Rules:{NC}
    • slyk{VARIANT_SUFFIX}-assessment-alerts   - Triggers on FAIL/WARNING assessments
    • slyk{VARIANT_SUFFIX}-critical-findings   - Triggers on CRITICAL/HIGH findings
    • slyk{VARIANT_SUFFIX}-remediation-alerts  - Triggers on remediation actions

  {YELLOW}IMPORTANT:{NC}
    Check your email ({EMAIL_ADDRESS}) and CONFIRM the subscription!
    You won't receive alerts until you click the confirmation link.

  {CYAN}How It Works:{NC}
    1. SLyK Lambda functions publish events to EventBridge
    2. EventBridge rules match security events
    3. Matching events trigger SNS notifications
    4. SNS sends email to {EMAIL_ADDRESS}

  {CYAN}Test It:{NC}
    In the Bedrock console, ask the agent:
    "Run an AC-2 assessment"
    
    If any controls fail, you'll receive an email alert.
""")


def main():
    print(f"""
{CYAN}╔═══════════════════════════════════════════════════════════════════════╗
║   SLyK-53 — Email Notification Setup                                   ║
╚═══════════════════════════════════════════════════════════════════════╝{NC}
""")
    
    account_id = get_account_id()
    ok(f"AWS Account: {account_id}")
    ok(f"Region: {REGION}")
    print()
    
    topic_arn = create_sns_topic()
    print()
    
    subscribe_email(topic_arn)
    print()
    
    create_eventbridge_rules(topic_arn)
    print()
    
    update_lambda_permissions()
    print()
    
    print_summary(topic_arn)


if __name__ == "__main__":
    main()
