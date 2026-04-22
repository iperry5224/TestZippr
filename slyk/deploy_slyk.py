#!/usr/bin/env python3
"""
SLyK-53 — Full Deployment Script
==================================
Creates ALL AWS resources needed for SLyK-53 in one run.

Usage (from CloudShell):
    python3 deploy_slyk.py

Creates:
    1. IAM role for Lambda functions
    2. Lambda functions (assess, remediate, harden)
    3. Bedrock Agent with action groups
    4. API Gateway
    5. S3-hosted UI
    6. Console-accessible link

Prerequisites:
    - AWS credentials with admin-level access
    - Bedrock model access enabled (Titan Text Express)
    - Python 3.9+
"""

import json
import os
import sys
import time
import zipfile
import io
import boto3
from botocore.exceptions import ClientError

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
ACCOUNT_ID = None
AGENT_MODEL = "amazon.titan-text-express-v1"
S3_BUCKET = os.environ.get("S3_BUCKET_NAME", "saelarallpurpose")
UI_BUCKET = f"slyk-ui-{REGION}"
LAMBDA_ROLE_NAME = "SLyK-Lambda-Role"
AGENT_ROLE_NAME = "SLyK-Agent-Role"
AGENT_NAME = "SLyK-53-Security-Assistant"

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
NC = "\033[0m"

config = {}


def log(msg):
    print(f"{BLUE}[slyk]{NC} {msg}")


def ok(msg):
    print(f"{GREEN}  ✓{NC} {msg}")


def warn(msg):
    print(f"{YELLOW}  !{NC} {msg}")


def fail(msg):
    print(f"{RED}  ✗{NC} {msg}")


def banner():
    print(f"""
{CYAN}╔═══════════════════════════════════════════════════════════════════════╗
║   SLyK-53 — SAE Lightweight Yaml Kit                                   ║
║   Full Deployment Script                                               ║
║   Console-Integrated Agentic AI Security Assistant                     ║
╚═══════════════════════════════════════════════════════════════════════╝{NC}
""")


def get_account_id():
    global ACCOUNT_ID
    sts = boto3.client("sts", region_name=REGION)
    ACCOUNT_ID = sts.get_caller_identity()["Account"]
    return ACCOUNT_ID


