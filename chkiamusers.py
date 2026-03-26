import boto3
import csv
from botocore.exceptions import ClientError

def get_user_groups(iam_client, username):
    """
    Fetches the groups for a specific user.
    """
    try:
        # Get groups for the user (handles pagination if user is in >100 groups)
        paginator = iam_client.get_paginator('list_groups_for_user')
        groups = []
        for page in paginator.paginate(UserName=username):
            for group in page['Groups']:
                groups.append(group['GroupName'])
        return groups
    except ClientError as e:
        print(f"    [!] Could not get groups for {username}: {e}")
        return []

def audit_iam_users():
    iam = boto3.client('iam')
    
    # Paginator for list_users ensures we get everyone (even if >100 users)
    paginator = iam.get_paginator('list_users')
    
    user_report = []
    
    print(f"{'USER NAME':<25} | {'GROUPS'}")
    print("-" * 60)
    
    try:
        for page in paginator.paginate():
            for user in page['Users']:
                username = user['UserName']
                arn = user['Arn']
                created = user['CreateDate'].strftime("%Y-%m-%d")
                
                # Fetch groups for this specific user
                group_list = get_user_groups(iam, username)
                groups_str = ", ".join(group_list) if group_list else "[No Groups]"
                
                # Print to console for immediate feedback
                print(f"{username:<25} | {groups_str}")
                
                # Add to list for CSV export
                user_report.append({
                    'UserName': username,
                    'Groups': groups_str,
                    'Created': created,
                    'Arn': arn
                })
                
    except ClientError as e:
        print(f"CRITICAL ERROR: {e}")
        return []

    return user_report

def save_to_csv(data, filename="aws_user_audit.csv"):
    if not data:
        print("\nNo data found to save.")
        return

    # Extract headers dynamically
    headers = data[0].keys()
    
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"\n[+] Audit saved to '{filename}'")

if __name__ == "__main__":
    print("--- Starting AWS IAM User & Group Audit ---\n")
    results = audit_iam_users()
    save_to_csv(results)