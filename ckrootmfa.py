import boto3
from botocore.exceptions import ClientError

def check_root_mfa():
    try:
        # Create an IAM client
        iam_client = boto3.client('iam')

        # Get the account summary
        # This API call returns a summary of the account's IAM usage, 
        # including a specific key 'AccountMFAEnabled' which refers to the ROOT account.
        response = iam_client.get_account_summary()
        
        # Access the SummaryMap dictionary
        summary_map = response.get('SummaryMap', {})
        
        # Check the 'AccountMFAEnabled' key
        # AWS returns 1 if enabled, 0 if disabled
        is_mfa_enabled = summary_map.get('AccountMFAEnabled', 0)

        if is_mfa_enabled == 1:
            print("✅ PASS: MFA is ENABLED for the root account.")
            return True
        else:
            print("❌ FAIL: MFA is NOT enabled for the root account.")
            return False

    except ClientError as e:
        print(f"Error checking MFA status: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

if __name__ == "__main__":
    check_root_mfa()