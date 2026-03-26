"""
Upload all project files to S3 bucket for backup/storage.
"""
import boto3
import os
from pathlib import Path
from datetime import datetime

S3_BUCKET = "saegrctest1"
S3_PREFIX = "security-tools/"
PROJECT_DIR = "/mnt/c/Users/iperr/TestZippr"

# File extensions to upload
UPLOAD_EXTENSIONS = {'.py', '.sh', '.txt', '.json', '.md', '.csv'}

# Files/folders to skip
SKIP_PATTERNS = {'__pycache__', 'security-venv', 'venv', '.git', 'node_modules', 'c'}

def upload_files():
    s3 = boto3.client('s3')
    uploaded = []
    skipped = []
    
    print(f"🚀 Uploading project files to s3://{S3_BUCKET}/{S3_PREFIX}")
    print("=" * 60)
    
    for root, dirs, files in os.walk(PROJECT_DIR):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in SKIP_PATTERNS]
        
        for filename in files:
            filepath = os.path.join(root, filename)
            ext = os.path.splitext(filename)[1].lower()
            
            # Only upload certain file types
            if ext not in UPLOAD_EXTENSIONS:
                skipped.append(filename)
                continue
            
            # Calculate relative path for S3 key
            rel_path = os.path.relpath(filepath, PROJECT_DIR)
            s3_key = f"{S3_PREFIX}{rel_path}"
            
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
                            'source': 'TestZippr-project'
                        }
                    )
                print(f"  ✅ {rel_path}")
                uploaded.append(rel_path)
            except Exception as e:
                print(f"  ❌ {rel_path}: {e}")
    
    print("=" * 60)
    print(f"\n📊 Summary:")
    print(f"  ✅ Uploaded: {len(uploaded)} files")
    print(f"  ⏭️ Skipped: {len(skipped)} files (non-matching extensions)")
    print(f"\n📦 Files available at: s3://{S3_BUCKET}/{S3_PREFIX}")
    
    # List what was uploaded
    print(f"\n📁 Uploaded files:")
    for f in sorted(uploaded):
        print(f"    - {f}")

if __name__ == "__main__":
    upload_files()