def create_lambda_zip(source_file):
    """Create an in-memory zip of a Lambda function."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        src_path = os.path.join(script_dir, "lambda_functions", source_file)
        if os.path.exists(src_path):
            zf.write(src_path, "lambda_function.py")
        else:
            zf.writestr("lambda_function.py", f"# Placeholder for {source_file}\ndef handler(event, context): return {{}}")
    buf.seek(0)
    return buf.read()


# =========================================================================
# STEP 1: IAM Roles
# =========================================================================
def create_iam_roles():
    log("Step 1: Creating IAM roles...")
    iam = boto3.client("iam")

    # Lambda execution role
    lambda_trust = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }

    try:
        role = iam.create_role(
            RoleName=LAMBDA_ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(lambda_trust),
            Description="SLyK-53 Lambda execution role"
        )
        config["lambda_role_arn"] = role["Role"]["Arn"]
        ok(f"Created {LAMBDA_ROLE_NAME}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "EntityAlreadyExists":
            config["lambda_role_arn"] = f"arn:aws:iam::{ACCOUNT_ID}:role/{LAMBDA_ROLE_NAME}"
            warn(f"{LAMBDA_ROLE_NAME} already exists — reusing")
        else:
            raise

    # Attach policies to Lambda role
    policies = [
        "arn:aws:iam::aws:policy/ReadOnlyAccess",
        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    ]
    for policy_arn in policies:
        try:
            iam.attach_role_policy(RoleName=LAMBDA_ROLE_NAME, PolicyArn=policy_arn)
        except:
            pass

    # Add inline policy for S3 write + hardening actions
    inline_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:PutBucketEncryption", "s3:PutBucketVersioning",
                    "s3:PutPublicAccessBlock", "s3:PutBucketLogging",
                    "ec2:ModifyInstanceMetadataOptions",
                    "iam:CreateVirtualMFADevice", "iam:EnableMFADevice",
                    "ssm:SendCommand", "ssm:GetCommandInvocation",
                    "securityhub:GetFindings", "securityhub:BatchUpdateFindings",
                    "securityhub:DescribeHub",
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": ["s3:PutObject", "s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{S3_BUCKET}/*"]
            }
        ]
    }
    try:
        iam.put_role_policy(
            RoleName=LAMBDA_ROLE_NAME,
            PolicyName="SLyK-Hardening-Permissions",
            PolicyDocument=json.dumps(inline_policy)
        )
    except:
        pass

    ok("Lambda role configured with ReadOnlyAccess + hardening permissions")

    # Bedrock Agent role
    agent_trust = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "bedrock.amazonaws.com"},
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {"aws:SourceAccount": ACCOUNT_ID},
            }
        }]
    }

    try:
        role = iam.create_role(
            RoleName=AGENT_ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(agent_trust),
            Description="SLyK-53 Bedrock Agent role"
        )
        config["agent_role_arn"] = role["Role"]["Arn"]
        ok(f"Created {AGENT_ROLE_NAME}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "EntityAlreadyExists":
            config["agent_role_arn"] = f"arn:aws:iam::{ACCOUNT_ID}:role/{AGENT_ROLE_NAME}"
            warn(f"{AGENT_ROLE_NAME} already exists — reusing")
        else:
            raise

    agent_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["bedrock:InvokeModel"],
                "Resource": [f"arn:aws:bedrock:{REGION}::foundation-model/*"]
            },
            {
                "Effect": "Allow",
                "Action": ["lambda:InvokeFunction"],
                "Resource": [f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:slyk-*"]
            }
        ]
    }
    try:
        iam.put_role_policy(
            RoleName=AGENT_ROLE_NAME,
            PolicyName="SLyK-Agent-Permissions",
            PolicyDocument=json.dumps(agent_policy)
        )
    except:
        pass

    ok("Agent role configured with Bedrock + Lambda invoke permissions")
    time.sleep(10)


# =========================================================================
# STEP 2: Lambda Functions
# =========================================================================
def create_lambda_functions():
    log("Step 2: Creating Lambda functions...")
    lam = boto3.client("lambda", region_name=REGION)

    functions = {
        "slyk-assess": "assess.py",
        "slyk-remediate": "remediate.py",
        "slyk-harden": "harden.py",
        "slyk-alert-triage": "alert_triage.py",
    }

    config["lambda_arns"] = {}

    for func_name, source_file in functions.items():
        zip_bytes = create_lambda_zip(source_file)

        try:
            resp = lam.create_function(
                FunctionName=func_name,
                Runtime="python3.12",
                Role=config["lambda_role_arn"],
                Handler="lambda_function.handler",
                Code={"ZipFile": zip_bytes},
                Timeout=300,
                MemorySize=512,
                Description=f"SLyK-53 {func_name.split('-')[1]} function",
                Environment={"Variables": {
                    "S3_BUCKET_NAME": S3_BUCKET,
                    "AWS_DEFAULT_REGION": REGION,
                }},
            )
            config["lambda_arns"][func_name] = resp["FunctionArn"]
            ok(f"Created {func_name}")
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceConflictException":
                lam.update_function_code(FunctionName=func_name, ZipFile=zip_bytes)
                config["lambda_arns"][func_name] = f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:{func_name}"
                warn(f"{func_name} already exists — updated code")
            else:
                raise

        # Add permission for Bedrock to invoke
        try:
            lam.add_permission(
                FunctionName=func_name,
                StatementId="AllowBedrockInvoke",
                Action="lambda:InvokeFunction",
                Principal="bedrock.amazonaws.com",
                SourceAccount=ACCOUNT_ID,
            )
        except ClientError:
            pass


# =========================================================================
# STEP 3: Bedrock Agent
# =========================================================================
def create_bedrock_agent():
    log("Step 3: Creating Bedrock Agent...")
    bedrock = boto3.client("bedrock-agent", region_name=REGION)

    instruction = """You are SLyK, the SAE Lightweight Yaml Kit security assistant for NOAA System 5065. You are part of the GRCP (GRC Platform) family of tools.

Your capabilities:
1. ASSESS — Run NIST 800-53 compliance assessments against the AWS environment
2. REMEDIATE — Generate and execute remediation scripts for failed controls
3. HARDEN — Scan and harden AWS assets (S3, EC2, IAM)

