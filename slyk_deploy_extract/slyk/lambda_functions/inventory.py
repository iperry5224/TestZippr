#!/usr/bin/env python3
"""
SLyK-View Inventory Lambda
==========================
Fetches real AWS resource inventory: S3, EC2, IAM, RDS
Returns compliance status based on security configurations.
"""

import json
import boto3
from botocore.exceptions import ClientError
from datetime import datetime


def get_s3_inventory():
    """Get all S3 buckets with compliance status."""
    s3 = boto3.client('s3')
    buckets = []
    
    try:
        response = s3.list_buckets()
        for bucket in response.get('Buckets', []):
            name = bucket['Name']
            created = bucket.get('CreationDate', datetime.now()).isoformat()
            
            # Check compliance: encryption, public access, versioning
            issues = []
            status = 'compliant'
            region = 'us-east-1'  # default
            
            try:
                # Get bucket location
                loc = s3.get_bucket_location(Bucket=name)
                region = loc.get('LocationConstraint') or 'us-east-1'
            except ClientError:
                pass
            
            try:
                # Check encryption
                s3.get_bucket_encryption(Bucket=name)
            except ClientError as e:
                if 'ServerSideEncryptionConfigurationNotFoundError' in str(e):
                    issues.append('No default encryption')
                    status = 'warning'
            
            try:
                # Check public access block
                pab = s3.get_public_access_block(Bucket=name)
                config = pab.get('PublicAccessBlockConfiguration', {})
                if not all([
                    config.get('BlockPublicAcls'),
                    config.get('IgnorePublicAcls'),
                    config.get('BlockPublicPolicy'),
                    config.get('RestrictPublicBuckets')
                ]):
                    issues.append('Public access not fully blocked')
                    status = 'non-compliant' if status == 'warning' else 'warning'
            except ClientError:
                issues.append('No public access block configured')
                status = 'non-compliant'
            
            try:
                # Check versioning
                ver = s3.get_bucket_versioning(Bucket=name)
                if ver.get('Status') != 'Enabled':
                    issues.append('Versioning not enabled')
            except ClientError:
                pass
            
            buckets.append({
                'id': name,
                'name': name,
                'status': status,
                'issues': len(issues),
                'issueDetails': issues,
                'region': region,
                'created': created
            })
    except ClientError as e:
        print(f"Error listing S3 buckets: {e}")
    
    return buckets


def get_ec2_inventory():
    """Get all EC2 instances with compliance status."""
    ec2 = boto3.client('ec2')
    instances = []
    
    try:
        response = ec2.describe_instances()
        for reservation in response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                instance_id = instance['InstanceId']
                state = instance['State']['Name']
                
                # Skip terminated instances
                if state == 'terminated':
                    continue
                
                # Get name tag
                name = instance_id
                for tag in instance.get('Tags', []):
                    if tag['Key'] == 'Name':
                        name = tag['Value']
                        break
                
                instance_type = instance.get('InstanceType', 'unknown')
                
                # Check compliance
                issues = []
                status = 'compliant'
                
                # Check if instance has IAM role
                if not instance.get('IamInstanceProfile'):
                    issues.append('No IAM instance profile')
                    status = 'warning'
                
                # Check if instance is in a VPC
                if not instance.get('VpcId'):
                    issues.append('Not in a VPC')
                    status = 'non-compliant'
                
                # Check if monitoring is enabled
                if instance.get('Monitoring', {}).get('State') != 'enabled':
                    issues.append('Detailed monitoring not enabled')
                
                # Check for public IP (potential issue)
                if instance.get('PublicIpAddress'):
                    issues.append('Has public IP address')
                    if status == 'compliant':
                        status = 'warning'
                
                instances.append({
                    'id': instance_id,
                    'name': name,
                    'status': status,
                    'issues': len(issues),
                    'issueDetails': issues,
                    'type': instance_type,
                    'state': state
                })
    except ClientError as e:
        print(f"Error listing EC2 instances: {e}")
    
    return instances


