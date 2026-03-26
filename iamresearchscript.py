import boto3
import datetime

def get_user_access_details(iam_client, username):
    """
    Fetches the Groups and Attached Policies (Access "Roles") for a user.
    """
    access_info = []

    # 1. Get Groups (often used as roles, e.g., "AdminGroup")
    try:
        group_paginator = iam_client.get_paginator('list_groups_for_user')
        for page in group_paginator.paginate(UserName=username):
            for group in page['Groups']:
                access_info.append(f"Group: {group['GroupName']}")
    except Exception as e:
        access_info.append(f"Error fetching groups: {e}")

    # 2. Get Attached Policies (e.g., "AdministratorAccess")
    try:
        policy_paginator = iam_client.get_paginator('list_attached_user_policies')
        for page in policy_paginator.paginate(UserName=username):
            for policy in page['AttachedPolicies']:
                access_info.append(f"Policy: {policy['PolicyName']}")
    except Exception as e:
        access_info.append(f"Error fetching policies: {e}")

    return access_info if access_info else ["No Groups or Policies Attached"]

def audit_users_to_file():
    # Initialize the IAM client
    iam = boto3.client('iam')
    output_file = 'IAM-users.txt'
    
    print(f"--- Starting Scan ---")
    print(f"Target Output File: {output_file}\n")

    try:
        # Use paginator to handle accounts with many users
        paginator = iam.get_paginator('list_users')
        
        with open(output_file, 'w') as f:
            # Write a header to the file
            f.write(f"{'USER NAME':<25} | {'CREATED':<12} | {'ACCESS (ROLES/GROUPS/POLICIES)'}\n")
            f.write(f"{'ARN'}\n")
            f.write("-" * 80 + "\n")

            user_count = 0

            for page in paginator.paginate():
                for user in page['Users']:
                    user_count += 1
                    name = user['UserName']
                    arn = user['Arn']
                    created_date = user['CreateDate'].strftime("%Y-%m-%d")
                    
                    # Print progress to terminal
                    print(f"[{user_count}] Processing user: {name}...")

                    # Fetch the "Role" information (Groups/Policies)
                    access_list = get_user_access_details(iam, name)
                    access_str = ", ".join(access_list)

                    # Write detailed block to text file
                    f.write(f"User: {name}\n")
                    f.write(f"Created: {created_date}\n")
                    f.write(f"ARN: {arn}\n")
                    f.write(f"Assigned Access: {access_str}\n")
                    f.write("-" * 40 + "\n")
        
        print(f"\n--- Success! ---")
        print(f"Scanned {user_count} users.")
        print(f"Details saved to local file: {output_file}")

    except Exception as e:
        print(f"\n[!] Critical Error: {e}")

if __name__ == "__main__":
    audit_users_to_file()