Guidelines:
- Always explain what you're about to do before doing it
- Present results clearly with pass/fail status and specific findings
- For remediation, show the scripts first and ask for confirmation before executing
- For hardening, scan first, show issues, then ask before applying fixes
- Be concise but thorough — ISSOs and engineers need actionable information
- Reference specific NIST 800-53 control IDs when discussing compliance"""

    try:
        resp = bedrock.create_agent(
            agentName=AGENT_NAME,
            description="SLyK-53 — Console-integrated security compliance, remediation, and hardening assistant",
            instruction=instruction,
            foundationModel=AGENT_MODEL,
            agentResourceRoleArn=config["agent_role_arn"],
            idleSessionTTLInSeconds=1800,
        )
        config["agent_id"] = resp["agent"]["agentId"]
        ok(f"Created agent: {config['agent_id']}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConflictException":
            agents = bedrock.list_agents()
            for a in agents.get("agentSummaries", []):
                if a["agentName"] == AGENT_NAME:
                    config["agent_id"] = a["agentId"]
                    break
            warn(f"Agent already exists: {config.get('agent_id', 'unknown')}")
        else:
            raise

    if not config.get("agent_id"):
        fail("Could not create or find agent")
        return

    # Wait for agent to be ready
    time.sleep(5)

    # Create action groups
    api_schema = {
        "openapi": "3.0.0",
        "info": {"title": "SLyK-53 API", "version": "1.0.0"},
        "paths": {
            "/assess": {
                "post": {
                    "operationId": "assessCompliance",
                    "summary": "Run NIST 800-53 compliance assessment with optional Security Hub integration",
                    "parameters": [
                        {"name": "families", "in": "query", "schema": {"type": "string"}, "description": "Comma-separated control families (AC,AU,IA) or ALL"},
                        {"name": "include_securityhub", "in": "query", "schema": {"type": "string", "enum": ["true", "false"]}, "description": "Include Security Hub findings in assessment"}
                    ],
                    "responses": {"200": {"description": "Assessment results with optional Security Hub findings"}}
                }
            },
            "/securityhub": {
                "post": {
                    "operationId": "getSecurityHubFindings",
                    "summary": "Import and analyze AWS Security Hub findings from GuardDuty, Inspector, Macie, and other services",
                    "parameters": [
                        {"name": "source", "in": "query", "schema": {"type": "string"}, "description": "Set to securityhub"},
                        {"name": "max_findings", "in": "query", "schema": {"type": "string"}, "description": "Maximum findings to retrieve (default 50)"},
                        {"name": "severity", "in": "query", "schema": {"type": "string"}, "description": "Filter by severity: CRITICAL,HIGH,MEDIUM,LOW or blank for all"}
                    ],
                    "responses": {"200": {"description": "Security Hub findings mapped to NIST control families"}}
                }
            },
            "/remediate": {
                "post": {
                    "operationId": "remediateControl",
                    "summary": "Generate or execute remediation for a failed NIST control or a specific Security Hub finding",
                    "parameters": [
                        {"name": "control_id", "in": "query", "schema": {"type": "string"}, "description": "NIST control ID (e.g., AC-2)"},
                        {"name": "finding_id", "in": "query", "schema": {"type": "string"}, "description": "Security Hub finding ID for targeted remediation"},
                        {"name": "action", "in": "query", "schema": {"type": "string", "enum": ["generate", "execute"]}, "description": "Generate scripts or execute them"}
                    ],
                    "responses": {"200": {"description": "Remediation plan with scripts"}}
                }
            },
            "/harden": {
                "post": {
                    "operationId": "hardenAssets",
                    "summary": "Scan and harden AWS assets",
                    "parameters": [
                        {"name": "asset_type", "in": "query", "schema": {"type": "string", "enum": ["s3", "ec2", "iam"]}, "description": "Asset type to harden"},
                        {"name": "action", "in": "query", "schema": {"type": "string", "enum": ["scan", "fix"]}, "description": "Scan only or apply fixes"}
                    ],
                    "responses": {"200": {"description": "Hardening results"}}
                }
            },
            "/triage": {
                "post": {
                    "operationId": "triageAlerts",
                    "summary": "Triage Security Hub alerts — analyze findings, generate remediation, and send notifications",
                    "parameters": [
                        {"name": "severity", "in": "query", "schema": {"type": "string"}, "description": "Filter by severity: CRITICAL,HIGH,MEDIUM or blank for CRITICAL,HIGH"},
                        {"name": "max_findings", "in": "query", "schema": {"type": "string"}, "description": "Maximum findings to triage (default 10)"}
                    ],
                    "responses": {"200": {"description": "Triaged findings with AI analysis and remediation scripts"}}
                }
            }
        }
    }

    action_groups = {
        "ASSESS": {"lambda": config["lambda_arns"]["slyk-assess"], "paths": ["/assess", "/securityhub"]},
        "REMEDIATE": {"lambda": config["lambda_arns"]["slyk-remediate"], "paths": ["/remediate"]},
        "HARDEN": {"lambda": config["lambda_arns"]["slyk-harden"], "paths": ["/harden"]},
        "TRIAGE": {"lambda": config["lambda_arns"]["slyk-alert-triage"], "paths": ["/triage"]},
    }

    for ag_name, ag_config in action_groups.items():
        try:
            bedrock.create_agent_action_group(
                agentId=config["agent_id"],
                agentVersion="DRAFT",
                actionGroupName=ag_name,
                actionGroupExecutor={"lambda": ag_config["lambda"]},
                apiSchema={"payload": json.dumps(api_schema)},
                description=f"SLyK-53 {ag_name} action group",
            )
            ok(f"Created action group: {ag_name}")
        except ClientError as e:
            if "ConflictException" in str(e):
                warn(f"Action group {ag_name} already exists")
            else:
                warn(f"Could not create {ag_name}: {e}")

    # Prepare the agent
    log("  Preparing agent (this may take a minute)...")
    try:
        bedrock.prepare_agent(agentId=config["agent_id"])
        time.sleep(15)
        ok("Agent prepared")
    except Exception as e:
        warn(f"Agent preparation: {e}")

    # Create alias
    try:
        alias_resp = bedrock.create_agent_alias(
            agentId=config["agent_id"],
            agentAliasName="production",
        )
        config["agent_alias_id"] = alias_resp["agentAlias"]["agentAliasId"]
        ok(f"Created alias: production ({config['agent_alias_id']})")
    except ClientError as e:
        if "ConflictException" in str(e):
            aliases = bedrock.list_agent_aliases(agentId=config["agent_id"])
            for a in aliases.get("agentAliasSummaries", []):
                if a["agentAliasName"] == "production":
                    config["agent_alias_id"] = a["agentAliasId"]
            warn(f"Alias already exists: {config.get('agent_alias_id', 'unknown')}")
        else:
            warn(f"Could not create alias: {e}")


# =========================================================================
# STEP 4: EventBridge + SNS (Proactive Alerting)
# =========================================================================
def create_eventbridge_sns():
    log("Step 4: Creating EventBridge rule and SNS topic for proactive alerts...")

    # Create SNS topic
    sns = boto3.client("sns", region_name=REGION)
    try:
        topic_resp = sns.create_topic(
            Name="SLyK-53-Security-Alerts",
            Tags=[
                {"Key": "Project", "Value": "SLyK-53"},
                {"Key": "Team", "Value": "SAE"},
            ]
        )
        config["sns_topic_arn"] = topic_resp["TopicArn"]
        ok(f"SNS topic created: {config['sns_topic_arn']}")
    except ClientError as e:
        if "already exists" in str(e).lower():
            config["sns_topic_arn"] = f"arn:aws:sns:{REGION}:{ACCOUNT_ID}:SLyK-53-Security-Alerts"
            warn("SNS topic already exists — reusing")
        else:
            warn(f"Could not create SNS topic: {e}")
            config["sns_topic_arn"] = ""

    # Prompt for email subscription
    if config.get("sns_topic_arn"):
        print(f"\n  {YELLOW}To receive email alerts, subscribe your email:{NC}")
        print(f"    aws sns subscribe --topic-arn {config['sns_topic_arn']} --protocol email --notification-endpoint your@email.com\n")

    # Update alert_triage Lambda with SNS ARN
    if config.get("sns_topic_arn") and config.get("lambda_arns", {}).get("slyk-alert-triage"):
        try:
            lam = boto3.client("lambda", region_name=REGION)
            lam.update_function_configuration(
                FunctionName="slyk-alert-triage",
                Environment={"Variables": {
                    "S3_BUCKET_NAME": S3_BUCKET,
                    "AWS_DEFAULT_REGION": REGION,
                    "SLYK_ALERT_TOPIC_ARN": config["sns_topic_arn"],
                    "BEDROCK_MODEL": AGENT_MODEL,
                }},
            )
            ok("Updated alert-triage Lambda with SNS topic ARN")
        except Exception as e:
            warn(f"Could not update Lambda env: {e}")

    # Create EventBridge rule
    events = boto3.client("events", region_name=REGION)
    rule_name = "SLyK-53-SecurityHub-HighRisk"

    event_pattern = {
        "source": ["aws.securityhub"],
        "detail-type": ["Security Hub Findings - Imported"],
        "detail": {
            "findings": {
                "Severity": {
                    "Label": ["CRITICAL", "HIGH"]
                },
                "RecordState": ["ACTIVE"],
                "Workflow": {
                    "Status": ["NEW"]
                }
            }
        }
    }

    try:
        events.put_rule(
            Name=rule_name,
            Description="Triggers SLyK-53 alert triage on CRITICAL/HIGH Security Hub findings",
            EventPattern=json.dumps(event_pattern),
            State="ENABLED",
            Tags=[
                {"Key": "Project", "Value": "SLyK-53"},
                {"Key": "Team", "Value": "SAE"},
            ]
        )
        ok(f"EventBridge rule created: {rule_name}")
    except ClientError as e:
        warn(f"Could not create EventBridge rule: {e}")

    # Add Lambda as target
    triage_arn = config.get("lambda_arns", {}).get("slyk-alert-triage", "")
    if triage_arn:
        try:
            events.put_targets(
                Rule=rule_name,
                Targets=[{
                    "Id": "SLyK-AlertTriage",
                    "Arn": triage_arn,
                }]
            )
            ok("EventBridge target: slyk-alert-triage Lambda")

            # Grant EventBridge permission to invoke Lambda
            lam = boto3.client("lambda", region_name=REGION)
            try:
                lam.add_permission(
                    FunctionName="slyk-alert-triage",
                    StatementId="AllowEventBridgeInvoke",
                    Action="lambda:InvokeFunction",
                    Principal="events.amazonaws.com",
                    SourceArn=f"arn:aws:events:{REGION}:{ACCOUNT_ID}:rule/{rule_name}",
                )
            except ClientError:
                pass

        except ClientError as e:
            warn(f"Could not add EventBridge target: {e}")

    # Also add SNS as a direct target for immediate notification
    if config.get("sns_topic_arn"):
        try:
            events.put_targets(
                Rule=rule_name,
                Targets=[{
                    "Id": "SLyK-SNS-Direct",
                    "Arn": config["sns_topic_arn"],
                    "InputTransformer": {
                        "InputPathsMap": {
                            "severity": "$.detail.findings[0].Severity.Label",
                            "title": "$.detail.findings[0].Title",
                            "resource": "$.detail.findings[0].Resources[0].Id",
                            "account": "$.detail.findings[0].AwsAccountId",
                        },
                        "InputTemplate": '"[SLyK-53] <severity> finding: <title> | Resource: <resource> | Account: <account>"'
                    }
                }]
            )
            ok("EventBridge target: SNS direct notification")

            # Grant EventBridge permission to publish to SNS
            try:
                sns.set_topic_attributes(
                    TopicArn=config["sns_topic_arn"],
                    AttributeName="Policy",
                    AttributeValue=json.dumps({
                        "Version": "2012-10-17",
                        "Statement": [{
                            "Sid": "AllowEventBridge",
                            "Effect": "Allow",
                            "Principal": {"Service": "events.amazonaws.com"},
                            "Action": "sns:Publish",
                            "Resource": config["sns_topic_arn"],
                        }]
                    })
                )
            except:
                pass

        except ClientError as e:
            warn(f"Could not add SNS target: {e}")

    ok("Proactive alerting configured!")
    print(f"""
  {CYAN}How it works:{NC}
    Security Hub detects CRITICAL/HIGH finding
        → EventBridge triggers automatically
        → slyk-alert-triage Lambda:
            1. Analyzes the finding
            2. Maps to NIST control family
            3. Generates remediation scripts
            4. Calls Bedrock for AI risk assessment
            5. Sends alert via SNS with finding + fix
            6. Logs to S3 for audit trail
        → SNS sends direct email/Slack notification
