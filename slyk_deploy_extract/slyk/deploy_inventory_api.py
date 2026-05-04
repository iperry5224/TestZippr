#!/usr/bin/env python3
"""
Deploy Inventory Lambda + API Gateway Endpoint
===============================================
Creates Lambda function for real AWS inventory and adds /inventory endpoint.

Usage:
    python3 deploy_inventory_api.py
"""

import json
import os
import time
import zipfile
import tempfile
import boto3
from botocore.exceptions import ClientError

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
LAMBDA_NAME = "slyk-inventory"
API_NAME = "slyk-view-api"

# Colors
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
RED = "\033[0;31m"
NC = "\033[0m"


def log(msg):
    print(f"{BLUE}[inventory]{NC} {msg}")


def ok(msg):
    print(f"{GREEN}  ✓{NC} {msg}")


def warn(msg):
    print(f"{YELLOW}  !{NC} {msg}")


def fail(msg):
    print(f"{RED}  ✗{NC} {msg}")


def get_account_id():
    sts = boto3.client("sts", region_name=REGION)
    return sts.get_caller_identity()["Account"]


def create_lambda_role(account_id):
    """Create IAM role for the inventory Lambda."""
    iam = boto3.client("iam", region_name=REGION)
    role_name = f"{LAMBDA_NAME}-role"
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    
    # Check if role exists
    try:
        role = iam.get_role(RoleName=role_name)
        ok(f"Role already exists: {role_name}")
        return role["Role"]["Arn"]
    except ClientError:
        pass
    
    # Create role
    role = iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description="Role for SLyK inventory Lambda"
    )
    role_arn = role["Role"]["Arn"]
    ok(f"Created role: {role_name}")
    
    # Attach policies
    policies = [
        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
        "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess",
        "arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess",
        "arn:aws:iam::aws:policy/IAMReadOnlyAccess",
        "arn:aws:iam::aws:policy/AmazonRDSReadOnlyAccess",
    ]
    
    for policy_arn in policies:
        try:
            iam.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
            ok(f"Attached: {policy_arn.split('/')[-1]}")
        except ClientError as e:
            warn(f"Could not attach {policy_arn}: {e}")
    
    # Wait for role to propagate
    log("Waiting for role to propagate...")
    time.sleep(10)
    
    return role_arn


