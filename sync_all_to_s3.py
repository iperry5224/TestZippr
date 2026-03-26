"""
Sync ALL security scripts from all project folders to S3.
Checks both TestZippr and my-newaws-app folders.
"""
import boto3
import os
from datetime import datetime
from botocore.exceptions import ClientError

S3_BUCKET = "saegrctest1"
S3_PREFIX = "security-tools/"

# All directories to scan for scripts
PROJECT_DIRS = [
    "/mnt/c/Users/iperr/TestZippr",
    "/mnt/c/Users/iperr/my-newaws-app"
]

# File extensions to upload
UPLOAD_EXTENSIONS = {'.py', '.sh', '.txt', '.json', '.md', '.csv'}

# Files/folders to skip
SKIP_PATTERNS = {'__pycache__', 'security-venv', 'venv', '.git', 'node_modules', 'c'}


def get_existing_s3_files():
    """Get list of files already in S3."""
    s3 = boto3.client('s3')
    existing = set()
    
    try:
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=S3_PREFIX):
            for obj in page.get('Contents', []):
                # Get just the filename
                filename = obj['Key'].split('/')[-1]
                existing.add(filename)
    except ClientError:
        pass
    
    return existing


def sync_to_s3():
    s3 = boto3.client('s3')
    existing_files = get_existing_s3_files()
    
    uploaded = []
    already_exists = []
    skipped = []
    
    print("🔄 Syncing ALL security scripts to S3")
    print("=" * 60)
    print(f"📦 Target: s3://{S3_BUCKET}/{S3_PREFIX}")
    print(f"📁 Scanning directories:")
    for d in PROJECT_DIRS:
        print(f"   - {d}")
    print("=" * 60)
    
    # Track files we've seen to avoid duplicates
    seen_files = set()
    
    for project_dir in PROJECT_DIRS:
        if not os.path.exists(project_dir):
            print(f"\n⚠️ Directory not found: {project_dir}")
            continue
        
        print(f"\n📂 Scanning: {project_dir}")
        
        for root, dirs, files in os.walk(project_dir):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in SKIP_PATTERNS]
            
            for filename in files:
                filepath = os.path.join(root, filename)
                ext = os.path.splitext(filename)[1].lower()
                
                # Only upload certain file types
                if ext not in UPLOAD_EXTENSIONS:
                    continue
                
                # Skip if we've already processed this filename
                if filename in seen_files:
                    continue
                seen_files.add(filename)
                
                s3_key = f"{S3_PREFIX}{filename}"
                
                # Check if already in S3
                if filename in existing_files:
                    already_exists.append(filename)
                    print(f"   ⏭️ Already in S3: {filename}")
                    continue
                
                # Determine content type
                content_types = {
                    '.py': 'text/x-python',
                    '.sh': 'text/x-shellscript',
                    '.txt': 'text/plain',
                    '.json': 'application/json',
                    '.md': 'text/markdown',
                    '.csv': 'text/csv'
                }
                content_type = content_types.get(ext, 'application/octet-stream')
                
                try:
                    with open(filepath, 'rb') as f:
                        s3.put_object(
                            Bucket=S3_BUCKET,
                            Key=s3_key,
                            Body=f.read(),
                            ContentType=content_type,
                            Metadata={
                                'uploaded-at': datetime.now().isoformat(),
                                'source-dir': os.path.basename(project_dir)
                            }
                        )
                    print(f"   ✅ Uploaded: {filename}")
                    uploaded.append(filename)
                except Exception as e:
                    print(f"   ❌ Failed: {filename} - {e}")
    
    print("\n" + "=" * 60)
    print("📊 SYNC SUMMARY")
    print("=" * 60)
    print(f"  ✅ Newly uploaded:    {len(uploaded)} files")
    print(f"  ⏭️ Already in S3:     {len(already_exists)} files")
    print(f"  📁 Total in S3:       {len(uploaded) + len(already_exists)} files")
    
    if uploaded:
        print(f"\n🆕 Newly uploaded files:")
        for f in sorted(uploaded):
            print(f"    + {f}")
    
    print(f"\n📦 All files available at: s3://{S3_BUCKET}/{S3_PREFIX}")
    
    # List all files now in S3
    print("\n📋 Complete S3 inventory:")
    all_files = get_existing_s3_files()
    for f in sorted(all_files):
        print(f"    - {f}")


if __name__ == "__main__":
    sync_to_s3()

