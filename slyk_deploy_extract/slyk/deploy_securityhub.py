#!/usr/bin/env python3
"""
Deploy Security Hub Integration for SLyK-53
============================================
Adds Security Hub findings capability to the SLyK-53 agent.

Usage:
    python3 deploy_securityhub.py
"""

import json
import os
import boto3
import zipfile
import tempfile
from botocore.exceptions import ClientError

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

# Colors
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
RED = "\033[0;31m"
NC = "\033[0m"


def log(msg):
    print(f"{BLUE}[securityhub]{NC} {msg}")


def ok(msg):
    print(f"{GREEN}  ✓{NC} {msg}")


def warn(msg):
    print(f"{YELLOW}  !{NC} {msg}")


def fail(msg):
    print(f"{RED}  ✗{NC} {msg}")


def get_account_id():
    sts = boto3.client("sts", region_name=REGION)
    return sts.get_caller_identity()["Account"]


def create_lambda_zip():
    """Create ZIP file for Lambda deployment."""
    lambda_dir = os.path.join(os.path.dirname(__file__), "lambda_functions")
    zip_path = os.path.join(tempfile.gettempdir(), "securityhub_lambda.zip")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        lambda_file = os.path.join(lambda_dir, "securityhub_findings.py")
        zf.write(lambda_file, "lambda_function.py")
    
    return zip_path


def deploy_lambda(account_id):
    """Deploy the Security Hub Lambda function."""
    log("Deploying Security Hub Lambda function...")
    
    lambda_client = boto3.client("lambda", region_name=REGION)
    function_name = "slyk-securityhub-findings"
    role_arn = f"arn:aws:iam::{account_id}:role/SLyK-Lambda-Role"
    
    # Create ZIP
    zip_path = create_lambda_zip()
    with open(zip_path, 'rb') as f:
        zip_bytes = f.read()
    
    try:
        # Try to update existing function
        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_bytes
        )
        ok(f"Updated Lambda: {function_name}")
    except ClientError as e:
        if "ResourceNotFoundException" in str(e):
            # Create new function
            lambda_client.create_function(
                FunctionName=function_name,
                Runtime="python3.11",
                Role=role_arn,
                Handler="lambda_function.lambda_handler",
                Code={"ZipFile": zip_bytes},
                Timeout=60,
                MemorySize=256,
                Description="SLyK-53 Security Hub Integration"
            )
            ok(f"Created Lambda: {function_name}")
        else:
            raise
    
    # Add Security Hub permissions to Lambda role
    iam = boto3.client("iam")
    policy_name = "SLyK-SecurityHub-Access"
    policy_doc = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "securityhub:GetFindings",
                    "securityhub:GetEnabledStandards",
                    "securityhub:DescribeHub",
                    "securityhub:ListFindingAggregators"
                ],
                "Resource": "*"
            }
        ]
    }
    
    try:
        iam.put_role_policy(
            RoleName="SLyK-Lambda-Role",
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_doc)
        )
        ok("Added Security Hub permissions to Lambda role")
    except ClientError as e:
        if "AccessDenied" in str(e):
            warn("Could not update IAM policy (AccessDenied) - may need admin")
        else:
            warn(f"Could not update IAM policy: {e}")
    
    # Clean up
    os.remove(zip_path)
    
    return f"arn:aws:lambda:{REGION}:{account_id}:function:{function_name}"


def add_resource_permission(account_id, lambda_arn):
    """Allow Bedrock to invoke the Lambda."""
    log("Adding Bedrock invoke permission...")
    
    lambda_client = boto3.client("lambda", region_name=REGION)
    
    try:
        lambda_client.add_permission(
            FunctionName="slyk-securityhub-findings",
            StatementId="AllowBedrockInvoke",
            Action="lambda:InvokeFunction",
            Principal="bedrock.amazonaws.com",
            SourceArn=f"arn:aws:bedrock:{REGION}:{account_id}:agent/*"
        )
        ok("Added Bedrock invoke permission")
    except ClientError as e:
        if "ResourceConflictException" in str(e):
            warn("Permission already exists")
        else:
            warn(f"Could not add permission: {e}")


def test_lambda():
    """Test the Lambda function."""
    log("Testing Security Hub Lambda...")
    
    lambda_client = boto3.client("lambda", region_name=REGION)
    
    try:
        response = lambda_client.invoke(
            FunctionName="slyk-securityhub-findings",
            InvocationType="RequestResponse",
            Payload=json.dumps({"action": "dashboard"})
        )
        
        result = json.loads(response["Payload"].read())
        
        if result.get("status") == "SUCCESS":
            ok(f"Lambda test passed - Found {result.get('total_active_findings', 0)} active findings")
            
            # Show summary
            print(f"\n{CYAN}Security Hub Summary:{NC}")
            severity = result.get("severity_summary", {})
            print(f"  CRITICAL: {severity.get('CRITICAL', 0)}")
            print(f"  HIGH:     {severity.get('HIGH', 0)}")
            print(f"  MEDIUM:   {severity.get('MEDIUM', 0)}")
            print(f"  LOW:      {severity.get('LOW', 0)}")
            
            if result.get("recent_alerts"):
                print(f"\n{CYAN}Recent Alerts:{NC}")
                for alert in result.get("recent_alerts", [])[:3]:
                    print(f"  [{alert['severity']}] {alert['title']}")
        else:
            warn(f"Lambda returned: {result}")
            
    except ClientError as e:
        fail(f"Lambda test failed: {e}")


def print_summary(account_id):
    print(f"""
{GREEN}╔═══════════════════════════════════════════════════════════════════════╗
║           SECURITY HUB INTEGRATION DEPLOYED!                           ║
╚═══════════════════════════════════════════════════════════════════════╝{NC}

  {CYAN}Lambda Function:{NC}
    Name: slyk-securityhub-findings
    ARN:  arn:aws:lambda:{REGION}:{account_id}:function:slyk-securityhub-findings

  {CYAN}Capabilities:{NC}
    • Get findings by NIST 800-53 control (AC-2, AU-6, CM-6, SI-2, RA-5)
    • Get CRITICAL and HIGH severity findings
    • Get compliance summary
    • Dashboard-formatted data for SLyK-View

  {CYAN}Test in Bedrock Agent:{NC}
    "Show me Security Hub findings for AC-2"
    "What are my critical Security Hub findings?"
    "Give me a Security Hub compliance summary"

  {CYAN}Next Steps:{NC}
    1. Update the Bedrock agent's action group to include this Lambda
    2. Update SLyK-View dashboard to display Security Hub data
""")


def main():
    print(f"""
{CYAN}╔═══════════════════════════════════════════════════════════════════════╗
║   SLyK-53 — Security Hub Integration Deployment                        ║
╚═══════════════════════════════════════════════════════════════════════╝{NC}
""")
    
    account_id = get_account_id()
    ok(f"AWS Account: {account_id}")
    ok(f"Region: {REGION}")
    print()
    
    lambda_arn = deploy_lambda(account_id)
    print()
    
    add_resource_permission(account_id, lambda_arn)
    print()
    
    test_lambda()
    
    print_summary(account_id)


if __name__ == "__main__":
    main()