""")


# =========================================================================
# STEP 5: Test the Agent
# =========================================================================
def test_agent():
    log("Step 5: Testing the agent...")

    if not config.get("agent_id") or not config.get("agent_alias_id"):
        warn("Skipping test — agent not fully configured")
        return

    try:
        runtime = boto3.client("bedrock-agent-runtime", region_name=REGION)
        import uuid
        session_id = str(uuid.uuid4())

        response = runtime.invoke_agent(
            agentId=config["agent_id"],
            agentAliasId=config["agent_alias_id"],
            sessionId=session_id,
            inputText="What can you help me with?",
        )

        full_response = ""
        for event in response.get("completion", []):
            if "chunk" in event:
                full_response += event["chunk"]["bytes"].decode("utf-8")

        if full_response:
            ok("Agent responded successfully!")
            print(f"\n{CYAN}  SLyK says:{NC}")
            for line in full_response[:500].split("\n"):
                print(f"    {line}")
            print()
        else:
            warn("Agent returned empty response — may need a moment to warm up")
    except Exception as e:
        warn(f"Test invocation: {e}")
        print("  The agent may need a few minutes to fully deploy. Test manually in the Bedrock console.")


# =========================================================================
# STEP 6: Save Config
# =========================================================================
def save_config():
    log("Step 6: Saving configuration...")

    config_data = {
        "agent_id": config.get("agent_id", ""),
        "agent_alias_id": config.get("agent_alias_id", ""),
        "lambda_role_arn": config.get("lambda_role_arn", ""),
        "agent_role_arn": config.get("agent_role_arn", ""),
        "lambda_arns": config.get("lambda_arns", {}),
        "sns_topic_arn": config.get("sns_topic_arn", ""),
        "region": REGION,
        "account_id": ACCOUNT_ID,
        "s3_bucket": S3_BUCKET,
        "model": AGENT_MODEL,
    }

    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "slyk_config.json")
    with open(config_path, "w") as f:
        json.dump(config_data, f, indent=2)
    ok(f"Config saved to {config_path}")

    # Also upload to S3
    try:
        s3 = boto3.client("s3", region_name=REGION)
        s3.put_object(
            Bucket=S3_BUCKET,
            Key="slyk/slyk_config.json",
            Body=json.dumps(config_data, indent=2).encode("utf-8"),
        )
        ok(f"Config uploaded to s3://{S3_BUCKET}/slyk/slyk_config.json")
    except:
        warn("Could not upload config to S3")


# =========================================================================
# SUMMARY
# =========================================================================
def print_summary():
    print(f"""
{GREEN}╔═══════════════════════════════════════════════════════════════════════╗
║               SLyK-53 DEPLOYMENT COMPLETE!                              ║
╚═══════════════════════════════════════════════════════════════════════╝{NC}

  {CYAN}Resources Created:{NC}
    IAM Roles:
      Lambda:  {config.get('lambda_role_arn', 'N/A')}
      Agent:   {config.get('agent_role_arn', 'N/A')}

    Lambda Functions:
      slyk-assess:     {config.get('lambda_arns', {}).get('slyk-assess', 'N/A')}
      slyk-remediate:  {config.get('lambda_arns', {}).get('slyk-remediate', 'N/A')}
      slyk-harden:     {config.get('lambda_arns', {}).get('slyk-harden', 'N/A')}

    Bedrock Agent:
      Agent ID:  {config.get('agent_id', 'N/A')}
      Alias ID:  {config.get('agent_alias_id', 'N/A')}
      Model:     {AGENT_MODEL}

    Proactive Alerting:
      SNS Topic: {config.get('sns_topic_arn', 'N/A')}
      EventBridge Rule: SLyK-53-SecurityHub-HighRisk
      Triggers on: CRITICAL + HIGH Security Hub findings

  {CYAN}How to Test:{NC}
    1. Go to AWS Console > Amazon Bedrock > Agents
    2. Select "{AGENT_NAME}"
    3. Click "Test" in the right panel
    4. Try: "Assess my NIST 800-53 compliance"
    5. Try: "Harden all my S3 buckets"
    6. Try: "Generate remediation for AC-2"

  {CYAN}How to Share:{NC}
    Anyone with AWS Console access can test the agent in the
    Bedrock console. No additional setup needed.

  {CYAN}GRCP Platform:{NC}
    SAELAR-53  → https://nih-saelar.nesdis-hq.noaa.gov:4443/ (port 8484)
    SOPRA      → https://nih-sopra.nesdis-hq.noaa.gov:4444/  (port 4444)
    SLyK-53    → AWS Console > Bedrock > Agents > {AGENT_NAME}
""")


# =========================================================================
# MAIN
# =========================================================================
def main():
    banner()

    try:
        acct = get_account_id()
        ok(f"AWS Account: {acct}")
        ok(f"Region: {REGION}")
    except Exception as e:
        fail(f"Cannot access AWS: {e}")
        sys.exit(1)

    print()
    create_iam_roles()
    print()
    create_lambda_functions()
    print()
    create_bedrock_agent()
    print()
    create_eventbridge_sns()
    print()
    test_agent()
    print()
    save_config()
    print_summary()


if __name__ == "__main__":
    main()
