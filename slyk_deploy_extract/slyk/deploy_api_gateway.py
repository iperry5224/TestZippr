#!/usr/bin/env python3
"""
Deploy API Gateway for SLyK-View Dashboard
===========================================
Creates a REST API that connects the dashboard to Lambda functions.

Usage:
    python3 deploy_api_gateway.py
"""

import json
import os
import time
import boto3
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
    print(f"{BLUE}[api-gateway]{NC} {msg}")


def ok(msg):
    print(f"{GREEN}  ✓{NC} {msg}")


def warn(msg):
    print(f"{YELLOW}  !{NC} {msg}")


def fail(msg):
    print(f"{RED}  ✗{NC} {msg}")


def get_account_id():
    sts = boto3.client("sts", region_name=REGION)
    return sts.get_caller_identity()["Account"]


def create_api_gateway(account_id):
    """Create REST API Gateway for SLyK-View."""
    log("Creating API Gateway...")
    
    apigw = boto3.client("apigateway", region_name=REGION)
    lambda_client = boto3.client("lambda", region_name=REGION)
    
    api_name = "slyk-view-api"
    
    # Check if API already exists
    existing_apis = apigw.get_rest_apis()
    for api in existing_apis.get("items", []):
        if api["name"] == api_name:
            api_id = api["id"]
            warn(f"API already exists: {api_id}")
            return api_id
    
    # Create new API
    api = apigw.create_rest_api(
        name=api_name,
        description="SLyK-View Dashboard API",
        endpointConfiguration={"types": ["REGIONAL"]}
    )
    api_id = api["id"]
    ok(f"Created API: {api_id}")
    
    # Get root resource
    resources = apigw.get_resources(restApiId=api_id)
    root_id = resources["items"][0]["id"]
    
    # Create /securityhub resource
    securityhub_resource = apigw.create_resource(
        restApiId=api_id,
        parentId=root_id,
        pathPart="securityhub"
    )
    securityhub_id = securityhub_resource["id"]
    ok("Created /securityhub resource")
    
    # Create GET method for /securityhub
    apigw.put_method(
        restApiId=api_id,
        resourceId=securityhub_id,
        httpMethod="GET",
        authorizationType="NONE"
    )
    
    # Lambda integration
    lambda_arn = f"arn:aws:lambda:{REGION}:{account_id}:function:slyk-securityhub-findings"
    
    apigw.put_integration(
        restApiId=api_id,
        resourceId=securityhub_id,
        httpMethod="GET",
        type="AWS_PROXY",
        integrationHttpMethod="POST",
        uri=f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
    )
    ok("Configured Lambda integration")
    
    # Add Lambda permission for API Gateway
    try:
        lambda_client.add_permission(
            FunctionName="slyk-securityhub-findings",
            StatementId=f"apigateway-{api_id}",
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
            SourceArn=f"arn:aws:execute-api:{REGION}:{account_id}:{api_id}/*"
        )
        ok("Added API Gateway invoke permission to Lambda")
    except ClientError as e:
        if "ResourceConflictException" in str(e):
            warn("Lambda permission already exists")
        else:
            warn(f"Could not add Lambda permission: {e}")
    
    # Enable CORS
    apigw.put_method(
        restApiId=api_id,
        resourceId=securityhub_id,
        httpMethod="OPTIONS",
        authorizationType="NONE"
    )
    
    apigw.put_integration(
        restApiId=api_id,
        resourceId=securityhub_id,
        httpMethod="OPTIONS",
        type="MOCK",
        requestTemplates={"application/json": '{"statusCode": 200}'}
    )
    
    apigw.put_method_response(
        restApiId=api_id,
        resourceId=securityhub_id,
        httpMethod="OPTIONS",
        statusCode="200",
        responseParameters={
            "method.response.header.Access-Control-Allow-Headers": True,
            "method.response.header.Access-Control-Allow-Methods": True,
            "method.response.header.Access-Control-Allow-Origin": True
        }
    )
    
    apigw.put_integration_response(
        restApiId=api_id,
        resourceId=securityhub_id,
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
        description="Production deployment"
    )
    ok("Deployed to 'prod' stage")
    
    return api_id


