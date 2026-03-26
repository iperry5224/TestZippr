import boto3
import datetime
from botocore.exceptions import ClientError

# --- Configuration ---
MAX_KEY_AGE_DAYS = 90
SENSITIVE_PORTS = [22, 3389, 3306, 5432, 1433]

def get_color(color_code):
    return f"\033[{color_code}m"

RESET = get_color("0")
RED = get_color("31")
GREEN = get_color("32")
YELLOW = get_color("33")

def print_status(check_name, status, message):
    if status == "PASS":
        print(f"[{GREEN}PASS{RESET}] {check_name}: {message}")
    elif status == "FAIL":
        print(f"[{RED}FAIL{RESET}] {check_name}: {message}")
    elif status == "WARN":
        print(f"[{YELLOW}WARN{RESET}] {check_name}: {message}")

def check_root_mfa():
    iam = boto3.client('iam')
    try:
        summary = iam.get_account_summary()
        # AccountMFAEnabled checks the Root account specifically
        if summary['SummaryMap']['AccountMFAEnabled'] == 1:
            print_status("Root MFA", "PASS", "MFA is enabled on the Root account.")
        else:
            print_status("Root MFA", "FAIL", "Root account does NOT have MFA enabled!")
    except ClientError as e:
        print_status("Root MFA", "WARN", f"Could not check Root MFA: {e}")

def check_open_security_groups():
    ec2 = boto3.client('ec2')
    try:
        sgs = ec2.describe_security_groups()
        open_groups = []
        
        for sg in sgs['SecurityGroups']:
            for perm in sg['IpPermissions']:
                # Check for 0.0.0.0/0 (Global Access)
                is_public = False
                for range_item in perm.get('IpRanges', []):
                    if range_item.get('CidrIp') == '0.0.0.0/0':
                        is_public = True
                        break
                
                if is_public:
                    from_port = perm.get('FromPort', -1)
                    to_port = perm.get('ToPort', -1)
                    
                    # Check if sensitive ports are exposed
                    if from_port in SENSITIVE_PORTS or to_port in SENSITIVE_PORTS or (from_port == -1 and to_port == -1):
                        open_groups.append(f"{sg['GroupName']} ({sg['GroupId']}) -> Port {from_port}")

        if open_groups:
            print_status("Firewall", "FAIL", f"Found {len(open_groups)} Security Groups open to the world on sensitive ports:")
            for group in open_groups:
                print(f"    - {group}")
        else:
            print_status("Firewall", "PASS", "No sensitive ports (22, 3389, DBs) open to 0.0.0.0/0 found.")
            
    except ClientError as e:
        print_status("Firewall", "WARN", f"Could not check Security Groups: {e}")

def check_s3_public_access():
    s3 = boto3.client('s3')
    try:
        buckets = s3.list_buckets()
        public_buckets = []
        
        for bucket in buckets['Buckets']:
            b_name = bucket['Name']
            try:
                # Check Public Access Block
                pab = s3.get_public_access_block(Bucket=b_name)
                conf = pab['PublicAccessBlockConfiguration']
                if not (conf['BlockPublicAcls'] and conf['IgnorePublicAcls'] and conf['BlockPublicPolicy'] and conf['RestrictPublicBuckets']):
                   public_buckets.append(f"{b_name} (Block Access settings are not fully enabled)")
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
                    public_buckets.append(f"{b_name} (No Block Public Access configuration found)")
        
        if public_buckets:
            print_status("S3 Storage", "WARN", f"Found {len(public_buckets)} buckets with potential public access risks:")
            for b in public_buckets[:5]: # Limit output to 5
                print(f"    - {b}")
            if len(public_buckets) > 5: print(f"    - ... and {len(public_buckets)-5} more.")
        else:
            print_status("S3 Storage", "PASS", "All buckets have 'Block Public Access' configured.")

    except ClientError as e:
        print_status("S3 Storage", "WARN", f"Could not list buckets: {e}")

def check_cloudtrail():
    ct = boto3.client('cloudtrail')
    try:
        trails = ct.describe_trails()
        if not trails['trailList']:
            print_status("Logging", "FAIL", "No CloudTrails found! Audit logging is disabled.")
        else:
            active_trails = [t for t in trails['trailList'] if t.get('IsMultiRegionTrail')]
            if active_trails:
                print_status("Logging", "PASS", f"Multi-region CloudTrail is enabled: {active_trails[0]['Name']}")
            else:
                print_status("Logging", "WARN", "CloudTrail exists but Multi-Region logging might be disabled.")
    except ClientError as e:
        print_status("Logging", "WARN", f"Could not check CloudTrail: {e}")

def check_old_access_keys():
    iam = boto3.client('iam')
    try:
        users = iam.list_users()
        old_keys = []
        now = datetime.datetime.now(datetime.timezone.utc)
        
        for user in users['Users']:
            paginator = iam.get_paginator('list_access_keys')
            for response in paginator.paginate(UserName=user['UserName']):
                for key in response['AccessKeyMetadata']:
                    if key['Status'] == 'Active':
                        age = (now - key['CreateDate']).days
                        if age > MAX_KEY_AGE_DAYS:
                            old_keys.append(f"User: {user['UserName']} (Age: {age} days)")

        if old_keys:
            print_status("IAM Keys", "FAIL", f"Found {len(old_keys)} active keys older than {MAX_KEY_AGE_DAYS} days:")
            for k in old_keys:
                print(f"    - {k}")
        else:
            print_status("IAM Keys", "PASS", "No old access keys found.")

    except ClientError as e:
         print_status("IAM Keys", "WARN", f"Could not check IAM keys: {e}")

if __name__ == "__main__":
    print(f"--- Starting Security Audit for AWS Account ---")
    check_root_mfa()
    check_cloudtrail()
    check_open_security_groups()
    check_s3_public_access()
    check_old_access_keys()
    print(f"--- Audit Complete ---")