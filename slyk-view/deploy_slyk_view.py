#!/usr/bin/env python3
"""
SLyK-View Deployment Script
============================
Deploys the SLyK-View React dashboard to AWS.

Creates:
    1. S3 bucket for static hosting
    2. CloudFront distribution
    3. Cognito User Pool for authentication
    4. Cognito Identity Pool for AWS credentials

Usage (from CloudShell):
    python3 deploy_slyk_view.py

Prerequisites:
    - Node.js 18+ (for building React app)
    - AWS credentials with admin access
"""

import json
import os
import sys
import time
import boto3
from botocore.exceptions import ClientError

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
ACCOUNT_ID = None

# Resource names
APP_NAME = "slyk-view"
S3_BUCKET_NAME = None  # Will be set dynamically
CLOUDFRONT_COMMENT = "SLyK-View Security Dashboard"
COGNITO_USER_POOL_NAME = "SLyK-View-Users"
COGNITO_IDENTITY_POOL_NAME = "SLyK-View-Identity"

# Colors
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
RED = "\033[0;31m"
NC = "\033[0m"

config = {}


def log(msg):
    print(f"{BLUE}[slyk-view]{NC} {msg}")


def ok(msg):
    print(f"{GREEN}  ✓{NC} {msg}")


def warn(msg):
    print(f"{YELLOW}  !{NC} {msg}")


def fail(msg):
    print(f"{RED}  ✗{NC} {msg}")


def get_account_id():
    global ACCOUNT_ID, S3_BUCKET_NAME
    sts = boto3.client("sts", region_name=REGION)
    ACCOUNT_ID = sts.get_caller_identity()["Account"]
    S3_BUCKET_NAME = f"slyk-view-{ACCOUNT_ID}-{REGION}"
    return ACCOUNT_ID


def create_s3_bucket():
    """Create S3 bucket for static website hosting."""
    log("Step 1: Creating S3 bucket for static hosting...")
    s3 = boto3.client("s3", region_name=REGION)

    try:
        if REGION == "us-east-1":
            s3.create_bucket(Bucket=S3_BUCKET_NAME)
        else:
            s3.create_bucket(
                Bucket=S3_BUCKET_NAME,
                CreateBucketConfiguration={"LocationConstraint": REGION}
            )
        ok(f"Created bucket: {S3_BUCKET_NAME}")
    except ClientError as e:
        if "BucketAlreadyOwnedByYou" in str(e):
            warn(f"Bucket already exists: {S3_BUCKET_NAME}")
        else:
            raise

    # Configure for static website hosting
    s3.put_bucket_website_configuration(
        Bucket=S3_BUCKET_NAME,
        WebsiteConfiguration={
            "IndexDocument": {"Suffix": "index.html"},
            "ErrorDocument": {"Key": "index.html"}  # SPA routing
        }
    )
    ok("Configured static website hosting")

    # Block public access (CloudFront will serve content)
    s3.put_public_access_block(
        Bucket=S3_BUCKET_NAME,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True
        }
    )
    ok("Blocked public access (CloudFront only)")

    config["s3_bucket"] = S3_BUCKET_NAME
    return S3_BUCKET_NAME