def get_iam_inventory():
    """Get IAM users and roles with compliance status."""
    iam = boto3.client('iam')
    resources = []
    
    # Get users
    try:
        users = iam.list_users().get('Users', [])
        for user in users:
            username = user['UserName']
            issues = []
            status = 'compliant'
            
            # Check MFA
            try:
                mfa = iam.list_mfa_devices(UserName=username)
                if not mfa.get('MFADevices'):
                    issues.append('MFA not enabled')
                    status = 'warning'
            except ClientError:
                pass
            
            # Check access keys age
            try:
                keys = iam.list_access_keys(UserName=username)
                for key in keys.get('AccessKeyMetadata', []):
                    age = (datetime.now(key['CreateDate'].tzinfo) - key['CreateDate']).days
                    if age > 90:
                        issues.append(f'Access key older than 90 days ({age} days)')
                        status = 'non-compliant' if status == 'warning' else 'warning'
            except ClientError:
                pass
            
            # Check for console access without MFA
            try:
                iam.get_login_profile(UserName=username)
                if 'MFA not enabled' in issues:
                    issues.append('Console access without MFA')
                    status = 'non-compliant'
            except ClientError:
                pass  # No console access
            
            resources.append({
                'id': username,
                'name': username,
                'status': status,
                'issues': len(issues),
                'issueDetails': issues,
                'type': 'User',
                'arn': user['Arn']
            })
    except ClientError as e:
        print(f"Error listing IAM users: {e}")
    
    # Get roles (limit to custom roles, skip AWS service roles)
    try:
        roles = iam.list_roles().get('Roles', [])
        for role in roles:
            role_name = role['RoleName']
            
            # Skip AWS service-linked roles
            if role_name.startswith('AWSServiceRole') or '/aws-service-role/' in role.get('Path', ''):
                continue
            
            issues = []
            status = 'compliant'
            
            # Check if role has overly permissive policies
            try:
                attached = iam.list_attached_role_policies(RoleName=role_name)
                for policy in attached.get('AttachedPolicies', []):
                    if policy['PolicyName'] in ['AdministratorAccess', 'PowerUserAccess']:
                        issues.append(f'Has {policy["PolicyName"]} attached')
                        status = 'warning'
            except ClientError:
                pass
            
            resources.append({
                'id': role_name,
                'name': role_name,
                'status': status,
                'issues': len(issues),
                'issueDetails': issues,
                'type': 'Role',
                'arn': role['Arn']
            })
    except ClientError as e:
        print(f"Error listing IAM roles: {e}")
    
    return resources


def get_rds_inventory():
    """Get RDS instances with compliance status."""
    rds = boto3.client('rds')
    databases = []
    
    try:
        response = rds.describe_db_instances()
        for db in response.get('DBInstances', []):
            db_id = db['DBInstanceIdentifier']
            issues = []
            status = 'compliant'
            
            # Check encryption
            if not db.get('StorageEncrypted'):
                issues.append('Storage not encrypted')
                status = 'non-compliant'
            
            # Check public accessibility
            if db.get('PubliclyAccessible'):
                issues.append('Publicly accessible')
                status = 'non-compliant' if status != 'non-compliant' else status
            
            # Check multi-AZ
            if not db.get('MultiAZ'):
                issues.append('Multi-AZ not enabled')
                if status == 'compliant':
                    status = 'warning'
            
            # Check backup retention
            if db.get('BackupRetentionPeriod', 0) < 7:
                issues.append('Backup retention less than 7 days')
                if status == 'compliant':
                    status = 'warning'
            
            # Check deletion protection
            if not db.get('DeletionProtection'):
                issues.append('Deletion protection not enabled')
            
            databases.append({
                'id': db_id,
                'name': db_id,
                'status': status,
                'issues': len(issues),
                'issueDetails': issues,
                'engine': db.get('Engine', 'unknown'),
                'engineVersion': db.get('EngineVersion', ''),
                'instanceClass': db.get('DBInstanceClass', '')
            })
    except ClientError as e:
        print(f"Error listing RDS instances: {e}")
    
    return databases


def lambda_handler(event, context):
    """Main Lambda handler for inventory."""
    
    # Handle API Gateway requests
    if event.get("httpMethod"):
        query_params = event.get("queryStringParameters") or {}
        resource_type = query_params.get("type", "all")
    else:
        resource_type = event.get("type", "all")
    
    result = {
        "status": "SUCCESS",
        "timestamp": datetime.now().isoformat()
    }
    
    if resource_type == "all" or resource_type == "s3":
        result["s3"] = get_s3_inventory()
    
    if resource_type == "all" or resource_type == "ec2":
        result["ec2"] = get_ec2_inventory()
    
    if resource_type == "all" or resource_type == "iam":
        result["iam"] = get_iam_inventory()
    
    if resource_type == "all" or resource_type == "rds":
        result["rds"] = get_rds_inventory()
    
    # Calculate totals
    all_resources = []
    for key in ["s3", "ec2", "iam", "rds"]:
        if key in result:
            all_resources.extend(result[key])
    
    result["summary"] = {
        "total": len(all_resources),
        "compliant": len([r for r in all_resources if r["status"] == "compliant"]),
        "warning": len([r for r in all_resources if r["status"] == "warning"]),
        "non_compliant": len([r for r in all_resources if r["status"] == "non-compliant"])
    }
    
    # API Gateway response format
    if event.get("httpMethod"):
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
    
    return result


if __name__ == "__main__":
    # Test locally
    result = lambda_handler({}, None)
    print(json.dumps(result, indent=2, default=str))
