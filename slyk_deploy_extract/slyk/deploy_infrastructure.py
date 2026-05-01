#!/usr/bin/env python3
"""
SLyK-53 Infrastructure Deployment
==================================
Creates the additional AWS infrastructure for the full SLyK-53 platform:
  - Cognito Identity Pool (for Console session federation)
  - API Gateway (REST API)
  - DynamoDB tables (sessions, audit log)
  - S3 bucket for UI hosting
  - CloudFront distribution
  - Knowledge Base (optional)

Run after deploy_slyk.py has created the core agent and Lambda functions.

Usage:
    python3 deploy_infrastructure.py
"""

import json
import os
import sys
import time
import boto3
from botocore.exceptions import ClientError

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
ACCOUNT_ID = None
S3_BUCKET = os.environ.get("S3_BUCKET_NAME", "saelarallpurpose")

# Resource names
# Resource naming - set SLYK_VARIANT env var to customize (e.g., "new" for New_SLyK-53)
VARIANT = os.environ.get("SLYK_VARIANT", "")
VARIANT_SUFFIX = f"-{VARIANT}" if VARIANT else ""
VARIANT_PREFIX = f"{VARIANT.capitalize()}_" if VARIANT else ""

IDENTITY_POOL_NAME = f"{VARIANT_PREFIX}SLyK-Identity-Pool"
USER_POOL_NAME = f"{VARIANT_PREFIX}SLyK-User-Pool"
API_NAME = f"{VARIANT_PREFIX}SLyK-API"
SESSIONS_TABLE = f"slyk{VARIANT_SUFFIX}-sessions"
AUDIT_TABLE = f"slyk{VARIANT_SUFFIX}-audit-log"
UI_BUCKET_PREFIX = f"slyk{VARIANT_SUFFIX}-ui"
KB_NAME = f"{VARIANT_PREFIX}SLyK-Knowledge-Base"

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
NC = "\033[0m"

config = {}


def log(msg):
    print(f"{BLUE}[slyk-infra]{NC} {msg}")


def ok(msg):
    print(f"{GREEN}  ✓{NC} {msg}")


def warn(msg):
    print(f"{YELLOW}  !{NC} {msg}")


def fail(msg):
    print(f"{RED}  ✗{NC} {msg}")


def banner():
    print(f"""
{CYAN}╔═══════════════════════════════════════════════════════════════════════╗
║   SLyK-53 Infrastructure Deployment                                    ║
║   Cognito, API Gateway, DynamoDB, CloudFront                          ║
╚═══════════════════════════════════════════════════════════════════════╝{NC}
""")


def get_account_id():
    global ACCOUNT_ID
    sts = boto3.client("sts", region_name=REGION)
    ACCOUNT_ID = sts.get_caller_identity()["Account"]
    return ACCOUNT_ID