def create_cloudfront_distribution():
    """Create CloudFront distribution."""
    log("Step 2: Creating CloudFront distribution...")
    cf = boto3.client("cloudfront", region_name="us-east-1")  # CloudFront is global

    # Create Origin Access Control
    oac_name = f"slyk-view-oac-{ACCOUNT_ID}"
    try:
        oac_response = cf.create_origin_access_control(
            OriginAccessControlConfig={
                "Name": oac_name,
                "Description": "OAC for SLyK-View S3 bucket",
                "SigningProtocol": "sigv4",
                "SigningBehavior": "always",
                "OriginAccessControlOriginType": "s3"
            }
        )
        oac_id = oac_response["OriginAccessControl"]["Id"]
        ok(f"Created Origin Access Control: {oac_id}")
    except ClientError as e:
        if "OriginAccessControlAlreadyExists" in str(e):
            # Get existing OAC
            oacs = cf.list_origin_access_controls()
            for oac in oacs.get("OriginAccessControlList", {}).get("Items", []):
                if oac["Name"] == oac_name:
                    oac_id = oac["Id"]
                    break
            warn(f"OAC already exists: {oac_id}")
        else:
            raise

    # Create distribution
    origin_id = f"S3-{S3_BUCKET_NAME}"
    
    try:
        dist_response = cf.create_distribution(
            DistributionConfig={
                "CallerReference": f"slyk-view-{int(time.time())}",
                "Comment": CLOUDFRONT_COMMENT,
                "Enabled": True,
                "Origins": {
                    "Quantity": 1,
                    "Items": [{
                        "Id": origin_id,
                        "DomainName": f"{S3_BUCKET_NAME}.s3.{REGION}.amazonaws.com",
                        "OriginAccessControlId": oac_id,
                        "S3OriginConfig": {
                            "OriginAccessIdentity": ""
                        }
                    }]
                },
                "DefaultCacheBehavior": {
                    "TargetOriginId": origin_id,
                    "ViewerProtocolPolicy": "redirect-to-https",
                    "AllowedMethods": {
                        "Quantity": 2,
                        "Items": ["GET", "HEAD"],
                        "CachedMethods": {
                            "Quantity": 2,
                            "Items": ["GET", "HEAD"]
                        }
                    },
                    "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",  # CachingOptimized
                    "Compress": True
                },
                "DefaultRootObject": "index.html",
                "CustomErrorResponses": {
                    "Quantity": 1,
                    "Items": [{
                        "ErrorCode": 404,
                        "ResponsePagePath": "/index.html",
                        "ResponseCode": "200",
                        "ErrorCachingMinTTL": 300
                    }]
                },
                "PriceClass": "PriceClass_100",  # US, Canada, Europe
                "ViewerCertificate": {
                    "CloudFrontDefaultCertificate": True
                }
            }
        )
        dist_id = dist_response["Distribution"]["Id"]
        dist_domain = dist_response["Distribution"]["DomainName"]
        ok(f"Created distribution: {dist_id}")
        ok(f"Domain: https://{dist_domain}")
    except ClientError as e:
        if "DistributionAlreadyExists" in str(e):
            # Find existing distribution
            dists = cf.list_distributions()
            for dist in dists.get("DistributionList", {}).get("Items", []):
                if dist.get("Comment") == CLOUDFRONT_COMMENT:
                    dist_id = dist["Id"]
                    dist_domain = dist["DomainName"]
                    break
            warn(f"Distribution already exists: {dist_id}")
        else:
            raise

    # Update S3 bucket policy to allow CloudFront
    s3 = boto3.client("s3", region_name=REGION)
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "AllowCloudFrontServicePrincipal",
            "Effect": "Allow",
            "Principal": {
                "Service": "cloudfront.amazonaws.com"
            },
            "Action": "s3:GetObject",
            "Resource": f"arn:aws:s3:::{S3_BUCKET_NAME}/*",
            "Condition": {
                "StringEquals": {
                    "AWS:SourceArn": f"arn:aws:cloudfront::{ACCOUNT_ID}:distribution/{dist_id}"
                }
            }
        }]
    }
    s3.put_bucket_policy(Bucket=S3_BUCKET_NAME, Policy=json.dumps(bucket_policy))
    ok("Updated S3 bucket policy for CloudFront")

    config["cloudfront_id"] = dist_id
    config["cloudfront_domain"] = dist_domain
    return dist_id, dist_domain


