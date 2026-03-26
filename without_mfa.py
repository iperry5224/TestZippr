import boto3
import time
import csv
import io

def check_mfa_status():
    client = boto3.client('iam')
    
    print("--- Generating Credential Report ---")
    
    # Step 1: Request the report generation
    # We loop because it might take a few seconds to generate
    while True:
        response = client.generate_credential_report()
        if response['State'] == 'COMPLETE':
            break
        print("Waiting for report to generate...")
        time.sleep(2)

    # Step 2: Get the report
    response = client.get_credential_report()
    
    # The content comes as bytes, so we decode it to a string
    content = response['Content'].decode('utf-8')
    
    # Step 3: Parse the CSV (Replicating 'cut -d, -f1,4,8')
    # The AWS report columns are usually:
    # Index 0: user
    # Index 3: password_enabled (Col 4 in bash 'cut' is index 3 in Python)
    # Index 7: mfa_active      (Col 8 in bash 'cut' is index 7 in Python)
    
    csv_reader = csv.reader(io.StringIO(content))
    
    print(f"{'USER':<30} | {'PASSWORD?':<10} | {'MFA ACTIVE?'}")
    print("-" * 60)
    
    for row in csv_reader:
        # Skip the header row if you want, or print it
        if row[0] == '<root_account>':
            user = "ROOT ACCOUNT"
        else:
            user = row[0]
            
        password_enabled = row[3]
        mfa_active = row[7]
        
        print(f"{user:<30} | {password_enabled:<10} | {mfa_active}")

if __name__ == "__main__":
    check_mfa_status()