# =========================================================================
# STEP 1: Cognito
# =========================================================================
def create_cognito():
    log("Step 1: Creating Cognito resources...")
    cognito = boto3.client("cognito-identity", region_name=REGION)
    cognito_idp = boto3.client("cognito-idp", region_name=REGION)

    # Create User Pool (optional - for username/password auth)
    try:
        user_pool = cognito_idp.create_user_pool(
            PoolName=USER_POOL_NAME,
            Policies={
                "PasswordPolicy": {
                    "MinimumLength": 12,
                    "RequireUppercase": True,
                    "RequireLowercase": True,
                    "RequireNumbers": True,
                    "RequireSymbols": True,
                }
            },
            AutoVerifiedAttributes=["email"],
            MfaConfiguration="OPTIONAL",
            UserPoolTags={"Application": "SLyK-53"},
        )
        config["user_pool_id"] = user_pool["UserPool"]["Id"]
        ok(f"Created User Pool: {config['user_pool_id']}")

        # Create User Pool Client
        client = cognito_idp.create_user_pool_client(
            UserPoolId=config["user_pool_id"],
            ClientName="slyk-web-client",
            GenerateSecret=False,
            ExplicitAuthFlows=[
                "ALLOW_USER_SRP_AUTH",
                "ALLOW_REFRESH_TOKEN_AUTH",
            ],
        )
        config["user_pool_client_id"] = client["UserPoolClient"]["ClientId"]
        ok(f"Created User Pool Client: {config['user_pool_client_id']}")

    except ClientError as e:
        if "ResourceExistsException" in str(e):
            # Find existing
            pools = cognito_idp.list_user_pools(MaxResults=50)
            for p in pools.get("UserPools", []):
                if p["Name"] == USER_POOL_NAME:
                    config["user_pool_id"] = p["Id"]
                    break
            warn(f"User Pool already exists: {config.get('user_pool_id', 'unknown')}")
        else:
            warn(f"Could not create User Pool: {e}")

    # Create Identity Pool
    try:
        identity_pool = cognito.create_identity_pool(
            IdentityPoolName=IDENTITY_POOL_NAME,
            AllowUnauthenticatedIdentities=False,
            AllowClassicFlow=False,
            CognitoIdentityProviders=[
                {
                    "ProviderName": f"cognito-idp.{REGION}.amazonaws.com/{config.get('user_pool_id', '')}",
                    "ClientId": config.get("user_pool_client_id", ""),
                    "ServerSideTokenCheck": True,
                }
            ] if config.get("user_pool_id") else [],
            IdentityPoolTags={"Application": "SLyK-53"},
        )
        config["identity_pool_id"] = identity_pool["IdentityPoolId"]
        ok(f"Created Identity Pool: {config['identity_pool_id']}")

    except ClientError as e:
        if "ResourceConflictException" in str(e):
            pools = cognito.list_identity_pools(MaxResults=50)
            for p in pools.get("IdentityPools", []):
                if p["IdentityPoolName"] == IDENTITY_POOL_NAME:
                    config["identity_pool_id"] = p["IdentityPoolId"]
                    break
            warn(f"Identity Pool already exists: {config.get('identity_pool_id', 'unknown')}")
        else:
            warn(f"Could not create Identity Pool: {e}")

    # Create IAM roles for Identity Pool
    if config.get("identity_pool_id"):
        create_cognito_roles(cognito)