def create_cognito_user_pool():
    """Create Cognito User Pool for authentication."""
    log("Step 3: Creating Cognito User Pool...")
    cognito = boto3.client("cognito-idp", region_name=REGION)

    try:
        pool_response = cognito.create_user_pool(
            PoolName=COGNITO_USER_POOL_NAME,
            Policies={
                "PasswordPolicy": {
                    "MinimumLength": 12,
                    "RequireUppercase": True,
                    "RequireLowercase": True,
                    "RequireNumbers": True,
                    "RequireSymbols": True
                }
            },
            AutoVerifiedAttributes=["email"],
            UsernameAttributes=["email"],
            MfaConfiguration="OPTIONAL",
            UserPoolTags={
                "Application": "SLyK-View",
                "Environment": "Production"
            }
        )
        pool_id = pool_response["UserPool"]["Id"]
        ok(f"Created User Pool: {pool_id}")
    except ClientError as e:
        if "ResourceExistsException" in str(e):
            # Find existing pool
            pools = cognito.list_user_pools(MaxResults=60)
            for pool in pools.get("UserPools", []):
                if pool["Name"] == COGNITO_USER_POOL_NAME:
                    pool_id = pool["Id"]
                    break
            warn(f"User Pool already exists: {pool_id}")
        else:
            raise

    # Create app client
    try:
        client_response = cognito.create_user_pool_client(
            UserPoolId=pool_id,
            ClientName="slyk-view-web",
            GenerateSecret=False,
            ExplicitAuthFlows=[
                "ALLOW_USER_SRP_AUTH",
                "ALLOW_REFRESH_TOKEN_AUTH"
            ],
            SupportedIdentityProviders=["COGNITO"],
            CallbackURLs=[f"https://{config.get('cloudfront_domain', 'localhost')}/"],
            LogoutURLs=[f"https://{config.get('cloudfront_domain', 'localhost')}/"],
            AllowedOAuthFlows=["code"],
            AllowedOAuthScopes=["email", "openid", "profile"],
            AllowedOAuthFlowsUserPoolClient=True
        )
        client_id = client_response["UserPoolClient"]["ClientId"]
        ok(f"Created App Client: {client_id}")
    except ClientError:
        # Get existing client
        clients = cognito.list_user_pool_clients(UserPoolId=pool_id, MaxResults=60)
        for client in clients.get("UserPoolClients", []):
            if client["ClientName"] == "slyk-view-web":
                client_id = client["ClientId"]
                break
        warn(f"App Client already exists: {client_id}")

    config["cognito_user_pool_id"] = pool_id
    config["cognito_client_id"] = client_id
    return pool_id, client_id


def create_cognito_identity_pool():
    """Create Cognito Identity Pool for AWS credentials."""
    log("Step 4: Creating Cognito Identity Pool...")
    cognito_identity = boto3.client("cognito-identity", region_name=REGION)
    iam = boto3.client("iam")

    user_pool_id = config.get("cognito_user_pool_id")
    client_id = config.get("cognito_client_id")

    try:
        pool_response = cognito_identity.create_identity_pool(
            IdentityPoolName=COGNITO_IDENTITY_POOL_NAME.replace("-", "_"),
            AllowUnauthenticatedIdentities=False,
            CognitoIdentityProviders=[{
                "ProviderName": f"cognito-idp.{REGION}.amazonaws.com/{user_pool_id}",
                "ClientId": client_id,
                "ServerSideTokenCheck": True
            }]
        )
        identity_pool_id = pool_response["IdentityPoolId"]
        ok(f"Created Identity Pool: {identity_pool_id}")
    except ClientError as e:
        if "ResourceConflictException" in str(e):
            pools = cognito_identity.list_identity_pools(MaxResults=60)
            for pool in pools.get("IdentityPools", []):
                if pool["IdentityPoolName"] == COGNITO_IDENTITY_POOL_NAME.replace("-", "_"):
                    identity_pool_id = pool["IdentityPoolId"]
                    break
            warn(f"Identity Pool already exists: {identity_pool_id}")
        else:
            raise

    # Create IAM role for authenticated users
    role_name = "SLyK-View-Cognito-Auth-Role"
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Federated": "cognito-identity.amazonaws.com"},
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringEquals": {
                    "cognito-identity.amazonaws.com:aud": identity_pool_id
                },
                "ForAnyValue:StringLike": {
                    "cognito-identity.amazonaws.com:amr": "authenticated"
                }
            }
        }]
    }

    try:
        role = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Role for SLyK-View authenticated users"
        )
        role_arn = role["Role"]["Arn"]
        ok(f"Created IAM role: {role_name}")
    except ClientError as e:
        if "EntityAlreadyExists" in str(e):
            role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/{role_name}"
            warn(f"IAM role already exists: {role_name}")
        else:
            raise

    # Attach policy for Bedrock agent invocation
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeAgent"
                ],
                "Resource": [
                    f"arn:aws:bedrock:{REGION}:{ACCOUNT_ID}:agent/*",
                    f"arn:aws:bedrock:{REGION}:{ACCOUNT_ID}:agent-alias/*"
                ]
            }
        ]
    }
    try:
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName="SLyK-View-Bedrock-Access",
            PolicyDocument=json.dumps(policy)
        )
        ok("Attached Bedrock access policy")
    except ClientError:
        warn("Could not attach policy (may already exist)")

    # Set identity pool roles
    try:
        cognito_identity.set_identity_pool_roles(
            IdentityPoolId=identity_pool_id,
            Roles={
                "authenticated": role_arn
            }
        )
        ok("Configured Identity Pool roles")
    except ClientError:
        warn("Could not set Identity Pool roles")

    config["cognito_identity_pool_id"] = identity_pool_id
    return identity_pool_id


