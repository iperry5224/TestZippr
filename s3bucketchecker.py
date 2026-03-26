import boto3
from botocore.exceptions import ClientError

def check_s3_encryption():
    # Create an S3 client
    s3 = boto3.client('s3')

    print("--- Starting S3 Encryption Audit ---\n")

    try:
        # List all buckets
        response = s3.list_buckets()
        buckets = response['Buckets']
        
        if not buckets:
            print("No buckets found in this account.")
            return

        for bucket in buckets:
            bucket_name = bucket['Name']
            
            try:
                # Get encryption configuration
                enc = s3.get_bucket_encryption(Bucket=bucket_name)
                rules = enc['ServerSideEncryptionConfiguration']['Rules']
                
                # Extract the type of encryption (e.g., AES256 or aws:kms)
                encryption_type = rules[0]['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']
                kms_key = rules[0]['ApplyServerSideEncryptionByDefault'].get('KMSMasterKeyID', 'N/A')
                
                print(f"✅ [ENCRYPTED] Bucket: {bucket_name}")
                print(f"   Type: {encryption_type}")
                if kms_key != 'N/A':
                    print(f"   KMS Key ID: {kms_key}")

            except ClientError as e:
                error_code = e.response['Error']['Code']
                
                # If the error code is ServerSideEncryptionConfigurationNotFoundError, it means no default encryption is set
                if error_code == 'ServerSideEncryptionConfigurationNotFoundError':
                    print(f"❌ [UNENCRYPTED] Bucket: {bucket_name}")
                    print("   Action Needed: Enable default encryption.")
                elif error_code == 'AccessDenied':
                    print(f"⚠️ [ACCESS DENIED] Bucket: {bucket_name}")
                    print("   Reason: Insufficient permissions to view configuration.")
                else:
                    print(f"⚠️ [ERROR] Bucket: {bucket_name}")
                    print(f"   Error: {e}")
            
            print("-" * 40)

    except ClientError as e:
        print(f"Fatal Error: Could not list buckets. {e}")

if __name__ == "__main__":
    check_s3_encryption()