def create_cognito_roles(cognito):
    """Create authenticated and unauthenticated roles for Cognito Identity Pool."""
    iam = boto3.client("iam")

    # Authenticated role
    auth_trust = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Federated": "cognito-identity.amazonaws.com"},
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringEquals": {
                    "cognito-identity.amazonaws.com:aud": config["identity_pool_id"]
                },
                "ForAnyValue:StringLike": {
                    "cognito-identity.amazonaws.com:amr": "authenticated"
                }
            }
        }]
    }

    auth_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeAgent",
                    "bedrock:InvokeModel",
                ],
                "Resource": [
                    f"arn:aws:bedrock:{REGION}:{ACCOUNT_ID}:agent/*",
                    f"arn:aws:bedrock:{REGION}::foundation-model/*",
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:Query",
                    "dynamodb:UpdateItem",
                ],
                "Resource": [
                    f"arn:aws:dynamodb:{REGION}:{ACCOUNT_ID}:table/{SESSIONS_TABLE}",
                    f"arn:aws:dynamodb:{REGION}:{ACCOUNT_ID}:table/{SESSIONS_TABLE}/index/*",
                    f"arn:aws:dynamodb:{REGION}:{ACCOUNT_ID}:table/{AUDIT_TABLE}",
                    f"arn:aws:dynamodb:{REGION}:{ACCOUNT_ID}:table/{AUDIT_TABLE}/index/*",
                ]
            },
            {
                "Effect": "Allow",
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{S3_BUCKET}/slyk/*"]
            }
        ]
    }

    try:
        role = iam.create_role(
            RoleName="SLyK-Cognito-Auth-Role",
            AssumeRolePolicyDocument=json.dumps(auth_trust),
            Description="SLyK-53 Cognito authenticated user role",
        )
        config["cognito_auth_role_arn"] = role["Role"]["Arn"]
        ok("Created Cognito Auth Role")

        iam.put_role_policy(
            RoleName="SLyK-Cognito-Auth-Role",
            PolicyName="SLyK-Auth-Permissions",
            PolicyDocument=json.dumps(auth_policy),
        )
    except ClientError as e:
        if "EntityAlreadyExists" in str(e):
            config["cognito_auth_role_arn"] = f"arn:aws:iam::{ACCOUNT_ID}:role/SLyK-Cognito-Auth-Role"
            warn("Cognito Auth Role already exists")
        else:
            warn(f"Could not create auth role: {e}")

    # Set roles on Identity Pool
    try:
        cognito.set_identity_pool_roles(
            IdentityPoolId=config["identity_pool_id"],
            Roles={
                "authenticated": config.get("cognito_auth_role_arn", ""),
            }
        )
        ok("Configured Identity Pool roles")
    except ClientError as e:
        warn(f"Could not set Identity Pool roles: {e}")


# =========================================================================
# STEP 2: DynamoDB
# =========================================================================
def create_dynamodb():
    log("Step 2: Creating DynamoDB tables...")
    ddb = boto3.client("dynamodb", region_name=REGION)

    # Sessions table
    try:
        ddb.create_table(
            TableName=SESSIONS_TABLE,
            KeySchema=[
                {"AttributeName": "sessionId", "KeyType": "HASH"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "sessionId", "AttributeType": "S"},
                {"AttributeName": "userId", "AttributeType": "S"},
                {"AttributeName": "updatedAt", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "userId-updatedAt-index",
                    "KeySchema": [
                        {"AttributeName": "userId", "KeyType": "HASH"},
                        {"AttributeName": "updatedAt", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
            Tags=[{"Key": "Application", "Value": "SLyK-53"}],
        )
        ok(f"Created table: {SESSIONS_TABLE}")
    except ClientError as e:
        if "ResourceInUseException" in str(e):
            warn(f"Table {SESSIONS_TABLE} already exists")
        else:
            warn(f"Could not create {SESSIONS_TABLE}: {e}")

    # Audit log table
    try:
        ddb.create_table(
            TableName=AUDIT_TABLE,
            KeySchema=[
                {"AttributeName": "eventId", "KeyType": "HASH"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "eventId", "AttributeType": "S"},
                {"AttributeName": "eventType", "AttributeType": "S"},
                {"AttributeName": "timestamp", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "eventType-timestamp-index",
                    "KeySchema": [
                        {"AttributeName": "eventType", "KeyType": "HASH"},
                        {"AttributeName": "timestamp", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
            Tags=[{"Key": "Application", "Value": "SLyK-53"}],
        )
        ok(f"Created table: {AUDIT_TABLE}")
    except ClientError as e:
        if "ResourceInUseException" in str(e):
            warn(f"Table {AUDIT_TABLE} already exists")
        else:
            warn(f"Could not create {AUDIT_TABLE}: {e}")

    config["sessions_table"] = SESSIONS_TABLE
    config["audit_table"] = AUDIT_TABLE


# =========================================================================
# STEP 3: API Gateway
# =========================================================================
def create_api_gateway():
    log("Step 3: Creating API Gateway...")
    apigw = boto3.client("apigateway", region_name=REGION)

    # Check if API already exists
    apis = apigw.get_rest_apis()
    for api in apis.get("items", []):
        if api["name"] == API_NAME:
            config["api_id"] = api["id"]
            warn(f"API Gateway already exists: {config['api_id']}")
            return

    try:
        api = apigw.create_rest_api(
            name=API_NAME,
            description="SLyK-53 Security Assistant API",
            endpointConfiguration={"types": ["REGIONAL"]},
            tags={"Application": "SLyK-53"},
        )
        config["api_id"] = api["id"]
        ok(f"Created API Gateway: {config['api_id']}")

        # Get root resource
        resources = apigw.get_resources(restApiId=config["api_id"])
        root_id = resources["items"][0]["id"]

        # Create /agent resource
        agent_resource = apigw.create_resource(
            restApiId=config["api_id"],
            parentId=root_id,
            pathPart="agent",
        )

        # Create POST method for /agent
        apigw.put_method(
            restApiId=config["api_id"],
            resourceId=agent_resource["id"],
            httpMethod="POST",
            authorizationType="AWS_IAM",
        )

        # Note: Integration with Bedrock Agent would be configured here
        # For now, we'll use the direct SDK approach from the UI

        # Enable CORS
        apigw.put_method(
            restApiId=config["api_id"],
            resourceId=agent_resource["id"],
            httpMethod="OPTIONS",
            authorizationType="NONE",
        )

        ok("Configured API Gateway resources")

        # Deploy API
        apigw.create_deployment(
            restApiId=config["api_id"],
            stageName="prod",
            description="Production deployment",
        )
        config["api_endpoint"] = f"https://{config['api_id']}.execute-api.{REGION}.amazonaws.com/prod"
        ok(f"Deployed API: {config['api_endpoint']}")

    except ClientError as e:
        warn(f"Could not create API Gateway: {e}")


# =========================================================================
# STEP 4: S3 + CloudFront for UI
# =========================================================================
def create_ui_hosting():
    log("Step 4: Creating UI hosting (S3 + CloudFront)...")
    s3 = boto3.client("s3", region_name=REGION)
    cf = boto3.client("cloudfront")

    ui_bucket = f"{UI_BUCKET_PREFIX}-{ACCOUNT_ID}"
    config["ui_bucket"] = ui_bucket

    # Create S3 bucket for UI
    try:
        if REGION == "us-east-1":
            s3.create_bucket(Bucket=ui_bucket)
        else:
            s3.create_bucket(
                Bucket=ui_bucket,
                CreateBucketConfiguration={"LocationConstraint": REGION},
            )
        ok(f"Created UI bucket: {ui_bucket}")

        # Configure for static website hosting
        s3.put_bucket_website(
            Bucket=ui_bucket,
            WebsiteConfiguration={
                "IndexDocument": {"Suffix": "index.html"},
                "ErrorDocument": {"Key": "index.html"},
            },
        )

        # Block public access (CloudFront will use OAI)
        s3.put_public_access_block(
            Bucket=ui_bucket,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
        )
        ok("Configured bucket for static hosting")

    except ClientError as e:
        if "BucketAlreadyOwnedByYou" in str(e):
            warn(f"UI bucket already exists: {ui_bucket}")
        else:
            warn(f"Could not create UI bucket: {e}")

    # Create CloudFront Origin Access Identity
    try:
        oai = cf.create_cloud_front_origin_access_identity(
            CloudFrontOriginAccessIdentityConfig={
                "CallerReference": f"slyk-oai-{ACCOUNT_ID}",
                "Comment": "SLyK-53 UI OAI",
            }
        )
        config["oai_id"] = oai["CloudFrontOriginAccessIdentity"]["Id"]
        ok(f"Created CloudFront OAI: {config['oai_id']}")
    except ClientError as e:
        warn(f"Could not create OAI: {e}")

    # Update bucket policy for CloudFront
    if config.get("oai_id"):
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {
                    "AWS": f"arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity {config['oai_id']}"
                },
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{ui_bucket}/*"
            }]
        }
        try:
            s3.put_bucket_policy(Bucket=ui_bucket, Policy=json.dumps(bucket_policy))
            ok("Updated bucket policy for CloudFront")
        except ClientError as e:
            warn(f"Could not update bucket policy: {e}")

    # Create CloudFront distribution
    try:
        dist = cf.create_distribution(
            DistributionConfig={
                "CallerReference": f"slyk-dist-{ACCOUNT_ID}-{int(time.time())}",
                "Comment": "SLyK-53 UI Distribution",
                "Enabled": True,
                "Origins": {
                    "Quantity": 1,
                    "Items": [{
                        "Id": "S3Origin",
                        "DomainName": f"{ui_bucket}.s3.{REGION}.amazonaws.com",
                        "S3OriginConfig": {
                            "OriginAccessIdentity": f"origin-access-identity/cloudfront/{config.get('oai_id', '')}"
                        },
                    }],
                },
                "DefaultCacheBehavior": {
                    "TargetOriginId": "S3Origin",
                    "ViewerProtocolPolicy": "redirect-to-https",
                    "AllowedMethods": {
                        "Quantity": 2,
                        "Items": ["GET", "HEAD"],
                        "CachedMethods": {"Quantity": 2, "Items": ["GET", "HEAD"]},
                    },
                    "ForwardedValues": {
                        "QueryString": False,
                        "Cookies": {"Forward": "none"},
                    },
                    "MinTTL": 0,
                    "DefaultTTL": 86400,
                    "MaxTTL": 31536000,
                    "Compress": True,
                },
                "DefaultRootObject": "index.html",
                "CustomErrorResponses": {
                    "Quantity": 1,
                    "Items": [{
                        "ErrorCode": 404,
                        "ResponsePagePath": "/index.html",
                        "ResponseCode": "200",
                        "ErrorCachingMinTTL": 300,
                    }],
                },
                "PriceClass": "PriceClass_100",
                "ViewerCertificate": {"CloudFrontDefaultCertificate": True},
            }
        )
        config["cloudfront_id"] = dist["Distribution"]["Id"]
        config["cloudfront_domain"] = dist["Distribution"]["DomainName"]
        ok(f"Created CloudFront distribution: {config['cloudfront_domain']}")
    except ClientError as e:
        warn(f"Could not create CloudFront distribution: {e}")


# =========================================================================
# STEP 5: Save Config
# =========================================================================
def save_config():
    log("Step 5: Saving configuration...")

    # Load existing config if present
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "slyk_config.json")
    existing = {}
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            existing = json.load(f)

    # Merge with new config
    full_config = {**existing, **config}
    full_config["region"] = REGION
    full_config["account_id"] = ACCOUNT_ID

    with open(config_path, "w") as f:
        json.dump(full_config, f, indent=2)
    ok(f"Config saved to {config_path}")

    # Upload to S3
    try:
        s3 = boto3.client("s3", region_name=REGION)
        s3.put_object(
            Bucket=S3_BUCKET,
            Key="slyk/slyk_config.json",
            Body=json.dumps(full_config, indent=2).encode("utf-8"),
        )
        ok(f"Config uploaded to s3://{S3_BUCKET}/slyk/slyk_config.json")
    except:
        warn("Could not upload config to S3")

    # Generate .env file for React app
    env_content = f"""# SLyK-53 UI Configuration
# Generated by deploy_infrastructure.py

REACT_APP_AWS_REGION={REGION}
REACT_APP_AGENT_ID={full_config.get('agent_id', '')}
REACT_APP_AGENT_ALIAS_ID={full_config.get('agent_alias_id', '')}
REACT_APP_IDENTITY_POOL_ID={full_config.get('identity_pool_id', '')}
REACT_APP_USER_POOL_ID={full_config.get('user_pool_id', '')}
REACT_APP_USER_POOL_CLIENT_ID={full_config.get('user_pool_client_id', '')}
REACT_APP_API_ENDPOINT={full_config.get('api_endpoint', '')}
REACT_APP_SESSIONS_TABLE={full_config.get('sessions_table', SESSIONS_TABLE)}
REACT_APP_AUDIT_TABLE={full_config.get('audit_table', AUDIT_TABLE)}
REACT_APP_DOCUMENTS_BUCKET={S3_BUCKET}
REACT_APP_ENABLE_KB=false
REACT_APP_ENABLE_SECURITYHUB=true
"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", ".env")
    os.makedirs(os.path.dirname(env_path), exist_ok=True)
    with open(env_path, "w") as f:
        f.write(env_content)
    ok(f"Generated UI .env file: {env_path}")


# =========================================================================
# SUMMARY
# =========================================================================
def print_summary():
    print(f"""
{GREEN}╔═══════════════════════════════════════════════════════════════════════╗
║           SLyK-53 INFRASTRUCTURE DEPLOYMENT COMPLETE!                  ║
╚═══════════════════════════════════════════════════════════════════════╝{NC}

  {CYAN}Resources Created:{NC}

    Cognito:
      Identity Pool:  {config.get('identity_pool_id', 'N/A')}
      User Pool:      {config.get('user_pool_id', 'N/A')}
      Client ID:      {config.get('user_pool_client_id', 'N/A')}

    DynamoDB:
      Sessions:       {config.get('sessions_table', SESSIONS_TABLE)}
      Audit Log:      {config.get('audit_table', AUDIT_TABLE)}

    API Gateway:
      API ID:         {config.get('api_id', 'N/A')}
      Endpoint:       {config.get('api_endpoint', 'N/A')}

    UI Hosting:
      S3 Bucket:      {config.get('ui_bucket', 'N/A')}
      CloudFront:     {config.get('cloudfront_domain', 'N/A')}

  {CYAN}Next Steps:{NC}
    1. Build the React UI:
       cd ui && npm install && npm run build

    2. Deploy UI to S3:
       aws s3 sync ui/build/ s3://{config.get('ui_bucket', 'slyk-ui-ACCOUNT')}/

    3. Access SLyK-53:
       https://{config.get('cloudfront_domain', 'CLOUDFRONT_DOMAIN')}

    4. Or use the Bedrock Console directly:
       AWS Console > Bedrock > Agents > SLyK-53-Security-Assistant
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
    create_cognito()
    print()
    create_dynamodb()
    print()
    create_api_gateway()
    print()
    create_ui_hosting()
    print()
    save_config()
    print_summary()


if __name__ == "__main__":
    main()