def save_config():
    """Save configuration for the React app."""
    log("Step 5: Saving configuration...")

    # Create config file for React app
    react_config = {
        "region": REGION,
        "userPoolId": config.get("cognito_user_pool_id", ""),
        "userPoolClientId": config.get("cognito_client_id", ""),
        "identityPoolId": config.get("cognito_identity_pool_id", ""),
        "s3Bucket": config.get("s3_bucket", ""),
        "cloudfrontDomain": config.get("cloudfront_domain", ""),
    }

    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "aws-config.json")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(react_config, f, indent=2)
    ok(f"Saved React config to {config_path}")

    # Also save full deployment config
    full_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deployment-config.json")
    with open(full_config_path, "w") as f:
        json.dump({**config, "account_id": ACCOUNT_ID, "region": REGION}, f, indent=2)
    ok(f"Saved deployment config to {full_config_path}")


def print_summary():
    print(f"""
{GREEN}╔═══════════════════════════════════════════════════════════════════════╗
║              SLyK-View INFRASTRUCTURE DEPLOYED!                        ║
╚═══════════════════════════════════════════════════════════════════════╝{NC}

  {CYAN}Resources Created:{NC}
    S3 Bucket:          {config.get('s3_bucket', 'N/A')}
    CloudFront:         https://{config.get('cloudfront_domain', 'N/A')}
    Cognito User Pool:  {config.get('cognito_user_pool_id', 'N/A')}
    Cognito Identity:   {config.get('cognito_identity_pool_id', 'N/A')}

  {CYAN}Next Steps:{NC}
    1. Build the React app:
       cd slyk-view
       npm install
       npm run build

    2. Upload to S3:
       aws s3 sync dist/ s3://{config.get('s3_bucket', 'BUCKET_NAME')}/ --delete

    3. Invalidate CloudFront cache:
       aws cloudfront create-invalidation --distribution-id {config.get('cloudfront_id', 'DIST_ID')} --paths "/*"

    4. Access the dashboard:
       https://{config.get('cloudfront_domain', 'N/A')}

  {CYAN}Share with Other ISSOs:{NC}
    Share the deployment-config.json file. They can:
    1. Run this script in their AWS account
    2. Update the Bedrock Agent ID in Settings
    3. Access their own SLyK-View instance

  {YELLOW}Note:{NC} CloudFront may take 10-15 minutes to fully deploy.
""")


def main():
    print(f"""
{CYAN}╔═══════════════════════════════════════════════════════════════════════╗
║   SLyK-View — Security Dashboard Deployment                            ║
╚═══════════════════════════════════════════════════════════════════════╝{NC}
""")

    try:
        acct = get_account_id()
        ok(f"AWS Account: {acct}")
        ok(f"Region: {REGION}")
    except Exception as e:
        fail(f"Cannot access AWS: {e}")
        sys.exit(1)

    print()
    create_s3_bucket()
    print()
    create_cloudfront_distribution()
    print()
    create_cognito_user_pool()
    print()
    create_cognito_identity_pool()
    print()
    save_config()
    print_summary()


if __name__ == "__main__":
    main()
