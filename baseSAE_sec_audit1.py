import boto3
import datetime
from botocore.exceptions import ClientError
from dateutil.tz import tzutc

# Initialize Clients
session = boto3.Session()
iam = session.client('iam')
ec2 = session.client('ec2')
rds = session.client('rds')
s3 = session.client('s3')
cloudtrail = session.client('cloudtrail')

def check_1_root_mfa():
    """Check if Root Account has MFA enabled."""
    print("\n--- 1. Root Account MFA Status ---")
    summary = iam.get_account_summary()
    if summary['SummaryMap']['AccountMFAEnabled'] == 1:
        print("PASS: Root MFA is enabled.")
    else:
        print("FAIL: Root MFA is NOT enabled.")

def check_2_open_ssh():
    """Find Security Groups with Port 22 Open to 0.0.0.0/0."""
    print("\n--- 2. Open SSH Ports (0.0.0.0/0) ---")
    sgs = ec2.describe_security_groups()['SecurityGroups']
    open_sgs = []
    
    for sg in sgs:
        for perm in sg['IpPermissions']:
            if perm.get('FromPort') == 22:
                for ip_range in perm.get('IpRanges', []):
                    if ip_range.get('CidrIp') == '0.0.0.0/0':
                        open_sgs.append(sg['GroupId'])
    
    if open_sgs:
        print(f"FAIL: Found Security Groups with open SSH: {open_sgs}")
    else:
        print("PASS: No Security Groups have SSH open to the world.")

def check_3_unencrypted_ebs():
    """List Unencrypted EBS Volumes."""
    print("\n--- 3. Unencrypted EBS Volumes ---")
    volumes = ec2.describe_volumes(Filters=[{'Name': 'encrypted', 'Values': ['false']}])['Volumes']
    
    if volumes:
        ids = [v['VolumeId'] for v in volumes]
        print(f"FAIL: Found unencrypted volumes: {ids}")
    else:
        print("PASS: All volumes are encrypted.")

def check_4_public_rds():
    """Check for Publicly Accessible RDS Instances."""
    print("\n--- 4. Publicly Accessible RDS Instances ---")
    dbs = rds.describe_db_instances()['DBInstances']
    public_dbs = [db['DBInstanceIdentifier'] for db in dbs if db['PubliclyAccessible']]
    
    if public_dbs:
        print(f"FAIL: Found public RDS instances: {public_dbs}")
    else:
        print("PASS: No public RDS instances found.")

def check_5_cloudtrail_enabled():
    """Verify Multi-Region CloudTrail is enabled."""
    print("\n--- 5. CloudTrail Multi-Region Check ---")
    trails = cloudtrail.describe_trails()['trailList']
    multi_region_trails = [t['Name'] for t in trails if t.get('IsMultiRegionTrail')]
    
    if multi_region_trails:
        print(f"PASS: Multi-region CloudTrail found: {multi_region_trails}")
    else:
        print("FAIL: No multi-region CloudTrail enabled.")

def check_6_iam_users_mfa():
    """Find IAM Users without MFA."""
    print("\n--- 6. IAM Users Without MFA ---")
    # Note: For large accounts, generate_credential_report is more efficient.
    # This iterative method is used here for script simplicity.
    users = iam.list_users()['Users']
    no_mfa_users = []
    
    for user in users:
        mfa = iam.list_mfa_devices(UserName=user['UserName'])['MFADevices']
        if not mfa:
            no_mfa_users.append(user['UserName'])
            
    if no_mfa_users:
        print(f"FAIL: Users without MFA: {no_mfa_users}")
    else:
        print("PASS: All users have MFA enabled.")

def check_7_s3_block_public_access():
    """Check S3 Buckets for Public Access Blocks."""
    print("\n--- 7. S3 Block Public Access ---")
    buckets = s3.list_buckets()['Buckets']
    
    for bucket in buckets:
        name = bucket['Name']
        try:
            response = s3.get_public_access_block(Bucket=name)
            conf = response['PublicAccessBlockConfiguration']
            if not all([conf['BlockPublicAcls'], conf['IgnorePublicAcls'], 
                        conf['BlockPublicPolicy'], conf['RestrictPublicBuckets']]):
                print(f"WARNING: Bucket '{name}' has partial Block Public Access settings.")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
                print(f"FAIL: Bucket '{name}' has NO Block Public Access configuration.")

def check_8_password_policy():
    """Check IAM Password Policy Strength."""
    print("\n--- 8. IAM Password Policy ---")
    try:
        policy = iam.get_account_password_policy()['PasswordPolicy']
        length = policy.get('MinimumPasswordLength', 0)
        symbols = policy.get('RequireSymbols', False)
        
        if length >= 14 and symbols:
            print(f"PASS: Strong policy (Length: {length}, Symbols: {symbols})")
        else:
            print(f"FAIL: Weak policy (Length: {length}, Symbols: {symbols})")
    except ClientError:
        print("FAIL: No Password Policy set.")

def check_9_old_access_keys():
    """List Access Keys Older Than 90 Days."""
    print("\n--- 9. Old Access Keys (>90 Days) ---")
    users = iam.list_users()['Users']
    now = datetime.datetime.now(tzutc())
    
    for user in users:
        keys = iam.list_access_keys(UserName=user['UserName'])['AccessKeyMetadata']
        for key in keys:
            if key['Status'] == 'Active':
                age = (now - key['CreateDate']).days
                if age > 90:
                    print(f"FAIL: User {user['UserName']} has active key {key['AccessKeyId']} aged {age} days.")

def check_10_unused_credentials():
    """Identify IAM Users inactive for >90 days."""
    print("\n--- 10. Unused IAM Users (>90 Days) ---")
    users = iam.list_users()['Users']
    now = datetime.datetime.now(tzutc())
    
    for user in users:
        last_used = user.get('PasswordLastUsed')
        if last_used:
            days_inactive = (now - last_used).days
            if days_inactive > 90:
                print(f"WARNING: User {user['UserName']} inactive for {days_inactive} days.")
        else:
            print(f"NOTE: User {user['UserName']} has never logged in (console).")

if __name__ == "__main__":
    print("Starting AWS Security Audit...\n")
    check_1_root_mfa()
    check_2_open_ssh()
    check_3_unencrypted_ebs()
    check_4_public_rds()
    check_5_cloudtrail_enabled()
    check_6_iam_users_mfa()
    check_7_s3_block_public_access()
    check_8_password_policy()
    check_9_old_access_keys()
    check_10_unused_credentials()
    print("\nAudit Complete.")