def deploy_lambda(account_id, role_arn):
    """Deploy the inventory Lambda function."""
    lambda_client = boto3.client("lambda", region_name=REGION)
    
    # Create ZIP
    lambda_dir = os.path.dirname(os.path.abspath(__file__))
    lambda_file = os.path.join(lambda_dir, "lambda_functions", "inventory.py")
    
    zip_path = os.path.join(tempfile.gettempdir(), "inventory_lambda.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(lambda_file, "lambda_function.py")
    
    with open(zip_path, 'rb') as f:
        zip_bytes = f.read()
    
    # Check if Lambda exists
    try:
        lambda_client.get_function(FunctionName=LAMBDA_NAME)
        # Update existing
        lambda_client.update_function_code(
            FunctionName=LAMBDA_NAME,
            ZipFile=zip_bytes
        )
        ok(f"Updated Lambda: {LAMBDA_NAME}")
    except ClientError:
        # Create new
        lambda_client.create_function(
            FunctionName=LAMBDA_NAME,
            Runtime="python3.11",
            Role=role_arn,
            Handler="lambda_function.lambda_handler",
            Code={"ZipFile": zip_bytes},
            Description="SLyK-View inventory - fetches real AWS resources",
            Timeout=60,
            MemorySize=256
        )
        ok(f"Created Lambda: {LAMBDA_NAME}")
    
    os.remove(zip_path)
    return f"arn:aws:lambda:{REGION}:{account_id}:function:{LAMBDA_NAME}"


def add_api_endpoint(account_id, lambda_arn):
    """Add /inventory endpoint to existing API Gateway."""
    apigw = boto3.client("apigateway", region_name=REGION)
    lambda_client = boto3.client("lambda", region_name=REGION)
    
    # Find existing API
    api_id = None
    apis = apigw.get_rest_apis()
    for api in apis.get("items", []):
        if api["name"] == API_NAME:
            api_id = api["id"]
            break
    
    if not api_id:
        fail(f"API '{API_NAME}' not found. Run deploy_api_gateway.py first.")
        return None
    
    ok(f"Found API: {api_id}")
    
    # Get root resource
    resources = apigw.get_resources(restApiId=api_id)
    root_id = None
    inventory_exists = False
    
    for resource in resources["items"]:
        if resource.get("path") == "/":
            root_id = resource["id"]
        if resource.get("path") == "/inventory":
            inventory_exists = True
            inventory_id = resource["id"]
    
    if inventory_exists:
        warn("/inventory endpoint already exists, updating...")
    else:
        # Create /inventory resource
        inventory_resource = apigw.create_resource(
            restApiId=api_id,
            parentId=root_id,
            pathPart="inventory"
        )
        inventory_id = inventory_resource["id"]
        ok("Created /inventory resource")
    
    # Create/update GET method
    try:
        apigw.put_method(
            restApiId=api_id,
            resourceId=inventory_id,
            httpMethod="GET",
            authorizationType="NONE"
        )
    except ClientError:
        pass  # Method already exists
    
    # Lambda integration
    apigw.put_integration(
        restApiId=api_id,
        resourceId=inventory_id,
        httpMethod="GET",
        type="AWS_PROXY",
        integrationHttpMethod="POST",
        uri=f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
    )
    ok("Configured Lambda integration")
    
    # Add Lambda permission
    try:
        lambda_client.add_permission(
            FunctionName=LAMBDA_NAME,
            StatementId=f"apigateway-inventory-{api_id}",
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
            SourceArn=f"arn:aws:execute-api:{REGION}:{account_id}:{api_id}/*"
        )
        ok("Added API Gateway invoke permission")
    except ClientError as e:
        if "ResourceConflictException" in str(e):
            warn("Lambda permission already exists")
        else:
            warn(f"Could not add permission: {e}")
    
    # Enable CORS
    try:
        apigw.put_method(
            restApiId=api_id,
            resourceId=inventory_id,
            httpMethod="OPTIONS",
            authorizationType="NONE"
        )
    except ClientError:
        pass
    
    apigw.put_integration(
        restApiId=api_id,
        resourceId=inventory_id,
        httpMethod="OPTIONS",
        type="MOCK",
        requestTemplates={"application/json": '{"statusCode": 200}'}
    )
    
    try:
        apigw.put_method_response(
            restApiId=api_id,
            resourceId=inventory_id,
            httpMethod="OPTIONS",
            statusCode="200",
            responseParameters={
                "method.response.header.Access-Control-Allow-Headers": True,
                "method.response.header.Access-Control-Allow-Methods": True,
                "method.response.header.Access-Control-Allow-Origin": True
            }
        )
    except ClientError:
        pass
    
    apigw.put_integration_response(
        restApiId=api_id,
        resourceId=inventory_id,
        httpMethod="OPTIONS",
        statusCode="200",
        responseParameters={
            "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key'",
            "method.response.header.Access-Control-Allow-Methods": "'GET,OPTIONS'",
            "method.response.header.Access-Control-Allow-Origin": "'*'"
        }
    )
    ok("Enabled CORS")
    
    # Deploy API
    apigw.create_deployment(
        restApiId=api_id,
        stageName="prod",
        description="Added inventory endpoint"
    )
    ok("Deployed to 'prod' stage")
    
    return api_id


def print_summary(account_id, api_id):
    api_url = f"https://{api_id}.execute-api.{REGION}.amazonaws.com/prod"
    
    print(f"""
{GREEN}╔═══════════════════════════════════════════════════════════════════════╗
║              INVENTORY API DEPLOYED!                                   ║
╚═══════════════════════════════════════════════════════════════════════╝{NC}

  {CYAN}Inventory Endpoint:{NC}
    GET {api_url}/inventory
    GET {api_url}/inventory?type=s3
    GET {api_url}/inventory?type=ec2
    GET {api_url}/inventory?type=iam
    GET {api_url}/inventory?type=rds

  {CYAN}Test it:{NC}
    curl "{api_url}/inventory"

  {CYAN}Next Steps:{NC}
    1. Update Inventory.tsx to fetch from this API
    2. Rebuild and redeploy the dashboard

  {CYAN}Dashboard Update:{NC}
    The Inventory page needs to be updated to use:
    API_URL = "{api_url}/inventory"
""")


def main():
    print(f"""
{CYAN}╔═══════════════════════════════════════════════════════════════════════╗
║   SLyK-View — Inventory API Deployment                                 ║
╚═══════════════════════════════════════════════════════════════════════╝{NC}
""")
    
    account_id = get_account_id()
    ok(f"AWS Account: {account_id}")
    ok(f"Region: {REGION}")
    print()
    
    log("Creating IAM role...")
    role_arn = create_lambda_role(account_id)
    print()
    
    log("Deploying Lambda function...")
    lambda_arn = deploy_lambda(account_id, role_arn)
    print()
    
    log("Adding API Gateway endpoint...")
    api_id = add_api_endpoint(account_id, lambda_arn)
    print()
    
    if api_id:
        print_summary(account_id, api_id)


if __name__ == "__main__":
    main()