def update_lambda_for_api_gateway():
    """Update Lambda to return proper API Gateway response format."""
    log("Updating Lambda for API Gateway response format...")
    
    # Read current Lambda code
    lambda_dir = os.path.join(os.path.dirname(__file__), "lambda_functions")
    lambda_file = os.path.join(lambda_dir, "securityhub_findings.py")
    
    with open(lambda_file, 'r') as f:
        content = f.read()
    
    # Check if already updated
    if "API Gateway response" in content:
        warn("Lambda already updated for API Gateway")
        return
    
    # Add API Gateway response wrapper
    new_handler = '''
def lambda_handler(event, context):
    """Main Lambda handler for Security Hub integration."""
    
    # Handle API Gateway requests
    if event.get("httpMethod"):
        # This is an API Gateway request
        query_params = event.get("queryStringParameters") or {}
        action = query_params.get("action", "dashboard")
        
        if action == "get_by_control":
            control_id = query_params.get("control_id", "AC-2")
            result = get_findings_by_control(control_id)
        elif action == "get_critical":
            result = get_critical_findings()
        elif action == "compliance_summary":
            result = get_compliance_summary()
        else:
            result = get_findings_for_dashboard()
        
        # API Gateway response format
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "GET, OPTIONS"
            },
            "body": json.dumps(result)
        }
    
    # Direct Lambda invocation (non-API Gateway)
    action = event.get("action", "summary")
    
    if action == "get_by_control":
        control_id = event.get("control_id", "AC-2")
        max_results = event.get("max_results", 25)
        return get_findings_by_control(control_id, max_results)
    
    elif action == "get_critical":
        max_results = event.get("max_results", 20)
        return get_critical_findings(max_results)
    
    elif action == "compliance_summary":
        return get_compliance_summary()
    
    elif action == "dashboard":
        return get_findings_for_dashboard()
    
    else:
        return {
            "status": "SUCCESS",
            "message": "Security Hub Integration for SLyK-53",
            "available_actions": [
                "get_by_control - Get findings for a NIST control (AC-2, AU-6, CM-6, SI-2, RA-5)",
                "get_critical - Get CRITICAL and HIGH severity findings",
                "compliance_summary - Get overall compliance status",
                "dashboard - Get summary formatted for SLyK-View dashboard"
            ]
        }
'''
    
    # Replace old handler
    old_handler_start = content.find("def lambda_handler(event, context):")
    if old_handler_start != -1:
        content = content[:old_handler_start] + new_handler
        
        with open(lambda_file, 'w') as f:
            f.write(content)
        
        ok("Updated Lambda handler for API Gateway")
    else:
        warn("Could not find lambda_handler to update")


def redeploy_lambda(account_id):
    """Redeploy the Lambda with updated code."""
    log("Redeploying Lambda function...")
    
    import zipfile
    import tempfile
    
    lambda_client = boto3.client("lambda", region_name=REGION)
    lambda_dir = os.path.join(os.path.dirname(__file__), "lambda_functions")
    
    # Create ZIP
    zip_path = os.path.join(tempfile.gettempdir(), "securityhub_lambda.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        lambda_file = os.path.join(lambda_dir, "securityhub_findings.py")
        zf.write(lambda_file, "lambda_function.py")
    
    with open(zip_path, 'rb') as f:
        zip_bytes = f.read()
    
    lambda_client.update_function_code(
        FunctionName="slyk-securityhub-findings",
        ZipFile=zip_bytes
    )
    ok("Redeployed Lambda function")
    
    os.remove(zip_path)


def print_summary(account_id, api_id):
    api_url = f"https://{api_id}.execute-api.{REGION}.amazonaws.com/prod"
    
    print(f"""
{GREEN}╔═══════════════════════════════════════════════════════════════════════╗
║              API GATEWAY DEPLOYED!                                     ║
╚═══════════════════════════════════════════════════════════════════════╝{NC}

  {CYAN}API Endpoint:{NC}
    {api_url}

  {CYAN}Available Endpoints:{NC}
    GET {api_url}/securityhub
    GET {api_url}/securityhub?action=dashboard
    GET {api_url}/securityhub?action=get_critical
    GET {api_url}/securityhub?action=get_by_control&control_id=AC-2

  {CYAN}Test it:{NC}
    curl "{api_url}/securityhub"

  {CYAN}Next Steps:{NC}
    Update SLyK-View dashboard to use this API endpoint

  {CYAN}Dashboard Config:{NC}
    Add this to your dashboard's config:
    API_URL = "{api_url}"
""")
    
    # Save config
    config = {
        "api_id": api_id,
        "api_url": api_url,
        "region": REGION,
        "account_id": account_id
    }
    
    config_path = os.path.join(os.path.dirname(__file__), "api_gateway_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    ok(f"Saved config to {config_path}")


def main():
    print(f"""
{CYAN}╔═══════════════════════════════════════════════════════════════════════╗
║   SLyK-View — API Gateway Deployment                                   ║
╚═══════════════════════════════════════════════════════════════════════╝{NC}
""")
    
    account_id = get_account_id()
    ok(f"AWS Account: {account_id}")
    ok(f"Region: {REGION}")
    print()
    
    update_lambda_for_api_gateway()
    print()
    
    redeploy_lambda(account_id)
    print()
    
    api_id = create_api_gateway(account_id)
    print()
    
    print_summary(account_id, api_id)


if __name__ == "__main__":
    main()
